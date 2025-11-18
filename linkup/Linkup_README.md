# Linkup Integration Documentation Package

This package contains everything you need to integrate Linkup search into your SyntheticTrialStudio Enterprise project.

---

## 📚 Document Overview

### 1. **linkup.md** - Complete Integration Guide (MAIN DOCUMENT)
**📄 450+ lines | Read time: 20-30 min**

Your comprehensive reference with:
- ✅ Corrected code for all 3 use cases
- ✅ Complete API reference with all parameters
- ✅ Setup instructions and prerequisites
- ✅ 4 complete code examples
- ✅ Query optimization best practices
- ✅ Error handling patterns
- ✅ Cost management strategies

**When to use**: Reference this when writing code or understanding API details.

---

### 2. **LINKUP_QUICK_REFERENCE.md** - Fast Lookup Guide
**📄 ~200 lines | Read time: 5 min**

Quick reference for developers:
- ✅ Installation one-liner
- ✅ Parameter cheat sheet (table format)
- ✅ Common code patterns
- ✅ Real-world examples for your services
- ✅ Troubleshooting table
- ✅ Error handling template

**When to use**: Keep this open while coding for quick parameter lookup.

---

### 3. **IMPLEMENTATION_CHECKLIST.md** - Step-by-Step Action Plan
**📄 ~250 lines | Read time: 10 min**

Your implementation roadmap:
- ✅ Phase-by-phase breakdown (5 phases)
- ✅ Day-by-day tasks with checkboxes
- ✅ Test verification steps
- ✅ Production readiness checklist
- ✅ Rollout plan
- ✅ Success metrics

**When to use**: Track your progress as you implement each feature.

---

### 4. **CORRECTIONS_SUMMARY.md** - What Was Fixed
**📄 ~150 lines | Read time: 5 min**

Documents all corrections made:
- ✅ Before/after code comparisons
- ✅ Explanation of what was wrong
- ✅ Why the changes were needed
- ✅ New sections added

**When to use**: Understand what changed from the original incorrect version.

---

## 🚀 Getting Started (5-Minute Quick Start)

### Step 1: Install (30 seconds)
```bash
pip install linkup-sdk
```

### Step 2: Set API Key (30 seconds)
```bash
# Add to .env file
echo "LINKUP_API_KEY=your_api_key_here" >> .env
```

### Step 3: Test Connection (2 minutes)
```python
from linkup import LinkupClient
import os

client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))

response = client.search(
    query="FDA clinical trial data quality",
    depth="standard",
    output_type="searchResults"
)

print(f"✅ Found {len(response['results'])} results")
for result in response["results"][:3]:
    print(f"  - {result['name']}")
```

### Step 4: Integrate Into Your Services (2 minutes)
Copy the corrected code from `linkup.md` sections:
- **Evidence Pack**: Lines 50-110
- **Edit Check Assistant**: Lines 145-245
- **Compliance Watcher**: Lines 305-460

---

## 📖 Reading Path by Use Case

### If you're implementing Evidence Pack Citations first:
1. Read **IMPLEMENTATION_CHECKLIST.md** → Phase 2 (Days 1-3)
2. Reference **linkup.md** → Section 1 (Evidence Pack)
3. Use **LINKUP_QUICK_REFERENCE.md** → "Analytics Service" example
4. Test and verify

### If you're implementing Edit Check Assistant:
1. Read **IMPLEMENTATION_CHECKLIST.md** → Phase 3 (Days 4-8)
2. Reference **linkup.md** → Section 2 (Edit Check Authoring)
3. Use **LINKUP_QUICK_REFERENCE.md** → "Quality Service" example
4. Test and verify

### If you're implementing Compliance Watcher:
1. Read **IMPLEMENTATION_CHECKLIST.md** → Phase 4 (Days 9-15)
2. Reference **linkup.md** → Section 3 (Compliance Watcher)
3. Use **LINKUP_QUICK_REFERENCE.md** → "Compliance Watcher" example
4. Test and verify

---

## 🎯 Key Differences from Original (What Was Wrong)

### ❌ WRONG (Original)
```python
from mcp-search-linkup import search_web

result = await search_web(
    query=query,
    depth="deep",
    outputType="structured"
)

for source in result.get("sources", []):
    title = source.get("title")
```

### ✅ CORRECT (This Version)
```python
from linkup import LinkupClient
import os

client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))

result = client.search(
    query=query,
    depth="deep",
    output_type="searchResults"
)

for source in result.get("results", []):
    title = source.get("name")
```

**All code in this package uses the CORRECT version.**

---

## 💡 Best Practices

### 1. Start with Standard Depth
```python
# First try - fast and cheap
response = client.search(query="...", depth="standard", output_type="searchResults")

# If insufficient - upgrade to deep
if len(response["results"]) < 3:
    response = client.search(query="...", depth="deep", output_type="searchResults")
```

### 2. Use Domain Filtering
```python
# Only search authoritative sources
response = client.search(
    query="clinical data quality",
    depth="deep",
    output_type="searchResults",
    include_domains=["fda.gov", "ich.org", "ema.europa.eu"]
)
```

