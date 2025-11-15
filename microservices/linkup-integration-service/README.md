# Linkup Integration Service

> AI-powered regulatory intelligence and evidence-based quality assessment for the Synthetic Medical Data Generation platform.

## 🎯 Overview

The Linkup Integration Service extends the Synthetic Medical Data Generation platform with three powerful AI-driven capabilities:

1. **Evidence Pack Citation Service** - Automatically fetch regulatory citations (FDA, ICH, CDISC) for quality metrics
2. **Edit-Check Authoring Assistant** - AI-assisted generation of YAML edit check rules with clinical range detection
3. **Compliance/RBQM Watcher** - Automated monitoring of regulatory sources for guidance updates

This service **complements** the existing backend without modifying it, providing additional value through deep web search and regulatory intelligence powered by Linkup.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Linkup Integration Service (Port 8007)          │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Evidence   │  │ Edit Check  │  │ Compliance  │    │
│  │    Pack     │  │  Generator  │  │   Watcher   │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                           │                             │
│                    ┌──────▼──────┐                      │
│                    │   Linkup    │                      │
│                    │   Client    │                      │
│                    └─────────────┘                      │
└──────────────────────────┬──────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │  Linkup Search API      │
              │  (Deep Web Intelligence)│
              └────────────┬────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
┌─────▼─────┐      ┌──────▼──────┐      ┌─────▼─────┐
│  FDA.gov  │      │  ICH.org    │      │ CDISC.org │
└───────────┘      └─────────────┘      └───────────┘
```

---

## 📋 Features

### 1. Evidence Pack Citation Service

Enhances quality assessment reports with authoritative regulatory citations.

**Key Capabilities:**
- Automatic citation fetching for quality metrics (Wasserstein distance, RMSE, etc.)
- Prioritizes FDA, ICH, CDISC, EMA, and TransCelerate sources
- Generates evidence packs suitable for regulatory submissions
- Stores citation history for audit trail

**Endpoints:**
- `POST /evidence/fetch-citations` - Fetch citations for a specific metric
- `POST /evidence/comprehensive-quality` - Quality assessment with full evidence pack

**Example Use Case:**
```bash
# Quality assessment with regulatory evidence
curl -X POST http://localhost:8007/evidence/comprehensive-quality \
  -H "Content-Type: application/json" \
  -d '{
    "original_data": [...],
    "synthetic_data": [...],
    "k": 5
  }'
```

**Response Includes:**
- Standard quality metrics (Wasserstein, RMSE, correlation, K-NN)
- Regulatory citations for each metric
- Evidence summary in Markdown format
- Regulatory readiness assessment

---

### 2. Edit-Check Authoring Assistant

AI-assisted generation of clinical data validation rules.

**Key Capabilities:**
- Automatic clinical range detection from FDA/ICH guidance
- YAML rule generation with citations
- Supports vitals, labs, and custom variables
- Confidence scoring (high/medium/low)
- Batch rule generation

**Endpoints:**
- `POST /edit-checks/generate-rule` - Generate single edit check rule
- `POST /edit-checks/batch-generate` - Generate multiple rules
- `GET /edit-checks/supported-variables` - List supported variables

**Supported Variables:**
- `systolic_bp`, `diastolic_bp` - Blood pressure (mmHg)
- `heart_rate` - Heart rate (bpm)
- `temperature` - Body temperature (°C)
- `respiratory_rate` - Respiratory rate (breaths/min)
- `oxygen_saturation` - SpO2 (%)
- `weight`, `height`, `bmi` - Anthropometrics

**Example Use Case:**
```bash
# Generate edit check rule for systolic BP
curl -X POST http://localhost:8007/edit-checks/generate-rule \
  -H "Content-Type: application/json" \
  -d '{
    "variable": "systolic_bp",
    "indication": "hypertension",
    "severity": "Major"
  }'
```

**Response Includes:**
- YAML rule definition
- Clinical range with citations
- Confidence score
- Requires review flag

---

### 3. Compliance/RBQM Watcher

Automated monitoring of regulatory sources for updates.

**Key Capabilities:**
- Daily scans of FDA, ICH, CDISC, TransCelerate, EMA
- Impact assessment (HIGH/MEDIUM/LOW)
- Affected rule identification
- Automated PR generation (GitHub integration)
- Alert notifications (Slack, email)

**Endpoints:**
- `POST /compliance/scan` - Trigger compliance scan (called by CronJob)
- `GET /compliance/recent-updates` - Retrieve recent updates
- `POST /compliance/assess-impact` - Assess impact on existing rules
- `GET /compliance/dashboard-summary` - Dashboard statistics

**Monitored Sources:**
- **FDA**: Clinical trial guidance, data quality, RBQM
- **ICH**: E6(R2), E6(R3), quality management
- **CDISC**: SDTM, CDASH, controlled terminology
- **TransCelerate**: RBQM, KRI, QTL guidance
- **EMA**: European clinical trial regulations

**Automated Workflow:**
```
1. CronJob triggers daily at 2 AM UTC
2. Deep search across all regulatory sources
3. Detect new/updated guidance documents
4. Assess impact (HIGH/MEDIUM/LOW)
5. If HIGH impact:
   - Generate PR with updated rules
   - Send alert notifications
   - Log to database for review
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Linkup API key (optional for testing - mock mode available)
- Docker (for containerized deployment)
- Kubernetes cluster (for production deployment)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Build Docker image
cd microservices/linkup-integration-service
docker build -t synthetictrial/linkup-integration-service:latest .

