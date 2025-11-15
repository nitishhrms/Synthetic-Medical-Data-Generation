# CLAUDE.md - Comprehensive Platform Reference for AI Assistants

## 📋 Document Purpose

This document provides a comprehensive reference of the **entire Synthetic Medical Data Generation platform** - both backend microservices and frontend React application. Use this as your primary reference when working on any part of the system to understand the architecture, conventions, and integration patterns.

**Last Updated**: 2025-11-15
**Backend Status**: ✅ Complete (pending million-scale optimizations)
**Frontend Status**: ✅ Complete and Integrated

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY (Port 8000)                    │
│                     FastAPI + Request Routing                       │
└──────────────┬──────────────────────────────────────────────────────┘
               │
     ┌─────────┴─────────┬──────────────┬──────────────┬──────────────┐
     │                   │              │              │              │
┌────▼────┐      ┌──────▼──────┐  ┌───▼─────┐  ┌─────▼──────┐  ┌───▼──────┐
│  Data   │      │  Analytics  │  │   EDC   │  │  Security  │  │ Quality  │
│Generation│      │   Service   │  │ Service │  │  Service   │  │ Service  │
│(Port 8002)│     │ (Port 8003) │  │(Pt 8004)│  │(Port 8005) │  │(Pt 8006) │
└────┬────┘      └──────┬──────┘  └───┬─────┘  └─────┬──────┘  └───┬──────┘
     │                  │              │              │              │
     └──────────────────┴──────────────┴──────────────┴──────────────┘
                                       │
                         ┌─────────────▼──────────────┐
                         │   PostgreSQL Database       │
                         │   + Redis Cache             │
                         └────────────────────────────┘
```

### Technology Stack

**Backend Framework**: FastAPI (Python 3.9+)
**Database**: PostgreSQL 14+ with SQLAlchemy ORM
**Caching**: Redis 7
**Authentication**: JWT tokens
**API Docs**: OpenAPI/Swagger (auto-generated)
**Deployment**: Docker + Kubernetes

---

## 🔐 Authentication & Security

### JWT Authentication

**Token Format**:
```json
{
  "user_id": "12345",
  "tenant_id": "tenant_abc",
  "username": "john.doe",
  "role": "researcher",
  "exp": 1700000000
}
```

**Headers Required**:
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### User Roles

| Role | Permissions | Endpoints Access |
|------|-------------|------------------|
| **admin** | Full access, user management | All endpoints |
| **researcher** | Generate data, view analytics | Generate, Analytics, EDC (read) |
| **viewer** | Read-only access | Analytics (read-only) |

### Security Service (Port 8005)

**Base URL**: `http://localhost:8005`

#### Endpoints

**1. User Authentication**
```http
POST /auth/login
Content-Type: application/json

Request:
{
  "username": "john.doe",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "12345",
    "username": "john.doe",
    "role": "researcher",
    "tenant_id": "tenant_abc"
  }
}
```

**2. User Registration**
```http
POST /auth/register
Content-Type: application/json

Request:
{
  "username": "jane.smith",
  "password": "secure_password",
  "email": "jane@example.com",
  "role": "researcher",
  "tenant_id": "tenant_abc"
}

Response:
{
  "user_id": "12346",
  "message": "User registered successfully"
}
```

**3. Token Verification**
```http
GET /auth/verify
Authorization: Bearer <token>

Response:
{
  "valid": true,
  "user_id": "12345",
  "expires_at": "2025-11-13T10:00:00Z"
}
```

**4. Get Current User**
```http
GET /auth/me
Authorization: Bearer <token>

Response:
{
  "user_id": "12345",
  "username": "john.doe",
  "email": "john@example.com",
  "role": "researcher",
  "tenant_id": "tenant_abc",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## 🎲 Data Generation Service (Port 8002)

**Base URL**: `http://localhost:8002`
**Purpose**: Generate synthetic clinical trial data using multiple methods

### Generation Methods

1. **MVN (Multivariate Normal)** - Statistical distribution-based
2. **Bootstrap** - Resampling from real data with jitter
3. **Rules-based** - Deterministic generation with business rules
4. **LLM** - OpenAI GPT-4o-mini powered generation

### Core Data Model

**Synthetic Vitals Record**:
```typescript
interface VitalsRecord {
  SubjectID: string;        // e.g., "RA001-001"
  VisitName: string;        // "Screening" | "Day 1" | "Week 4" | "Week 12"
  TreatmentArm: string;     // "Active" | "Placebo"
  SystolicBP: number;       // 95-200 mmHg
  DiastolicBP: number;      // 55-130 mmHg
  HeartRate: number;        // 50-120 bpm
  Temperature: number;      // 35.0-40.0 °C
}
```

### Endpoints

#### 1. Generate with MVN
```http
POST /generate/mvn
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "n_per_arm": 50,           // Subjects per treatment arm (default: 50)
  "target_effect": -5.0,     // Target SBP reduction in mmHg (default: -5.0)
  "seed": 123                // Random seed for reproducibility (optional)
}

Response:
{
  "data": [
    {
      "SubjectID": "RA001-001",
      "VisitName": "Screening",
      "TreatmentArm": "Active",
      "SystolicBP": 142,
      "DiastolicBP": 88,
      "HeartRate": 72,
      "Temperature": 36.7
    },
    // ... 400 total records (100 subjects × 4 visits)
  ],
  "metadata": {
    "records": 400,
    "subjects": 100,
    "method": "mvn",
    "generation_time_ms": 28
  }
}
```

**Performance**: ~29,000 records/second
**Use Case**: Fast, statistically realistic data

#### 2. Generate with Bootstrap
```http
POST /generate/bootstrap
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "n_per_arm": 50,
  "target_effect": -5.0,
  "jitter_frac": 0.05,      // Gaussian jitter fraction (default: 0.05)
  "seed": 42
}

Response:
{
  "data": [ /* VitalsRecord[] */ ],
  "metadata": {
    "records": 568,           // Variable due to resampling
    "subjects": 100,
    "method": "bootstrap",
    "generation_time_ms": 30
  }
}
```

**Performance**: ~140,000 records/second
**Use Case**: Preserves real data characteristics, fast

#### 3. Generate with Rules
```http
POST /generate/rules
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "n_per_arm": 50,
  "target_effect": -5.0,
  "seed": 777
}

Response:
{
  "data": [ /* VitalsRecord[] */ ],
  "metadata": {
    "records": 400,
    "subjects": 100,
    "method": "rules",
    "generation_time_ms": 50
  }
}
```

**Performance**: ~80,000 records/second
**Use Case**: Deterministic, business-rule driven

