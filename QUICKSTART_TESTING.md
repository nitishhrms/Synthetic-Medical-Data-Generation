# Quick Start - Testing the Complete System

**Complete microservices platform with PostgreSQL + Redis integration**

## Prerequisites

- Docker & Docker Compose installed
- curl or Postman for API testing
- (Optional) PostgreSQL client (psql)

## Step 1: Start All Services

```bash
# Navigate to project directory
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation

# Or from parent directory:
cd Synthetic-Medical-Data-Generation

# Start everything (database + all microservices)
docker-compose up -d

# Wait 30 seconds for all services to initialize

# Check all containers are running
docker-compose ps
```

You should see:
- ✅ clinical_postgres (PostgreSQL)
- ✅ clinical_redis (Redis)
- ✅ api-gateway (port 8000)
- ✅ security-service (port 8005)
- ✅ edc-service (port 8001)
- ✅ data-generation-service (port 8002)
- ✅ analytics-service (port 8003)
- ✅ quality-service (port 8004)

## Step 2: Verify Database Connectivity

Check that all services are connected to the database:

```bash
# Check each service health
curl http://localhost:8001/health | jq  # EDC Service
curl http://localhost:8002/health | jq  # Data Generation
curl http://localhost:8003/health | jq  # Analytics
curl http://localhost:8004/health | jq  # Quality
curl http://localhost:8005/health | jq  # Security
curl http://localhost:8000/health | jq  # API Gateway
```

**Expected output:**
```json
{
  "status": "healthy",
  "service": "edc-service",
  "timestamp": "2025-01-15T10:30:00.123456",
  "database": "connected",
  "cache": "connected"
}
```

If you see `"database": "disconnected"`, check logs:
```bash
docker-compose logs edc-service
docker-compose logs postgres
```

## Step 3: Test Data Flow (End-to-End)

### 3.1 Generate Vitals Data
```bash
curl -X POST http://localhost:8002/generate/rules \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 10,
    "target_effect": -5.0,
    "seed": 42
  }' | jq > generated_data.json
```

### 3.2 Validate the Data
```bash
# Extract records from generated data
jq '.data' generated_data.json > records.json

# Validate (returns checks and all_passed status)
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d "{\"records\": $(cat records.json)}" | jq
```

### 3.3 Store Data in Database
```bash
# Store vitals in PostgreSQL
curl -X POST http://localhost:8001/store-vitals \
  -H "Content-Type: application/json" \
  -d "{\"records\": $(cat records.json)}" | jq
```

**Expected output:**
```json
{
  "success": true,
  "records_stored": 20,
  "timestamp": "2025-01-15T10:35:00.123456"
}
```

### 3.4 Verify Data in Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U clinical_user -d clinical_trials

# In psql, run:
SELECT COUNT(*) FROM patients;
SELECT COUNT(*) FROM vital_signs;
SELECT subject_number, treatment_arm, status FROM patients LIMIT 5;

# Exit psql
\q
```

### 3.5 Run Analytics on Stored Data
```bash
# Calculate Week-12 statistics
curl -X POST http://localhost:8003/stats/week12 \
  -H "Content-Type: application/json" \
  -d "{\"vitals_data\": $(cat records.json)}" | jq
```

**Expected output:**
```json
{
  "n_active": 10,
  "n_placebo": 10,
  "mean_active": 123.5,
  "mean_placebo": 128.7,
  "diff_active_minus_placebo": -5.2,
  "p_value_two_sided": 0.023
}
```

## Step 4: Test Individual Services

### EDC Service (Port 8001)

**Validate vitals:**
```bash
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "SubjectID": "RA001-001",
        "VisitName": "Week 12",
        "TreatmentArm": "Active",
        "SystolicBP": 125,
        "DiastolicBP": 80,
        "HeartRate": 72,
        "Temperature": 36.8
      }
    ]
  }' | jq
```

**Auto-repair data:**
```bash
curl -X POST http://localhost:8001/repair \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "SubjectID": "RA001-001",
        "VisitName": "Week 12",
        "TreatmentArm": "Active",
        "SystolicBP": 95,
        "DiastolicBP": 55,
        "HeartRate": 50,
        "Temperature": 35.0
      }
    ]
  }' | jq
```

### Data Generation Service (Port 8002)

**Rules-based generation:**
```bash
curl -X POST http://localhost:8002/generate/rules \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 50, "target_effect": -5.0, "seed": 123}' | jq
```

**MVN generation:**
```bash
curl -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 50, "target_effect": -5.0, "seed": 123, "train_source": "pilot"}' | jq
```

**Oncology AE generation:**
```bash
curl -X POST http://localhost:8002/generate/ae \
  -H "Content-Type: application/json" \
  -d '{"n_subjects": 30, "seed": 7}' | jq
```

### Analytics Service (Port 8003)

**Week-12 statistics:**
```bash
curl -X POST http://localhost:8003/stats/week12 \
  -H "Content-Type: application/json" \
  -d "{\"vitals_data\": $(cat records.json)}" | jq
