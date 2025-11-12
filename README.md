# SyntheticTrialStudio Enterprise Platform

Enterprise-grade microservices platform for clinical trial management with Kubernetes orchestration.

## 🏗️ Architecture

This project transforms the monolithic Streamlit application into a scalable microservices architecture:

### Microservices (6 Core Services)

1. **EDC Service** (Port 8001) - Electronic Data Capture
   - Subject data validation
   - Auto-repair functionality
   - Visit data management

2. **Data Generation Service** (Port 8002) - Synthetic Data
   - Rules-based generation
   - MVN (Multivariate Normal) generation
   - LLM-based generation with auto-repair
   - Oncology AE generation

3. **Analytics Service** (Port 8003) - Statistics & Reporting
   - Week-12 statistics (Welch's t-test)
   - RECIST + ORR analysis
   - RBQM summaries
   - CSR draft generation
   - SDTM export

4. **Quality Service** (Port 8004) - Edit Checks
   - YAML-based edit check engine
   - Range validation
   - Pattern matching
   - Duplicate detection
   - Entry noise simulation

5. **Security Service** (Port 8005) - Authentication & Authorization
   - JWT authentication
   - PHI encryption/decryption
   - PHI detection
   - HIPAA audit logging

6. **API Gateway** (Port 8000) - Central Routing
   - Request routing to all services
   - Token validation
   - Rate limiting
   - Service discovery

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Kubernetes (Minikube, Kind, or cloud provider)
- kubectl CLI
- Python 3.11+ (for local development)

### Local Development with Docker Compose

```bash
# Clone the repository
cd synthetictrial-enterprise

# Start all services
docker-compose up --build

# Access services
# API Gateway: http://localhost:8000
# EDC Service: http://localhost:8001
# Data Generation: http://localhost:8002
# Analytics: http://localhost:8003
# Quality: http://localhost:8004
# Security: http://localhost:8005
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

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Individual service health
curl http://localhost:8001/health  # EDC
curl http://localhost:8002/health  # Data Generation
curl http://localhost:8003/health  # Analytics
curl http://localhost:8004/health  # Quality
curl http://localhost:8005/health  # Security
```

### Load Testing

```bash
# Install k6
brew install k6

# Run load test (create load-test.js first)
k6 run load-test.js
```

## 📁 Project Structure

```
synthetictrial-enterprise/
├── microservices/
│   ├── api-gateway/
│   │   ├── src/main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── edc-service/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── validation.py
│   │   │   └── repair.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── data-generation-service/
│   ├── analytics-service/
│   ├── quality-service/
│   └── security-service/
├── kubernetes/
│   ├── deployments/
│   ├── services/
│   ├── hpa/
│   └── configmaps/
├── docker-compose.yml
└── README.md
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
