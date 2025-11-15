# Linkup Architecture Overview for SyntheticTrialStudio

## System Architecture with Linkup Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SyntheticTrialStudio Enterprise                  │
│                         Clinical Trials Platform                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐          ┌───────────────┐        ┌─────────────────┐
│   Analytics   │          │   Quality     │        │   Compliance    │
│   Service     │          │   Service     │        │   Watcher       │
│   (Port 8003) │          │   (Port 8002) │        │   (Port 8007)   │
│               │          │               │        │                 │
│ ┌───────────┐ │          │ ┌───────────┐ │        │ ┌─────────────┐ │
│ │Evidence   │ │          │ │Edit Check │ │        │ │Regulatory   │ │
│ │Pack       │ │          │ │Generator  │ │        │ │Monitor      │ │
│ │Citations  │ │          │ │           │ │        │ │             │ │
│ └─────┬─────┘ │          │ └─────┬─────┘ │        │ └──────┬──────┘ │
└───────┼───────┘          └───────┼───────┘        └─────────┼────────┘
        │                          │                          │
        │      Linkup SDK          │      Linkup SDK          │
        │   (linkup-sdk)           │   (linkup-sdk)           │
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
                         ┌──────────────────┐
                         │   Linkup API     │
                         │  api.linkup.so   │
                         │                  │
                         │  • Search Web    │
                         │  • Deep Search   │
                         │  • Structured    │
                         │    Output        │
                         └────────┬─────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────┐
        │         Authoritative Data Sources              │
        │                                                 │
        │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
        │  │   FDA    │  │   ICH    │  │     EMA      │ │
        │  │  .gov    │  │   .org   │  │ .europa.eu   │ │
        │  └──────────┘  └──────────┘  └──────────────┘ │
        │                                                 │
        │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
        │  │  CDISC   │  │TransCele │  │   PubMed     │ │
        │  │  .org    │  │  rate    │  │ .nih.gov     │ │
        │  └──────────┘  └──────────┘  └──────────────┘ │
        └─────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Evidence Pack Citation Flow

```
User Request                    Analytics Service              Linkup API
     │                                │                            │
     │  POST /quality/               │                            │
     │  comprehensive-with-evidence  │                            │
     ├──────────────────────────────>│                            │
     │                                │                            │
     │                                │  Calculate Quality Metrics │
     │                                │  (Wasserstein, RMSE, etc.) │
     │                                │                            │
     │                                │  search(                   │
     │                                │    "Wasserstein clinical"  │
     │                                │    depth="deep"            │
     │                                │    include_domains=[       │
     │                                │      "fda.gov",            │
     │                                │      "ich.org"             │
     │                                │    ]                       │
     │                                │  )                         │
     │                                ├───────────────────────────>│
     │                                │                            │
     │                                │                      FDA.gov
     │                                │                      ICH.org
     │                                │                      EMA
     │                                │                      CDISC
     │                                │                       ▲
     │                                │                       │
     │                                │              Search & Retrieve
     │                                │                       │
     │                                │                       ▼
     │                                │  {                     │
     │                                │    results: [          │
     │                                │      {name, url, ...}  │
     │                                │    ]                   │
     │                                │  }                     │
     │                                │<───────────────────────┤
     │                                │                            │
     │                                │  Parse Citations           │
     │                                │  Filter Authoritative      │
     │                                │  Store in DB               │
     │                                │                            │
     │  {                             │                            │
     │    metrics: {...},             │                            │
     │    regulatory_evidence: {      │                            │
     │      wasserstein: [            │                            │
     │        {title, url, snippet}   │                            │
     │      ]                          │                            │
     │    }                            │                            │
     │  }                              │                            │
     │<───────────────────────────────┤                            │
     │                                                              │
     │  Display Metrics + Citations                                │
     │                                                              │
```

**Key Points:**
- Quality metrics calculated first (no external dependencies)
- Linkup searches only for citation/evidence
- Results filtered to authoritative domains
- Citations stored alongside metrics

**Cost**: ~€0.05 per quality report (4 metrics × deep search)

---

### 2. Edit Check Rule Generation Flow

