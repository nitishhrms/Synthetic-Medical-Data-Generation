# Database Layer - PostgreSQL + Redis

Complete database infrastructure for the Clinical Trials Platform.

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      Microservices Layer            │
│  (FastAPI services)                 │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼──────┐    ┌────▼─────┐
│PostgreSQL│    │  Redis   │
│(Persistent)   │  (Cache) │
└──────────┘    └──────────┘
```

### Components

1. **PostgreSQL 15** - Primary database
   - Patient records
   - Clinical documents (JSON)
   - Vital signs (time-series)
   - Audit logs (HIPAA compliance)
   - MCP agent context

2. **Redis 7** - Cache layer
   - Query result caching
   - Session management
   - Rate limiting
   - Patient data cache (5 min TTL)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended for Development)

```bash
# From project root
docker-compose up -d postgres redis

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Access PostgreSQL
docker-compose exec postgres psql -U clinical_user -d clinical_trials

# Access Redis
docker-compose exec redis redis-cli
```

The database will be automatically initialized with the schema from `init.sql`.

### Option 2: Local PostgreSQL Installation

```bash
# Install PostgreSQL
brew install postgresql@15  # macOS
# or
sudo apt-get install postgresql-15  # Ubuntu

# Start PostgreSQL
brew services start postgresql@15

# Create database and user
psql postgres
CREATE DATABASE clinical_trials;
CREATE USER clinical_user WITH PASSWORD 'clinical_pass';
GRANT ALL PRIVILEGES ON DATABASE clinical_trials TO clinical_user;
\q

# Initialize schema
psql -U clinical_user -d clinical_trials < init.sql
```

### Option 3: AWS RDS (Production)

```bash
# Deploy with Terraform
cd ../terraform/
terraform apply

# Get connection details
terraform output database_connection_string

# Initialize schema
export DATABASE_URL=$(terraform output -raw database_connection_string)
psql $DATABASE_URL < init.sql
```

## 📊 Database Schema

### Tables

#### 1. patients
Main entity for storing patient/subject information.

```sql
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY,
    subject_number VARCHAR(50) UNIQUE,  -- e.g., "RA001-001"
    site_id VARCHAR(50),
    protocol_id VARCHAR(50),
    enrollment_date DATE,
    treatment_arm VARCHAR(100),
    demographics JSONB,
    medical_history JSONB,
    status VARCHAR(50) DEFAULT 'ENROLLED',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Example:**
```json
{
  "subject_number": "RA001-001",
  "site_id": "SITE001",
  "protocol_id": "PROTO-001",
  "enrollment_date": "2025-01-15",
  "treatment_arm": "Active",
  "demographics": {
    "age": 45,
    "gender": "F",
    "race": "Caucasian"
  }
}
```

#### 2. documents
Clinical documents stored as JSON (replaces MongoDB).

```sql
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients,
    document_type VARCHAR(50),  -- 'protocol', 'consent', 'csr'
    title VARCHAR(500),
    content JSONB,  -- Full document
    metadata JSONB,
    version INTEGER,
    created_at TIMESTAMP
);
```

#### 3. vital_signs
Time-series vitals data.

```sql
CREATE TABLE vital_signs (
    vital_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients,
    visit_date DATE,
    measurement_time TIMESTAMP,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature DECIMAL(4,1),
    data_batch JSONB
);
```

#### 4. audit_events
HIPAA-compliant audit trail.

```sql
CREATE TABLE audit_events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id UUID,
    user_id VARCHAR(100),
    action VARCHAR(50),
    payload JSONB,
    ip_address INET,
    timestamp TIMESTAMP
);
```

#### 5. mcp_context
MCP agent state and decisions.

```sql
CREATE TABLE mcp_context (
    agent_id VARCHAR(100) PRIMARY KEY,
    context_type VARCHAR(50),
    context_data JSONB,
    decisions JSONB,
    last_updated TIMESTAMP
);
```

## 🔧 Using the Database Layer

### Python Integration

```python
from database.database import db

# Initialize connection
await db.connect()

# Create patient
patient_id = await db.create_patient({
    "subject_number": "RA001-050",
    "site_id": "SITE001",
    "protocol_id": "PROTO-001",
    "enrollment_date": "2025-01-15",
    "treatment_arm": "Active",
    "demographics": {"age": 45, "gender": "F"}
})

# Get patient with cache
patient = await db.get_patient(patient_id)

# Store vitals
vital_id = await db.store_vitals(patient_id, {
    "visit_date": "2025-01-15",
    "measurement_time": "2025-01-15T10:30:00",
    "systolic_bp": 125,
    "diastolic_bp": 80,
    "heart_rate": 72,
    "temperature": 36.8
})

# Get analytics
stats = await db.get_site_analytics("SITE001")
```

### Redis Caching

