# SyntheticTrialStudio Enterprise Platform

Enterprise-grade microservices platform for clinical trial management with Kubernetes orchestration.

## 🏗️ Architecture

This project transforms the monolithic Streamlit application into a scalable microservices architecture:

### Microservices (7 Core Services)

1. **API Gateway** (Port 8000) - Central Routing
   - Request routing to all services
   - Token validation
   - Rate limiting
   - Service discovery

2. **EDC Service** (Port 8001) - Electronic Data Capture
   - Subject data validation
   - Auto-repair functionality
   - Visit data management
   - Database persistence

3. **Data Generation Service** (Port 8002) - Synthetic Data
   - Rules-based generation
   - MVN (Multivariate Normal) generation
   - Bootstrap resampling
   - Bayesian Network generation
   - MICE (Multiple Imputation by Chained Equations)
   - Diffusion model generation
   - LLM-based generation with auto-repair
   - **AACT-enhanced versions** (uses real data from 557K+ ClinicalTrials.gov trials)
   - Complete Study generation (coordinates Vitals, Demographics, Labs, AEs)
   - Oncology AE generation

4. **Analytics Service** (Port 8003) - Statistics & Reporting
   - Week-12 statistics (Welch's t-test)
   - RECIST + ORR analysis
   - RBQM summaries
   - CSR draft generation
   - SDTM export

5. **Quality Service** (Port 8004) - Edit Checks
   - YAML-based edit check engine
   - Range validation
   - Pattern matching
   - Duplicate detection
   - Entry noise simulation

6. **Security Service** (Port 8005) - Authentication & Authorization
   - JWT authentication
   - PHI encryption/decryption
   - PHI detection
   - HIPAA audit logging

7. **Daft Analytics Service** (Port 8007) - Distributed Data Analysis
   - High-performance distributed DataFrame processing
   - Treatment effect analysis
   - Responder analysis
   - Outlier detection
   - SQL-like queries on clinical data

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ (for backend services)
- Node.js 18+ (for frontend)
- npm or yarn
- (Optional) Docker & Docker Compose for containerized deployment

### Local Development (Current Setup)

**Backend Services** (running directly):
```bash
# Data Generation Service (Port 8002)
cd microservices/data-generation-service/src
python3 -m uvicorn main:app --reload --port 8002

# Analytics Service (Port 8003)
cd microservices/analytics-service/src
python3 -m uvicorn main:app --reload --port 8003

# EDC Service (Port 8001)
cd microservices/edc-service/src
python3 -m uvicorn main:app --reload --port 8001

# Security Service (Port 8005)
cd microservices/security-service/src
python3 -m uvicorn main:app --reload --port 8005

# Quality Service (Port 8004)
cd microservices/quality-service/src
python3 -m uvicorn main:app --reload --port 8004
```

**Frontend Application**:
```bash
cd frontend
npm install
npm run dev
# Access at: http://localhost:3000
```

### Access Services

- **Frontend UI**: http://localhost:3000
- **Data Generation**: http://localhost:8002
- **Analytics**: http://localhost:8003
- **EDC Service**: http://localhost:8001
- **Security**: http://localhost:8005
- **Quality**: http://localhost:8004
- **Daft Analytics**: http://localhost:8007

### Docker Compose Deployment (Alternative)

```bash
# Start all services with Docker
docker-compose up --build

# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### Kubernetes Deployment

```bash
# Start local cluster (Minikube)
minikube start --cpus 4 --memory 8192

# Create namespace and secrets
kubectl apply -f kubernetes/configmaps/namespace.yaml

# Deploy all services
kubectl apply -f kubernetes/deployments/
kubectl apply -f kubernetes/services/
kubectl apply -f kubernetes/hpa/

# Check deployment status
kubectl get pods -n clinical-trials
kubectl get svc -n clinical-trials

# Access API Gateway
minikube service api-gateway -n clinical-trials

# Or with port forwarding
kubectl port-forward -n clinical-trials svc/api-gateway 8000:80
```

## 📊 Service Details

### EDC Service API

```bash
# Validate vitals data
POST /validate
{
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
}

# Auto-repair data
POST /repair
```

### Data Generation Service API

```bash
# Generate rules-based data
POST /generate/rules
{
  "n_per_arm": 50,
  "target_effect": -5.0,
  "seed": 42
}

# Generate MVN-based data
POST /generate/mvn

# Generate LLM-based data
POST /generate/llm
{
  "indication": "Rheumatoid Arthritis",
  "n_per_arm": 50,
  "api_key": "your-openai-key"
}
```

### Analytics Service API

```bash
# Calculate Week-12 statistics
POST /stats/week12
{
  "vitals_data": [...]
}

# Generate RBQM summary
POST /rbqm/summary

# Generate CSR draft
POST /csr/draft

# Export to SDTM
POST /sdtm/export
```

### Quality Service API

```bash
# Run edit checks
POST /checks/validate
{
  "data": [...],
  "rules_yaml": "..."
}

# Get default rules
GET /checks/rules

# Simulate entry noise
POST /quality/simulate-noise
```

### Security Service API

```bash
# Login
POST /auth/login
{
  "username": "user",
  "password": "pass"
}

# Validate token
POST /auth/validate
Header: Authorization: Bearer <token>

# Encrypt PHI
POST /encryption/encrypt

# Detect PHI
POST /phi/detect


```

## 🔒 Security

### Authentication Flow

1. Client authenticates via Security Service (`/security/auth/login`)
2. Receives JWT token
3. Includes token in all subsequent requests: `Authorization: Bearer <token>`
4. API Gateway validates token with Security Service
5. Request forwarded to target microservice

### HIPAA Compliance

- **PHI Encryption**: All sensitive data encrypted at rest
- **Audit Logging**: Immutable audit trail of all access
- **PHI Detection**: Automatic blocking of suspected PHI uploads
- **Access Control**: Role-based authorization

## 📈 Scalability

### Horizontal Pod Autoscaling (HPA)

All services automatically scale based on CPU/memory usage:

- **API Gateway**: 2-10 replicas (70% CPU threshold)
- **EDC Service**: 2-10 replicas (70% CPU)
- **Analytics**: 2-8 replicas (70% CPU)
- **Data Generation**: 1-5 replicas (75% CPU)
- **Quality**: 2-6 replicas (70% CPU)

```bash
# Check HPA status
kubectl get hpa -n clinical-trials

# Watch autoscaling in action
kubectl get hpa -n clinical-trials --watch
```

### Resource Allocation

| Service | CPU Request | Memory Request | CPU Limit | Memory Limit |
|---------|-------------|----------------|-----------|--------------|
| API Gateway | 250m | 256Mi | 500m | 512Mi |
| EDC | 250m | 256Mi | 500m | 512Mi |
| Data Generation | 500m | 512Mi | 1000m | 1Gi |
| Analytics | 500m | 512Mi | 1000m | 1Gi |
| Quality | 250m | 256Mi | 500m | 512Mi |
| Security | 250m | 256Mi | 500m | 512Mi |

## 🧪 Testing

**For comprehensive testing procedures, see [COMPREHENSIVE_TESTING_GUIDE.md](COMPREHENSIVE_TESTING_GUIDE.md)**

This guide includes:
- ✅ Complete frontend + backend testing workflows
- ✅ Analytics dashboard testing (what to look for, what to expect)
- ✅ Quality metrics interpretation
- ✅ Statistical analysis validation
- ✅ Performance benchmarks
- ✅ Troubleshooting common issues

### Quick Health Checks

```bash
# Check all backend services
for port in 8002 8003 8004 8005 8006; do
  echo "Port $port: $(curl -s http://localhost:$port/health 2>/dev/null || echo 'NOT RUNNING')"
done

# Check frontend
curl -s http://localhost:3000 > /dev/null && echo "Frontend: RUNNING" || echo "Frontend: NOT RUNNING"
```

### Quick Functionality Test

```bash
# Generate test data
curl -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 5, "target_effect": -5.0, "seed": 123}'

