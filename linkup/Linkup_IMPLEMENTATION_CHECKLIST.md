# Linkup Integration Implementation Checklist
## For SyntheticTrialStudio Enterprise Project

This checklist guides you through implementing the corrected Linkup integration step-by-step.

---

## Phase 1: Environment Setup (15 minutes)

### Prerequisites
- [ ] Sign up for Linkup account at https://linkup.so
- [ ] Get your API key from Linkup dashboard
- [ ] Verify you have Python 3.8+ installed

### Installation
```bash
# 1. Install Linkup SDK in each microservice
cd microservices/analytics-service
pip install linkup-sdk

cd ../quality-service
pip install linkup-sdk

cd ../compliance-watcher
pip install linkup-sdk
```

### Environment Configuration
- [ ] Add to `.env` file (project root):
```bash
LINKUP_API_KEY=your_actual_api_key_here
```

- [ ] Add to `docker-compose.yml` for each service:
```yaml
environment:
  - LINKUP_API_KEY=${LINKUP_API_KEY}
```

### Verification Test
- [ ] Create and run test script:
```python
# test_linkup.py
from linkup import LinkupClient
import os

client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))

try:
    response = client.search(
        query="FDA clinical trial data quality",
        depth="standard",
        output_type="searchResults"
    )
    print("✅ Linkup connected successfully!")
    print(f"Found {len(response.get('results', []))} results")
except Exception as e:
    print(f"❌ Error: {e}")
```

```bash
python test_linkup.py
```

**Expected output**: `✅ Linkup connected successfully!`

---

## Phase 2: Evidence Pack Citation Service (Sprint 1 - Days 1-3)

### Day 1: Database Schema
- [ ] Add quality evidence table
```bash
cd database
```

- [ ] Add to `init.sql`:
```sql
CREATE TABLE IF NOT EXISTS quality_evidence (
    evidence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,
    quality_run_id UUID,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL,
    citation_title VARCHAR(500),
    citation_url TEXT,
    citation_snippet TEXT,
    source_domain VARCHAR(200),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_metric (tenant_id, metric_name)
);
```

- [ ] Run migration:
```bash
docker-compose exec postgres psql -U admin -d clinical_trials -f /docker-entrypoint-initdb.d/init.sql
```

### Day 2: Analytics Service Integration
- [ ] Open `microservices/analytics-service/src/main.py`

- [ ] Add imports at top of file:
```python
from linkup import LinkupClient
from urllib.parse import urlparse
import os

# Initialize Linkup client (add after FastAPI app initialization)
linkup_client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))
```

- [ ] Add helper function (from corrected linkup.md line 20-60):
```python
async def fetch_metric_citations(metric_name: str, metric_value: float) -> List[Dict]:
    # Copy complete function from linkup.md
```

- [ ] Add new endpoint (from corrected linkup.md line 56-89):
```python
@app.post("/quality/comprehensive-with-evidence")
async def comprehensive_quality_with_citations(request: ComprehensiveQualityRequest):
    # Copy complete function from linkup.md
```

- [ ] Test endpoint:
```bash
curl -X POST http://localhost:8003/quality/comprehensive-with-evidence \
  -H "Content-Type: application/json" \
  -d '{
    "synthetic_dataset": [...],
    "real_dataset": [...]
  }'
```

### Day 3: Frontend Integration
- [ ] Add citation display component to your React/Vue app
- [ ] Show citations with each quality metric
- [ ] Add "View Evidence" button for detailed citations
- [ ] Test end-to-end with real data

**Checkpoint**: Evidence Pack working with citations from FDA/ICH

---

## Phase 3: Edit-Check Authoring Assistant (Sprint 2 - Days 4-8)

### Day 4: Quality Service Integration
- [ ] Open `microservices/quality-service/src/main.py`

- [ ] Add imports:
```python
from linkup import LinkupClient
from urllib.parse import urlparse
from datetime import datetime
import yaml
import re
import os

linkup_client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))
```

- [ ] Add functions (from corrected linkup.md line 126-228):
```python
@app.post("/checks/generate-rule")
async def generate_edit_check_rule(variable: str, indication: str = "general"):
    # Copy complete function from linkup.md

def extract_clinical_ranges(search_result: Dict, variable: str) -> Dict:
    # Copy complete function from linkup.md
```

### Day 5: YAML Preview UI
- [ ] Create rule preview component
- [ ] Add "Generate from Clinical Guidelines" button
- [ ] Show confidence scores and citations
- [ ] Add "Requires Review" warning

### Day 6-7: CDASH Integration
- [ ] Download CDASH standards from CDISC
- [ ] Parse standard variables into database
- [ ] Add variable dropdown with CDASH standards
- [ ] Test rule generation for common vitals

### Day 8: Testing & Refinement
- [ ] Test with all vital signs (BP, HR, Temp, etc.)
- [ ] Verify citations are from authoritative sources
- [ ] Add unit tests
- [ ] Document for your team

**Checkpoint**: Auto-generate edit check rules with FDA citations

---

## Phase 4: Compliance Watcher (Sprint 3 - Days 9-15)

### Day 9-10: New Microservice Setup
- [ ] Create new service structure:
```bash
cd microservices
mkdir -p compliance-watcher/src
cd compliance-watcher
```

- [ ] Create `src/main.py` (from corrected linkup.md line 286-443)
- [ ] Create `requirements.txt`:
```
fastapi==0.104.1
uvicorn==0.24.0
linkup-sdk==latest
pydantic==2.5.0
```

