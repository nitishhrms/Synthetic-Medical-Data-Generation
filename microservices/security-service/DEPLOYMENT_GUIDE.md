# Security Service Enhancement - Safe Deployment Guide

## ⚠️ IMPORTANT: Zero-Downtime Deployment Strategy

This guide ensures **safe deployment** without breaking your existing application.

---

## 📋 Pre-Deployment Checklist

### 1. **Backup Current Database**
```bash
# PostgreSQL backup
pg_dump -h localhost -U clinical_user clinical_trials > backup_before_security_upgrade_$(date +%Y%m%d).sql

# Or if using Docker:
docker exec -t postgres pg_dump -U clinical_user clinical_trials > backup_before_security_upgrade_$(date +%Y%m%d).sql
```

### 2. **Verify Redis is Running**
```bash
docker-compose ps redis
# or
redis-cli ping  # Should return PONG
```

### 3. **Check Current Service Status**
```bash
curl http://localhost:8005/health
# Should return: {"status": "healthy"}
```

---

## 🚀 Deployment Steps (Production-Safe)

### **Step 1: Install New Dependencies**

```bash
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/security-service

# Install new dependencies
pip install -r requirements.txt

# Verify installations
python -c "import pyotp, qrcode, PIL; print('✅ Dependencies OK')"
```

### **Step 2: Run Database Migration** (BACKWARD COMPATIBLE)

```bash
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/security-service

# Run Alembic migration
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade  -> 001_enhanced_security
# ✅ Migration successful
```

**What this does**:
- ✅ Adds new columns to `users` table with safe defaults
- ✅ Creates new RBAC tables (`roles`, `permissions`, etc.)
- ✅ Creates `security_incidents` table
- ✅ **Does NOT modify** existing data
- ✅ **Does NOT break** existing authentication

### **Step 3: Seed Roles and Permissions**

```bash
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/security-service/src

# Seed default roles and permissions
python seed_roles.py

# Expected output:
# 🌱 SEEDING ROLES AND PERMISSIONS
# ✅ Seeded 11 permissions
# ✅ Seeded 5 roles with permissions
# ✅ Migrated existing users to RBAC
# ✅ SEED COMPLETED SUCCESSFULLY!
```

**What this does**:
- ✅ Creates 5 default roles: admin, researcher, data_analyst, viewer, auditor
- ✅ Creates 11 permissions
- ✅ **Migrates existing users** to new RBAC system based on their current `role` column
- ✅ Preserves all existing user access

### **Step 4: Restart Security Service**

```bash
# If using Docker:
docker-compose restart security-service

# If running directly:
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/security-service/src
pkill -f "uvicorn main:app"
python -m uvicorn main:app --reload --port 8005 &
```

### **Step 5: Verify New Features**

```bash
# Check service status
curl http://localhost:8005/ | jq

# Expected: Version 2.0.0 with enhanced features listed

# Check health
curl http://localhost:8005/health | jq

# Test existing endpoint (should still work)
curl -X POST http://localhost:8005/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "test_password"}'
```

---

## 🔒 What's Changed vs. What's Backward Compatible

### ✅ **100% Backward Compatible**:

1. **Existing Authentication Endpoints**:
   - `/auth/login` - Still works exactly as before
   - `/auth/register` - Still works (now validates password policy)
   - `/auth/validate` - No changes
   - `/auth/me` - No changes

2. **Existing User Accounts**:
   - All existing users remain active
   - Existing passwords still work
   - Old role assignments preserved

3. **Database Schema**:
   - All new columns have safe defaults
   - No data loss or modification
   - Old code can still read `users.role` column

### ⚡ **New Features (Optional Use)**:

1. **MFA Endpoints** (New - won't affect existing users):
   - `/auth/mfa/setup` - Setup MFA for a user
   - `/auth/mfa/verify` - Verify MFA code

2. **Token Management** (New):
   - `/auth/refresh` - Refresh access token
   - `/auth/logout` - Properly revoke tokens

3. **Password Management** (New):
   - `/auth/password/change` - Change password with policy enforcement

4. **Rate Limiting** (Active but lenient):
   - Login: 5 attempts per 15 minutes
   - API calls: Role-based (100-500/min)
   - Returns 429 if exceeded

5. **Account Lockout** (Active):
   - 5 failed login attempts → 30 min lockout
   - Automatic unlock after timeout

---

## 🧪 Testing Plan

### Test 1: Existing User Login (Should Work)
```bash
curl -X POST http://localhost:8005/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "existing_user",
    "password": "existing_password"
  }'

# Expected: 200 OK with access_token
```

### Test 2: New User Registration with Password Policy
```bash
curl -X POST http://localhost:8005/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "WeakPassword",
    "role": "researcher"
  }'

# Expected: 400 Bad Request (password too weak)

curl -X POST http://localhost:8005/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "StrongP@ssw0rd123",
    "role": "researcher"
  }'

# Expected: 201 Created
```

### Test 3: Rate Limiting
```bash
# Attempt 6 failed logins rapidly
for i in {1..6}; do
  curl -X POST http://localhost:8005/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "test", "password": "wrong"}' \
    -w "\nStatus: %{http_code}\n"
  sleep 1
done

# Expected: First 5 return 401, 6th returns 429 (Too Many Requests)
```

### Test 4: Account Lockout
```bash
# After 5 failed attempts, account should be locked
curl -X POST http://localhost:8005/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "correct_password"}'

# Expected: 401 with message "Account is locked. Try again in X minutes."
```

---

## 🔧 Environment Variables (Required)

Add these to your `.env` file or environment:

```bash
# ==================== Security Service Enhanced Config ====================

# Redis (Required for rate limiting, sessions, MFA)
REDIS_HOST=redis
REDIS_PORT=6379

# JWT (Required - CHANGE THE SECRET!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MFA
MFA_ISSUER_NAME="Synthetic Medical Data Platform"

# Password Policy
PASSWORD_EXPIRY_DAYS=90
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30

# Sessions
MAX_CONCURRENT_SESSIONS=3
REFRESH_TOKEN_EXPIRY_DAYS=7

# Rate Limiting
RATE_LIMIT_ENABLED=true

# CORS (Update for your frontend)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Environment
ENVIRONMENT=development  # or 'production'
```

---

## 📊 Monitoring Post-Deployment

### Check Redis Connection:
```bash
# From within security service container or host:
python -c "
from src.redis_client import security_redis
import asyncio

async def test():
    await security_redis.connect()
    health = await security_redis.health_check()
    print(health)
    await security_redis.disconnect()

asyncio.run(test())
"
```

### Check Database Tables:
```bash
# Connect to PostgreSQL
psql -h localhost -U clinical_user -d clinical_trials

# Verify new tables exist:
\dt

# Should show:
# - roles
# - permissions
# - role_permissions
# - user_role_assignments
# - security_incidents

# Verify user table has new columns:
\d users

# Should show new columns:
# - is_active
# - is_locked
# - mfa_enabled
# - password_history
# - etc.
```

---

## ⏪ Rollback Plan (If Needed)

### Quick Rollback (Keep new features in database):
```bash
# Just restart with old code
git checkout <previous_commit>
docker-compose restart security-service
```

### Full Rollback (Remove database changes):
```bash
# Run downgrade migration
alembic downgrade -1

# Restore from backup
psql -h localhost -U clinical_user clinical_trials < backup_before_security_upgrade_YYYYMMDD.sql

# Restart service
docker-compose restart security-service
```

---

## 🚨 Troubleshooting

### Issue: Service won't start
**Check**:
```bash
# Check logs
docker-compose logs security-service

# Common issues:
# 1. Redis not running: docker-compose up -d redis
# 2. Missing dependencies: pip install -r requirements.txt
# 3. Database connection: Check DATABASE_URL env var
```

### Issue: Existing users can't login
**Check**:
```bash
# Verify password hasn't changed
SELECT username, is_active, is_locked FROM users WHERE username = 'problem_user';

# If locked, unlock manually:
UPDATE users SET is_locked = false, locked_until = NULL, failed_login_attempts = 0 WHERE username = 'problem_user';
```

### Issue: Rate limiting too strict
**Temporary fix**:
```bash
# Disable rate limiting temporarily
export RATE_LIMIT_ENABLED=false
docker-compose restart security-service
```

---

## ✅ Post-Deployment Verification Checklist

- [ ] All existing users can login
- [ ] New users can register
- [ ] Password policy is enforced
- [ ] Rate limiting is working (test with 6 failed logins)
- [ ] Redis connection is healthy
- [ ] Database migration completed successfully
- [ ] Roles and permissions seeded
- [ ] No errors in service logs
- [ ] `/health` endpoint returns healthy
- [ ] API documentation accessible at `/docs`

---

## 📞 Support

If you encounter issues during deployment:

1. **Check logs**: `docker-compose logs -f security-service`
2. **Verify environment variables**: `docker-compose config | grep -A 10 security-service`
3. **Test Redis**: `redis-cli ping`
4. **Check database connection**: `psql -h localhost -U clinical_user -d clinical_trials -c "\dt"`

---

**Last Updated**: 2025-11-14
**Version**: 2.0.0 (Enhanced Security)
**Backward Compatible**: ✅ Yes