```

**SDTM export:**
```bash
curl -X POST http://localhost:8003/sdtm/export \
  -H "Content-Type: application/json" \
  -d "{\"vitals_data\": $(cat records.json)}" | jq '.sdtm_data | .[0:3]'
```

### Quality Service (Port 8004)

**Get default edit check rules:**
```bash
curl http://localhost:8004/checks/rules | jq
```

**Run edit checks:**
```bash
curl -X POST http://localhost:8004/checks/validate \
  -H "Content-Type: application/json" \
  -d "{\"data\": $(cat records.json)}" | jq
```

**Simulate entry noise:**
```bash
curl -X POST http://localhost:8004/quality/simulate-noise \
  -H "Content-Type: application/json" \
  -d "{\"data\": $(cat records.json), \"typo_rate\": 0.1, \"temp_unit_flip_rate\": 0.05}" | jq
```

## Step 5: Database Operations

### Check Database Size
```bash
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
  FROM pg_tables
  WHERE schemaname='public';"
```

### View Recent Audit Events
```bash
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c "
  SELECT event_type, entity_type, action, timestamp
  FROM audit_events
  ORDER BY timestamp DESC
  LIMIT 10;"
```

### Check Redis Cache
```bash
# View cache keys
docker-compose exec redis redis-cli KEYS '*'

# Get cache info
docker-compose exec redis redis-cli INFO memory

# Monitor cache in real-time (Ctrl+C to stop)
docker-compose exec redis redis-cli MONITOR
```

## Step 6: Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs edc-service

# Restart specific service
docker-compose restart edc-service

# Rebuild and restart
docker-compose up -d --build edc-service
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c "SELECT version();"
```

### Clear Database and Restart
```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Restart fresh
docker-compose up -d

# Database will be re-initialized from init.sql
```

### Check Service Dependencies
```bash
# View service dependency tree
docker-compose config

# Check which services are waiting
docker-compose ps
```

## Step 7: Performance Testing

### Load Test with Apache Bench
```bash
# Install Apache Bench (ab)
# macOS: already installed
# Ubuntu: sudo apt-get install apache2-utils

# Test EDC validation endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 -p test_payload.json -T application/json \
   http://localhost:8001/validate
```

### Monitor Database Load
```bash
# Active connections
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c "
  SELECT count(*) as connections
  FROM pg_stat_activity
  WHERE state != 'idle';"

# Slow queries (if enabled)
docker-compose exec postgres psql -U clinical_user -d clinical_trials -c "
  SELECT query, query_start, state
  FROM pg_stat_activity
  WHERE state != 'idle'
  ORDER BY query_start;"
```

## Complete Test Script

Save this as `test_all.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting complete system test..."

echo "✅ Step 1: Starting services..."
docker-compose up -d
sleep 30

echo "✅ Step 2: Checking health..."
for port in 8001 8002 8003 8004 8005 8000; do
  echo "  - Port $port: $(curl -s http://localhost:$port/health | jq -r .database)"
done

echo "✅ Step 3: Generating data..."
curl -s -X POST http://localhost:8002/generate/rules \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 10, "target_effect": -5.0, "seed": 42}' \
  | jq '.data' > /tmp/records.json

echo "✅ Step 4: Validating data..."
curl -s -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d "{\"records\": $(cat /tmp/records.json)}" \
  | jq '.all_passed'

echo "✅ Step 5: Storing in database..."
curl -s -X POST http://localhost:8001/store-vitals \
  -H "Content-Type: application/json" \
  -d "{\"records\": $(cat /tmp/records.json)}" \
  | jq '.records_stored'

echo "✅ Step 6: Running analytics..."
curl -s -X POST http://localhost:8003/stats/week12 \
  -H "Content-Type: application/json" \
  -d "{\"vitals_data\": $(cat /tmp/records.json)}" \
  | jq '{mean_active, mean_placebo, p_value: .p_value_two_sided}'

echo "✅ Step 7: Checking database..."
docker-compose exec -T postgres psql -U clinical_user -d clinical_trials \
  -c "SELECT COUNT(*) as patient_count FROM patients;" \
  -c "SELECT COUNT(*) as vitals_count FROM vital_signs;"

echo "🎉 All tests passed! System is working correctly."
```

Make it executable and run:
```bash
chmod +x test_all.sh
./test_all.sh
```

## API Documentation

Access interactive API docs:
- EDC Service: http://localhost:8001/docs
- Data Generation: http://localhost:8002/docs
- Analytics: http://localhost:8003/docs
- Quality: http://localhost:8004/docs
- Security: http://localhost:8005/docs
- API Gateway: http://localhost:8000/docs

## Next Steps

1. ✅ Run complete end-to-end test (Steps 1-5)
2. Test individual service endpoints (Step 4)
3. Explore database schema (Step 5)
4. Try performance testing (Step 7)
5. Deploy to AWS using Terraform (see `/terraform/README.md`)
6. Set up monitoring and alerting
7. Implement additional database endpoints

## Support

- Database docs: `/database/README.md`
- Integration summary: `/DATABASE_INTEGRATION_SUMMARY.md`
- Implementation status: `/IMPLEMENTATION_STATUS.md`
- AWS deployment: `/terraform/README.md`

---

**Happy testing! 🚀**