#### 4. Generate with LLM
```http
POST /generate/llm
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "indication": "Hypertension",
  "n_per_arm": 50,
  "target_effect": -5.0,
  "api_key": "sk-...",      // OpenAI API key
  "model": "gpt-4o-mini"    // Optional, default: gpt-4o-mini
}

Response:
{
  "data": [ /* VitalsRecord[] */ ],
  "metadata": {
    "records": 200,           // Variable, depends on LLM
    "subjects": 50,
    "method": "llm",
    "generation_time_ms": 2500,
    "prompt_used": "Generate a VITALS CSV..."
  }
}
```

**Performance**: ~70 records/second (LLM latency)
**Use Case**: Creative, context-aware generation

#### 5. Compare Methods
```http
GET /compare
Query Parameters:
  - n_per_arm: 50 (default)
  - target_effect: -5.0 (default)

Response:
{
  "mvn": { /* VitalsRecord[] */ },
  "bootstrap": { /* VitalsRecord[] */ },
  "rules": { /* VitalsRecord[] */ },
  "comparison": {
    "statistical_tests": { /* KS test results */ },
    "performance": {
      "mvn_time_ms": 28,
      "bootstrap_time_ms": 30,
      "rules_time_ms": 50
    }
  }
}
```

### Real Data Source

**File**: `data/pilot_trial_cleaned.csv`
**Records**: 945 (cleaned and validated)
**Source**: CDISC SDTM Pilot Study
**Validation Applied**: Range checks, duplicate removal, missing value imputation

**Access via API**:
```http
GET /data/pilot
Response: VitalsRecord[] (945 records)
```

---

## 📊 Analytics Service (Port 8003)

**Base URL**: `http://localhost:8003`
**Purpose**: Statistical analysis, RBQM, CSR generation, quality metrics

### Endpoints

#### 1. Week-12 Statistics (Efficacy Analysis)
```http
POST /stats/week12
Content-Type: application/json

Request:
{
  "vitals_data": [ /* VitalsRecord[] */ ]
}

Response:
{
  "treatment_groups": {
    "Active": {
      "n": 50,
      "mean_systolic": 135.2,
      "std_systolic": 10.4,
      "se_systolic": 1.47
    },
    "Placebo": {
      "n": 50,
      "mean_systolic": 140.1,
      "std_systolic": 9.8,
      "se_systolic": 1.39
    }
  },
  "treatment_effect": {
    "difference": -4.9,
    "se_difference": 2.03,
    "t_statistic": -2.41,
    "p_value": 0.018,
    "ci_95_lower": -8.9,
    "ci_95_upper": -0.9
  },
  "interpretation": {
    "significant": true,
    "effect_size": "moderate",
    "clinical_relevance": "Clinically meaningful reduction"
  }
}
```

**Use Case**: Primary efficacy endpoint analysis

#### 2. RECIST/ORR Analysis (Oncology)
```http
POST /stats/recist
Content-Type: application/json

Request:
{
  "vitals_data": [ /* VitalsRecord[] */ ],
  "p_active": 0.35,         // Response probability for active arm
  "p_placebo": 0.20,        // Response probability for placebo
  "seed": 777
}

Response:
{
  "recist_data": [
    {
      "SubjectID": "RA001-001",
      "TreatmentArm": "Active",
      "Response": "CR",       // CR|PR|SD|PD
      "is_responder": true
    }
  ],
  "orr_active": 0.38,
  "orr_placebo": 0.18,
  "orr_difference": 0.20,
  "p_value": 0.032
}
```

**Use Case**: Oncology response rate analysis

#### 3. RBQM (Risk-Based Quality Management)
```http
POST /rbqm/summary
Content-Type: application/json

Request:
{
  "vitals_data": [ /* VitalsRecord[] */ ],
  "queries_data": [ /* QueryRecord[] */ ],
  "ae_data": [ /* AdverseEventRecord[] */ ],
  "thresholds": {
    "q_rate_site": 6.0,     // Query rate threshold per 100 CRFs
    "missing_subj": 3,      // Missing data threshold per subject
    "serious_related": 5    // Serious related AE threshold
  }
}

Response:
{
  "summary_markdown": "# RBQM Summary\n...",
  "site_summary": [
    {
      "site_id": "Site001",
      "query_rate": 4.2,
      "missing_rate": 1.5,
      "ae_serious_related": 2,
      "risk_level": "low"
    }
  ],
  "kris": {
    "query_rate_overall": 5.1,
    "missing_data_overall": 2.3,
    "ae_serious_related_overall": 3
  }
}
```

**Use Case**: Site-level quality monitoring

#### 4. CSR (Clinical Study Report) Generation
```http
POST /csr/draft
Content-Type: application/json

Request:
{
  "statistics": { /* Week-12 stats response */ },
  "ae_data": [ /* AdverseEventRecord[] */ ],
  "n_rows": 400
}

Response:
{
  "csr_markdown": "# Clinical Study Report\n\n## Efficacy Results\n..."
}
```

**Use Case**: Automated CSR draft generation

#### 5. SDTM Export
```http
POST /sdtm/export
Content-Type: application/json

Request:
{
  "vitals_data": [ /* VitalsRecord[] */ ]
}

Response:
{
  "sdtm_data": [
    {
      "USUBJID": "RA001-001",
      "VSTESTCD": "SYSBP",
      "VSORRES": "142",
      "VSORRESU": "mmHg",
      "VISITNUM": 1,
      "VISIT": "Screening"
    }
  ],
  "rows": 1600  // 4 vitals × 400 records
}
```

**Use Case**: CDISC SDTM-compliant data export

#### 6. PCA Comparison (Data Quality)
```http
POST /quality/pca-comparison
Content-Type: application/json

Request:
{
  "original_data": [ /* Real VitalsRecord[] */ ],
  "synthetic_data": [ /* Synthetic VitalsRecord[] */ ]
}

Response:
{
  "original_pca": [
    {"pca1": 0.23, "pca2": -0.45},
    // ... coordinates for each record
  ],
  "synthetic_pca": [
    {"pca1": 0.21, "pca2": -0.43},
    // ... coordinates for each record
  ],
  "explained_variance": [0.62, 0.28],
  "quality_score": 0.87  // 0-1, higher is better
}
```

**Use Case**: Visual quality assessment

