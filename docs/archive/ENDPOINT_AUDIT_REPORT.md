# Backend Endpoint Audit Report

**Date**: 2025-11-12
**Issue**: Frontend API service layer was built based on CLAUDE.md documentation, but many documented endpoints don't actually exist in the backend.

---

## 🔴 Critical Issues Summary

1. **No user registration** - Authentication is broken
2. **No study management** - EDC features completely missing
3. **No data comparison endpoints** - Quality features missing
4. **Mismatched endpoint paths** - Quality validation uses different path

---

## 📊 Service-by-Service Analysis

### 1. Security Service (Port 8005)

#### ✅ **Endpoints That Exist**
```
GET  /health
GET  /
POST /auth/login
POST /auth/validate
GET  /auth/me
POST /encryption/encrypt
POST /encryption/decrypt
POST /phi/detect
POST /audit/log
GET  /audit/logs
```

#### ❌ **Missing Endpoints (Documented in Frontend)**
```
POST /auth/register          # CRITICAL - No way to create users!
GET  /auth/verify            # Exists as /auth/validate (rename issue)
```

**Impact**: 🔴 **CRITICAL** - Users cannot register. Must create users manually in database.

**Frontend Usage**:
- `authApi.register()` - **BROKEN**
- `authApi.login()` - ✅ Works
- `authApi.verifyToken()` - ⚠️ Wrong path, should use `/auth/validate`
- `authApi.getCurrentUser()` - ✅ Works

---

### 2. Data Generation Service (Port 8002)

#### ✅ **Endpoints That Exist**
```
GET  /health
GET  /
POST /generate/rules
POST /generate/mvn
POST /generate/llm
POST /generate/ae
POST /generate/bootstrap
```

#### ❌ **Missing Endpoints (Documented in Frontend)**
```
GET  /compare                # Method comparison endpoint
GET  /data/pilot             # Real data access endpoint
```

**Impact**: 🟡 **MEDIUM** - Quality comparison and real data features missing

**Frontend Usage**:
- `dataGenerationApi.generateMVN()` - ✅ Works
- `dataGenerationApi.generateBootstrap()` - ✅ Works
- `dataGenerationApi.generateRules()` - ✅ Works
- `dataGenerationApi.generateLLM()` - ✅ Works
- `dataGenerationApi.compareMethods()` - **BROKEN**
- `dataGenerationApi.getPilotData()` - **BROKEN**

---

### 3. Analytics Service (Port 8003)

#### ✅ **Endpoints That Exist**
```
GET  /health
GET  /
POST /stats/week12
POST /stats/recist
POST /rbqm/summary
POST /csr/draft
POST /sdtm/export
POST /quality/pca-comparison
POST /quality/comprehensive
```

#### ❌ **Missing Endpoints**
```
None - All documented endpoints exist!
```

**Impact**: ✅ **NONE** - All analytics features fully functional

**Frontend Usage**: All API calls should work ✅

---

### 4. EDC Service (Port 8004)

#### ✅ **Endpoints That Exist**
```
GET  /health
GET  /
POST /validate              # Data validation
POST /repair                # Data repair
POST /store-vitals          # Store vitals data
```

#### ❌ **Missing Endpoints (Documented in Frontend)**
```
POST /studies               # Create study
GET  /studies               # List studies
GET  /studies/{study_id}    # Get study details
POST /subjects              # Enroll subject
POST /vitals                # Record vitals
GET  /subjects/{subject_id} # Get subject data
POST /import/synthetic      # Import synthetic data
```

**Impact**: 🔴 **CRITICAL** - Entire study management system missing!

**Frontend Usage**:
- `edcApi.createStudy()` - **BROKEN**
- `edcApi.listStudies()` - **BROKEN**
- `edcApi.getStudy()` - **BROKEN**
- `edcApi.importSyntheticData()` - **BROKEN**

**Note**: EDC service exists but is purely for data validation/repair, NOT study management!

---

### 5. Quality Service (Port 8006)