```
Rule Author                    Quality Service               Linkup API
     │                              │                            │
     │  POST /checks/generate-rule  │                            │
     │  {                           │                            │
     │    variable: "systolic_bp",  │                            │
     │    indication: "hypertension"│                            │
     │  }                           │                            │
     ├─────────────────────────────>│                            │
     │                               │                            │
     │                               │  search(                   │
     │                               │    "systolic bp normal     │
     │                               │     range hypertension     │
     │                               │     FDA ICH",              │
     │                               │    depth="deep",           │
     │                               │    include_domains=[       │
     │                               │      "fda.gov",            │
     │                               │      "ich.org"             │
     │                               │    ]                       │
     │                               │  )                         │
     │                               ├───────────────────────────>│
     │                               │                            │
     │                               │                         Search
     │                               │                   FDA Guidelines
     │                               │                    ICH Standards
     │                               │                            │
     │                               │  {results: [...]}          │
     │                               │<───────────────────────────┤
     │                               │                            │
     │                               │  Extract Ranges            │
     │                               │  (regex patterns)          │
     │                               │  e.g., 90-120 mmHg         │
     │                               │                            │
     │                               │  Generate YAML Rule:       │
     │                               │  - name: SBP Range Check   │
     │                               │  - type: range             │
     │                               │  - min: 90                 │
     │                               │  - max: 120                │
     │                               │  - unit: mmHg              │
     │                               │  - citations: [...]        │
     │                               │                            │
     │  {                            │                            │
     │    rule_yaml: "...",          │                            │
     │    rule_dict: {...},          │                            │
     │    confidence: "high",        │                            │
     │    citations: [               │                            │
     │      {title, url, snippet}    │                            │
     │    ],                         │                            │
     │    requires_review: true      │                            │
     │  }                            │                            │
     │<──────────────────────────────┤                            │
     │                                                             │
     │  Review & Approve                                          │
     │  Add to Rule Library                                       │
     │                                                             │
```

**Key Points:**
- AI-assisted, but requires human review
- Extracts clinical ranges from authoritative sources
- Generates YAML-ready rule with citations
- Reduces authoring time from hours to minutes

**Cost**: ~€0.05 per rule generation (1 deep search)

---

### 3. Compliance Watcher Flow (Automated)

```
Cron Schedule          Compliance Watcher         Linkup API         GitHub
  (Daily 2 AM)                                                      
      │                      │                        │                │
      │  Trigger             │                        │                │
      ├─────────────────────>│                        │                │
      │                      │                        │                │
      │                      │  For each source:      │                │
      │                      │  (FDA, ICH, EMA,       │                │
      │                      │   CDISC, TransCelerate)│                │
      │                      │                        │                │
      │                      │  search(               │                │
      │                      │    "clinical trial     │                │
      │                      │     guidance updates", │                │
      │                      │    depth="deep",       │                │
      │                      │    from_date="last_30",│                │
      │                      │    include_domains=[..]│                │
      │                      │  )                     │                │
      │                      ├───────────────────────>│                │
      │                      │                        │                │
      │                      │                  Search Recent         │
      │                      │                  Guidance Updates      │
      │                      │                        │                │
      │                      │  {results: [...]}      │                │
      │                      │<───────────────────────┤                │
      │                      │                        │                │
      │                      │  Filter HIGH impact    │                │
      │                      │  (revised, updated,    │                │
      │                      │   new requirement)     │                │
      │                      │                        │                │
      │                      │  If HIGH impact found: │                │
      │                      │  - Update YAML rules   │                │
      │                      │  - Generate PR body    │                │
      │                      │                        │                │
      │                      │  create_pull_request(  │                │
      │                      │    title="Auto:        │                │
      │                      │     Compliance Update",│                │
      │                      │    body=PR_DESC,       │                │
      │                      │    updated_rules=[...] │                │
      │                      │  )                     │                │
      │                      ├───────────────────────────────────────>│
      │                      │                        │                │
      │                      │                        │    PR Created  │
      │                      │  PR URL                │                │
      │                      │<───────────────────────────────────────┤
      │                      │                        │                │
      │                      │  send_slack_alert(     │                │
      │                      │    pr_url,             │                │
      │                      │    high_impact_updates │                │
      │                      │  )                     │                │
      │                      │                        │                │
      │                      ▼                        │                │
                    Slack Alert Sent                                  
                    Team Reviews PR                                   
```

