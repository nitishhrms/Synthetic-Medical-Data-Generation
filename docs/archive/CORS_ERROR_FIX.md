# CORS Error Fix Guide

## The Problem

You're seeing this error in your browser console:
```
Access to fetch at 'http://localhost:8001/queries' from origin 'http://localhost:3000' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause

**This is NOT actually a CORS issue!** The backend services are not running. When the browser cannot connect to the server, it reports it as a CORS error.

### How We Diagnosed This

1. ✅ Checked EDC service CORS config - properly configured to allow `localhost:3000`
2. ❌ Tested `curl http://localhost:8001/health` - Connection Refused
3. ❌ Checked running processes - No uvicorn/FastAPI services found

## Solution

### Quick Fix (In Your Terminal)

#### Option 1: Using Docker Compose (Recommended)

```bash
# Navigate to project directory
cd /path/to/Synthetic-Medical-Data-Generation

# Start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option 2: Using the Startup Script (Without Docker)

```bash
# Navigate to project directory
cd /path/to/Synthetic-Medical-Data-Generation

# Run the startup script
./start-services.sh

# Check if services are running
curl http://localhost:8001/health  # Should return {"status":"healthy"}
curl http://localhost:8003/health  # Should return {"status":"healthy"}
curl http://localhost:8002/health  # Should return {"status":"healthy"}
```

#### Option 3: Manual Service Start

Install dependencies and start each service:

```bash
# Install uvicorn
pip3 install uvicorn fastapi pandas

# Terminal 1: Start EDC Service
cd microservices/edc-service
pip3 install -r requirements.txt
cd src
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start Analytics Service
cd microservices/analytics-service
pip3 install -r requirements.txt
cd src
python3 -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload

# Terminal 3: Start Data Generation Service
cd microservices/data-generation-service
pip3 install -r requirements.txt
cd src
python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## Verification Steps

Once services are running, verify they're accessible:

```bash
# Test EDC Service
curl http://localhost:8001/health
# Expected: {"status":"healthy","service":"edc-service",...}

# Test queries endpoint (the one that was failing)
curl http://localhost:8001/queries
# Expected: [] or query data

# Test Analytics Service
curl http://localhost:8003/health
# Expected: {"status":"healthy","service":"analytics-service",...}

# Test Data Generation Service
curl http://localhost:8002/health
# Expected: {"status":"healthy","service":"data-generation-service",...}
```

## Frontend Changes (If Needed)

The RBQMDashboard.tsx is currently trying to fetch from:
- `http://localhost:8004/vitals/all` - WRONG (should be 8001)
- `http://localhost:8004/queries` - WRONG (should be 8001)

But your error shows port 8001, so you may have already fixed this locally. Just ensure:

```typescript
// Correct URLs:
const vitalsRes = await fetch('http://localhost:8001/vitals/all');
const queriesRes = await fetch('http://localhost:8001/queries');
```

## Port Reference

| Service | Port | Endpoints |
|---------|------|-----------|
| EDC Service | 8001 | `/queries`, `/subjects`, `/studies`, `/vitals`, etc. |
| Data Generation | 8002 | `/generate/mvn`, `/generate/bootstrap`, etc. |
| Analytics | 8003 | `/rbqm/summary`, `/stats/week12`, etc. |
| Quality | 8004 | `/validate/vitals`, `/checks/validate`, etc. |
| Security | 8005 | `/auth/login`, `/auth/register`, etc. |

## Troubleshooting

### Services still not starting?

1. **Check port conflicts:**
   ```bash
   # Linux/Mac
   lsof -i :8001
   lsof -i :8003

   # Windows
   netstat -ano | findstr :8001
   ```

2. **Check service logs:**
   ```bash
   # If using startup script
   tail -f /tmp/edc-service.log
   tail -f /tmp/analytics-service.log

   # If using Docker
   docker-compose logs -f edc-service
   docker-compose logs -f analytics-service
   ```

3. **Kill stuck processes:**
   ```bash
   # Find PIDs
   ps aux | grep uvicorn

   # Kill them
   kill -9 <PID>
   ```

### Still getting CORS errors after services are running?

1. **Clear browser cache:** Hard refresh with Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. **Check browser console:** Look for the actual error, not just CORS
3. **Verify frontend is using correct ports:** Check the fetch URLs in your code

## Summary

The "CORS error" was actually a "service not running" error. Once you start your backend services using one of the methods above, the error should disappear. The EDC service CORS configuration is already correct and allows requests from `localhost:3000`.
