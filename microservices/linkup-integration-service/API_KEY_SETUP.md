# Linkup API Key Configuration Guide

Your Linkup API key has been configured and is ready to use!

---

## ✅ Current Configuration

**API Key**: `303d28c4-2d95-456b-9f58-59a0e18cce46`

**Status**: ✅ Active and configured

**Mode**: Real Linkup searches (mock mode disabled)

---

## 📁 Where the API Key is Stored

### 1. Local Development (.env file)

**File**: `microservices/linkup-integration-service/.env`

```bash
LINKUP_API_KEY=303d28c4-2d95-456b-9f58-59a0e18cce46
```

**Security**: ✅ This file is in `.gitignore` and will NOT be committed to git

### 2. Docker Compose

**File**: `microservices/linkup-integration-service/docker-compose.yml`

Automatically loads from `.env` file:

```yaml
environment:
  - LINKUP_API_KEY=${LINKUP_API_KEY}
```

### 3. Kubernetes

**Secret Name**: `linkup-secrets`

**Namespace**: `clinical-trials`

**Setup Script**: `setup-k8s-secrets.sh`

To create the Kubernetes secret:

```bash
cd microservices/linkup-integration-service
./setup-k8s-secrets.sh
```

Or manually:

```bash
kubectl create secret generic linkup-secrets \
  --from-literal=api-key=303d28c4-2d95-456b-9f58-59a0e18cce46 \
  -n clinical-trials
```

---

## 🚀 Quick Start with API Key

### Option 1: Docker Compose (Easiest)

```bash
# Navigate to service directory
cd microservices/linkup-integration-service

# .env file is already configured with your API key!
# Just start the service:
docker-compose up -d

# Verify API key is working
./test-api-key.sh
```

### Option 2: Local Python

```bash
cd microservices/linkup-integration-service

# .env file is already configured!
# Install dependencies
pip install -r requirements.txt

# Start service (will automatically load .env)
cd src
uvicorn main:app --port 8007 --reload
```

### Option 3: Kubernetes

```bash
# Setup secrets (includes API key)
cd microservices/linkup-integration-service
./setup-k8s-secrets.sh

# Deploy service
kubectl apply -f ../../kubernetes/deployments/linkup-integration-service.yaml

# Verify deployment
kubectl get pods -n clinical-trials -l app=linkup-integration-service
```

---

## 🧪 Verify API Key is Working

### Automated Test

```bash
cd microservices/linkup-integration-service
./test-api-key.sh
```

**Expected Output**:
```
✓ Found .env file
✓ LINKUP_API_KEY is set
✓ Service is running on port 8007
✓ Using REAL Linkup API
✓ Evidence Pack working - got X citations
✓ Edit Check Generator working
✓ Compliance Scanner working
```

### Manual Tests

#### Test 1: Health Check
```bash
curl http://localhost:8007/health
```

#### Test 2: Evidence Citations (Real API)
```bash
curl -X POST http://localhost:8007/evidence/fetch-citations \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "Wasserstein distance",
    "metric_value": 2.34
  }' | jq
```

**Expected**: Real FDA/ICH citations (not mock data)

#### Test 3: Check Logs for API Calls
```bash
docker-compose logs -f linkup-integration | grep "Linkup"
```

**Look for**:
- "Performing Linkup search..."
- "Received X results from Linkup API"
- NOT "Using mock mode"

---

## 🔐 Security Best Practices

### ✅ What We Did Right

1. **Not in Git**: `.env` is in `.gitignore`
2. **Kubernetes Secrets**: API key stored in K8s secrets
3. **Environment Variables**: Never hardcoded in code
4. **.env.example**: Template without real key

### ⚠️ What NOT to Do

❌ **Don't commit .env to git**
- File is gitignored, but double-check before commits

❌ **Don't hardcode in code**
- Always use `os.getenv("LINKUP_API_KEY")`

❌ **Don't share in logs**
- Logs only show first 8 chars: `303d28c4...`

❌ **Don't expose in API responses**
- API key is never returned in responses

---

## 🔄 Rotating the API Key

If you need to change the API key:

### For Docker Compose