# Run container
docker run -d \
  -p 8007:8007 \
  -e LINKUP_API_KEY=your_api_key_here \
  -e DATABASE_URL=postgresql://user:pass@localhost/db \
  --name linkup-integration \
  synthetictrial/linkup-integration-service:latest
```

#### Option 2: Local Development

```bash
# Install dependencies
cd microservices/linkup-integration-service
pip install -r requirements.txt

# Set environment variables
export LINKUP_API_KEY=your_api_key_here
export DATABASE_URL=postgresql://user:pass@localhost/db

# Run the service
cd src
uvicorn main:app --host 0.0.0.0 --port 8007 --reload
```

#### Option 3: Kubernetes

```bash
# Create secrets
kubectl create namespace clinical-trials
kubectl create secret generic linkup-secrets \
  --from-literal=api-key=YOUR_LINKUP_API_KEY \
  -n clinical-trials

# Apply database schema
psql -U postgres -d synthetic_db -f database_schema.sql

# Deploy service
kubectl apply -f kubernetes/deployments/linkup-integration-service.yaml

# Deploy CronJob
kubectl apply -f kubernetes/cronjobs/compliance-watcher.yaml
```

### Database Setup

```bash
# Run database migrations
psql -U postgres -d synthetic_db -f microservices/linkup-integration-service/database_schema.sql
```

This creates the following tables:
- `quality_evidence` - Evidence pack storage
- `evidence_packs` - Complete evidence packs
- `auto_generated_rules` - Generated edit check rules
- `compliance_scans` - Scan results
- `regulatory_updates` - Detected updates
- `update_impact_assessments` - Impact assessments
- `linkup_audit_log` - Audit trail
- `linkup_config` - Configuration

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LINKUP_API_KEY` | Linkup API key | None | No (mock mode if missing) |
| `DATABASE_URL` | PostgreSQL connection string | None | Yes |
| `PORT` | Service port | 8007 | No |
| `HOST` | Bind host | 0.0.0.0 | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `ALLOWED_ORIGINS` | CORS origins | * | No |

### Mock Mode

If `LINKUP_API_KEY` is not set, the service runs in **mock mode** using pre-defined sample responses. This is useful for:
- Local development without API costs
- Testing and demos
- CI/CD pipelines

Mock mode provides realistic sample data for all endpoints.

---

## 📊 API Documentation

### Interactive Documentation

Once the service is running, access:

- **Swagger UI**: http://localhost:8007/docs
- **ReDoc**: http://localhost:8007/redoc
- **OpenAPI JSON**: http://localhost:8007/openapi.json

### Quick API Reference

#### Health Check
```bash
GET /health
```

#### Evidence Pack
```bash
POST /evidence/fetch-citations
POST /evidence/comprehensive-quality
```

#### Edit Check Generator
```bash
POST /edit-checks/generate-rule
POST /edit-checks/batch-generate
GET /edit-checks/supported-variables
```

#### Compliance Watcher
```bash
POST /compliance/scan
GET /compliance/recent-updates
POST /compliance/assess-impact
GET /compliance/dashboard-summary
```

---

## 🔄 Integration with Existing Services

The Linkup Integration Service is designed to **complement**, not replace, existing services:

### Integration Points

1. **Analytics Service**
   - Linkup service calls analytics service for quality calculations
   - Enhances results with regulatory citations
   - No modification to analytics service required

2. **Quality Service**
   - Edit check generator produces YAML rules
   - Rules can be imported into existing quality service
   - Backward compatible with manual rules

3. **EDC Service**
   - Compliance updates can trigger rule library updates
   - Edit check rules apply to EDC data validation
   - No changes to EDC service needed

4. **API Gateway**
   - Add route: `/linkup/*` → `linkup-integration-service:8007`
   - All Linkup endpoints accessible via gateway
   - Maintains existing authentication/authorization

### Example Gateway Configuration

```yaml
# In API Gateway routing
routes:
  - path: /linkup/*
    target: http://linkup-integration-service:8007
    strip_prefix: /linkup
    auth_required: true
```

---

## 🧪 Testing

### Unit Tests

```bash
cd microservices/linkup-integration-service
pytest tests/ -v
```

### Integration Tests

