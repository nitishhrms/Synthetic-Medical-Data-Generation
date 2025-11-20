# SyntheticTrialStudio Enterprise - Quick Start Guide

A comprehensive guide to run and demo the SyntheticTrialStudio Enterprise platform.

---

## Table of Contents

1. [What You're About to Run](#what-youre-about-to-run)
2. [Prerequisites](#prerequisites)
3. [Quick Setup (5 Minutes)](#quick-setup-5-minutes)
4. [Verifying Installation](#verifying-installation)
5. [Demo Walkthrough](#demo-walkthrough)
6. [API Documentation](#api-documentation)
7. [Stopping the Services](#stopping-the-services)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

---

## What You're About to Run

SyntheticTrialStudio Enterprise is a **microservices platform** for clinical trial data management that includes:

- **6 Microservices** (API Gateway, Security, EDC, Data Generation, Analytics, Quality)
- **PostgreSQL Database** for persistent storage
- **Redis Cache** for performance optimization
- **REST APIs** with interactive Swagger documentation
- **HIPAA-compliant** security features

All services run in Docker containers and communicate with each other automatically.

---

## Prerequisites

### Required Software

1. **Docker Desktop** (version 4.x or higher)
   - Windows: [Download Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
   - macOS: [Download Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
   - Linux: Install Docker Engine and Docker Compose

2. **curl** (for testing APIs)
   - Windows: Included in Windows 10/11, or use [Git Bash](https://git-scm.com/downloads)
   - macOS/Linux: Pre-installed

3. **Web Browser** (Chrome, Firefox, Edge, or Safari)

### System Requirements

- **CPU:** 2+ cores (4+ recommended)
- **RAM:** 4GB minimum (8GB+ recommended)
- **Disk:** 10GB free space
- **Ports:** 8000-8005, 5432, 6379 must be available

### Check Your Installation

```bash
# Check Docker version
docker --version
# Should show: Docker version 20.10.x or higher

# Check Docker Compose version
docker-compose --version
# Should show: Docker Compose version 2.x.x or higher

# Check curl
curl --version
# Should show curl version info
```

---

## Quick Setup (5 Minutes)

### Step 1: Navigate to Project Directory

```bash
# Navigate to the project directory
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation

# Or from the parent directory:
cd Synthetic-Medical-Data-Generation

# Verify you're in the correct directory
ls -la docker-compose.yml  # Should show the docker-compose file
```

### Step 2: Start Docker Desktop

1. Open **Docker Desktop** application
2. Wait for Docker to fully start (the Docker icon in system tray should be steady)
3. Ensure Docker Desktop shows "Engine running"

### Step 3: Start All Services

```bash
docker-compose up --build
```

**What this does:**
- Downloads necessary Docker images (first time only - may take 5-10 minutes)
- Builds all 6 microservices
- Starts PostgreSQL and Redis databases
- Initializes database schema
- Starts all microservices with health checks

**Expected output:**
```
[+] Running 8/8
 ✔ Container clinical_postgres              Started
 ✔ Container clinical_redis                 Started
 ✔ Container security-service               Started
 ✔ Container edc-service                    Started
 ✔ Container data-generation-service        Started
 ✔ Container analytics-service              Started
 ✔ Container quality-service                Started
 ✔ Container api-gateway                    Started
```

**Wait time:** 30-60 seconds for all services to become healthy.

### Step 4: Verify Services Are Running

Open a **new terminal** (keep the first one running) and run:

```bash
# Check all containers are running
docker-compose ps
```

**Expected output:**
```
NAME                        STATUS              PORTS
api-gateway                 Up (healthy)        0.0.0.0:8000->8000/tcp
clinical_postgres           Up (healthy)        0.0.0.0:5432->5432/tcp
clinical_redis              Up (healthy)        0.0.0.0:6379->6379/tcp
data-generation-service     Up (healthy)        0.0.0.0:8002->8002/tcp
analytics-service           Up (healthy)        0.0.0.0:8003->8003/tcp
edc-service                 Up (healthy)        0.0.0.0:8001->8001/tcp
quality-service             Up (healthy)        0.0.0.0:8004->8004/tcp
security-service            Up (healthy)        0.0.0.0:8005->8005/tcp
```

All services should show **"Up (healthy)"** status.

---

## Verifying Installation

### Health Check

```bash
# Test API Gateway health
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "api_gateway": "healthy",
  "security_service": "connected",
  "database": "connected",
  "cache": "connected",
  "services": {
    "edc": "healthy",
    "generation": "healthy",
    "analytics": "healthy",
    "quality": "healthy"
  }
}
```

### Check Individual Services

```bash
# Security Service
curl http://localhost:8005/health

# EDC Service
curl http://localhost:8001/health

# Data Generation Service
curl http://localhost:8002/health

# Analytics Service
curl http://localhost:8003/health

# Quality Service
curl http://localhost:8004/health
```

All should return `{"status": "healthy"}`.

### Access Web Documentation

Open your browser and navigate to:

- **API Gateway Docs:** http://localhost:8000/docs
- **Security Service Docs:** http://localhost:8005/docs
- **EDC Service Docs:** http://localhost:8001/docs

You should see interactive Swagger UI documentation.

---

## Demo Walkthrough

This section demonstrates the complete workflow: Authentication → Data Generation → Validation → Analytics.

### Demo 1: Authentication & Authorization

#### Step 1: Login to Get JWT Token

```bash
curl -X POST http://localhost:8005/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"admin\", \"password\": \"admin123\"}"
```

**Expected response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "1",
  "roles": ["admin", "data_analyst", "clinician"]
}
```

#### Step 2: Save the Token

**Windows (PowerShell):**
```powershell
$TOKEN = "your-token-from-above"
```

**macOS/Linux (Bash):**
```bash
export TOKEN="your-token-from-above"
```

**Alternative (all platforms):** Copy the token manually and use it in subsequent commands.

#### Step 3: Validate Token

```bash
# Windows (PowerShell)
curl -X POST http://localhost:8005/auth/validate `
  -H "Authorization: Bearer $TOKEN"

# macOS/Linux (Bash)
curl -X POST http://localhost:8005/auth/validate \
  -H "Authorization: Bearer $TOKEN"
```

**Expected response:**
```json
{
  "valid": true,
  "user_id": "admin",
  "roles": ["admin", "data_analyst", "clinician"],
  "expires_at": "2025-11-12T15:30:00"
}
```

#### Step 4: Get Current User Info

```bash
curl -X GET http://localhost:8005/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### Demo 2: Generate Synthetic Clinical Trial Data

#### Generate 20 Patient Records (10 Active, 10 Placebo)

```bash
curl -X POST http://localhost:8002/generate/rules \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 10,
    "target_effect": -5.0,
    "seed": 42
  }' > generated_data.json
```

**What this does:**
- Generates 20 synthetic patient records
- Active arm: Target systolic BP reduction of -5 mmHg vs Placebo
- Includes realistic vitals: BP, heart rate, temperature
- Outputs to `generated_data.json` file

**View the generated data:**
```bash
# Windows (PowerShell)
Get-Content generated_data.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# macOS/Linux
cat generated_data.json | python -m json.tool | head -50
```

**Sample output:**
```json
[
  {
    "SubjectID": "RA001-001",
    "VisitName": "Week 12",
    "TreatmentArm": "Active",
    "SystolicBP": 118,
    "DiastolicBP": 78,
    "HeartRate": 72,
    "Temperature": 36.8
  },
  ...
]
```

---

### Demo 2b: Generate AACT-Enhanced Data (Recommended)

#### Why Use AACT-Enhanced Generation?

AACT-enhanced endpoints use **real data from 557,805 clinical trials** on ClinicalTrials.gov to make synthetic data indistinguishable from real trials:

**Benefits**:
- ✅ Real baseline vitals (e.g., 152/92 mmHg for hypertension vs generic 140/85)
- ✅ Real dropout rates (e.g., 13.4% actual vs 15% estimated)
- ✅ Real adverse event patterns from actual trials
- ✅ Real demographics and visit schedules
- ✅ Real geographic distributions

#### Generate AACT-Enhanced Hypertension Trial Data

```bash
curl -X POST http://localhost:8002/generate/mvn-aact \
  -H "Content-Type: application/json" \
  -d '{
    "indication": "Hypertension",
    "phase": "Phase 3",
    "n_per_arm": 10,
    "target_effect": -5.0,
    "use_duration": true
  }' > aact_generated_data.json
```

**What makes this more realistic:**
- Baseline SBP/DBP from actual hypertension Phase 3 trials
- Real dropout rate (13.4% from AACT data)
- Visit schedules based on actual trial durations (18 months median)
- Demographics match real hypertension trial populations

**View the AACT-enhanced data:**
```bash
cat aact_generated_data.json | python -m json.tool | head -50
```

**Expected output** (notice more realistic baseline values):
```json
[
  {
    "SubjectID": "RA001-001",
    "VisitName": "Screening",
    "TreatmentArm": "Active",
    "SystolicBP": 152,    // Real hypertension baseline (not generic 140)
    "DiastolicBP": 92,    // Real hypertension baseline (not generic 85)
    "HeartRate": 74,      // From actual trial data
    "Temperature": 36.6
  },
  ...
]
```

#### Generate Complete Study with AACT

Generate all data types (Vitals, Demographics, Labs, AEs) with consistent Subject IDs:

```bash
curl -X POST http://localhost:8002/generate/complete-study \
  -H "Content-Type: application/json" \
  -d '{
    "indication": "Hypertension",
    "phase": "Phase 3",
    "n_per_arm": 10,
    "target_effect": -5.0,
    "use_aact": true
  }' > complete_study.json
```

**Response includes**:
- `vitals`: Vital signs for all visits
- `demographics`: Age, gender, race, ethnicity, country
- `labs`: Glucose, creatinine, electrolytes
- `adverse_events`: Headache, fatigue, dizziness (real AE patterns)

#### Available Indications

Check what indications are available in AACT:

```bash
curl http://localhost:8002/aact/indications
```

**Common indications** with AACT data:
- Hypertension
- Diabetes
- Cancer (various types)
- Heart Failure
- COPD
- Asthma
- Depression
- Alzheimer's Disease
- Rheumatoid Arthritis

---

### Demo 3: Validate Clinical Data

#### Validate Generated Data Against Clinical Constraints

```bash
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d "{\"records\": $(cat generated_data.json)}"
```

**Expected response:**
```json
{
  "rows": 20,
  "checks": [
    {
      "name": "Has required columns",
      "passed": true
    },
    {
      "name": "SystolicBP in range (95-200)",
      "passed": true
    },
    {
      "name": "DiastolicBP in range (55-130)",
      "passed": true
    },
    {
      "name": "HeartRate in range (50-120)",
      "passed": true
    },
    {
      "name": "Temperature in range (35.0-40.0)",
      "passed": true
    },
    {
      "name": "Has 1-2 fever rows (temp > 38)",
      "passed": true
    },
    {
      "name": "Fever rows have HR >= 67",
      "passed": true
    },
    {
      "name": "Week-12 effect approximately -5 mmHg",
      "passed": true
    }
  ],
  "week12_effect": -5.2,
  "fever_count": 2,
  "all_passed": true
}
```

#### Understanding Validation Results:

- **rows:** Number of records validated
- **checks:** List of validation rules and their pass/fail status
- **week12_effect:** Calculated treatment effect (Active - Placebo)
- **fever_count:** Number of patients with fever (temp > 38°C)
- **all_passed:** Overall validation status

---

### Demo 4: Auto-Repair Invalid Data

#### Create Invalid Data (for demonstration)

```bash
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "SubjectID": "RA001-TEST",
        "VisitName": "Week 12",
        "TreatmentArm": "Active",
        "SystolicBP": 250,
        "DiastolicBP": 150,
        "HeartRate": 150,
        "Temperature": 42.0
      }
    ]
  }'
```

**Expected response:** Multiple checks will fail.

#### Auto-Repair the Data

```bash
curl -X POST http://localhost:8001/repair \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "SubjectID": "RA001-TEST",
        "VisitName": "Week 12",
        "TreatmentArm": "Active",
        "SystolicBP": 250,
        "DiastolicBP": 150,
        "HeartRate": 150,
        "Temperature": 42.0
      }
    ]
  }'
```

**Expected response:**
```json
{
  "repaired_records": [
    {
      "SubjectID": "RA001-TEST",
      "VisitName": "Week 12",
      "TreatmentArm": "Active",
      "SystolicBP": 200,
      "DiastolicBP": 130,
      "HeartRate": 120,
      "Temperature": 40.0
    }
  ],
  "validation_after": {
    "all_passed": true,
    ...
  }
}
```

**What happened:**
- SystolicBP: 250 → 200 (clipped to max)
- DiastolicBP: 150 → 130 (clipped to max)
- HeartRate: 150 → 120 (clipped to max)
- Temperature: 42.0 → 40.0 (clipped to max)

---

### Demo 5: Store Data in Database

```bash
curl -X POST http://localhost:8001/store-vitals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"records\": $(cat generated_data.json)}"
```

**Expected response:**
```json
{
  "success": true,
  "records_stored": 20,
  "timestamp": "2025-11-12T10:30:45.123456"
}
```

**Verify data in PostgreSQL:**
```bash
# Connect to PostgreSQL
docker exec -it clinical_postgres psql -U clinical_user -d clinical_trials

# Query stored data
SELECT COUNT(*) FROM vital_signs;
SELECT COUNT(*) FROM patients;

# View sample records
SELECT * FROM vital_signs LIMIT 5;

# Exit PostgreSQL
\q
```

---

### Demo 6: Statistical Analysis

#### Calculate Week-12 Efficacy Statistics

```bash
curl -X POST http://localhost:8003/stats/week12 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"vitals_data\": $(cat generated_data.json)}"
```

**Expected response:**
```json
{
  "treatment_groups": {
    "Active": {
      "n": 10,
      "mean_systolic": 118.5,
      "std_systolic": 8.2,
      "se_systolic": 2.6
    },
    "Placebo": {
      "n": 10,
      "mean_systolic": 123.7,
      "std_systolic": 7.9,
      "se_systolic": 2.5
    }
  },
  "treatment_effect": {
    "difference": -5.2,
    "se_difference": 3.6,
    "t_statistic": -1.44,
    "p_value": 0.167,
    "ci_95_lower": -12.8,
    "ci_95_upper": 2.4
  },
  "interpretation": {
    "significant": false,
    "effect_size": "small",
    "clinical_relevance": "borderline"
  }
}
```

**Understanding the results:**
- **mean_systolic:** Average systolic BP for each group
- **treatment_effect:** Active - Placebo (negative = reduction)
- **p_value:** Statistical significance (< 0.05 = significant)
- **ci_95:** 95% confidence interval for the effect

---

### Demo 7: Quality Checks with Edit Rules

#### Run Edit Checks on Data

```bash
curl -X POST http://localhost:8004/checks/validate \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "SubjectID": "RA001-001",
        "Age": 45,
        "SystolicBP": 130,
        "DiastolicBP": 85
      },
      {
        "SubjectID": "RA001-002",
        "Age": 17,
        "SystolicBP": 145,
        "DiastolicBP": 95
      }
    ],
    "rules_yaml": "- name: Age >= 18\n  type: range\n  column: Age\n  min: 18\n  max: 100\n  severity: error\n\n- name: BP Valid Range\n  type: range\n  column: SystolicBP\n  min: 95\n  max: 200\n  severity: warning"
  }'
```

**Expected response:**
```json
{
  "total_records": 2,
  "total_checks": 4,
  "violations": [
    {
      "record": "RA001-002",
      "rule": "Age >= 18",
      "severity": "error",
      "message": "Age value 17 is below minimum 18"
    }
  ],
  "quality_score": 0.75,
  "passed": false
}
```

---

### Demo 8: PHI Detection and Encryption

#### Detect PHI (Protected Health Information)

```bash
curl -X POST http://localhost:8005/phi/detect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "name": "John Doe",
      "ssn": "123-45-6789",
      "mrn": "MRN-12345",
      "date_of_birth": "1980-01-01"
    }
  }'
```

**Expected response:**
```json
{
  "has_phi": true,
  "findings": [
    "Potential SSN detected in field 'ssn': 123-45-6789",
    "Potential Medical Record Number in field 'mrn': MRN-12345"
  ],
  "safe_to_process": false
}
```

#### Encrypt Sensitive Data

```bash
curl -X POST http://localhost:8005/encryption/encrypt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": "Patient SSN: 123-45-6789"
  }'
```

**Expected response:**
```json
{
  "encrypted_data": "gAAAAABhY3J5cHRlZF9kYXRhX2hlcmU...",
  "algorithm": "AES-256-GCM"
}
```

#### Decrypt Data

```bash
curl -X POST http://localhost:8005/encryption/decrypt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "encrypted_data": "gAAAAABhY3J5cHRlZF9kYXRhX2hlcmU..."
  }'
```

---

### Demo 9: HIPAA Audit Logs

#### View Audit Logs (Admin Only)

```bash
curl -X GET "http://localhost:8005/audit/logs?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected response:**
```json
[
  {
    "event_id": "uuid-here",
    "event_type": "LOGIN",
    "user_id": "admin",
    "action": "LOGIN",
    "resource": "security-service",
    "timestamp": "2025-11-12T10:15:30.123456",
    "ip_address": "0.0.0.0"
  },
  {
    "event_id": "uuid-here",
    "event_type": "ENCRYPT",
    "user_id": "admin",
    "action": "ENCRYPT",
    "resource": "phi_data",
    "timestamp": "2025-11-12T10:20:45.123456"
  }
]
```

---

## API Documentation

### Interactive Swagger UI

Each service provides interactive API documentation:

| Service | URL | Description |
|---------|-----|-------------|
| **API Gateway** | http://localhost:8000/docs | Central routing and orchestration |
| **Security Service** | http://localhost:8005/docs | Authentication, encryption, audit |
| **EDC Service** | http://localhost:8001/docs | Data validation and storage |
| **Data Generation** | http://localhost:8002/docs | Synthetic data generation |
| **Analytics Service** | http://localhost:8003/docs | Statistical analysis |
| **Quality Service** | http://localhost:8004/docs | Edit checks and quality |

### Using Swagger UI

1. Open any service URL (e.g., http://localhost:8005/docs)
2. Click on any endpoint to expand it
3. Click **"Try it out"** button
4. Fill in parameters (add Bearer token for protected endpoints)
5. Click **"Execute"** to test the API
6. View response in the browser

### Default Test Accounts

| Username | Password | Roles | Use Case |
|----------|----------|-------|----------|
| **admin** | admin123 | admin, data_analyst, clinician | Full access |
| **analyst** | analyst123 | data_analyst | Data analysis only |
| **clinician** | clinician123 | clinician | Clinical data access |

---

## Stopping the Services

### Graceful Shutdown

In the terminal where `docker-compose up` is running:

1. Press `Ctrl + C` (or `Cmd + C` on macOS)
2. Wait for all services to stop gracefully

### Stop and Remove Containers

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data!)
docker-compose down -v
```

### View Container Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs api-gateway
docker-compose logs security-service
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f api-gateway
```

---

## Troubleshooting

### Problem: Port Already in Use

**Error:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using the port (example: port 8000)
# Windows (PowerShell)
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000

# Kill the process or change the port in docker-compose.yml
```

### Problem: Services Not Healthy

**Error:**
```
Container api-gateway is unhealthy
```

**Solution:**
```bash
# Check service logs
docker-compose logs api-gateway

# Restart specific service
docker-compose restart api-gateway

# Full restart
docker-compose down
docker-compose up --build
```

### Problem: Database Connection Failed

**Error:**
```
database connection failed: connection refused
```

**Solution:**
```bash
# Wait 30-60 seconds for PostgreSQL to fully initialize
# Check PostgreSQL logs
docker-compose logs postgres

# Verify PostgreSQL is running
docker-compose ps postgres

# Connect to PostgreSQL manually
docker exec -it clinical_postgres psql -U clinical_user -d clinical_trials
```

### Problem: Docker Out of Memory

**Error:**
```
docker: Error response from daemon: OCI runtime create failed
```

**Solution:**
1. Open **Docker Desktop**
2. Go to **Settings** → **Resources**
3. Increase **Memory** to at least 4GB (8GB recommended)
4. Click **Apply & Restart**

### Problem: Cannot Access http://localhost:8000

**Solution:**
```bash
# Check if Docker Desktop is running
# Check if containers are up
docker-compose ps

# Check if port 8000 is accessible
curl http://localhost:8000/health

# Try using 127.0.0.1 instead of localhost
curl http://127.0.0.1:8000/health
```

### Problem: Token Validation Fails

**Error:**
```
{"detail": "Invalid authentication credentials"}
```

**Solution:**
1. Ensure you copied the full token (including all characters)
2. Check token hasn't expired (tokens expire after 30 minutes)
3. Login again to get a new token
4. Ensure `Bearer ` prefix is included in Authorization header

### Problem: Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'validation'
```

**Solution:**
```bash
# Rebuild containers
docker-compose down
docker-compose up --build

# This forces Docker to reinstall all dependencies
```

### Common Issues Summary

| Issue | Quick Fix |
|-------|-----------|
| Port conflict | Stop other services or change ports |
| Service unhealthy | Check logs, wait longer, or restart |
| Database error | Wait for initialization, check logs |
| Out of memory | Increase Docker memory allocation |
| Token expired | Login again to get new token |
| Import errors | Rebuild with `--build` flag |

---

## Advanced Usage

### Running in Background (Detached Mode)

```bash
# Start services in background
docker-compose up -d

# View logs when needed
docker-compose logs -f

# Stop background services
docker-compose down
```

### Scaling Services

```bash
# Scale data-generation-service to 3 instances
docker-compose up -d --scale data-generation-service=3

# Verify scaling
docker-compose ps
```

### Database Backup and Restore

#### Backup Database

```bash
# Backup PostgreSQL
docker exec clinical_postgres pg_dump -U clinical_user clinical_trials > backup_$(date +%Y%m%d).sql

# Verify backup
ls -lh backup_*.sql
```

#### Restore Database

```bash
# Restore from backup
docker exec -i clinical_postgres psql -U clinical_user -d clinical_trials < backup_20251112.sql
```

### Performance Monitoring

#### View Resource Usage

```bash
# Real-time stats
docker stats

# Container-specific stats
docker stats api-gateway security-service
```

#### Prometheus Metrics

```bash
# Each service exposes Prometheus metrics
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:8005/metrics
```

### Development Tips

#### Auto-Reload Code Changes

For development, mount source code as volumes (modify `docker-compose.yml`):

```yaml
services:
  edc-service:
    volumes:
      - ./microservices/edc-service:/app
```

Then restart to pick up changes:
```bash
docker-compose restart edc-service
```

#### Connect to Running Container

```bash
# Open shell in container
docker exec -it edc-service /bin/bash

# Or use sh if bash is not available
docker exec -it edc-service /bin/sh
```

#### Connect to Redis

```bash
# Open Redis CLI
docker exec -it clinical_redis redis-cli

# Test Redis connection
127.0.0.1:6379> PING
PONG

# View all keys
127.0.0.1:6379> KEYS *

# Exit
127.0.0.1:6379> EXIT
```

---

## Next Steps

### What to Try Next

1. **Explore all API endpoints** using Swagger UI
2. **Generate larger datasets** (100+ patients) for stress testing
3. **Experiment with different validation rules** in Quality Service
4. **Run statistical analyses** with various data distributions
5. **Test HIPAA compliance features** (encryption, audit logs)
6. **Integrate with frontend application** using API Gateway

### Customization

1. **Modify environment variables** in `.env` file
2. **Change JWT expiration** for longer/shorter sessions
3. **Add custom validation rules** in Quality Service
4. **Configure CORS** for your frontend domain
5. **Adjust rate limits** for higher throughput

### Production Deployment

For production deployment, see:
- `terraform/` - AWS infrastructure provisioning
- `kubernetes/` - Kubernetes manifests
- `SETUP_GITHUB.md` - CI/CD pipeline setup

---

## Support and Resources

### Documentation

- **Project README:** `../README.md`
- **Database Schema:** `database/README.md`
- **Implementation Status:** `IMPLEMENTATION_STATUS.md`
- **Microservices Plan:** `REALISTIC_MICROSERVICES_PLAN.md`

### Common Commands Reference

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f [service-name]

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart [service-name]

# Remove all containers and volumes
docker-compose down -v
```

---

## Summary

You've successfully set up and demoed the SyntheticTrialStudio Enterprise platform! You can now:

✅ Generate synthetic clinical trial data
✅ Validate data against clinical constraints
✅ Auto-repair invalid data
✅ Store data in PostgreSQL database
✅ Perform statistical analysis
✅ Run quality checks with edit rules
✅ Authenticate users with JWT tokens
✅ Detect and encrypt PHI data
✅ View HIPAA-compliant audit logs

The platform is production-ready with microservices architecture, database persistence, caching, security, and comprehensive API documentation.

**Happy coding!** 🚀