**Key Points:**
- Fully automated, runs nightly
- Monitors 5+ regulatory sources
- Creates PR only for high-impact changes
- Requires human review before merging

**Cost**: ~€0.15 per night (5 sources × deep search)

---

## Cost Breakdown

### Monthly API Usage (Estimated)

| Service | Use Case | Frequency | Depth | Cost/Call | Monthly Cost |
|---------|----------|-----------|-------|-----------|--------------|
| Analytics | Evidence Pack | 10 reports/day × 4 metrics | deep | €0.05 | €60 |
| Quality | Rule Generation | 3 rules/day | deep | €0.05 | €4.50 |
| Compliance | Nightly Scan | 1/day × 5 sources | deep | €0.05 | €7.50 |
| **Total** | - | ~1,000 calls/month | - | - | **€72** |

**Optimization Opportunities:**
1. Use `standard` depth for testing: saves 90% (€0.005 vs €0.05)
2. Cache results for 24 hours: saves ~30%
3. Batch queries: reduce overhead
4. **Optimized monthly cost: ~€50**

---

## Integration Points

### Database Schema Additions

```sql
-- Store evidence with quality metrics
CREATE TABLE quality_evidence (
    evidence_id UUID PRIMARY KEY,
    tenant_id VARCHAR(100),
    metric_name VARCHAR(100),
    citation_title VARCHAR(500),
    citation_url TEXT,
    citation_snippet TEXT,
    source_domain VARCHAR(200),
    fetched_at TIMESTAMP,
    INDEX idx_tenant_metric (tenant_id, metric_name)
);

-- Store generated edit check rules
CREATE TABLE generated_rules (
    rule_id UUID PRIMARY KEY,
    variable_name VARCHAR(100),
    indication VARCHAR(100),
    rule_yaml TEXT,
    confidence VARCHAR(20),
    citations JSONB,
    requires_review BOOLEAN DEFAULT true,
    reviewed_by VARCHAR(100),
    approved_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Store compliance scan results
CREATE TABLE compliance_scans (
    scan_id UUID PRIMARY KEY,
    scan_date TIMESTAMP,
    source_name VARCHAR(100),
    updates_found INTEGER,
    high_impact_count INTEGER,
    pr_url TEXT,
    scan_results JSONB,
    created_at TIMESTAMP
);
```

### Environment Variables

```bash
# .env file additions
LINKUP_API_KEY=your_linkup_api_key_here

# Optional: Configuration
LINKUP_DEFAULT_DEPTH=deep
LINKUP_CACHE_TTL=86400  # 24 hours
LINKUP_MAX_RETRIES=3
LINKUP_RETRY_DELAY=2  # seconds
```

### Docker Compose Updates

```yaml
# docker-compose.yml
services:
  analytics-service:
    environment:
      - LINKUP_API_KEY=${LINKUP_API_KEY}
    
  quality-service:
    environment:
      - LINKUP_API_KEY=${LINKUP_API_KEY}
    
  compliance-watcher:
    image: synthetictrial/compliance-watcher:latest
    ports:
      - "8007:8007"
    environment:
      - LINKUP_API_KEY=${LINKUP_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
    depends_on:
      - postgres
```

---

## API Rate Limiting Strategy

### Linkup Rate Limits
- **10 queries/second** per account
- No charge for failed requests

### Your Service Rate Limiting

```python
# Add to each service
from functools import wraps
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls=10, period=1.0):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Remove old calls outside period
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()
            
            # Check rate limit
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Record call
            self.calls.append(time.time())
            return func(*args, **kwargs)
        
        return wrapper

# Usage
rate_limiter = RateLimiter(max_calls=8, period=1.0)  # 8/sec buffer

@rate_limiter
def fetch_from_linkup(query):
    return linkup_client.search(query=query, depth="deep")
```

---

## Monitoring & Alerting

### Key Metrics to Track

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram

linkup_api_calls = Counter(
    'linkup_api_calls_total',
    'Total Linkup API calls',
    ['service', 'depth', 'output_type', 'status']
)

linkup_api_duration = Histogram(
    'linkup_api_duration_seconds',
    'Linkup API call duration',
    ['service', 'depth']
)