```bash
# Test with mock mode
export LINKUP_API_KEY=""
pytest tests/integration/ -v

# Test with real API (requires key)
export LINKUP_API_KEY=your_key
pytest tests/integration/ -v --real-api
```

### Manual Testing

```bash
# Test evidence pack
curl -X POST http://localhost:8007/evidence/fetch-citations \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "Wasserstein distance",
    "metric_value": 2.34
  }' | jq

# Test edit check generator
curl -X POST http://localhost:8007/edit-checks/generate-rule \
  -H "Content-Type: application/json" \
  -d '{
    "variable": "heart_rate",
    "indication": "cardiology"
  }' | jq

# Test compliance scan
curl -X POST http://localhost:8007/compliance/scan | jq
```

---

## 📈 Monitoring & Logging

### Logs

Service logs include:
- HTTP request/response logs
- Linkup API call logs
- Error traces
- Performance metrics

**Access logs:**
```bash
# Docker
docker logs -f linkup-integration

# Kubernetes
kubectl logs -f deployment/linkup-integration-service -n clinical-trials
```

### Metrics

Key metrics to monitor:
- Linkup API call volume and latency
- Citation fetch success rate
- Rule generation success rate
- Compliance scan duration
- Database query performance

### Health Checks

```bash
# Service health
curl http://localhost:8007/health

# Kubernetes health probes
kubectl get pods -n clinical-trials -l app=linkup-integration-service
```

---

## 🔐 Security Considerations

### API Key Management

- **Never** commit `LINKUP_API_KEY` to version control
- Use Kubernetes secrets in production
- Rotate keys regularly
- Monitor API usage for anomalies

### Database Security

- All tables include `tenant_id` for multi-tenancy
- Audit log tracks all Linkup searches
- Evidence packs are tenant-isolated
- Use Row-Level Security (RLS) in production

### CORS Configuration

- **Development**: `ALLOWED_ORIGINS=*` (permissive)
- **Production**: Set specific origins
  ```bash
  ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
  ```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Service won't start
```bash
# Check logs
docker logs linkup-integration

# Verify database connection
psql $DATABASE_URL -c "SELECT 1"

# Check port availability
lsof -i :8007
```

#### 2. Citations not being found
- Verify `LINKUP_API_KEY` is set correctly
- Check mock mode is disabled (if you want real results)
- Review Linkup API rate limits
- Check authoritative domains configuration

#### 3. Compliance scan failing
- Verify CronJob permissions
- Check service account has API access
- Review scan logs:
  ```bash
  kubectl logs -l component=compliance-watcher-pod -n clinical-trials
  ```

#### 4. Database errors
- Ensure schema is applied: `psql -f database_schema.sql`
- Check database permissions
- Verify connection string format

---

## 📚 Additional Resources

### Linkup API Documentation
- [Linkup API Docs](https://linkup.so/docs) (external)
- [MCP Integration Guide](https://modelcontextprotocol.io)

### Regulatory Sources
- [FDA Clinical Trial Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents)
- [ICH Guidelines](https://www.ich.org/page/efficacy-guidelines)
- [CDISC Standards](https://www.cdisc.org/standards)
- [TransCelerate RBQM](https://www.transceleratebiopharmainc.com/rbqm/)

### Related Documentation
- `../../linkup.md` - Original integration plan
- `../../CLAUDE.md` - Backend reference
- `../../README.md` - Main project documentation

---

## 🤝 Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/linkup-enhancement`
2. Make changes and add tests
3. Run tests: `pytest tests/ -v`
4. Submit PR with detailed description

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all functions
- Add docstrings to all public functions
- Keep functions focused and testable

### Testing Requirements

- All new features must have unit tests
- Integration tests for API endpoints
- Update documentation for new features

---

## 📝 License

Copyright (c) 2025 Synthetic Medical Data Generation Team

---

## 🙋 Support

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourorg/synthetic-medical-data/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourorg/synthetic-medical-data/discussions)
- **Email**: support@yourorg.com

### Reporting Bugs

When reporting bugs, please include:
1. Service version
2. Deployment environment (Docker/K8s/local)
3. Error logs (sanitized of sensitive data)
4. Steps to reproduce
5. Expected vs actual behavior

---

## 🗺️ Roadmap

### Planned Features

- [ ] PDF evidence pack generation
- [ ] GitHub PR automation for compliance updates
- [ ] Slack/email alert integration
- [ ] Advanced NLP for range extraction
- [ ] Support for additional data types (labs, AEs)
- [ ] Multi-language support for international regulations
- [ ] ML-based impact prediction
- [ ] Integration with clinical trial registries

### Future Enhancements

- Real-time compliance monitoring dashboard
- LLM-powered rule explanation
- Automated regression testing for rule changes
- Citation quality scoring
- Collaborative rule review workflow

---

**Version**: 1.0.0
**Last Updated**: 2025-11-15
**Maintainers**: Synthetic Medical Data Generation Team
