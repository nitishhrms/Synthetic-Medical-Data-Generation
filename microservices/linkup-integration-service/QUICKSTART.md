# Linkup Integration Service - Quick Start Guide

Get the Linkup Integration Service up and running in **5 minutes**!

## 🚀 Quick Start

### Option 1: Docker Compose (Easiest)

```bash
# 1. Navigate to service directory
cd microservices/linkup-integration-service

# 2. Copy environment file
cp .env.example .env

# 3. (Optional) Add your Linkup API key to .env
# If you don't have one, the service will run in mock mode
nano .env  # or use your favorite editor

# 4. Start all services
docker-compose up -d

# 5. Check service health
curl http://localhost:8008/health

# 6. View API documentation
open http://localhost:8008/docs
```

**That's it!** The service is now running on http://localhost:8008

---

### Option 2: Local Python (For Development)

```bash
# 1. Navigate to service directory
cd microservices/linkup-integration-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export LINKUP_API_KEY=""  # Leave empty for mock mode
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/synthetic_db"

# 5. Apply database schema (if PostgreSQL is running)
psql -U postgres -d synthetic_db -f database_schema.sql

# 6. Start the service
cd src
uvicorn main:app --host 0.0.0.0 --port 8008 --reload

# 7. Service is running!
# Visit: http://localhost:8008/docs
```

---

## 🧪 Test the Service

### 1. Health Check

```bash
curl http://localhost:8008/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T22:00:00.000000",
  "service": "linkup-integration-service"
}
```

### 2. Fetch Evidence Citations

```bash
curl -X POST http://localhost:8008/evidence/fetch-citations \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "Wasserstein distance",
    "metric_value": 2.34,
    "context": "synthetic data quality validation"
  }' | jq
```

**Expected Response:**
```json
[
  {
    "metric_name": "Wasserstein distance",
    "metric_value": 2.34,
    "title": "Wasserstein Distance for Quality Assessment - FDA Guidance",
    "url": "https://www.fda.gov/regulatory-information/...",
    "snippet": "The Wasserstein distance is recommended for...",
    "domain": "fda.gov",
    "relevance_score": 0.95,
    "fetched_at": "2025-11-15T22:00:00.000000"
  }
]
```

### 3. Generate Edit Check Rule

```bash
curl -X POST http://localhost:8008/edit-checks/generate-rule \
  -H "Content-Type: application/json" \
  -d '{
    "variable": "systolic_bp",
    "indication": "hypertension",
    "severity": "Major"
  }' | jq
```

**Expected Response:**
```json
{
  "rule_yaml": "rules:\n- id: AUTO_SYSTOLIC_BP_20251115220000\n  name: Systolic Blood Pressure Clinical Range Check\n  ...",
  "rule_dict": {
    "id": "AUTO_SYSTOLIC_BP_20251115220000",
    "name": "Systolic Blood Pressure Clinical Range Check",
    "type": "range",
    "field": "systolic_bp",
    "min": 95,
    "max": 200,
    "severity": "Major",
    "evidence": [...]
  },
  "confidence": "high",
  "requires_review": true,
  "citations": [...],
  "generated_at": "2025-11-15T22:00:00.000000"
}
```

### 4. Run Compliance Scan

```bash
curl -X POST http://localhost:8008/compliance/scan | jq
```

**Expected Response:**
```json
{
  "total_updates": 12,
  "high_impact_count": 2,
  "medium_impact_count": 5,
  "low_impact_count": 5,
  "sources_scanned": 5,
  "updates": [...],
  "scan_timestamp": "2025-11-15T22:00:00.000000"
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Quality Assessment with Evidence

**Scenario:** You've generated synthetic data and want regulatory-ready quality assessment.

```bash
# Step 1: Generate synthetic data (using existing data-generation-service)
curl -X POST http://localhost:8002/generate/mvn \
  -d '{"n_per_arm": 50}' | jq > synthetic_data.json

# Step 2: Get quality assessment with evidence
curl -X POST http://localhost:8008/evidence/comprehensive-quality \
  -H "Content-Type: application/json" \
  -d '{
    "original_data": $(cat data/pilot_trial_cleaned.csv | jq -Rs .),
    "synthetic_data": $(cat synthetic_data.json | jq .data),
    "k": 5
  }' | jq
```

**Result:** You get quality metrics + FDA/ICH citations suitable for regulatory submission!

---

### Use Case 2: Auto-Generate Edit Check Rules

**Scenario:** You're setting up a new study and need edit check rules for all vitals.

```bash
# Generate rules for all vitals
curl -X POST http://localhost:8008/edit-checks/batch-generate \
  -H "Content-Type: application/json" \
  -d '{
    "variables": [
      "systolic_bp",
      "diastolic_bp",
      "heart_rate",
      "temperature"
    ],
    "indication": "hypertension"
  }' | jq > generated_rules.json