#### 7. Comprehensive Quality Assessment
```http
POST /quality/comprehensive
Content-Type: application/json

Request:
{
  "original_data": [ /* Real VitalsRecord[] */ ],
  "synthetic_data": [ /* Synthetic VitalsRecord[] */ ],
  "k": 5  // Number of nearest neighbors
}

Response:
{
  "wasserstein_distances": {
    "SystolicBP": 2.34,
    "DiastolicBP": 1.87,
    "HeartRate": 3.12,
    "Temperature": 0.15
  },
  "correlation_preservation": 0.94,  // How well correlations preserved
  "rmse_by_column": {
    "SystolicBP": 8.45,
    "DiastolicBP": 5.23,
    "HeartRate": 6.78,
    "Temperature": 0.32
  },
  "knn_imputation_score": 0.88,
  "overall_quality_score": 0.87,
  "euclidean_distances": {
    "mean_distance": 3.45,
    "median_distance": 2.98,
    "min_distance": 0.12,
    "max_distance": 12.34,
    "std_distance": 2.10
  },
  "summary": "✅ EXCELLENT - Quality score: 0.87..."
}
```

**Use Case**: Comprehensive synthetic data quality validation

**Quality Score Interpretation**:
- **≥ 0.85**: Excellent - Production ready
- **0.70-0.85**: Good - Minor adjustments needed
- **< 0.70**: Needs improvement - Review parameters

---

## 📝 EDC Service (Port 8004)

**Base URL**: `http://localhost:8004`
**Purpose**: Electronic Data Capture - Store and manage clinical trial data

### Data Models

#### Study
```typescript
interface Study {
  study_id: string;
  study_name: string;
  indication: string;
  phase: string;          // "Phase 1" | "Phase 2" | "Phase 3"
  sponsor: string;
  start_date: string;     // ISO 8601
  status: string;         // "active" | "completed" | "suspended"
  tenant_id: string;
}
```

#### Subject
```typescript
interface Subject {
  subject_id: string;
  study_id: string;
  site_id: string;
  treatment_arm: string;  // "Active" | "Placebo"
  enrollment_date: string;
  status: string;         // "enrolled" | "completed" | "withdrawn"
}
```

#### Visit
```typescript
interface Visit {
  visit_id: string;
  subject_id: string;
  visit_name: string;
  visit_date: string;
  status: string;         // "scheduled" | "completed" | "missed"
}
```

#### Vitals Observation
```typescript
interface VitalsObservation {
  observation_id: string;
  visit_id: string;
  subject_id: string;
  systolic_bp: number;
  diastolic_bp: number;
  heart_rate: number;
  temperature: number;
  observation_date: string;
}
```

### Endpoints

#### 1. Create Study
```http
POST /studies
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "study_name": "Hypertension Phase 3 Trial",
  "indication": "Hypertension",
  "phase": "Phase 3",
  "sponsor": "PharmaCo Inc",
  "start_date": "2025-01-01"
}

Response:
{
  "study_id": "STU001",
  "message": "Study created successfully"
}
```

#### 2. List Studies
```http
GET /studies
Authorization: Bearer <token>

Response:
{
  "studies": [
    {
      "study_id": "STU001",
      "study_name": "Hypertension Phase 3 Trial",
      "status": "active",
      "subjects_enrolled": 100,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 3. Enroll Subject
```http
POST /subjects
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "study_id": "STU001",
  "site_id": "Site001",
  "treatment_arm": "Active"
}

Response:
{
  "subject_id": "RA001-001",
  "message": "Subject enrolled successfully"
}
```

#### 4. Record Vitals
```http
POST /vitals
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "subject_id": "RA001-001",
  "visit_name": "Week 4",
  "systolic_bp": 138,
  "diastolic_bp": 84,
  "heart_rate": 72,
  "temperature": 36.7,
  "observation_date": "2025-02-01"
}

Response:
{
  "observation_id": "OBS001",
  "message": "Vitals recorded successfully"
}
```

#### 5. Get Subject Data
```http
GET /subjects/{subject_id}
Authorization: Bearer <token>

Response:
{
  "subject_id": "RA001-001",
  "study_id": "STU001",
  "treatment_arm": "Active",
  "visits": [
    {
      "visit_name": "Screening",
      "visit_date": "2025-01-15",
      "vitals": {
        "systolic_bp": 142,
        "diastolic_bp": 88,
        "heart_rate": 72,
        "temperature": 36.7
      }
    }
  ]
}
```

#### 6. Bulk Import Synthetic Data
```http
POST /import/synthetic
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "study_id": "STU001",
  "data": [ /* VitalsRecord[] from generation service */ ],
  "source": "mvn"
}

Response:
{
  "subjects_imported": 100,
  "observations_imported": 400,
  "message": "Synthetic data imported successfully"
}
```

---

## 🔍 Quality Service (Port 8006)

**Base URL**: `http://localhost:8006`
**Purpose**: Data validation and quality checks

### Endpoints

#### 1. Validate Vitals
```http
POST /validate/vitals
Content-Type: application/json

Request:
{
  "data": [ /* VitalsRecord[] */ ]
}

Response:
{
  "valid": true,
  "total_records": 400,
  "validation_results": {
    "range_checks": {
      "passed": 400,
      "failed": 0,
      "errors": []
    },
    "bp_differential": {
      "passed": 400,
      "failed": 0,
      "errors": []
    },
    "completeness": {
      "missing_values": 0,
      "completeness_rate": 1.0
    },
    "duplicates": {
      "duplicate_count": 0
    }
  }
}
```

#### 2. Validation Rules

**Range Checks**:
- SystolicBP: 95-200 mmHg
- DiastolicBP: 55-130 mmHg
- HeartRate: 50-120 bpm
- Temperature: 35.0-40.0 °C

**Differential Checks**:
- SBP > DBP by at least 5 mmHg

**Completeness Checks**:
- No missing SubjectID, VisitName, TreatmentArm
- All vitals populated

---

## 🗄️ Database Schema

### PostgreSQL Tables

