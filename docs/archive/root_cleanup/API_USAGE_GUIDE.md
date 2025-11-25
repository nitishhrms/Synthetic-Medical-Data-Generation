# 🚀 API Usage Guide - Working Endpoints

Your services are running and the core generation endpoints are working! Here's how to use them.

## ✅ Working Endpoints

### **1. Data Generation Service** (Port 8002)
- `/generate/rules` - Rules-based generation
- `/generate/mvn` - MVN (Multivariate Normal) generation
- `/generate/llm` - LLM-based generation with auto-repair
- `/generate/ae` - Adverse Events generation
- `/health` - Health check
- `/` - Service info

### **2. Analytics Service** (Port 8003)
- `/stats/week12` - Week-12 statistics
- `/stats/recist` - RECIST analysis
- `/rbqm/summary` - RBQM summary
- `/csr/draft` - CSR draft generation
- `/sdtm/export` - SDTM export
- `/health` - Health check

## 🎯 Quick Start - Using the API

### **Method 1: Interactive API Documentation (EASIEST)**

**Open in your browser:**
- Data Generation: http://localhost:8002/docs
- Analytics: http://localhost:8003/docs

**Steps:**
1. Click on any endpoint (e.g., `/generate/rules`)
2. Click "Try it out"
3. Modify the parameters
4. Click "Execute"
5. See the results!

### **Method 2: Using curl (Command Line)**

#### Generate Vitals Data (Rules-Based)
```bash
curl -X POST "http://localhost:8002/generate/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 50,
    "target_effect": -5.0,
    "seed": 42
  }'
```

#### Generate Vitals Data (MVN)
```bash
curl -X POST "http://localhost:8002/generate/mvn" \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 50,
    "target_effect": -5.0,
    "seed": 123,
    "train_source": "pilot"
  }'
```

#### Generate Adverse Events
```bash
curl -X POST "http://localhost:8002/generate/ae" \
  -H "Content-Type: application/json" \
  -d '{
    "n_subjects": 30,
    "seed": 7
  }'
```

#### Generate with LLM (Requires API Key)
```bash
curl -X POST "http://localhost:8002/generate/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "indication": "Solid Tumor (Immuno-Oncology)",
    "n_per_arm": 20,
    "target_effect": -5.0,
    "model": "gpt-4o-mini",
    "api_key": "YOUR_OPENAI_API_KEY",
    "extra_instructions": "",
    "max_repair_iters": 2
  }'
```

### **Method 3: Using Python**

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8002"

# Generate vitals data using rules
response = requests.post(
    f"{BASE_URL}/generate/rules",
    json={
        "n_per_arm": 50,
        "target_effect": -5.0,
        "seed": 42
    }
)

data = response.json()
print(f"Generated {len(data['data'])} records")
print(f"First subject: {data['data'][0]}")

# Save to file
with open('generated_vitals.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Data saved to generated_vitals.json")
```

### **Method 4: Using Postman**

1. Open Postman
2. Create a new POST request
3. URL: `http://localhost:8002/generate/rules`
4. Headers: `Content-Type: application/json`
5. Body (raw JSON):
```json
{
  "n_per_arm": 50,
  "target_effect": -5.0,
  "seed": 42
}
```
6. Click Send

## 📊 Analytics Endpoints

### Run Week-12 Statistics
```bash
curl -X POST "http://localhost:8003/stats/week12" \
  -H "Content-Type: application/json" \
  -d '{
    "vitals_data": [...],
    "test_type": "welch"
  }'
```

### Generate RECIST Analysis
```bash
curl -X POST "http://localhost:8003/stats/recist" \
  -H "Content-Type: application/json" \
  -d '{
    "tumor_data": [...]
  }'
```

## 📝 Complete Workflow Example

### Step 1: Generate Vitals Data
```bash
curl -X POST "http://localhost:8002/generate/rules" \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm":50,"target_effect":-5.0,"seed":42}' \
  > vitals_data.json
```

### Step 2: Generate Adverse Events
```bash
curl -X POST "http://localhost:8002/generate/ae" \
  -H "Content-Type: application/json" \
  -d '{"n_subjects":30,"seed":7}' \
  > ae_data.json
```

### Step 3: Analyze Vitals Data
```bash
curl -X POST "http://localhost:8003/stats/week12" \
  -H "Content-Type: application/json" \
  -d @vitals_data.json \
  > analysis_results.json
```

## 🎨 Sample Response Format

### Vitals Data Response:
```json
{
  "data": [
    {
      "SubjectID": "RA001-001",
      "VisitName": "Screening",
      "TreatmentArm": "Active",
      "SystolicBP": 127,
      "DiastolicBP": 86,
      "HeartRate": 63,
      "Temperature": 36.21
    },
    ...
  ],
  "metadata": {
    "n_subjects": 100,
    "method": "rules",
    "generated_at": "2025-11-21T..."
  }
}
```

## 🔍 Checking Service Status

### Check if services are healthy:
```bash
curl http://localhost:8002/health
curl http://localhost:8003/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "data-generation-service",
  "timestamp": "2025-11-21T...",
  "database": "connected",
  "cache": "connected"
}
```

## 📖 Full API Documentation

**Interactive Docs:**
- http://localhost:8002/docs (Swagger UI)
- http://localhost:8002/redoc (ReDoc UI)
- http://localhost:8003/docs (Analytics Swagger UI)

## 💡 Tips

1. **Start with Rules-based**: Fastest and doesn't require API keys
2. **Use MVN for realistic correlations**: Better for trial simulation
3. **LLM for complex scenarios**: Requires OpenAI API key but most flexible
4. **Save responses**: All endpoints return JSON you can save to files
5. **Adjust parameters**: Change n_per_arm, target_effect, seed for different results

## 🎯 Common Use Cases

### Quick Test Data Generation:
```bash
curl -X POST "http://localhost:8002/generate/rules" \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm":10,"target_effect":-8.0,"seed":1}' | jq '.'
```

### Large Dataset Generation:
```bash
curl -X POST "http://localhost:8002/generate/mvn" \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm":500,"target_effect":-5.0,"seed":42}' | jq '.data | length'
```

## ✅ Your Services Are Ready!

- ✅ Data Generation: http://localhost:8002/docs
- ✅ Analytics: http://localhost:8003/docs
- ✅ Health checks passing
- ✅ AACT data integrated (557K+ trials)

**Start generating synthetic clinical trial data now!**
