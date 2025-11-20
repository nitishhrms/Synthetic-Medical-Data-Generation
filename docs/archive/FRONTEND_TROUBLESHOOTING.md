# Frontend Troubleshooting Guide

## ✅ Quick Start Checklist

### 1. Start Backend Services

The frontend requires **ALL 5 backend services** to be running:

```bash
# From the project root directory

# Terminal 1: Data Generation Service
cd microservices/data-generation-service/src
uvicorn main:app --reload --port 8002

# Terminal 2: Analytics Service
cd microservices/analytics-service/src
uvicorn main:app --reload --port 8003

# Terminal 3: EDC Service
cd microservices/edc-service/src
uvicorn main:app --reload --port 8004

# Terminal 4: Security Service
cd microservices/security-service/src
uvicorn main:app --reload --port 8005

# Terminal 5: Quality Service
cd microservices/quality-service/src
uvicorn main:app --reload --port 8006
```

**OR** use Docker Compose (if configured):
```bash
docker-compose up
```

### 2. Verify Backend is Running

Open these URLs in your browser - all should return JSON responses:

- http://localhost:8002/health - Data Generation Service
- http://localhost:8003/health - Analytics Service
- http://localhost:8004/health - EDC Service
- http://localhost:8005/health - Security Service ⚠️ **CRITICAL for login**
- http://localhost:8006/health - Quality Service

If any return errors or "This site can't be reached", that service is not running.

### 3. Start Frontend

```bash
cd frontend
npm install  # if not already done
npm run dev
```

Frontend will open at http://localhost:3000

## 🔍 Troubleshooting Common Issues

### Issue 1: "Cannot connect to backend service"

**Symptoms**: Login fails immediately with connection error

**Solution**:
1. Check if Security Service is running on port 8005:
   ```bash
   curl http://localhost:8005/health
   ```
2. If not running, start it:
   ```bash
   cd microservices/security-service/src
   uvicorn main:app --reload --port 8005
   ```

**How to verify**: Click "Check system health" on the login error message

---

### Issue 2: Login button doesn't work

**Symptoms**: Nothing happens when clicking "Sign In"

**Debugging steps**:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Click "Sign In" again
4. Look for error messages

**Common errors**:
- `Failed to fetch` → Backend not running
- `HTTP 404` → Wrong URL, check .env file
- `HTTP 500` → Backend error, check backend logs
- `CORS error` → CORS not configured (should be fixed already)

---

### Issue 3: Database connection errors

**Symptoms**: Backend starts but login fails with "database error"

**Solution**:
Ensure PostgreSQL is running:
```bash
# Check if PostgreSQL is running
pg_isready

# If not, start it (macOS)
brew services start postgresql

# Or (Linux)
sudo systemctl start postgresql
```

Initialize the database:
```bash
cd database
python init_db.py
```

---

### Issue 4: Port conflicts

**Symptoms**: "Address already in use" when starting services

**Solution**:
Check what's using the port:
```bash
# macOS/Linux
lsof -i :8005  # Replace with problematic port

# Kill the process
kill -9 <PID>
```

Or change the port in the backend service and update frontend .env:
```env
# frontend/.env
VITE_SECURITY_URL=http://localhost:8015  # New port
```

---

### Issue 5: CORS errors in browser console

**Symptoms**: "Access-Control-Allow-Origin" error in console

**Solution**:
This should already be fixed, but if you see it:

1. Check backend CORS config in each service's `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should allow all for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

2. Restart the backend service after changes

---

## 🧪 Testing the System

### Use the Built-in System Check

1. Go to http://localhost:3000
2. If login fails, click "Check system health"
3. Click "Check All Services"
4. All services should show "Online" (green)

### Manual API Test

Test the security service directly:
```bash
# Register a test user
curl -X POST http://localhost:8005/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123",
    "email": "test@example.com",
    "role": "researcher",
    "tenant_id": "default"
  }'

# Login
curl -X POST http://localhost:8005/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123"
  }'
```

You should get back a JSON response with an `access_token`.

---

## 🔧 Environment Configuration

Ensure `frontend/.env` has the correct URLs:

```env
VITE_DATA_GEN_URL=http://localhost:8002
VITE_ANALYTICS_URL=http://localhost:8003
VITE_EDC_URL=http://localhost:8004
VITE_SECURITY_URL=http://localhost:8005
VITE_QUALITY_URL=http://localhost:8006
```

If you changed any backend ports, update these URLs accordingly.

---

## 📋 Complete Startup Sequence

**Recommended order**:

1. ✅ Start PostgreSQL database
2. ✅ Start Redis (if using)
3. ✅ Start all 5 backend microservices (ports 8002-8006)
4. ✅ Verify all health endpoints return 200 OK
5. ✅ Start frontend dev server (port 3000)
6. ✅ Open browser to http://localhost:3000
7. ✅ Register a new user or use existing credentials
8. ✅ Test data generation

---

## 🐛 Still Having Issues?

### Enable Debug Logging

**Frontend**: Open browser DevTools → Console tab (all API calls are logged)

**Backend**: Check uvicorn logs in each terminal where services are running

### Check Backend Logs

Look for errors in the terminal where you started each service:
- `404 Not Found` → Endpoint doesn't exist
- `422 Unprocessable Entity` → Invalid request data
- `500 Internal Server Error` → Backend bug
- `Connection refused` → Service not running

### Common Root Causes

1. **Services not running** (90% of issues)
   - Check: `curl http://localhost:8005/health`

2. **Database not initialized**
   - Run: `cd database && python init_db.py`

3. **Wrong ports in .env**
   - Verify: `cat frontend/.env`

4. **Python dependencies missing**
   - Run: `pip install -r requirements.txt` in each service

---

## ✅ Verification Checklist

Before reporting an issue, verify:

- [ ] All 5 backend services are running
- [ ] All health endpoints return JSON
- [ ] Database is running and initialized
- [ ] Frontend .env file has correct URLs
- [ ] Browser console shows what error occurs
- [ ] No CORS errors in browser console
- [ ] Can register a user via curl (see above)

---

## 📞 Need Backend Code Changes?

If you need any backend CORS or configuration changes, provide:
1. The exact error message from browser console
2. Which service is failing (from System Check)
3. The backend logs from that service

Most issues are configuration/startup related, not code bugs.