# Should return 40 VitalsRecords (5 × 2 × 4)
```

## 📁 Project Structure

```
Synthetic-Medical-Data-Generation/
├── microservices/
│   ├── api-gateway/           # Port 8000 - Central routing
│   │   ├── src/main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── edc-service/           # Port 8001 - Data validation
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── validation.py
│   │   │   └── repair.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── data-generation-service/  # Port 8002 - Data generation
│   ├── analytics-service/     # Port 8003 - Analytics
│   ├── quality-service/       # Port 8004 - Quality checks
│   ├── security-service/      # Port 8005 - Auth & Security
│   └── shared/                # Shared utilities
├── database/
│   ├── init.sql              # PostgreSQL schema
│   ├── database.py           # Database client
│   └── cache.py              # Redis cache layer
├── kubernetes/
│   ├── deployments/
│   ├── services/
│   ├── hpa/
│   └── configmaps/
├── terraform/                 # AWS infrastructure
├── scripts/                   # Deployment scripts
├── data/                      # Sample data
├── docker-compose.yml
├── README.md
├── CLAUDE.md                  # Backend API reference
└── QUICKSTART_GUIDE.md        # Getting started guide
```

## 🛠️ Development

### Building Services Locally

```bash
# Build single service
cd microservices/edc-service
docker build -t synthetictrial/edc-service:latest .

# Build all services
docker-compose build

# Run locally without containers
cd microservices/edc-service
pip install -r requirements.txt
python src/main.py
```

### Adding a New Service

1. Create service directory in `microservices/`
2. Add `src/main.py` with FastAPI application
3. Add `requirements.txt`
4. Add `Dockerfile`
5. Add Kubernetes manifests
6. Update API Gateway service registry
7. Update docker-compose.yml

## 🔍 Monitoring

### Logs

```bash
# View logs (Docker Compose)
docker-compose logs -f api-gateway

# View logs (Kubernetes)
kubectl logs -f -n clinical-trials deployment/api-gateway
kubectl logs -f -n clinical-trials deployment/edc-service
```

### Metrics

```bash
# Pod metrics
kubectl top pods -n clinical-trials

# Node metrics
kubectl top nodes
```

## 📝 Environment Variables

### Security Service
- `JWT_SECRET_KEY`: Secret key for JWT signing
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 30)

### Data Generation Service
- `OPENAI_API_KEY`: OpenAI API key for LLM generation (optional)

### API Gateway
- `*_SERVICE_URL`: Service URLs (auto-configured in Kubernetes)

## 🤝 Contributing

This project was developed as part of a 2-week sprint to transform a monolithic application into a microservices architecture.

## 📄 License

MIT License - See existing-app/LICENSE

## 🔗 Related Documentation

- [Original Monolithic App](../existing-app/README.md)
- [Realistic Microservices Plan](../REALISTIC_MICROSERVICES_PLAN.md)
- [AI-Accelerated Development Strategy](../ai_accelerated_development_strategy.md)

## 📞 Support

For issues or questions, please check:
- API Documentation: `http://localhost:8000/docs` (after deployment)
- Service-specific docs: `http://localhost:800X/docs` (replace X with service port)

---

**Built with:** FastAPI, Docker, Kubernetes, Python 3.11

**Domain:** Clinical Trials Management, HIPAA Compliance, Regulatory Submission

**Status:** Production-ready microservices architecture