linkup_api_cost = Counter(
    'linkup_api_cost_euros',
    'Estimated Linkup API cost',
    ['service', 'depth']
)

# Usage
with linkup_api_duration.labels('analytics', 'deep').time():
    response = linkup_client.search(...)
    
linkup_api_calls.labels('analytics', 'deep', 'searchResults', '200').inc()
linkup_api_cost.labels('analytics', 'deep').inc(0.05)  # €0.05 per deep call
```

### Alert Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: linkup
    rules:
      - alert: HighLinkupCost
        expr: sum(rate(linkup_api_cost_euros[1h])) > 5
        for: 5m
        annotations:
          summary: "Linkup costs exceed €5/hour"
      
      - alert: LinkupRateLimitExceeded
        expr: rate(linkup_api_calls_total{status="429"}[5m]) > 0.1
        for: 2m
        annotations:
          summary: "Linkup rate limit errors detected"
      
      - alert: LinkupHighLatency
        expr: linkup_api_duration_seconds{quantile="0.95"} > 10
        for: 5m
        annotations:
          summary: "Linkup API 95th percentile latency > 10s"
```

---

## Security Considerations

### 1. API Key Management
```python
# ❌ NEVER commit API keys
LINKUP_API_KEY=sk_live_abc123...

# ✅ Use environment variables
LINKUP_API_KEY = os.getenv("LINKUP_API_KEY")

# ✅ For production: Use secrets manager
from aws_secretsmanager_caching import SecretCache
secret_cache = SecretCache()
LINKUP_API_KEY = secret_cache.get_secret_string("linkup/api_key")
```

### 2. Request Validation
```python
# Validate user queries before sending to Linkup
def sanitize_query(query: str) -> str:
    # Remove potential injection attempts
    query = query.strip()
    query = re.sub(r'[^\w\s\-.,?]', '', query)
    
    # Limit length
    if len(query) > 500:
        query = query[:500]
    
    return query
```

### 3. Result Filtering
```python
# Only return safe domains to users
ALLOWED_DOMAINS = [
    "fda.gov", "ich.org", "ema.europa.eu",
    "cdisc.org", "transcelerate.org",
    "nih.gov", "who.int"
]

def filter_results(results):
    return [
        r for r in results
        if any(domain in r["url"] for domain in ALLOWED_DOMAINS)
    ]
```

---

## Disaster Recovery

### Fallback Strategy

```python
class LinkupClient:
    def __init__(self):
        self.cache = redis.Redis()
        self.fallback_enabled = True
    
    def search_with_fallback(self, query, **kwargs):
        # Try Linkup first
        try:
            return self.linkup_client.search(query, **kwargs)
        except Exception as e:
            logger.error(f"Linkup failed: {e}")
            
            if self.fallback_enabled:
                # Try cache
                cached = self.cache.get(f"linkup:{hash(query)}")
                if cached:
                    logger.info("Using cached results")
                    return json.loads(cached)
                
                # Graceful degradation
                logger.warning("No cached results, degrading gracefully")
                return {"results": [], "fallback": True}
            
            raise
```

---

## Success Metrics

### Technical KPIs
- ✅ API success rate > 99%
- ✅ Average response time < 5s
- ✅ Rate limit errors < 1%
- ✅ Monthly cost < €100

### Business KPIs
- ✅ Quality report generation time: 10 min → 2 min (80% reduction)
- ✅ Edit check authoring time: 2 hrs → 10 min (90% reduction)
- ✅ Regulatory updates detected: 100% within 24 hours
- ✅ Citation accuracy: >95% from authoritative sources

---

## Next Steps

1. **Week 1**: Evidence Pack (Low Risk, High Value)
2. **Week 2**: Edit Check Assistant (Medium Risk, Very High Value)
3. **Week 3**: Compliance Watcher (High Value, Differentiator)
4. **Week 4**: Optimization & Monitoring

**Estimated Total Implementation Time**: 3-4 weeks
**Estimated ROI**: 50-100x (time savings + risk reduction)
**Monthly Operating Cost**: €45-90

---

For detailed implementation, see:
- `linkup.md` - Complete code examples
- `IMPLEMENTATION_CHECKLIST.md` - Step-by-step tasks
- `LINKUP_QUICK_REFERENCE.md` - Quick lookup