#### users
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### studies
```sql
CREATE TABLE studies (
    study_id VARCHAR(50) PRIMARY KEY,
    study_name VARCHAR(255) NOT NULL,
    indication VARCHAR(100),
    phase VARCHAR(50),
    sponsor VARCHAR(255),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    tenant_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### subjects
```sql
CREATE TABLE subjects (
    subject_id VARCHAR(50) PRIMARY KEY,
    study_id VARCHAR(50) REFERENCES studies(study_id),
    site_id VARCHAR(50),
    treatment_arm VARCHAR(50),
    enrollment_date DATE,
    status VARCHAR(50) DEFAULT 'enrolled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### visits
```sql
CREATE TABLE visits (
    visit_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(50) REFERENCES subjects(subject_id),
    visit_name VARCHAR(50) NOT NULL,
    visit_date DATE,
    status VARCHAR(50) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### vitals_observations
```sql
CREATE TABLE vitals_observations (
    observation_id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(visit_id),
    subject_id VARCHAR(50) REFERENCES subjects(subject_id),
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature DECIMAL(4,2),
    observation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### audit_log
```sql
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 Key Workflows

### Workflow 1: Generate and Analyze Synthetic Data

```
1. Frontend → POST /generate/mvn (n_per_arm=50)
2. Data Generation Service → Returns 400 records
3. Frontend → POST /stats/week12 (with generated data)
4. Analytics Service → Returns statistical analysis
5. Frontend → POST /quality/comprehensive (original vs synthetic)
6. Analytics Service → Returns quality metrics
7. Frontend → Display results to user
```

### Workflow 2: Import Synthetic Data to Study

```
1. Frontend → POST /generate/bootstrap (n_per_arm=100)
2. Data Generation Service → Returns 568 records
3. Frontend → POST /import/synthetic (study_id + data)
4. EDC Service → Creates subjects and records vitals
5. EDC Service → Returns import summary
6. Frontend → Show success message
```

### Workflow 3: Quality Assessment Pipeline

```
1. Load real data: GET /data/pilot
2. Generate synthetic: POST /generate/mvn
3. Validate synthetic: POST /validate/vitals
4. Compare quality: POST /quality/comprehensive
5. Generate visualizations: POST /quality/pca-comparison
6. Display quality dashboard
```

---

## 📁 File Structure

### Full Project Structure

```
Synthetic-Medical-Data-Generation/
├── frontend/                              # ✅ React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── TopAppBar.tsx         # Header with user info
│   │   │   │   └── NavigationRail.tsx    # Sidebar navigation
│   │   │   ├── screens/
│   │   │   │   ├── Dashboard.tsx         # Landing page
│   │   │   │   ├── DataGeneration.tsx    # 4 generation methods
│   │   │   │   ├── Analytics.tsx         # Statistical analysis
│   │   │   │   ├── Quality.tsx           # Edit checks
│   │   │   │   ├── Studies.tsx           # Study management
│   │   │   │   ├── Settings.tsx          # User settings
│   │   │   │   ├── SystemCheck.tsx       # Health checks
│   │   │   │   └── Login.tsx             # Authentication
│   │   │   └── ui/                       # shadcn/ui components
│   │   ├── contexts/
│   │   │   └── DataContext.tsx           # Global state management
│   │   ├── hooks/
│   │   │   └── useAuth.tsx               # Auth hook
│   │   ├── services/
│   │   │   └── api.ts                    # API integration layer
│   │   ├── types/
│   │   │   └── index.ts                  # TypeScript types
│   │   ├── App.tsx                       # Main app component
│   │   ├── main.tsx                      # Entry point
│   │   └── index.css                     # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── microservices/
│   ├── api-gateway/                      # Port 8000 - Central routing
│   │   └── src/main.py
│   │
│   ├── data-generation-service/          # Port 8002
│   │   └── src/
│   │       ├── main.py                   # FastAPI app, generation endpoints
│   │       ├── generators.py             # Core generation logic (MVN, Bootstrap, Rules)
│   │       └── llm_generator.py          # LLM-based generation
│   │
│   ├── analytics-service/                # Port 8003
│   │   └── src/
│   │       ├── main.py                   # Analytics endpoints
│   │       ├── stats.py                  # Statistical analysis functions
│   │       ├── rbqm.py                   # RBQM calculations
│   │       ├── csr.py                    # CSR generation
│   │       └── sdtm.py                   # SDTM export logic
│   │
│   ├── edc-service/                      # Port 8004
│   │   └── src/
│   │       ├── main.py                   # EDC endpoints
│   │       ├── models.py                 # Database models
│   │       └── repair.py                 # Data repair logic
│   │
│   ├── security-service/                 # Port 8005
│   │   └── src/
│   │       ├── main.py                   # Auth endpoints
│   │       ├── auth.py                   # JWT handling
│   │       └── encryption.py             # Data encryption (Fernet)
│   │
│   ├── quality-service/                  # Port 8006
│   │   └── src/
│   │       ├── main.py                   # Validation endpoints
│   │       └── validators.py             # Validation logic
│   │
│   └── shared/                           # Shared utilities
│
├── database/
│   ├── init.sql                          # PostgreSQL schema
│   ├── database.py                       # SQLAlchemy connection
│   └── cache.py                          # Redis cache layer
│
├── data/
│   ├── pilot_trial_cleaned.csv           # Real data (945 records)
│   ├── pilot_trial.csv                   # Original real data (2,079 records)
│   ├── validate_and_repair_real_data.py  # Data cleaning script
│   ├── knn_imputation_analysis.py        # K-NN imputation analysis
│   └── streamlit_dashboard.py            # Legacy dashboard (reference)
│
├── kubernetes/                           # K8s deployment manifests
│   ├── deployments/
│   ├── services/
│   ├── hpa/
│   └── configmaps/
│
├── terraform/                            # Infrastructure as code
├── scripts/                              # Deployment scripts
├── docker-compose.yml                    # Local development
├── CLAUDE.md                             # This file - AI assistant reference
├── FRONTEND_BACKEND_INTEGRATION_COMPLETE.md
├── QUICKSTART_GUIDE.md
└── README.md
```

### Important Code Locations

**MVN Generator**: `microservices/data-generation-service/src/generators.py:219-283`
**Bootstrap Generator**: `microservices/data-generation-service/src/generators.py:426-620`
**Week-12 Statistics**: `microservices/analytics-service/src/stats.py:10-150`
**Quality Assessment**: `microservices/analytics-service/src/main.py:443-594`
**JWT Auth**: `microservices/security-service/src/auth.py:15-120`

---

## ⚙️ Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/synthetic_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI (for LLM generation)
OPENAI_API_KEY=sk-...

# CORS (for frontend)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Services
API_GATEWAY_PORT=8000
DATA_GENERATION_PORT=8002
ANALYTICS_PORT=8003
EDC_PORT=8004
SECURITY_PORT=8005
QUALITY_PORT=8006
```

### CORS Configuration

**Current Setting**: `allow_origins=["*"]` (⚠️ Change for production)

**For Frontend Development**:
```python
# In each service's main.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

---

## 🚀 Running the Backend

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f data-generation-service

# Stop all services
docker-compose down
```

### Individual Services

```bash
# Data Generation Service
cd microservices/data-generation-service/src
uvicorn main:app --reload --port 8002

# Analytics Service
cd microservices/analytics-service/src
uvicorn main:app --reload --port 8003

# EDC Service
cd microservices/edc-service/src
uvicorn main:app --reload --port 8004
```

---

## 📊 Current Implementation Status

### ✅ Completed (Backend)

1. **Data Generation**
   - ✅ MVN generator (29K records/sec)
   - ✅ Bootstrap generator (140K records/sec)
   - ✅ Rules-based generator
   - ✅ LLM generator (GPT-4o-mini)
   - ✅ Real data integration (CDISC pilot)
   - ✅ Data validation and repair
   - ✅ K-NN imputation analysis

2. **Analytics**
   - ✅ Week-12 statistical analysis
   - ✅ RECIST/ORR analysis
   - ✅ RBQM summary generation
   - ✅ CSR draft generation
   - ✅ SDTM export
   - ✅ PCA comparison
   - ✅ Comprehensive quality assessment (K-NN)

3. **EDC**
   - ✅ Study management
   - ✅ Subject enrollment
   - ✅ Vitals recording
   - ✅ Bulk synthetic data import

4. **Security**
   - ✅ JWT authentication
   - ✅ User registration/login
   - ✅ Role-based access control
   - ✅ Token verification

5. **Quality**
   - ✅ Vitals validation
   - ✅ Range checks
   - ✅ Completeness checks
   - ✅ YAML-based edit checks

6. **Data Analysis**
   - ✅ Distribution comparisons
   - ✅ Column-level analysis
   - ✅ Multi-panel visualizations
   - ✅ K-NN imputation with MAR pattern

### ✅ Completed (Frontend)

1. **Core Infrastructure**
   - ✅ React 19 + TypeScript setup
   - ✅ Vite build configuration
   - ✅ Tailwind CSS + shadcn/ui
   - ✅ React Context API for state management
   - ✅ API service layer with typed responses
   - ✅ Environment configuration

2. **Authentication & Layout**
   - ✅ Login screen with JWT authentication
   - ✅ User registration workflow
   - ✅ TopAppBar with user info and logout
   - ✅ NavigationRail with Material Design 3 styling
   - ✅ Protected routes

3. **Data Generation Screen**
   - ✅ MVN generation method
   - ✅ Bootstrap generation method
   - ✅ Rules-based generation method
   - ✅ LLM generation method (with API key input)
   - ✅ Parameter configuration forms
   - ✅ Data preview table (first 10 records)
   - ✅ CSV download functionality
   - ✅ Global state integration

4. **Analytics Screen**
   - ✅ Week-12 statistical analysis display
   - ✅ Treatment effect results (Active vs Placebo)
   - ✅ Comprehensive quality metrics
   - ✅ Quality score interpretation
   - ✅ Dataset summary cards
   - ✅ Integration with generated data from context

5. **Quality Screen**
   - ✅ YAML-based edit checks validation
   - ✅ Violation display with severity levels
   - ✅ Quality score calculation
   - ✅ Pass/fail indicators
   - ✅ Separate from Analytics (as intended)

6. **Studies Management**
   - ✅ List all studies (card layout)
   - ✅ Create new study (dialog form)
   - ✅ Study details view
   - ✅ Import synthetic data workflow
   - ✅ Real-time updates after creation

7. **Additional Screens**
   - ✅ Dashboard with quick actions
   - ✅ SystemCheck for service health
   - ✅ Settings (placeholder)

8. **UI/UX Features**
   - ✅ Loading states on all async operations
   - ✅ Error handling with user-friendly messages
   - ✅ Material Design 3 styling
   - ✅ Responsive design
   - ✅ Gradient animations and hover effects
   - ✅ Empty state handling

### 🚧 Pending (Future Enhancements)

1. **Async Job System** (for million-scale generation)
   - ❌ Redis queue
   - ❌ Background workers
   - ❌ Progress tracking
   - ❌ Job status endpoints

2. **Performance Optimizations**
   - ❌ Vectorized generation
   - ❌ Parallel processing
   - ❌ Chunked file writing

3. **Production Readiness**
   - ❌ Distributed generation
   - ❌ Monitoring/metrics
   - ❌ Auto-scaling

**See**: `SCALING_TO_MILLIONS_GUIDE.md` for full roadmap

---

## 🎨 Frontend Architecture & Implementation

### Overview

The frontend is a **React 19 + TypeScript + Vite** application using **Material Design 3** principles with **shadcn/ui** components and **Tailwind CSS** for styling.

**Status**: ✅ Fully implemented and integrated with all backend services
**Deployment**: http://localhost:3001 (development)
**Last Integration Update**: 2025-11-13

### Technology Stack

- **Framework**: React 19.2.0
- **Language**: TypeScript 5.9.3
- **Build Tool**: Vite 7.2.2
- **Styling**: Tailwind CSS 4.1.17
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Charts**: Recharts 3.4.1
- **Icons**: lucide-react 0.553.0
- **Date Utilities**: date-fns 4.1.0
- **State Management**: React Context API

### Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── TopAppBar.tsx           # Header with user info, logout
│   │   │   └── NavigationRail.tsx      # Sidebar navigation with gradients
│   │   ├── screens/
│   │   │   ├── Dashboard.tsx           # Landing page with quick actions
│   │   │   ├── DataGeneration.tsx      # 4 generation methods (MVN, Bootstrap, Rules, LLM)
│   │   │   ├── Analytics.tsx           # Week-12 stats + quality metrics
│   │   │   ├── Quality.tsx             # Edit checks validation (separate from Analytics)
│   │   │   ├── Studies.tsx             # Study management + data import
│   │   │   ├── Settings.tsx            # User settings (placeholder)
│   │   │   ├── SystemCheck.tsx         # Service health checks
│   │   │   └── Login.tsx               # Authentication
│   │   └── ui/                         # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── table.tsx
│   │       └── badge.tsx
│   ├── contexts/
│   │   └── DataContext.tsx             # Global state management
│   ├── hooks/
│   │   └── useAuth.tsx                 # Authentication hook
│   ├── services/
│   │   └── api.ts                      # All API integrations (5 services)
│   ├── types/
│   │   └── index.ts                    # TypeScript type definitions
│   ├── App.tsx                         # Main app with routing
│   ├── main.tsx                        # Entry point
│   └── index.css                       # Global styles + Tailwind
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### State Management Architecture

**Pattern**: React Context API with custom hooks
**File**: `frontend/src/contexts/DataContext.tsx`

**Why Context API?**
- No external state management library needed
- Sufficient for current complexity
- Type-safe with TypeScript
- Easy to understand and maintain
- Data persists across screen navigation

**DataContext Provider Structure**:
```typescript
interface DataContextType {
  // Generated Data
  generatedData: VitalsRecord[] | null
  setGeneratedData: (data: VitalsRecord[] | null) => void
  generationMethod: string | null
  setGenerationMethod: (method: string | null) => void

  // Pilot/Real Data
  pilotData: VitalsRecord[] | null
  setPilotData: (data: VitalsRecord[] | null) => void

  // Analytics Results
  week12Stats: Week12StatsResponse | null
  setWeek12Stats: (stats: Week12StatsResponse | null) => void
  qualityMetrics: QualityAssessmentResponse | null
  setQualityMetrics: (metrics: QualityAssessmentResponse | null) => void
  pcaComparison: PCAComparisonResponse | null
  setPcaComparison: (pca: PCAComparisonResponse | null) => void

  // Quality/Validation Results
  validationResults: ValidationResponse | null
  setValidationResults: (results: ValidationResponse | null) => void

  // Utility
  clearAllData: () => void
}
```

**Usage Pattern**:
```typescript
// In any component
import { useData } from "@/contexts/DataContext";

function MyComponent() {
  const { generatedData, setGeneratedData } = useData();

  // Generate data
  const response = await dataGenerationApi.generateMVN(params);
  setGeneratedData(response.data); // Stored globally

  // Use in another component later
  if (generatedData) {
    // Run analytics, quality checks, or import to study
  }
}
```

### API Service Layer

**File**: `frontend/src/services/api.ts`
**Pattern**: Organized by microservice with typed responses

**Service Groups**:
1. **authApi** - Security Service (Port 8005)
2. **dataGenerationApi** - Data Generation Service (Port 8002)
3. **analyticsApi** - Analytics Service (Port 8003)
4. **edcApi** - EDC Service (Port 8004)
5. **qualityApi** - Quality Service (Port 8006)

**Key Features**:
- Environment variable configuration (VITE_*_URL)
- Automatic JWT token handling
- Type-safe request/response handling
- Centralized error handling
- Response normalization

**Example Implementation**:
```typescript
// API Configuration
const DATA_GEN_SERVICE = import.meta.env.VITE_DATA_GEN_URL || "http://localhost:8002";

// Helper for auth headers
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// Typed API call
export const dataGenerationApi = {
  async generateMVN(params: GenerationRequest): Promise<GenerationResponse> {
    const response = await fetch(`${DATA_GEN_SERVICE}/generate/mvn`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(params),
    });
    return handleResponse<GenerationResponse>(response);
  }
};
```

### Component Architecture

**Pattern**: Functional components with hooks
**Styling**: Tailwind CSS utility classes + Material Design 3 tokens
**UI Components**: shadcn/ui (Radix UI primitives)

**Screen Components** (7 main screens):

1. **Dashboard** (`Dashboard.tsx`)
   - Entry point after login
   - Quick action cards (Generate, Analyze, Create Study)
   - Navigation to main features
   - Statistics overview cards

2. **DataGeneration** (`DataGeneration.tsx`)
   - Method selection tabs (MVN, Bootstrap, Rules, LLM)
   - Parameter configuration forms
   - Real-time generation with loading states
   - Data preview table (first 10 records)
   - CSV download functionality
   - **Stores data in global context**

3. **Analytics** (`Analytics.tsx`)
   - Uses generated data from context
   - Week-12 statistical analysis (t-test, p-value, CI)
   - Treatment effect calculation (Active vs Placebo)
   - Comprehensive quality metrics:
     - Wasserstein distances
     - RMSE by column
     - Correlation preservation
     - K-NN imputation score
     - Overall quality score
   - Dataset summary with subject counts

4. **Quality** (`Quality.tsx`) - **SEPARATE FROM ANALYTICS**
   - YAML-based edit checks validation
   - Range checks, differential checks
   - Violation display with severity levels
   - Quality score calculation
   - Pass/fail indicators

5. **Studies** (`Studies.tsx`)
   - List all studies (card layout)
   - Create new study (dialog form)
   - View study details
   - Import synthetic data workflow
   - Real-time updates

6. **Settings** (`Settings.tsx`)
   - User preferences (placeholder)
   - System configuration

7. **SystemCheck** (`SystemCheck.tsx`)
   - Service health checks
   - Backend connectivity status

**Layout Components**:

- **TopAppBar**: Header with user info, logout button
- **NavigationRail**: Left sidebar with gradient styling, Material Design 3

### Key Development Conventions

#### 1. TypeScript Usage
- **Strict mode enabled** (`tsconfig.json`)
- All API responses typed (`types/index.ts`)
- No `any` types except in legacy code
- Interface over type for object shapes

#### 2. Component Patterns
```typescript
// ✅ Preferred pattern
interface MyComponentProps {
  data: VitalsRecord[];
  onUpdate: (data: VitalsRecord[]) => void;
}

export function MyComponent({ data, onUpdate }: MyComponentProps) {
  const [loading, setLoading] = useState(false);

  // Component logic

  return (
    <div className="p-4">
      {/* JSX */}
    </div>
  );
}
```

#### 3. Error Handling
```typescript
// ✅ Standard error handling pattern
try {
  setLoading(true);
  const response = await api.someCall();
  setData(response.data);
} catch (error) {
  console.error("Error:", error);
  alert(error instanceof Error ? error.message : "An error occurred");
} finally {
  setLoading(false);
}
```

#### 4. Loading States
- Always show loading indicators for async operations
- Disable buttons during loading
- Use `Loader2` icon with spin animation
- Example: `<Loader2 className="h-4 w-4 animate-spin" />`

#### 5. Styling Conventions
- Use Tailwind utility classes
- Material Design 3 color tokens: `--color-primary`, `--color-secondary`
- Gradient backgrounds on cards: `bg-gradient-to-r from-purple-500 to-pink-500`
- Hover effects: `hover:scale-105 transition-transform`
- Responsive classes: `lg:grid-cols-3 md:grid-cols-2`

#### 6. File Naming
- **Components**: PascalCase (`DataGeneration.tsx`)
- **Hooks**: camelCase with `use` prefix (`useAuth.tsx`)
- **Utilities**: camelCase (`api.ts`)
- **Types**: camelCase (`index.ts`)

#### 7. Import Organization
```typescript
// External imports
import { useState, useEffect } from "react";
import { Loader2, CheckCircle2 } from "lucide-react";

// Internal imports
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useData } from "@/contexts/DataContext";
import { dataGenerationApi } from "@/services/api";
import type { VitalsRecord, GenerationResponse } from "@/types";
```

### User Workflows

#### Complete End-to-End Workflow

**1. Authentication**
```
Login screen → Enter credentials → Authenticate → Dashboard
OR
Register → Fill form → Auto-login → Dashboard
```

**2. Generate Synthetic Data**
```
Dashboard → "Generate Synthetic Data" → DataGeneration screen
→ Select method (MVN/Bootstrap/Rules/LLM)
→ Configure parameters (n_per_arm, target_effect, seed)
→ Click "Generate with [Method]"
→ View data preview table
→ (Optional) Download CSV
→ Data stored in context for other screens
```

**3. Run Analytics**
```
Navigate to Analytics screen
→ See "Analyze X generated records" message
→ Click "Run Statistical Analysis"
→ Wait for computation (2-3 seconds)
→ View Week-12 statistics:
  • Active vs Placebo comparison
  • Mean SBP, confidence intervals
  • p-value and statistical significance
  • Clinical interpretation
→ View comprehensive quality metrics:
  • Overall quality score (0-1 scale)
  • Wasserstein distances by column
  • RMSE values
  • Correlation preservation
  • K-NN imputation score
  • Euclidean distance statistics
```

**4. Validate Data Quality**
```
Navigate to Quality screen
→ Click "Run Quality Checks"
→ Wait for YAML-based validation
→ View results:
  • Total checks run
  • Quality score percentage
  • Pass/Fail status
→ Review violations (if any):
  • Subject ID
  • Rule violated
  • Severity level (error/warning/info)
  • Descriptive message
```

**5. Manage Studies**
```
Navigate to Studies screen
→ Click "Create Study"
→ Fill in study details:
  • Study name
  • Indication (e.g., Hypertension)
  • Phase (dropdown: Phase 1-4)
  • Sponsor organization
  • Start date (date picker)
→ Click "Create Study"
→ Study appears in list with card
→ Click "Import Data" on study card
→ Generated data imported with subjects
→ Success message with subject/observation counts
```

### Critical Integration Points

#### 1. Authentication Flow
```typescript
// Login → Store token → Include in all requests
const response = await authApi.login({ username, password });
localStorage.setItem("token", response.access_token);

// All subsequent API calls include token automatically
headers: {
  "Authorization": `Bearer ${localStorage.getItem("token")}`
}
```

#### 2. Data Generation → Analytics Flow
```typescript
// Generate data (DataGeneration.tsx)
const response = await dataGenerationApi.generateMVN(params);
setGeneratedData(response.data); // Stored in context

// Use in Analytics (Analytics.tsx)
const { generatedData } = useData();
if (generatedData) {
  const stats = await analyticsApi.getWeek12Stats({ vitals_data: generatedData });
  setWeek12Stats(stats);
}
```

#### 3. Data Generation → Studies Flow
```typescript
// Generate data first
const response = await dataGenerationApi.generateMVN(params);
setGeneratedData(response.data);

// Import to study (Studies.tsx)
const { generatedData } = useData();
await edcApi.importSyntheticData(studyId, generatedData, "mvn");
```

### Environment Configuration

**File**: `frontend/.env` (create from `.env.example`)

```bash
# Backend Service URLs
VITE_DATA_GEN_URL=http://localhost:8002
VITE_ANALYTICS_URL=http://localhost:8003
VITE_EDC_URL=http://localhost:8004
VITE_SECURITY_URL=http://localhost:8005
VITE_QUALITY_URL=http://localhost:8006

# Optional: API Gateway
VITE_API_GATEWAY_URL=http://localhost:8000
```

### Development Commands

```bash
# Install dependencies
cd frontend
npm install

# Run development server (http://localhost:3001)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Type check
npx tsc --noEmit
```

### Testing Strategy

**Current Status**: Manual testing
**Coverage**: All major workflows tested

**Manual Test Checklist**:
- [x] User registration and login
- [x] Generate data with all 4 methods
- [x] Data preview and CSV download
- [x] Run statistical analysis
- [x] Run quality checks
- [x] Create study
- [x] Import data to study
- [x] Navigation between screens
- [x] Data persistence across screens
- [x] Error handling and loading states
- [x] Logout and token expiration

**Future**: Add automated tests (Jest, React Testing Library, Playwright)

### UI/UX Design Principles

1. **Material Design 3**
   - Gradient navigation rail
   - Colored gradient bars on cards
   - Icon backgrounds with brand colors
   - Scale animations on hover
   - Subtle background gradients

2. **Loading States**
   - Spinner icons during async operations
   - Disabled buttons when loading
   - Skeleton loaders (future enhancement)

3. **Error Handling**
   - User-friendly error messages
   - No technical jargon in user-facing errors
   - Red destructive styling for errors

4. **Empty States**
   - Helpful messages when no data available
   - Clear calls-to-action
   - Example: "Generate data first to see analytics"

5. **Feedback**
   - Success indicators (CheckCircle2 icon)
   - Loading spinners (Loader2 icon)
   - Alert dialogs for confirmations
   - Toast notifications (future enhancement)

### Known Frontend Limitations

1. **No Charts/Visualizations Yet**
   - Recharts installed but not implemented
   - PCA scatter plots pending
   - Distribution histograms pending

2. **Limited Error Recovery**
   - Token expiration requires manual re-login
   - No automatic retry for failed requests

3. **No Pagination**
   - Tables show all records (can be slow for large datasets)
   - Future: Add pagination for 1000+ records

4. **Settings Page Placeholder**
   - User preferences not implemented
   - Theme switching not available

5. **No Real-time Updates**
   - Manual refresh required for study list
   - No WebSocket integration

---

## 🎨 Frontend Development Guidelines

### API Integration

**Base URLs**:
```typescript
const API_GATEWAY = "http://localhost:8000";
const DATA_GEN_SERVICE = "http://localhost:8002";
const ANALYTICS_SERVICE = "http://localhost:8003";
const EDC_SERVICE = "http://localhost:8004";
const SECURITY_SERVICE = "http://localhost:8005";
```

**Authentication Example**:
```typescript
// Login
const loginResponse = await fetch(`${SECURITY_SERVICE}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});
const { access_token } = await loginResponse.json();