# Extract YAML rules
cat generated_rules.json | jq -r '.rules[].rule_yaml' > edit_check_rules.yaml

# Review and use the generated rules!
cat edit_check_rules.yaml
```

**Result:** You have clinical range-based edit check rules with FDA/ICH citations in minutes!

---

### Use Case 3: Monitor Regulatory Changes

**Scenario:** You want to be notified when FDA updates RBQM guidance.

```bash
# Trigger manual compliance scan
curl -X POST http://localhost:8008/compliance/scan | jq

# View recent high-impact updates
curl http://localhost:8008/compliance/recent-updates?impact_level=HIGH | jq

# Get dashboard summary
curl http://localhost:8008/compliance/dashboard-summary | jq
```

**Result:** Stay ahead of regulatory changes without manual monitoring!

---

## 🔧 Configuration Tips

### Working Without Linkup API Key

The service works in **mock mode** without an API key:

1. Leave `LINKUP_API_KEY` empty in `.env`
2. Service returns realistic sample data
3. Perfect for development and testing
4. No API costs!

### Getting a Linkup API Key

If you want real regulatory search results:

1. Visit https://linkup.so
2. Sign up for an account
3. Get your API key
4. Add to `.env`: `LINKUP_API_KEY=your_key_here`
5. Restart the service

### Database Setup

If PostgreSQL isn't running:

```bash
# Start just PostgreSQL
docker-compose up -d postgres

# Apply schema
docker exec -i linkup-postgres psql -U postgres -d synthetic_db < database_schema.sql

# Verify
docker exec -it linkup-postgres psql -U postgres -d synthetic_db -c "\dt"
```

---

## 📊 Viewing Results

### Swagger UI (Interactive API Docs)

```bash
open http://localhost:8008/docs
```

Features:
- Try out all endpoints
- See request/response schemas
- View examples
- Test authentication

### Database (PgAdmin)

```bash
# Start PgAdmin (if using docker-compose)
docker-compose up -d pgadmin

# Access at: http://localhost:5050
# Email: admin@example.com
# Password: admin
```

Add server connection:
- Host: postgres
- Port: 5432
- Database: synthetic_db
- Username: postgres
- Password: postgres

View tables:
- `quality_evidence` - Citation storage
- `auto_generated_rules` - Generated rules
- `regulatory_updates` - Compliance scan results

---

## 🐛 Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs -f linkup-integration

# Common fixes:
# 1. Port 8008 already in use
sudo lsof -i :8008
# Kill the process or change PORT in .env

# 2. Database not ready
docker-compose up -d postgres
sleep 10  # Wait for DB to be ready
docker-compose up -d linkup-integration
```

### Database connection error

```bash
# Test database connection
docker exec -it linkup-postgres psql -U postgres -c "SELECT 1"

# Apply schema
docker exec -i linkup-postgres psql -U postgres -d synthetic_db < database_schema.sql

# Restart service
docker-compose restart linkup-integration
```

### Citations not realistic

```bash
# You're in mock mode. To get real citations:
# 1. Get Linkup API key from https://linkup.so
# 2. Add to .env: LINKUP_API_KEY=your_key
# 3. Restart: docker-compose restart linkup-integration
```

---

## 📚 Next Steps

Now that the service is running:

1. **Read the Full Docs**: `README.md`
2. **Explore API**: http://localhost:8008/docs
3. **Integrate with Frontend**: See `README.md` for frontend integration guide
4. **Set Up CronJob**: For automated compliance monitoring (Kubernetes)
5. **Configure Alerts**: Add Slack webhook or email in `.env`

---

## 🆘 Need Help?

- **Documentation**: See `README.md` in this directory
- **API Docs**: http://localhost:8008/docs
- **Issues**: GitHub Issues
- **Email**: support@yourorg.com

---

## ✅ Checklist

- [ ] Service running on http://localhost:8008
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Swagger UI accessible at /docs
- [ ] Database schema applied successfully
- [ ] Evidence citations endpoint working
- [ ] Edit check generator working
- [ ] Compliance scan working
- [ ] (Optional) Linkup API key configured
- [ ] (Optional) Alerts configured (Slack/email)

---

**🎉 Congratulations!** You're all set to use AI-powered regulatory intelligence!

**Version**: 1.0.0
**Last Updated**: 2025-11-15