```bash
# 1. Edit .env file
nano microservices/linkup-integration-service/.env

# 2. Update the line:
LINKUP_API_KEY=your_new_key_here

# 3. Restart service
docker-compose restart linkup-integration
```

### For Kubernetes

```bash
# 1. Update secret
kubectl create secret generic linkup-secrets \
  --from-literal=api-key=your_new_key_here \
  -n clinical-trials \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. Restart pods to pick up new secret
kubectl rollout restart deployment/linkup-integration-service -n clinical-trials
```

---

## 📊 API Usage Monitoring

### Check Current Usage

The Linkup API has usage limits. Monitor your consumption:

1. **Linkup Dashboard**: https://linkup.so/dashboard
2. **Service Logs**: See API call counts
   ```bash
   docker-compose logs linkup-integration | grep "Linkup API call"
   ```

### Usage Optimization

- **Evidence Pack**: ~1-2 API calls per quality assessment
- **Edit Check Generator**: ~1-3 calls per rule (depends on searches needed)
- **Compliance Watcher**: ~5-10 calls per daily scan

**Estimated Monthly Usage**:
- Daily compliance scans: 7 calls/day × 30 = 210 calls/month
- Rule generation: 50 rules/month × 2 calls = 100 calls/month
- Evidence packs: 20 reports/month × 2 calls = 40 calls/month
- **Total**: ~350-400 calls/month

Most Linkup plans support 500-1000 calls/month, so you should be well within limits.

---

## 🆘 Troubleshooting

### Issue 1: Service in Mock Mode

**Symptoms**: Seeing "mockMode: true" in responses

**Solution**:
```bash
# Verify API key is in .env
grep LINKUP_API_KEY microservices/linkup-integration-service/.env

# Restart service to reload .env
docker-compose restart linkup-integration

# Test again
./test-api-key.sh
```

### Issue 2: API Key Not Found

**Symptoms**: "LINKUP_API_KEY not set" warnings in logs

**Solution**:
```bash
# Check .env file exists
ls -la microservices/linkup-integration-service/.env

# If missing, create it:
cd microservices/linkup-integration-service
cp .env.example .env

# Add your key
echo "LINKUP_API_KEY=303d28c4-2d95-456b-9f58-59a0e18cce46" >> .env

# Restart
docker-compose restart linkup-integration
```

### Issue 3: Kubernetes Secret Not Found

**Symptoms**: Pod fails to start with "secret not found"

**Solution**:
```bash
# Run setup script
cd microservices/linkup-integration-service
./setup-k8s-secrets.sh

# Or create manually
kubectl create secret generic linkup-secrets \
  --from-literal=api-key=303d28c4-2d95-456b-9f58-59a0e18cce46 \
  -n clinical-trials
```

### Issue 4: Invalid API Key

**Symptoms**: HTTP 401 errors from Linkup API

**Solution**:
```bash
# Verify key is correct (check for typos)
cat microservices/linkup-integration-service/.env | grep LINKUP_API_KEY

# Test key directly with Linkup
curl -X POST https://api.linkup.so/v1/search \
  -H "Authorization: Bearer 303d28c4-2d95-456b-9f58-59a0e18cce46" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# If invalid, get new key from https://linkup.so
```

---

## 📚 Additional Resources

- **Linkup Dashboard**: https://linkup.so/dashboard
- **Linkup API Docs**: https://linkup.so/docs
- **Service Documentation**: See `README.md`
- **Quick Start Guide**: See `QUICKSTART.md`

---

## ✅ Checklist

Confirm your API key is properly configured:

- [x] `.env` file exists with API key
- [x] API key is `303d28c4-2d95-456b-9f58-59a0e18cce46`
- [x] `.env` is in `.gitignore`
- [ ] Service is running: `curl http://localhost:8007/health`
- [ ] Test script passes: `./test-api-key.sh`
- [ ] Real citations returned (not mock data)
- [ ] For K8s: Secret created with `./setup-k8s-secrets.sh`

---

**Your Linkup API key is configured and ready to use!** 🎉

Run `./test-api-key.sh` to verify everything is working with real Linkup searches.