// Store token
localStorage.setItem('token', access_token);

// Use token in requests
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('token')}`
};
```

**Generation Example**:
```typescript
// Generate synthetic data
const generateData = async (nPerArm: number) => {
  const response = await fetch(`${DATA_GEN_SERVICE}/generate/mvn`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ n_per_arm: nPerArm, target_effect: -5.0 })
  });
  const { data, metadata } = await response.json();
  return data;
};
```

### Error Handling

**Standard Error Response**:
```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes**:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

### Recommended UI Components

1. **Dashboard**
   - Generation statistics
   - Active studies overview
   - Recent activities

2. **Data Generation Page**
   - Method selection (MVN, Bootstrap, Rules, LLM)
   - Parameter configuration (n_per_arm, target_effect)
   - Real-time generation progress
   - Data preview table
   - Download options (CSV, Parquet)

3. **Analytics Page**
   - Statistical analysis results
   - Interactive visualizations (charts.js, recharts, etc.)
   - Quality metrics display
   - PCA scatter plots
   - Comparison tables

4. **Study Management**
   - Study list/creation
   - Subject enrollment
   - Data entry forms
   - Import synthetic data

5. **Quality Dashboard**
   - Validation results
   - K-NN imputation analysis
   - Distribution comparisons
   - Quality score indicators

### Data Visualization Libraries

**Recommended**:
- **Recharts** - React charts, easy integration
- **Chart.js** - Versatile, well-documented
- **Plotly.js** - Interactive, scientific plots
- **D3.js** - Maximum flexibility (advanced)

**For Tables**:
- **TanStack Table** (React Table v8)
- **AG Grid** - Feature-rich, enterprise-grade

---

## 📚 API Documentation

**Interactive Docs** (Swagger UI):
- Data Generation: http://localhost:8002/docs
- Analytics: http://localhost:8003/docs
- EDC: http://localhost:8004/docs
- Security: http://localhost:8005/docs
- Quality: http://localhost:8006/docs

**OpenAPI Spec** (JSON):
- Data Generation: http://localhost:8002/openapi.json
- Analytics: http://localhost:8003/openapi.json
- etc.

---

## 🔍 Testing the Backend

### Health Checks

```bash
# Check all services
curl http://localhost:8002/health  # Data Generation
curl http://localhost:8003/health  # Analytics
curl http://localhost:8004/health  # EDC
curl http://localhost:8005/health  # Security
curl http://localhost:8006/health  # Quality
```

### Sample API Calls

**Generate Synthetic Data**:
```bash
curl -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 10, "target_effect": -5.0}'
```

**Get Statistics**:
```bash
curl -X POST http://localhost:8003/stats/week12 \
  -H "Content-Type: application/json" \
  -d '{"vitals_data": [...]}'
