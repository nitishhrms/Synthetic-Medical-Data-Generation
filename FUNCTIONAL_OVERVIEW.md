# SyntheticTrialStudio Enterprise - Comprehensive Functional Overview

**Platform**: Clinical Trial Data Management & Synthetic Data Generation
**Architecture**: Microservices (FastAPI Backend + React Frontend)
**Main Branch**: `daft` (distributed analytics with Daft library)
**Version**: 2.0
**Last Updated**: 2025-11-19

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Services](#core-services)
3. [Data Models](#data-models)
4. [Complete Functional Flows](#complete-functional-flows)
5. [Frontend Screens](#frontend-screens)
6. [API Endpoints Reference](#api-endpoints-reference)
7. [Data Generation Methods](#data-generation-methods)
8. [Analytics & Quality](#analytics--quality)
9. [Security & Compliance](#security--compliance)
10. [Database Schema](#database-schema)

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)                     │
│                         Port 3000 (Vite)                             │
│  Screens: Dashboard | Generate | Analytics | RBQM | Queries |       │
│           Studies | Quality | Data Entry | Settings                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ REST API / JSON
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Port 8000)                         │
│              Request Routing | Auth | Rate Limiting                  │
└──────┬──────────────┬──────────────┬──────────────┬─────────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│   Security   │ │   EDC    │ │   Data   │ │  Analytics   │
│   Service    │ │ Service  │ │Generation│ │   Service    │
│  Port 8005   │ │Port 8001 │ │Port 8002 │ │  Port 8003   │
└──────────────┘ └──────────┘ └──────────┘ └──────────────┘
       │              │              │              │
       │         ┌────┴────┐    ┌────┴────┐         │
       │         ▼         ▼    ▼         ▼         │
       │    ┌──────────┐ ┌──────────┐ ┌──────────┐ │
       │    │ Quality  │ │  Daft    │ │  GAIN    │ │
       │    │ Service  │ │Analytics │ │ Service  │ │
       │    │Port 8004 │ │Port 8007 │ │Port 8008 │ │
       │    └──────────┘ └──────────┘ └──────────┘ │
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                      │
         ┌────────────┴──────────────┐
         ▼                           ▼
┌──────────────────┐        ┌──────────────┐
│   PostgreSQL     │        │    Redis     │
│   Database       │        │    Cache     │
│   Port 5432      │        │  Port 6379   │
└──────────────────┘        └──────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python 3.9+) - REST API framework
- PostgreSQL 15+ - Primary database
- Redis 7 - Caching layer
- SQLAlchemy - ORM
- Pandas/NumPy - Data processing
- Daft - Distributed dataframe processing
- OpenAI GPT-4o-mini - LLM generation

**Frontend:**
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- Tailwind CSS - Styling
- shadcn/ui - Component library
- Recharts - Data visualization

**Infrastructure:**
- Docker & Docker Compose
- Kubernetes (optional)
- NGINX - Reverse proxy (production)

---

## Core Services

### 1. Security Service (Port 8005)

**Purpose**: Authentication, authorization, and data security

**Key Features:**
- ✅ JWT-based authentication
- ✅ User registration and login
- ✅ Role-based access control (Admin, Researcher, Viewer)
- ✅ PHI encryption (Fernet symmetric encryption)
- ✅ PHI detection (regex-based)
- ✅ HIPAA audit logging
- ✅ Multi-tenant support

**Main Endpoints:**
- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `GET /auth/verify` - Token verification
- `GET /auth/me` - Get current user
- `POST /security/encrypt` - Encrypt PHI data
- `POST /security/decrypt` - Decrypt PHI data
- `POST /security/detect-phi` - Detect PHI in text
- `GET /security/audit-log` - View audit trail

**User Roles:**
| Role | Permissions |
|------|-------------|
| **Admin** | Full access, user management, system configuration |
| **Researcher** | Generate data, view analytics, EDC read/write |
| **Viewer** | Read-only access to analytics and reports |

---

### 2. EDC Service (Port 8001)

**Purpose**: Electronic Data Capture - Clinical trial data management

**Key Features:**
- ✅ Subject enrollment and management
- ✅ Study creation and configuration
- ✅ Vitals data capture (BP, HR, Temperature)
- ✅ Demographics collection
- ✅ Lab results entry
- ✅ Query management workflow
- ✅ Form definition engine
- ✅ Data validation and auto-repair
- ✅ Privacy assessment (K-anonymity)
- ✅ Multi-tenant data isolation (RLS)

**Main Endpoints:**

**Study Management:**
- `POST /studies` - Create new study
- `GET /studies` - List all studies
- `GET /studies/{study_id}` - Get study details

**Subject Management:**
- `POST /subjects` - Enroll subject
- `GET /subjects/{subject_id}` - Get subject data

**Data Capture:**
- `POST /validate` - Validate vitals data
- `POST /repair` - Auto-repair invalid data
- `POST /store-vitals` - Store vitals to database
- `GET /vitals/all` - **NEW** - Get all vitals for RBQM
- `POST /demographics` - Record demographics
- `POST /labs` - Record lab results

**Query Management:**
- `GET /queries` - List queries (filterable)
- `GET /queries/{query_id}` - Get query details
- `PUT /queries/{query_id}/respond` - CRC responds
- `PUT /queries/{query_id}/close` - Close query

**Forms & Privacy:**
- `POST /forms/definitions` - Create form template
- `GET /forms/definitions` - List forms
- `POST /forms/data` - Submit form data
- `POST /privacy/assess/comprehensive` - Privacy assessment

**Import:**
- `POST /import/synthetic` - Bulk import synthetic data

---

### 3. Data Generation Service (Port 8002)

**Purpose**: Generate synthetic clinical trial data using multiple methods

**Key Features:**
- ✅ 5 generation methods (MVN, Rules, Bootstrap, LLM, Oncology AE)
- ✅ **Comprehensive study generation** (all data types in one call)
- ✅ Vitals, Demographics, Adverse Events, Labs
- ✅ Real data integration (CDISC pilot dataset)
- ✅ Configurable parameters (n_per_arm, target_effect, seed)
- ✅ Quality validation built-in
- ✅ Fast performance (29K-140K records/sec)

**Main Endpoints:**

**Individual Data Types:**
- `POST /generate/rules` - Rules-based vitals
- `POST /generate/mvn` - Multivariate Normal vitals
- `POST /generate/bootstrap` - Bootstrap from real data
- `POST /generate/llm` - LLM-based generation (GPT-4o-mini)
- `POST /generate/ae` - Oncology adverse events
- `POST /generate/demographics` - Demographics data
- `POST /generate/labs` - Lab results

**NEW - Comprehensive Generation:**
- `POST /generate/comprehensive-study` - **Complete study in one call**
  - Returns: vitals + demographics + AEs + labs
  - Shared subject IDs across all datasets
  - Flexible options to include/exclude data types

**Utilities:**
- `GET /data/pilot` - Get real CDISC pilot data
- `GET /compare` - Compare generation methods

**Performance Benchmarks:**
| Method | Speed | Use Case |
|--------|-------|----------|
| Bootstrap | ~140K records/sec | Fast, preserves real data patterns |
| MVN | ~29K records/sec | Statistically realistic |
| Rules | ~80K records/sec | Deterministic, business rules |
| LLM | ~70 records/sec | Creative, context-aware |

---

### 4. Analytics Service (Port 8003)

**Purpose**: Statistical analysis, RBQM, reporting, quality assessment

**Key Features:**
- ✅ Week-12 efficacy analysis (Welch's t-test)
- ✅ RECIST/ORR analysis (oncology endpoints)
- ✅ RBQM (Risk-Based Quality Management)
- ✅ CSR draft generation
- ✅ SDTM export
- ✅ PCA-based quality comparison
- ✅ Comprehensive quality metrics
- ✅ KS distance calculations

**Main Endpoints:**

**Statistical Analysis:**
- `POST /stats/week12` - Primary efficacy analysis
  - Treatment effect estimation
  - t-test, confidence intervals
  - Clinical significance assessment
- `POST /stats/recist` - Oncology response rates
  - Complete Response (CR), Partial Response (PR)
  - Objective Response Rate (ORR)
  - Statistical comparison between arms

**RBQM (Risk-Based Quality Management):**
- `POST /rbqm/summary` - Generate RBQM dashboard
  - Site-level KRIs (Key Risk Indicators)
  - Query rates, protocol deviations
  - AE monitoring
  - QTL (Quality Tolerance Limits) flagging

**Quality Assessment:**
- `POST /quality/pca-comparison` - PCA-based quality check
- `POST /quality/comprehensive` - Full quality suite
  - Wasserstein distances
  - Correlation preservation
  - K-NN imputation score
  - Euclidean distance metrics
  - Overall quality score (0-1)

**Reporting:**
- `POST /csr/draft` - Generate CSR (Clinical Study Report)
- `POST /sdtm/export` - Export to CDISC SDTM format

---

### 5. Quality Service (Port 8004)

**Purpose**: Data validation, edit checks, quality assurance

**Key Features:**
- ✅ YAML-based edit check engine
- ✅ Range validation
- ✅ Pattern matching (regex)
- ✅ Duplicate detection
- ✅ Missing data checks
- ✅ Entry noise simulation
- ✅ Custom validation rules

**Main Endpoints:**
- `POST /checks/validate` - Run edit checks
- `POST /checks/execute` - Execute validation rules
- `GET /checks/definitions` - List available checks

**Validation Types:**
| Check Type | Description | Example |
|------------|-------------|---------|
| Range | Value within bounds | SystolicBP: 95-200 mmHg |
| Pattern | Regex matching | SubjectID: `RA\d{3}-\d{3}` |
| Required | Non-null fields | SubjectID, VisitName required |
| Differential | Logical constraints | SBP > DBP + 5 |
| Duplicate | Uniqueness checks | No duplicate (Subject, Visit) |

---

### 6. Daft Analytics Service (Port 8007)

**Purpose**: Distributed data processing for large-scale analytics

**Key Features:**
- ✅ Distributed dataframe operations
- ✅ Fast aggregations on large datasets
- ✅ UDFs (User-Defined Functions) for medical calculations
- ✅ SQL query support
- ✅ Parquet file export
- ✅ Treatment effect analysis at scale
- ✅ Outlier detection

**Main Endpoints:**
- `POST /daft/filter` - Filter datasets
- `POST /daft/aggregate` - Group-by aggregations
- `POST /daft/treatment-effect` - Efficacy analysis
- `POST /daft/responder-analysis` - Responder classification
- `POST /daft/outlier-detection` - Outlier identification
- `POST /daft/sql-query` - Execute SQL on data
- `POST /daft/export-parquet` - Export to Parquet format

---

## Data Models

### Core Clinical Data Types

#### 1. Vitals Record
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

#### 2. Demographics Record
```typescript
interface Demographics {
  SubjectID: string;
  Age: number;              // 18-85 years
  Gender: string;           // "Male" | "Female" | "Other"
  Race: string;             // "White" | "Black" | "Asian" | etc.
  Ethnicity: string;        // "Hispanic or Latino" | "Not Hispanic or Latino"
  Height_cm: number;        // 140-220 cm
  Weight_kg: number;        // 40-200 kg
  BMI: number;              // Calculated
  SmokingStatus: string;    // "Never" | "Former" | "Current"
}
```

#### 3. Adverse Event Record
```typescript
interface AdverseEvent {
  SubjectID: string;
  AE_Term: string;          // e.g., "Headache", "Nausea"
  Severity: string;         // "Mild" | "Moderate" | "Severe"
  StartDay: number;
  EndDay: number;
  Causality: string;        // "Unrelated" | "Possibly Related" | "Probably Related"
  Serious: boolean;
  ActionTaken: string;
}
```

#### 4. Lab Results Record
```typescript
interface LabResults {
  SubjectID: string;
  VisitName: string;
  TestDate: string;
  // Hematology
  Hemoglobin?: number;      // g/dL
  Hematocrit?: number;      // %
  WBC?: number;             // x10^9/L
  Platelets?: number;       // x10^9/L
  // Chemistry
  Glucose?: number;         // mg/dL
  Creatinine?: number;      // mg/dL
  BUN?: number;             // mg/dL
  ALT?: number;             // U/L
  AST?: number;             // U/L
  Bilirubin?: number;       // mg/dL
  // Lipids
  TotalCholesterol?: number; // mg/dL
  LDL?: number;
  HDL?: number;
  Triglycerides?: number;
}
```

#### 5. Query Record
```typescript
interface Query {
  query_id: number;
  subject_id: string;
  query_text: string;
  severity: string;         // "info" | "warning" | "error" | "critical"
  status: string;           // "open" | "answered" | "closed" | "cancelled"
  opened_at: string;
  opened_by: number;
  response_text?: string;
  responded_at?: string;
  resolved_at?: string;
}
```

---

## Complete Functional Flows

### Flow 1: User Authentication & Authorization

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. Navigate to http://localhost:3000
       ▼
┌─────────────┐
│Login Screen │
└──────┬──────┘
       │ 2. Enter username/password
       │ 3. POST /auth/login
       ▼
┌──────────────────┐
│Security Service  │
│  (Port 8005)     │
└────┬─────────────┘
     │ 4. Validate credentials
     │ 5. Generate JWT token
     │ 6. Return token + user info
     ▼
┌─────────────┐
│  Frontend   │
│stores token │
│in localStorage
└──────┬──────┘
       │ 7. Redirect to Dashboard
       │ 8. All subsequent requests include:
       │    Authorization: Bearer <token>
       ▼
┌─────────────┐
│  Dashboard  │
└─────────────┘
```

**Steps:**
1. User navigates to frontend
2. Login screen presented
3. User enters credentials, clicks "Login"
4. Frontend sends `POST /auth/login` to Security Service
5. Security Service validates credentials against database
6. JWT token generated with user ID, role, tenant ID
7. Token returned to frontend
8. Frontend stores token in localStorage
9. User redirected to Dashboard
10. All API calls include `Authorization: Bearer <token>` header

---

### Flow 2: Generate Synthetic Study Data (Comprehensive)

```
┌──────────────┐
│Data Gen Page │
└──────┬───────┘
       │ 1. User selects:
       │    - n_per_arm: 50
       │    - method: "mvn"
       │    - Include: vitals, demographics, AEs, labs
       │ 2. Click "Generate Comprehensive Study"
       ▼
┌──────────────────────┐
│POST /generate/       │
│comprehensive-study   │
└──────┬───────────────┘
       │ 3. Data Generation Service
       ▼
┌──────────────────────┐
│ Generate Vitals      │
│ - MVN method         │
│ - 100 subjects       │
│ - 400 records        │
│ - Visits: Screening, │
│   Day 1, Week 4,     │
│   Week 12            │
└──────┬───────────────┘
       │ 4. Generate Demographics
       ▼
┌──────────────────────┐
│ Generate Demographics│
│ - 100 records        │
│ - Age, Gender, BMI   │
│ - Race, Ethnicity    │
└──────┬───────────────┘
       │ 5. Generate Adverse Events
       ▼
┌──────────────────────┐
│ Generate AEs         │
│ - ~87 events         │
│ - Severity, Causality│
└──────┬───────────────┘
       │ 6. Generate Labs
       ▼
┌──────────────────────┐
│ Generate Labs        │
│ - 300 records        │
│ - Hematology         │
│ - Chemistry, Lipids  │
└──────┬───────────────┘
       │ 7. Combine all data
       │ 8. Return JSON response
       ▼
┌──────────────────────┐
│  Frontend receives:  │
│  {                   │
│    vitals: [...],    │
│    demographics:[...],
│    adverse_events:[],│
│    labs: [...],      │
│    metadata: {...}   │
│  }                   │
└──────┬───────────────┘
       │ 9. Display data in tables
       │ 10. User can:
       │     - Download CSV
       │     - Import to study
       │     - Analyze quality
       ▼
┌──────────────────────┐
│   Data Tables        │
│   Quality Metrics    │
│   Download Options   │
└──────────────────────┘
```

**API Call:**
```json
POST http://localhost:8002/generate/comprehensive-study
{
  "n_per_arm": 50,
  "target_effect": -5.0,
  "method": "mvn",
  "include_vitals": true,
  "include_demographics": true,
  "include_ae": true,
  "include_labs": true,
  "seed": 42
}
```

**Response:**
```json
{
  "vitals": [ /* 400 vitals records */ ],
  "demographics": [ /* 100 demographic records */ ],
  "adverse_events": [ /* ~87 AE records */ ],
  "labs": [ /* 300 lab records */ ],
  "metadata": {
    "total_subjects": 100,
    "subjects_per_arm": 50,
    "vitals_records": 400,
    "demographics_records": 100,
    "ae_records": 87,
    "labs_records": 300,
    "method": "mvn",
    "generation_timestamp": "2025-11-19T10:00:00Z",
    "summary": "Generated comprehensive study..."
  }
}
```

---

### Flow 3: RBQM Dashboard (Risk-Based Quality Management)

```
┌──────────────┐
│RBQM Dashboard│
└──────┬───────┘
       │ 1. Load on mount
       │ 2. Fetch vitals data
       ▼
┌──────────────────────┐
│GET /vitals/all       │
│(EDC Service 8001)    │
└──────┬───────────────┘
       │ 3. Returns all vitals from DB
       │    (or empty array if no data)
       ▼
┌──────────────────────┐
│GET /queries          │
│(EDC Service 8001)    │
└──────┬───────────────┘
       │ 4. Returns all queries
       ▼
┌──────────────────────┐
│POST /rbqm/summary    │
│(Analytics 8003)      │
│                      │
│Request:              │
│{                     │
│  vitals_data: [...], │
│  queries_data: [...],│
│  ae_data: [],        │
│  thresholds: {       │
│    q_rate_site: 6.0, │
│    site_deviations:5,│
│    serious_related:5 │
│  },                  │
│  site_size: 20       │
│}                     │
└──────┬───────────────┘
       │ 5. Analytics Service calculates:
       │    - Query rate per 100 CRFs
       │    - Protocol deviations
       │    - Serious related AEs
       │    - Site-level KRIs
       │    - QTL flags (Quality Tolerance Limits)
       ▼
┌──────────────────────┐
│Response:             │
│{                     │
│  site_summary: [     │
│    {                 │
│      SiteID: "001",  │
│      queries_per_100:│
│      QTL_flag: false │
│    }                 │
│  ],                  │
│  kris: {             │
│    total_queries: 45,│
│    query_rate: 5.2,  │
│    late_entry_pct:12 │
│  }                   │
│}                     │
└──────┬───────────────┘
       │ 6. Frontend displays:
       ▼
┌──────────────────────┐
│  KRI Summary Cards   │
│  - Total Queries     │
│  - Protocol Devs     │
│  - Serious AEs       │
│  - Late Entry %      │
│                      │
│  Site Risk Heatmap   │
│  - Color-coded cards │
│  - Red = High Risk   │
│  - Green = Low Risk  │
│                      │
│  Query Rate Chart    │
│  - Bar chart by site │
│                      │
│  Site Details Table  │
└──────────────────────┘
```

---

### Flow 4: Quality Assessment Pipeline

```
┌──────────────┐
│Analytics Page│
└──────┬───────┘
       │ 1. Load real data
       ▼
┌──────────────────────┐
│GET /data/pilot       │
│(Data Gen 8002)       │
└──────┬───────────────┘
       │ 2. Returns 945 real records
       ▼
┌──────────────────────┐
│User generates        │
│synthetic data        │
│POST /generate/mvn    │
└──────┬───────────────┘
       │ 3. Returns 400 synthetic records
       ▼
┌──────────────────────┐
│POST /quality/        │
│comprehensive         │
│(Analytics 8003)      │
│                      │
│{                     │
│  original_data: real,│
│  synthetic_data:synth│
│}                     │
└──────┬───────────────┘
       │ 4. Calculate quality metrics:
       ▼
┌──────────────────────┐
│Quality Assessment:   │
│                      │
│1. Wasserstein Dist   │
│   - Per column       │
│   - Measures         │
│     distribution     │
│     similarity       │
│                      │
│2. Correlation        │
│   - Original vs synth│
│   - Preservation     │
│     score            │
│                      │
│3. RMSE               │
│   - Root mean square │
│   - Error per column │
│                      │
│4. K-NN Imputation    │
│   - Neighbor quality │
│   - Pattern matching │
│                      │
│5. Overall Score      │
│   - 0-1 scale        │
│   - 0.85+ = Excellent│
└──────┬───────────────┘
       │ 5. Return results
       ▼
┌──────────────────────┐
│Response:             │
│{                     │
│  wasserstein: {      │
│    SystolicBP: 2.34  │
│  },                  │
│  correlation: 0.94,  │
│  rmse: {...},        │
│  knn_score: 0.88,    │
│  overall: 0.87,      │
│  summary: "✅ EXCL" │
│}                     │
└──────┬───────────────┘
       │ 6. Display results
       ▼
┌──────────────────────┐
│Quality Dashboard:    │
│ - Score gauge        │
│ - Distribution plots │
│ - Metric cards       │
│ - Recommendations    │
└──────────────────────┘
```

**Quality Score Interpretation:**
- **≥ 0.85**: ✅ EXCELLENT - Production ready
- **0.70-0.85**: ⚠️ GOOD - Minor adjustments needed
- **< 0.70**: ❌ NEEDS IMPROVEMENT - Review parameters

---

### Flow 5: Query Management Workflow

```
┌──────────────┐
│Query Mgmt    │
│Page          │
└──────┬───────┘
       │ 1. Load queries
       │ GET /queries
       ▼
┌──────────────────────┐
│Display query list    │
│- Open queries (red)  │
│- Answered (yellow)   │
│- Closed (green)      │
└──────┬───────────────┘
       │ 2. User clicks query
       │ GET /queries/{id}
       ▼
┌──────────────────────┐
│Query Detail View     │
│                      │
│Query: "Systolic BP   │
│       200 at Week 4" │
│Subject: RA001-042    │
│Status: Open          │
│Severity: Warning     │
│                      │
│History:              │
│ - Opened by DM       │
│                      │
│[Respond Button]      │
└──────┬───────────────┘
       │ 3. CRC responds
       │ PUT /queries/{id}/respond
       │ { response_text: "..." }
       ▼
┌──────────────────────┐
│Status → "answered"   │
│                      │
│History updated:      │
│ - Opened by DM       │
│ - Answered by CRC    │
│                      │
│[Close Button]        │
│(Data Manager only)   │
└──────┬───────────────┘
       │ 4. DM closes query
       │ PUT /queries/{id}/close
       │ { resolution_notes: "..." }
       ▼
┌──────────────────────┐
│Status → "closed"     │
│                      │
│Full audit trail:     │
│ - Opened: 2025-11-15 │
│ - Answered: 2025-11-16
│ - Closed: 2025-11-17 │
│                      │
│Resolution: "Confirmed"
└──────────────────────┘
```

**Query Lifecycle:**
1. **Open** - Data Manager identifies issue, creates query
2. **Answered** - CRC responds with clarification/correction
3. **Closed** - Data Manager reviews and closes query
4. **Cancelled** - (Optional) Query no longer relevant

---

### Flow 6: Study Creation & Data Import

```
┌──────────────┐
│Studies Page  │
└──────┬───────┘
       │ 1. Create new study
       │ POST /studies
       ▼
┌──────────────────────┐
│{                     │
│  study_name: "HTN-001"
│  indication: "HTN",  │
│  phase: "Phase 3",   │
│  sponsor: "PharmaCo",│
│  start_date:"2025-01"│
│}                     │
└──────┬───────────────┘
       │ 2. Study created
       │    study_id = "STU001"
       ▼
┌──────────────────────┐
│Study Dashboard       │
│                      │
│Name: HTN-001         │
│Phase: Phase 3        │
│Subjects: 0           │
│                      │
│[Import Synthetic Data]
└──────┬───────────────┘
       │ 3. User generates data
       │    (see Flow 2)
       │ 4. Click "Import to Study"
       │ POST /import/synthetic
       ▼
┌──────────────────────┐
│{                     │
│  study_id: "STU001", │
│  data: [ /* vitals */],
│  source: "mvn"       │
│}                     │
└──────┬───────────────┘
       │ 5. EDC Service:
       │    - Creates subjects
       │    - Links to study
       │    - Stores vitals
       ▼
┌──────────────────────┐
│Response:             │
│{                     │
│  subjects_imported:100
│  observations: 400,  │
│  message: "Success"  │
│}                     │
└──────┬───────────────┘
       │ 6. Update UI
       ▼
┌──────────────────────┐
│Study Dashboard       │
│                      │
│Name: HTN-001         │
│Subjects: 100 ✅      │
│Observations: 400 ✅  │
│                      │
│[View Subjects]       │
│[Run Analytics]       │
└──────────────────────┘
```

---

## Frontend Screens

### Screen Navigation Map

```
┌────────────────────────────────────────────────────────────┐
│                      TOP APP BAR                           │
│  SyntheticTrialStudio | User: john.doe | [Logout]         │
└────────────────────────────────────────────────────────────┘
│                      │                                      │
│  ┌────────────────┐ │  ┌────────────────────────────────┐ │
│  │Navigation Rail │ │  │        Main Content Area        │ │
│  ├────────────────┤ │  └────────────────────────────────┘ │
│  │ 📊 Dashboard   │ │                                      │
│  │ 🎲 Generate    │ │  Active screen renders here         │
│  │ 📈 Analytics   │ │                                      │
│  │ 🎯 RBQM        │ │  - Dashboard (default)              │
│  │ 💬 Queries     │ │  - Data Generation                  │
│  │ 📝 Data Entry  │ │  - Analytics                        │
│  │ 🔬 Studies     │ │  - Quality                          │
│  │ ✅ Quality     │ │  - RBQM Dashboard                   │
│  │ ⚙️  Settings   │ │  - Query Management                 │
│  │ 🔧 System Check│ │  - Studies                          │
│  └────────────────┘ │  - Settings                         │
└────────────────────────────────────────────────────────────┘
```

### 1. Dashboard Screen

**Purpose**: Overview and quick navigation

**Components:**
- Summary cards (studies, subjects, queries)
- Recent activities feed
- Quick action buttons
- System health indicators

**Actions:**
- Navigate to any other screen
- View system status
- Quick data generation

---

### 2. Data Generation Screen

**Purpose**: Generate synthetic clinical trial data

**Features:**
- ✅ **NEW: Comprehensive Study Generation**
  - Select data types (vitals, demographics, AEs, labs)
  - Configure parameters (n_per_arm, method, seed)
  - One-click generation
- ✅ Individual data type generation
- ✅ Method selection (MVN, Rules, Bootstrap, LLM)
- ✅ Parameter configuration
- ✅ Real-time preview
- ✅ Download options (CSV, JSON, Parquet)
- ✅ Quality metrics display
- ✅ Import to study

**Tabs:**
1. **Comprehensive** - All data types
2. **Vitals** - Blood pressure, heart rate
3. **Demographics** - Age, gender, BMI
4. **Adverse Events** - AE generation
5. **Labs** - Lab results

---

### 3. Analytics Screen

**Purpose**: Statistical analysis and reporting

**Features:**
- ✅ Week-12 efficacy analysis
- ✅ Treatment effect estimation
- ✅ Statistical tests (t-test, CI)
- ✅ Quality assessment
- ✅ PCA visualization
- ✅ Distribution comparisons
- ✅ Correlation heatmaps
- ✅ CSR generation
- ✅ SDTM export

**Charts:**
- Box plots (by treatment arm)
- Histograms (overlaid)
- Scatter plots (PCA)
- Time series (vitals over time)

---

### 4. RBQM Dashboard Screen

**Purpose**: Risk-based quality management and monitoring

**Components:**
- **KRI Summary Cards**
  - Total queries
  - Protocol deviations
  - Serious + related AEs
  - Late data entry %

- **Site Risk Heatmap**
  - Color-coded site cards
  - QTL flags
  - Risk indicators

- **Query Rate Chart**
  - Bar chart by site
  - Threshold line

- **Site Details Table**
  - Sortable columns
  - Filterable by risk level

**Real-time Updates:**
- Fetches latest data on mount
- Refresh button for manual updates

---

### 5. Query Management Screen

**Purpose**: Manage data queries and clarifications

**Features:**
- ✅ Query list (filterable)
- ✅ Status-based filtering (open, answered, closed)
- ✅ Severity indicators
- ✅ Query detail view
- ✅ Response workflow
- ✅ Close workflow
- ✅ Audit history
- ✅ Search functionality

**Query States:**
- 🔴 **Open** - Awaiting response
- 🟡 **Answered** - CRC responded
- 🟢 **Closed** - Resolved
- ⚪ **Cancelled** - No longer applicable

---

### 6. Studies Screen

**Purpose**: Manage clinical trial studies

**Features:**
- ✅ Study list
- ✅ Create new study
- ✅ Study dashboard
- ✅ Subject enrollment
- ✅ Import synthetic data
- ✅ Study analytics

---

### 7. Data Entry Screen

**Purpose**: Manual clinical data entry

**Features:**
- Form-based data entry
- Validation on submit
- Auto-save drafts
- Query creation

---

### 8. Quality Screen

**Purpose**: Data quality monitoring

**Features:**
- Edit check results
- Validation reports
- Data completeness metrics
- Duplicate detection

---

### 9. Settings Screen

**Purpose**: User and system configuration

**Features:**
- User profile management
- Theme selection
- Notification preferences
- API configuration

---

### 10. System Check Screen

**Purpose**: Backend health monitoring

**Features:**
- ✅ Service health checks
- ✅ Port availability
- ✅ Database connectivity
- ✅ API response times
- ✅ Color-coded status indicators

**Services Monitored:**
- EDC Service (8001)
- Data Generation (8002)
- Analytics (8003)
- Quality (8004)
- Security (8005)
- Daft Analytics (8007)

---

## API Endpoints Reference

### Complete Endpoint Catalog

#### Security Service (8005)
```
POST   /auth/login              - Authenticate user
POST   /auth/register           - Register new user
GET    /auth/verify             - Verify JWT token
GET    /auth/me                 - Get current user
POST   /security/encrypt        - Encrypt PHI data
POST   /security/decrypt        - Decrypt PHI data
POST   /security/detect-phi     - Detect PHI in text
GET    /security/audit-log      - View audit trail
GET    /health                  - Health check
```

#### EDC Service (8001)
```
# Study Management
POST   /studies                 - Create study
GET    /studies                 - List studies
GET    /studies/{id}            - Get study details

# Subject Management
POST   /subjects                - Enroll subject
GET    /subjects/{id}           - Get subject data

# Data Capture
POST   /validate                - Validate vitals
POST   /repair                  - Auto-repair data
POST   /store-vitals            - Store to database
GET    /vitals/all              - Get all vitals (NEW)
POST   /demographics            - Record demographics
POST   /labs                    - Record lab results

# Query Management
GET    /queries                 - List queries
GET    /queries/{id}            - Get query details
PUT    /queries/{id}/respond    - Respond to query
PUT    /queries/{id}/close      - Close query

# Forms
POST   /forms/definitions       - Create form template
GET    /forms/definitions       - List forms
GET    /forms/definitions/{id}  - Get form schema
POST   /forms/data              - Submit form data

# Privacy
POST   /privacy/assess/comprehensive - Privacy assessment

# Import
POST   /import/synthetic        - Bulk import

GET    /health                  - Health check
```

#### Data Generation Service (8002)
```
# Individual Generation
POST   /generate/rules          - Rules-based vitals
POST   /generate/mvn            - MVN vitals
POST   /generate/bootstrap      - Bootstrap vitals
POST   /generate/llm            - LLM vitals
POST   /generate/ae             - Adverse events
POST   /generate/demographics   - Demographics
POST   /generate/labs           - Lab results

# Comprehensive (NEW)
POST   /generate/comprehensive-study - All data types

# Utilities
GET    /data/pilot              - Get real CDISC data
GET    /compare                 - Compare methods

GET    /health                  - Health check
```

#### Analytics Service (8003)
```
# Statistics
POST   /stats/week12            - Week-12 efficacy
POST   /stats/recist            - RECIST/ORR

# RBQM
POST   /rbqm/summary            - RBQM dashboard

# Quality
POST   /quality/pca-comparison  - PCA quality check
POST   /quality/comprehensive   - Full quality suite

# Reporting
POST   /csr/draft               - Generate CSR
POST   /sdtm/export             - SDTM export

GET    /health                  - Health check
```

#### Quality Service (8004)
```
POST   /checks/validate         - Run edit checks
POST   /checks/execute          - Execute validation
GET    /checks/definitions      - List checks

GET    /health                  - Health check
```

#### Daft Analytics Service (8007)
```
POST   /daft/filter             - Filter data
POST   /daft/aggregate          - Aggregations
POST   /daft/treatment-effect   - Efficacy analysis
POST   /daft/responder-analysis - Responder classification
POST   /daft/outlier-detection  - Outlier detection
POST   /daft/sql-query          - SQL queries
POST   /daft/export-parquet     - Export Parquet

GET    /health                  - Health check
```

---

## Data Generation Methods

### Method Comparison

| Method | Speed | Quality | Use Case | Parameters |
|--------|-------|---------|----------|------------|
| **MVN** | 29K rec/sec | High | Statistical realism | `n_per_arm`, `target_effect`, `seed` |
| **Bootstrap** | 140K rec/sec | Very High | Preserve patterns | `training_data`, `jitter_frac` |
| **Rules** | 80K rec/sec | Medium | Deterministic | `n_per_arm`, `target_effect` |
| **LLM** | 70 rec/sec | Variable | Creative/Context | `api_key`, `indication`, `prompt` |

### Generation Parameters

**Common Parameters:**
- `n_per_arm`: Number of subjects per treatment arm (10-200)
- `target_effect`: Target treatment effect in mmHg (-10 to 0, typically -5)
- `seed`: Random seed for reproducibility (any integer)

**Method-Specific:**
- **Bootstrap**: `jitter_frac` (0.01-0.1) - Gaussian noise fraction
- **LLM**: `api_key`, `model`, `extra_instructions`, `max_repair_iters`

---

## Analytics & Quality

### Statistical Tests

#### Week-12 Efficacy Analysis
- **Test**: Welch's t-test (unequal variances)
- **Null Hypothesis**: No difference between arms
- **Alternative**: Active < Placebo (one-tailed)
- **Significance Level**: α = 0.05
- **Output**: t-statistic, p-value, 95% CI, effect size

#### RECIST/ORR Analysis
- **Test**: Fisher's exact test (small samples)
- **Outcome**: Objective Response Rate (CR + PR)
- **Output**: ORR by arm, difference, p-value

### Quality Metrics

#### 1. Wasserstein Distance
- Measures distribution similarity
- Per-column calculation
- Lower is better (0 = identical)

#### 2. Correlation Preservation
- Compares correlation matrices
- Original vs synthetic
- Score: 0-1 (1 = perfect preservation)

#### 3. RMSE (Root Mean Square Error)
- Per-column accuracy
- Lower is better

#### 4. K-NN Imputation Score
- Nearest neighbor quality
- Tests data pattern matching
- Score: 0-1 (higher is better)

#### 5. Overall Quality Score
- Composite metric
- Range: 0-1
- **≥ 0.85**: Excellent
- **0.70-0.85**: Good
- **< 0.70**: Needs improvement

---

## Security & Compliance

### HIPAA Compliance Features

1. **Data Encryption**
   - At-rest: PostgreSQL encryption
   - In-transit: HTTPS/TLS
   - PHI fields: Fernet symmetric encryption

2. **Audit Logging**
   - All data access logged
   - User actions tracked
   - Immutable audit trail
   - IP address logging

3. **Access Control**
   - Role-based permissions
   - JWT token expiration
   - Session management

4. **Multi-Tenancy**
   - Row-Level Security (RLS)
   - Tenant isolation
   - Separate data partitions

5. **PHI Detection**
   - Automated scanning
   - Regex patterns for:
     - SSN, MRN, phone numbers
     - Email addresses
     - Dates of birth

### Data Privacy

#### K-Anonymity Assessment
- Ensures records cannot be uniquely identified
- Configurable threshold (k=5 default)
- Quasi-identifier detection
- Re-identification risk scoring

#### Privacy Metrics:
- **Privacy Score**: 0-1 (higher = better privacy)
- **K-Anonymity**: Minimum group size
- **Uniqueness Ratio**: Proportion of unique records
- **Re-identification Risk**: Probability of identification

---

## Database Schema

### Core Tables

```sql
-- Users & Authentication
users (user_id, tenant_id, username, email, password_hash, roles)

-- Studies & Subjects
studies (study_id, study_name, indication, phase, sponsor, status)
subjects (subject_id, study_id, site_id, treatment_arm, status)

-- Clinical Data
patients (patient_id, tenant_id, subject_number, demographics)
vital_signs (vital_id, patient_id, visit_date, systolic_bp, diastolic_bp, heart_rate)
demographics (demo_id, subject_id, age, gender, race, bmi)
lab_results (lab_id, subject_id, visit_name, hemoglobin, wbc, glucose)

-- Quality & Queries
queries (query_id, subject_id, query_text, severity, status, opened_at)
query_history (history_id, query_id, action, action_by, action_at)
form_definitions (form_id, form_name, form_schema, edit_checks_yaml)
form_data (data_id, form_id, subject_id, form_data, status)

-- Audit & Security
audit_events (event_id, event_type, user_id, action, payload, timestamp)
mcp_context (agent_id, context_type, context_data, decisions)
```

### Multi-Tenant Isolation

**Row-Level Security (RLS):**
```sql
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON patients
    USING (tenant_id = current_setting('app.current_tenant', TRUE));
```

**Usage:**
```sql
-- Set tenant context
SET app.current_tenant = 'tenant_abc';

-- Now all queries automatically filtered by tenant
SELECT * FROM patients;  -- Only sees tenant_abc data
```

---

## Performance & Scalability

### Current Capabilities

| Metric | Value |
|--------|-------|
| Max subjects/generation | 200 (synchronous) |
| Max records/generation | ~800 vitals |
| Generation speed (MVN) | 29,000 records/sec |
| Generation speed (Bootstrap) | 140,000 records/sec |
| Database connections | Pool of 20 |
| API response time | < 100ms (avg) |

### Scaling to Millions

**See**: `SCALING_TO_MILLIONS_GUIDE.md` for:
- Async job system (Redis queue)
- Distributed generation
- Chunked file writing
- Progress tracking
- Background workers

**Future Architecture:**
```
Frontend → API Gateway → Job Queue (Redis)
                            ↓
                    Background Workers (Celery)
                            ↓
                    Distributed Processing
                            ↓
                    Chunked Storage (S3/Parquet)
```

---

## Deployment

### Development (Current)

**Backend:**
```bash
# Terminal 1 - EDC
cd microservices/edc-service/src
python3 -m uvicorn main:app --port 8001 --reload

# Terminal 2 - Data Generation
cd microservices/data-generation-service/src
python3 -m uvicorn main:app --port 8002 --reload

# Terminal 3 - Analytics
cd microservices/analytics-service/src
python3 -m uvicorn main:app --port 8003 --reload

# Terminal 4 - Quality
cd microservices/quality-service/src
python3 -m uvicorn main:app --port 8004 --reload

# Terminal 5 - Security
cd microservices/security-service/src
python3 -m uvicorn main:app --port 8005 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Docker Compose

```bash
docker-compose up --build -d
```

**Services:**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- All microservices on their respective ports

### Kubernetes

```bash
# Start cluster
minikube start --cpus 4 --memory 8192

# Deploy
kubectl apply -f kubernetes/deployments/
kubectl apply -f kubernetes/services/
kubectl apply -f kubernetes/hpa/

# Access
kubectl port-forward -n clinical-trials svc/api-gateway 8000:80
```

---

## Summary

**SyntheticTrialStudio** is a comprehensive clinical trial management platform with:

✅ **6 Core Microservices** (Security, EDC, Data Gen, Analytics, Quality, Daft)
✅ **10 Frontend Screens** (Dashboard, Generate, Analytics, RBQM, Queries, etc.)
✅ **50+ API Endpoints** (RESTful, OpenAPI documented)
✅ **5 Generation Methods** (MVN, Bootstrap, Rules, LLM, AE)
✅ **NEW: Comprehensive Study Generation** (all data types in one call)
✅ **Complete RBQM Dashboard** (site-level KRIs, QTL flags)
✅ **Quality Assessment Suite** (Wasserstein, K-NN, correlation)
✅ **Query Management Workflow** (open → answered → closed)
✅ **HIPAA Compliance** (encryption, audit, RLS)
✅ **Multi-Tenant Architecture** (tenant isolation)
✅ **PostgreSQL + Redis** (persistent storage + caching)
✅ **Production Ready** (Docker, Kubernetes, monitoring)

**Main Branch**: `daft` (includes distributed analytics capabilities)

---

**For More Details, See:**
- `QUICKSTART_GUIDE.md` - Getting started
- `CLAUDE.md` - Backend reference for frontend development
- `COMPREHENSIVE_FIX_SUMMARY.md` - Recent CORS fixes and new features
- `USER_JOURNEY_AND_EVENT_FLOWS.md` - Detailed user flows
- `SCALING_TO_MILLIONS_GUIDE.md` - Scaling architecture