- [ ] Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]
```

### Day 11-12: GitHub PR Integration
- [ ] Set up GitHub API token
- [ ] Add function to create PRs (linkup.md line 411-443)
- [ ] Test PR creation with dummy data
- [ ] Set up rule library repository if not exists

### Day 13: Kubernetes CronJob
- [ ] Create `kubernetes/cronjobs/compliance-watcher.yaml`
- [ ] Configure to run nightly at 2 AM
- [ ] Test manual trigger first
- [ ] Monitor logs

### Day 14: Alerting Setup
- [ ] Add Slack webhook integration
- [ ] Send alerts for HIGH impact updates
- [ ] Format alerts with links to PRs
- [ ] Test alert flow

### Day 15: Testing & Documentation
- [ ] Test full workflow: scan → PR → alert
- [ ] Document for your team
- [ ] Set up monitoring

**Checkpoint**: Automated compliance monitoring with nightly scans

---

## Phase 5: Dataset Integration (Ongoing)

### MAUDE Dataset
- [ ] Download from FDA website
- [ ] Create data loading pipeline
- [ ] Integrate with AE generation
- [ ] Validate with real patterns

### ClinicalTrials.gov
- [ ] Set up API access
- [ ] Create sync script
- [ ] Use for study templates
- [ ] Update quarterly

### CDASH Standards
- [ ] Download latest version
- [ ] Parse into database
- [ ] Use for rule templates
- [ ] Update when CDISC publishes

---

## Verification & Testing

### Unit Tests
- [ ] Test Linkup client initialization
- [ ] Test search with mock responses
- [ ] Test error handling (401, 429)
- [ ] Test result parsing

### Integration Tests
- [ ] Test Evidence Pack end-to-end
- [ ] Test Edit Check generation
- [ ] Test Compliance Watcher scan
- [ ] Test with real FDA queries

### Load Testing
- [ ] Monitor rate limits (10 queries/sec)
- [ ] Test with 100 concurrent requests
- [ ] Implement exponential backoff
- [ ] Add caching for repeated queries

---

## Production Readiness

### Monitoring
- [ ] Add logging for all Linkup calls
- [ ] Track API usage (standard vs deep)
- [ ] Monitor costs
- [ ] Set up alerts for failures

### Error Handling
- [ ] Implement retry logic for 429 errors
- [ ] Handle 401 errors gracefully
- [ ] Log all failures
- [ ] Fallback to cached results

### Documentation
- [ ] Update README with Linkup setup
- [ ] Document API key rotation process
- [ ] Create runbook for common issues
- [ ] Add examples to team wiki

### Security
- [ ] Store API key in secrets management (not .env in prod)
- [ ] Rotate API keys quarterly
- [ ] Audit Linkup API calls
- [ ] Implement rate limiting on your endpoints

---

## Cost Management

### Budget Planning
- [ ] Estimate monthly call volume:
  - Evidence Pack: ~500 calls/month (deep) = €25
  - Edit Checks: ~100 calls/month (deep) = €5
  - Compliance: ~300 calls/month (deep) = €15
  - **Total: ~€45-90/month**

### Optimization
- [ ] Cache results for 24 hours where appropriate
- [ ] Use `standard` depth for non-critical queries
- [ ] Batch queries when possible
- [ ] Monitor and alert on unusual usage

---

## Rollout Plan

### Week 1: Evidence Pack (Low Risk)
- Enable for internal testing only
- Monitor API usage and costs
- Collect feedback from QA team

### Week 2: Edit Check Assistant (Medium Risk)
- Enable for rule authors
- Require human review for all generated rules
- Track which rules are accepted/rejected

### Week 3: Compliance Watcher (High Value)
- Enable nightly scans
- Start with email alerts only
- Add Slack after 1 week of stability

### Week 4: Full Production
- Enable all features for all users
- Monitor closely for first month
- Iterate based on usage patterns

---

## Success Metrics

### Technical Metrics
- [ ] API success rate > 99%
- [ ] Average response time < 5s
- [ ] Rate limit errors < 1%
- [ ] Cost within budget

### Business Metrics
- [ ] Time to generate quality report: -50%
- [ ] Edit check authoring time: -80%
- [ ] Regulatory updates detected: 100%
- [ ] False positive compliance alerts: <10%

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check LINKUP_API_KEY in environment |
| 429 Rate Limited | Implement exponential backoff |
| Empty results | Try depth="deep" or broader query |
| Wrong domain results | Use include_domains filter |
| Slow response | Use standard depth or cache |
| High costs | Use standard depth, implement caching |

---

## Resources

- **Full Documentation**: `linkup.md` (450+ lines with all code)
- **Quick Reference**: `LINKUP_QUICK_REFERENCE.md` (fast lookup)
- **API Changes**: `CORRECTIONS_SUMMARY.md` (what was fixed)
- **This Checklist**: Step-by-step implementation guide

---

## Support Contacts

- **Linkup Support**: support@linkup.so
- **Linkup Discord**: https://discord.gg/linkup
- **Documentation**: https://docs.linkup.so

---

## Final Checklist Before Going Live

- [ ] All environment variables set correctly
- [ ] Database schema updated
- [ ] All services have Linkup SDK installed
- [ ] Error handling implemented
- [ ] Logging and monitoring configured
- [ ] Rate limiting implemented
- [ ] Cost monitoring set up
- [ ] Team trained on new features
- [ ] Documentation updated
- [ ] Rollback plan prepared

---

**Last Updated**: Based on corrected Linkup integration (November 2025)
**Project**: SyntheticTrialStudio Enterprise
**Target Completion**: 3-4 weeks for all phases