```

**Login**:
```bash
curl -X POST http://localhost:8005/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'
```

---

## 🎯 Frontend Implementation Priorities

### Phase 1: Core Functionality (Week 1)
1. Authentication (login/register)
2. Data generation interface (MVN, Bootstrap)
3. Basic data visualization (tables)
4. Download generated data

### Phase 2: Analytics (Week 2)
1. Statistical analysis display
2. Quality metrics dashboard
3. Interactive charts (distributions, correlations)
4. Comparison views (real vs synthetic)

### Phase 3: Study Management (Week 3)
1. Study CRUD operations
2. Subject enrollment workflow
3. Data entry forms
4. Bulk data import

### Phase 4: Advanced Features (Week 4+)
1. RBQM dashboard
2. K-NN imputation visualization
3. CSR generation interface
4. Export to SDTM

---

## 💡 Tips for Frontend Development

1. **Use TypeScript** - All API types are well-defined
2. **Handle Loading States** - Some operations take seconds (LLM, large datasets)
3. **Implement Pagination** - Tables with 400+ records need pagination
4. **Add Download Options** - CSV, JSON, Excel formats
5. **Show Progress Indicators** - Especially for generation
6. **Cache API Responses** - Avoid redundant requests
7. **Validate User Input** - Before sending to API
8. **Display Error Messages** - User-friendly error handling
9. **Add Tooltips** - Explain statistical terms
10. **Support Dark Mode** - Nice-to-have for long sessions

---

## 🐛 Known Issues & Limitations

1. **LLM Generation**
   - Requires OpenAI API key
   - Slower than other methods (~70 records/sec)
   - Can be expensive for large datasets

2. **Million-Scale Generation**
   - Current architecture limited to ~10K records synchronously
   - Async system pending implementation
   - See `SCALING_TO_MILLIONS_GUIDE.md`

3. **Multi-Tenancy**
   - RLS (Row-Level Security) not fully enforced
   - Tenant ID propagation needs improvement
   - See `272-project- new features.md` for details

4. **Security**
   - CORS set to wildcard (`*`) - needs restriction
   - Password hashing implemented but strength could improve
   - Audit trail exists but not immutable (no blockchain)

---

## 📞 Getting Help

**API Documentation**: http://localhost:8002/docs
**Backend Issues**: Check service logs via `docker-compose logs`
**Database Issues**: Check PostgreSQL logs
**Redis Issues**: Check Redis connection via `redis-cli ping`

---

**Document Version**: 2.0
**Last Updated**: 2025-11-15
**Status**: ✅ Full-stack implementation complete
**Backend**: All 5 microservices operational
**Frontend**: React application fully integrated
**Integration**: Complete end-to-end workflows tested

---

## 🎯 AI Assistant Guidelines

When working with this codebase, follow these principles:

### 1. **Understand Before Modifying**
- Always read relevant sections of this document before making changes
- Check both backend and frontend sections for integration points
- Review existing code patterns before implementing new features

### 2. **Maintain Consistency**
- Follow established naming conventions
- Use existing patterns for new components/endpoints
- Match the current code style and structure

### 3. **Type Safety First**
- Maintain TypeScript strict mode compliance
- Define interfaces for all API contracts
- Update type definitions in `frontend/src/types/index.ts`

### 4. **Test Integration Points**
- Verify backend endpoints before frontend integration
- Test state management changes across multiple screens
- Ensure authentication flows remain functional

### 5. **Document Changes**
- Update this CLAUDE.md when adding major features
- Add inline comments for complex logic
- Update API documentation for endpoint changes

### 6. **Respect Architecture**
- Keep frontend state management in Context API
- Don't bypass the API service layer
- Maintain microservices separation on backend
- No direct database access from frontend

### 7. **Common Tasks Reference**

**Adding a new backend endpoint**:
1. Add endpoint to appropriate service (`microservices/*/src/main.py`)
2. Update API documentation (Swagger auto-generated)
3. Add corresponding API call to `frontend/src/services/api.ts`
4. Define TypeScript types in `frontend/src/types/index.ts`
5. Test the endpoint with curl or Postman first
6. Integrate into frontend component

**Adding a new frontend screen**:
1. Create component in `frontend/src/components/screens/`
2. Add route in `App.tsx`
3. Add navigation item in `NavigationRail.tsx`
4. Use `useData()` hook for global state access
5. Follow existing error handling patterns
6. Add loading states for async operations

**Modifying data models**:
1. Update backend Pydantic models
2. Update database schema if needed (`database/init.sql`)
3. Update TypeScript interfaces (`frontend/src/types/index.ts`)
4. Update API service layer calls
5. Update affected components

### 8. **Quick Reference URLs**

- **Frontend Dev**: http://localhost:3001
- **Backend APIs**: http://localhost:8002-8006
- **API Docs**: http://localhost:800X/docs (replace X with service port)
- **Documentation**: See `FRONTEND_BACKEND_INTEGRATION_COMPLETE.md`
- **Quickstart**: See `QUICKSTART_GUIDE.md`

---

**Ready for**: Production deployment, feature enhancement, performance optimization
**Next Milestones**: Charts/visualizations, million-scale generation, automated testing