```python
from database.cache import cache

# Initialize
await cache.connect()

# Cache patient data
await cache.cache_patient_data(patient_id, patient_data, ttl=300)

# Get from cache
cached = await cache.get_patient_cache(patient_id)

# Rate limiting
allowed = await cache.rate_limit_check("user123", limit=100, window=60)

# Health check
health = await cache.health_check()
```

## 📈 Performance Features

### Indexing Strategy
- **GIN indexes** on JSONB columns for fast JSON queries
- **Composite indexes** on (site_id, protocol_id)
- **Time-series indexes** on vital_signs(patient_id, measurement_time DESC)

### Caching Strategy
- Patient data: 5 minute TTL
- Query results: 5 minute TTL
- Session data: 1 hour TTL
- Rate limit counters: 60 second window

### Materialized View
```sql
-- Refreshed hourly for analytics
CREATE MATERIALIZED VIEW patient_analytics AS
SELECT
    site_id,
    protocol_id,
    COUNT(DISTINCT patient_id) as patient_count,
    AVG(days_enrolled) as avg_days_enrolled,
    COUNT(DISTINCT vital_id) as total_vitals
FROM patients LEFT JOIN vital_signs ...
GROUP BY site_id, protocol_id;
```

## 🔒 Security & Compliance

### HIPAA Compliance
- ✅ Audit logging for all patient data access
- ✅ Encryption at rest (AWS RDS)
- ✅ Encryption in transit (SSL/TLS)
- ✅ Access controls via PostgreSQL roles
- ✅ Data retention policies

### Triggers
```sql
-- Auto-update timestamp
CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Audit all changes
CREATE TRIGGER audit_patients
    AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger();
```

## 🔍 Monitoring & Debugging

### Check Database Status
```bash
# Connection count
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Table sizes
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_tables WHERE schemaname='public';"

# Recent queries
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c \
  "SELECT query, state, query_start FROM pg_stat_activity WHERE state != 'idle';"
```

### Check Redis Status
```bash
# Redis info
docker-compose exec redis redis-cli INFO

# Memory usage
docker-compose exec redis redis-cli INFO memory

# Connected clients
docker-compose exec redis redis-cli CLIENT LIST

# Monitor commands in real-time
docker-compose exec redis redis-cli MONITOR
```

### Performance Tuning
```bash
# Analyze query performance
EXPLAIN ANALYZE SELECT * FROM patients WHERE site_id = 'SITE001';

# Rebuild indexes
REINDEX TABLE patients;

# Update statistics
ANALYZE patients;
```

## 🧪 Testing

### Sample Data
```sql
-- Insert test patient
INSERT INTO patients (subject_number, site_id, protocol_id, enrollment_date, treatment_arm)
VALUES ('TEST-001', 'TEST_SITE', 'TEST_PROTO', CURRENT_DATE, 'Active');

-- Query test data
SELECT * FROM patients WHERE subject_number LIKE 'TEST%';

-- Clean up test data
DELETE FROM patients WHERE site_id = 'TEST_SITE';
```

### Load Testing
```python
# test_database_load.py
import asyncio
from database.database import db

async def load_test():
    await db.connect()

    # Create 1000 patients
    for i in range(1000):
        await db.create_patient({
            "subject_number": f"LOAD-{i:04d}",
            "site_id": "LOAD_TEST",
            "protocol_id": "LOAD_PROTO",
            "enrollment_date": "2025-01-15",
            "treatment_arm": "Active"
        })

    print("Load test complete")

asyncio.run(load_test())
```

## 📦 Backup & Restore

### Backup
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U clinical_user clinical_trials > backup.sql

# Redis backup
docker-compose exec redis redis-cli SAVE
docker-compose exec redis cat /data/dump.rdb > redis_backup.rdb
```

### Restore
```bash
# PostgreSQL restore
cat backup.sql | docker-compose exec -T postgres psql -U clinical_user -d clinical_trials

# Redis restore
docker-compose stop redis
docker-compose exec redis cat > /data/dump.rdb < redis_backup.rdb
docker-compose start redis
```

## 🐛 Troubleshooting

### Issue: "Connection refused"
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs postgres redis

# Restart services
docker-compose restart postgres redis
```

### Issue: "Out of memory" (Redis)
```bash
# Check memory usage
docker-compose exec redis redis-cli INFO memory

# Clear cache
docker-compose exec redis redis-cli FLUSHALL

# Increase max memory in docker-compose.yml
command: redis-server --maxmemory 512mb
```

### Issue: "Slow queries"
```bash
# Enable slow query log (PostgreSQL)
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c \
  "ALTER SYSTEM SET log_min_duration_statement = 1000;"  # Log queries > 1s

# Restart to apply
docker-compose restart postgres
```

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [Redis Documentation](https://redis.io/documentation)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [HIPAA Compliance Guide](https://www.hhs.gov/hipaa/index.html)

## 🔗 Related Files

- `init.sql` - Database schema
- `database.py` - Python database client
- `cache.py` - Redis cache client
- `../terraform/` - AWS infrastructure
- `../docker-compose.yml` - Local development setup