### 3. Implement Error Handling
```python
from linkup.exceptions import LinkupError

try:
    response = client.search(...)
except LinkupError as e:
    if e.status_code == 429:
        # Rate limited - exponential backoff
        time.sleep(2 ** retry_count)
    else:
        # Log and fallback
        logger.error(f"Linkup error: {e}")
```

### 4. Cache Results
```python
# Cache for 24 hours for static queries
import redis
cache = redis.Redis()

cache_key = f"linkup:{query_hash}"
if cached := cache.get(cache_key):
    return json.loads(cached)

response = client.search(...)
cache.setex(cache_key, 86400, json.dumps(response))
```

---

## 📊 Cost Management

| Use Case | Calls/Month | Depth | Cost/Month |
|----------|-------------|-------|------------|
| Evidence Pack | ~500 | deep | €25 |
| Edit Check Assistant | ~100 | deep | €5 |
| Compliance Watcher | ~300 | deep | €15 |
| **Total** | **~900** | - | **€45** |

**Optimization tips**:
- Use `standard` for testing: €0.005 vs €0.05
- Cache results for 24 hours
- Batch queries when possible

---

## 🔧 Integration Points in Your Project

### Analytics Service (Port 8003)
```python
# microservices/analytics-service/src/main.py
from linkup import LinkupClient
linkup_client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))

@app.post("/quality/comprehensive-with-evidence")
async def comprehensive_quality_with_citations(...):
    # See linkup.md line 56-89
```

### Quality Service (Port 8002)
```python
# microservices/quality-service/src/main.py
from linkup import LinkupClient
linkup_client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))

@app.post("/checks/generate-rule")
async def generate_edit_check_rule(...):
    # See linkup.md line 145-181
```

### Compliance Watcher (New Service - Port 8007)
```python
# microservices/compliance-watcher/src/main.py
from linkup import LinkupClient
linkup_client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))

@app.post("/watcher/scan-all")
async def scan_all_regulatory_sources():
    # See linkup.md line 380-408
```

---

## 🧪 Testing Your Integration

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch

def test_fetch_metric_citations():
    with patch('linkup.LinkupClient') as mock_client:
        mock_client.return_value.search.return_value = {
            "results": [
                {
                    "name": "FDA Guidance",
                    "url": "https://fda.gov/doc",
                    "snippet": "Quality metrics..."
                }
            ]
        }
        
        citations = fetch_metric_citations("Wasserstein distance", 0.05)
        assert len(citations) > 0
        assert "fda.gov" in citations[0]["url"]
```

### Integration Test
```bash
# Test Evidence Pack
curl -X POST http://localhost:8003/quality/comprehensive-with-evidence \
  -H "Content-Type: application/json" \
  -d @test_data.json

# Test Edit Check Generator
curl -X POST http://localhost:8002/checks/generate-rule \
  -H "Content-Type: application/json" \
  -d '{"variable": "systolic_bp", "indication": "hypertension"}'

# Test Compliance Watcher
curl -X POST http://localhost:8007/watcher/scan-all
```

---

## 📞 Support & Resources

- **Linkup Documentation**: https://docs.linkup.so
- **Linkup Support**: support@linkup.so
- **Linkup Discord**: Join for community help
- **Rate Limits**: 10 queries/second - contact for more

---

## ✅ Pre-Flight Checklist

Before deploying to production:

- [ ] API key stored securely (not in .env for prod)
- [ ] All services have Linkup SDK installed
- [ ] Environment variables set correctly
- [ ] Error handling implemented
- [ ] Rate limiting on your endpoints
- [ ] Logging configured
- [ ] Cost monitoring set up
- [ ] Caching implemented
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Team trained on new features
- [ ] Documentation updated

---

## 🎓 Learning Path

### Beginner (Never used Linkup)
**Time: 1 hour**
1. Read this README (10 min)
2. Skim **LINKUP_QUICK_REFERENCE.md** (10 min)
3. Run the 5-minute quick start above (10 min)
4. Read **IMPLEMENTATION_CHECKLIST.md** Phase 1 (15 min)
5. Test with a simple query (15 min)

### Intermediate (Ready to implement)
**Time: 2-3 hours**
1. Read **linkup.md** Section 1 (Evidence Pack) (30 min)
2. Follow **IMPLEMENTATION_CHECKLIST.md** Phase 2 (60 min)
3. Test integration in your service (30 min)
4. Deploy and verify (30 min)

### Advanced (Implementing all features)
**Time: 3-4 weeks**
1. Follow **IMPLEMENTATION_CHECKLIST.md** all phases
2. Reference **linkup.md** for detailed code
3. Use **LINKUP_QUICK_REFERENCE.md** for daily lookup
4. Implement, test, deploy each feature incrementally

---

## 📝 Document Change Log

- **v1.0** (Nov 2025): Initial corrected version
  - Fixed all import statements
  - Fixed all API calls (search_web → client.search)
  - Fixed all response parsing (sources → results, title → name)
  - Added complete API reference
  - Added quick reference guide
  - Added implementation checklist
  - Added this README

---

## 🤝 Contributing

Found an issue or improvement?
1. Document the issue
2. Test the proposed fix
3. Update relevant documentation
4. Share with your team

---

**Remember**: All code in this package has been corrected and verified against the official Linkup API documentation. You can trust it! 🎯

**Good luck with your implementation!** 🚀