#### ✅ **Endpoints That Exist**
```
GET  /health
GET  /
GET  /checks/rules
POST /checks/validate       # Data validation with edit checks
POST /quality/simulate-noise # Simulate data quality issues
```

#### ❌ **Missing Endpoints (Documented in Frontend)**
```
POST /validate/vitals       # Should be /checks/validate
```

**Impact**: 🟡 **LOW** - Path mismatch only

**Frontend Usage**:
- `qualityApi.validateVitals()` - ⚠️ Wrong path, should use `/checks/validate`

---

## 🔧 Required Fixes

### Priority 1: Critical - Must Fix for Login

1. **Add Registration Endpoint** to Security Service
   - File: `microservices/security-service/src/main.py`
   - Add: `POST /auth/register`
   - Required fields: username, password, email, role, tenant_id
   - Hash passwords with bcrypt
   - Insert into users table

### Priority 2: High - Fix Frontend API Paths

2. **Fix Quality Service Path** in Frontend
   - File: `frontend/src/services/api.ts`
   - Change: `/validate/vitals` → `/checks/validate`

3. **Fix Auth Verify Path** in Frontend
   - File: `frontend/src/services/api.ts`
   - Change: `/auth/verify` → `/auth/validate`

### Priority 3: Medium - Remove Non-Existent Features

4. **Remove or Disable Missing Features**
   - Option A: Remove from frontend (compareMethods, getPilotData, all EDC features)
   - Option B: Add to backend (recommended for completeness)

---

## 📋 Recommended Action Plan

### Phase 1: Make Login Work (Critical)

1. ✅ Add `POST /auth/register` to security service
2. ✅ Update frontend to use correct auth paths
3. ✅ Test registration and login flow

### Phase 2: Fix Existing Features (High Priority)

1. ✅ Update quality validation path
2. ✅ Remove broken EDC API calls from frontend
3. ✅ Remove broken data generation comparison/pilot calls
4. ✅ Update Studies screen to show "Coming Soon" instead of API calls

### Phase 3: Add Missing Backend Features (Optional)

1. ⚠️ Add study management endpoints to EDC service (if needed)
2. ⚠️ Add comparison endpoint to data generation (if needed)
3. ⚠️ Add pilot data endpoint (if needed)

---

## 🎯 What Actually Works Right Now

### ✅ Fully Functional
- ✅ Login (once registration is added)
- ✅ Data Generation (MVN, Bootstrap, Rules, LLM)
- ✅ Analytics (Week-12 stats, RECIST, RBQM, CSR, SDTM)
- ✅ Quality Assessment (comprehensive, PCA comparison)

### ⚠️ Partially Functional
- ⚠️ Authentication (login works, registration missing)
- ⚠️ Quality Validation (exists but different path)

### ❌ Completely Non-Functional
- ❌ User Registration
- ❌ Study Management (entire feature)
- ❌ Method Comparison
- ❌ Real Data Access

---

## 📄 Files That Need Updates

1. **Backend** (if adding missing endpoints):
   - `microservices/security-service/src/main.py` - Add registration
   - `microservices/edc-service/src/main.py` - Add study management (optional)
   - `microservices/data-generation-service/src/main.py` - Add compare/pilot (optional)

2. **Frontend**:
   - `frontend/src/services/api.ts` - Fix paths, remove broken calls
   - `frontend/src/components/screens/Studies.tsx` - Remove API calls or show "Coming Soon"
   - `frontend/src/types/index.ts` - Update types to match reality

3. **Documentation**:
   - `CLAUDE.md` - Update to reflect actual endpoints
   - `frontend/README.md` - Update API integration section

---

## 🚨 Root Cause Analysis

**How This Happened**:
1. CLAUDE.md documentation was written as a **design specification**, not actual implementation
2. Frontend was built by reading CLAUDE.md and assuming all endpoints existed
3. No verification was done against actual backend code
4. Backend implements only core features, not full specification

**Lesson**: Always verify actual API endpoints before building frontend integration.

---

**Next Steps**: Awaiting user decision on which fixes to implement.
