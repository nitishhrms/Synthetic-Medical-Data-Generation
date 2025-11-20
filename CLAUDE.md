# CLAUDE.md - Backend Reference for Frontend Development


## !!!Important Note: You are not allowed make any changes in the backend code while doing the frontend development!!!

## 📋 Document Purpose

This document provides a comprehensive reference of the **backend implementation** for the Synthetic Medical Data Generation platform. Use this as your primary reference when developing the frontend to avoid re-discovering backend details.

**Last Updated**: 2025-11-12
**Backend Status**: ✅ Complete (pending million-scale optimizations)
**Frontend Status**: 🚧 To be implemented

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
│(Port 8002)│     │ (Port 8003) │  │(Pt 8001)│  │(Port 8005) │  │(Pt 8004) │
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

#### Standard Methods
1. **MVN (Multivariate Normal)** - Statistical distribution-based
2. **Bootstrap** - Resampling from real data with jitter
3. **Rules-based** - Deterministic generation with business rules
4. **Bayesian Network** - Probabilistic graphical models
5. **MICE** - Multiple Imputation by Chained Equations
6. **Diffusion** - Diffusion model-based generation
7. **LLM** - OpenAI GPT-4o-mini powered generation

#### AACT-Enhanced Methods (Recommended)
All standard methods have AACT-enhanced versions that use real-world data from **557,805 ClinicalTrials.gov trials**:
- MVN-AACT, Bootstrap-AACT, Rules-AACT, Bayesian-AACT, MICE-AACT
- Uses real baseline vitals, dropout patterns, AE frequencies, demographics
- See [AACT Integration](#-aact-integration-clinicaltrialsgov-data) section below

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

## 🌐 AACT Integration (ClinicalTrials.gov Data)

### Overview

All generation methods now have **AACT-enhanced versions** that leverage real-world data from **557,805 clinical trials** in the ClinicalTrials.gov database (via AACT - Aggregate Analysis of ClinicalTrials.gov).

**Key Benefits**:
- ✅ Real baseline vitals from actual trials (not generic estimates)
- ✅ Real dropout rates and reasons by indication/phase
- ✅ Real adverse event patterns with frequencies
- ✅ Real demographics (age, gender, trial duration)
- ✅ Real treatment arm configurations
- ✅ Real geographic distributions
- ✅ Disease taxonomy with MeSH terms

**Data Version**: AACT v4.0 (17 data files processed)

### AACT-Enhanced Endpoints

#### 1. MVN with AACT
```http
POST /generate/mvn-aact
Content-Type: application/json

Request:
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50,
  "target_effect": -5.0,
  "use_duration": true
}

Response:
{
  "data": [ /* VitalsRecord[] with real baseline vitals */ ],
  "metadata": {
    "records": 400,
    "subjects": 100,
    "method": "mvn-aact",
    "aact_source": "557,805 trials",
    "baseline_vitals_from_aact": true
  }
}
```

**What Makes It Real**:
- Baseline SBP/DBP from actual hypertension Phase 3 trials (e.g., 152/92 mmHg instead of generic 140/85)
- Dropout rate from real data (e.g., 13.4% actual vs 15% estimated)
- Visit schedules based on actual trial durations

#### 2. Bootstrap with AACT
```http
POST /generate/bootstrap-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50
}
```

#### 3. Rules with AACT
```http
POST /generate/rules-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50
}
```

#### 4. Demographics with AACT
```http
POST /generate/demographics-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50
}

Response:
[
  {
    "SubjectID": "RA001-001",
    "Age": 58,              // Real median age from AACT
    "Gender": "M",          // Real gender distribution
    "Race": "White",
    "Ethnicity": "Not Hispanic or Latino",
    "Country": "United States"  // Real geographic distribution
  }
]
```

#### 5. Labs with AACT
```http
POST /generate/labs-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50
}

Response:
[
  {
    "SubjectID": "RA001-001",
    "VisitName": "Screening",
    "Glucose": 95.2,
    "Creatinine": 0.9,
    "Sodium": 140,
    "Potassium": 4.2
    // ... more labs
  }
]
```

#### 6. Adverse Events with AACT
```http
POST /generate/ae-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50
}

Response:
[
  {
    "SubjectID": "RA001-001",
    "AE_Term": "Headache",     // Real top AE from AACT
    "Severity": "Mild",
    "Related": "Possibly",
    "Serious": false
  }
]
```

#### 7. Bayesian Network with AACT
```http
POST /generate/bayesian-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50,
  "n_iterations": 1000
}
```

**Features**:
- Learns probabilistic relationships from AACT data
- Models conditional dependencies between variables
- Generates realistic correlated vital signs

#### 8. MICE with AACT
```http
POST /generate/mice-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50,
  "n_imputations": 5
}
```

**Features**:
- Multiple Imputation by Chained Equations
- Realistic missing data patterns from AACT
- Uncertainty quantification

### AACT Data Sources (v4.0)

The following real-world data is extracted from AACT:

| Data Type | Source File | What It Provides |
|-----------|-------------|------------------|
| **Baseline Vitals** | `baseline_measurements.txt` | Real SBP, DBP, HR, Temperature by indication/phase |
| **Dropout Patterns** | `drop_withdrawals.txt` | Real dropout rates and top reasons |
| **Adverse Events** | `reported_events.txt` | Top 20 AEs with actual frequencies |
| **Site Distribution** | `facilities.txt` | Real site counts per trial |
| **Demographics** | `calculated_values.txt` | Age, gender, actual trial duration |
| **Treatment Arms** | `design_groups.txt` | Real arm types and configurations |
| **Geography** | `countries.txt` | Trial locations by country |
| **Baseline Characteristics** | `baseline_counts.txt` | Disease severity distributions |
| **Disease Taxonomy** | `browse_conditions.txt` | MeSH terms for semantic matching |

### Available Indications

Use `/aact/indications` to get the full list of available indications with AACT data.

**Common indications**:
- Hypertension
- Diabetes
- Cancer (various types)
- Heart Failure
- COPD
- Asthma
- Depression
- Alzheimer's Disease
- Rheumatoid Arthritis

### Complete Study Generation

Generate all data types for a complete study with consistent Subject IDs:

```http
POST /generate/complete-study
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 50,
  "target_effect": -5.0,
  "use_aact": true           // Enable AACT enhancement
}

Response:
{
  "vitals": [ /* VitalsRecord[] */ ],
  "demographics": [ /* Demographics[] */ ],
  "labs": [ /* Labs[] */ ],
  "adverse_events": [ /* AE[] */ ],
  "metadata": {
    "subjects": 100,
    "aact_enhanced": true,
    "indication": "Hypertension",
    "phase": "Phase 3"
  }
}
```

### AACT Utility Functions

The `aact_utils.py` module provides programmatic access to AACT data:

```python
from aact_utils import get_aact_loader

aact = get_aact_loader()

# Get available indications
indications = aact.get_available_indications()

# Get realistic defaults
defaults = aact.get_realistic_defaults("hypertension", "Phase 3")

# Get specific data types
baseline_vitals = aact.get_baseline_vitals("hypertension", "Phase 3")
dropout_patterns = aact.get_dropout_patterns("hypertension", "Phase 3")
adverse_events = aact.get_adverse_events("hypertension", "Phase 3", top_n=20)
demographics = aact.get_demographics("hypertension", "Phase 3")
treatment_arms = aact.get_treatment_arms("hypertension", "Phase 3")
geo_distribution = aact.get_geographic_distribution("hypertension", "Phase 3")
```

### Example: Real vs Estimated

**Without AACT** (estimated):
```python
# Old approach - generic estimates
baseline_sbp = 140  # Same for all indications
dropout_rate = 0.15  # Industry average
```

**With AACT** (real data):
```python
# New approach - real data from hypertension Phase 3 trials
vitals = aact.get_baseline_vitals("hypertension", "Phase 3")
# Returns: {'systolic': {'mean': 152.3, 'std': 14.2, ...}}

dropout = aact.get_dropout_patterns("hypertension", "Phase 3")
# Returns: {'dropout_rate': 0.134, 'top_reasons': [...]}
```

**Impact**: Synthetic data is now indistinguishable from real clinical trials for the specified indication and phase.

### References

- **Comprehensive Integration Guide**: `/AACT_COMPREHENSIVE_INTEGRATION.md`
- **Data Integration Guide**: `/data/aact/NEW_DATA_INTEGRATION_GUIDE.md`
- **AACT Database**: https://aact.ctti-clinicaltrials.org/

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

### Critical Backend Files

```
Synthetic-Medical-Data-Generation/
├── microservices/
│   ├── data-generation-service/
│   │   └── src/
│   │       ├── main.py                    # FastAPI app, generation endpoints
│   │       ├── generators.py              # Core generation logic (MVN, Bootstrap, Rules)
│   │       └── llm_generator.py           # LLM-based generation
│   │
│   ├── analytics-service/
│   │   └── src/
│   │       ├── main.py                    # Analytics endpoints
│   │       ├── stats.py                   # Statistical analysis functions
│   │       ├── rbqm.py                    # RBQM calculations
│   │       ├── csr.py                     # CSR generation
│   │       └── sdtm.py                    # SDTM export logic
│   │
│   ├── edc-service/
│   │   └── src/
│   │       ├── main.py                    # EDC endpoints
│   │       └── models.py                  # Database models
│   │
│   ├── security-service/
│   │   └── src/
│   │       ├── main.py                    # Auth endpoints
│   │       ├── auth.py                    # JWT handling
│   │       └── encryption.py              # Data encryption (Fernet)
│   │
│   └── quality-service/
│       └── src/
│           ├── main.py                    # Validation endpoints
│           └── validators.py              # Validation logic
│
├── database/
│   ├── init.sql                           # Database schema
│   └── database.py                        # SQLAlchemy connection
│
└── data/
    ├── pilot_trial_cleaned.csv            # Real data (945 records)
    ├── pilot_trial.csv                    # Original real data (2,079 records)
    ├── validate_and_repair_real_data.py   # Data cleaning script
    ├── knn_imputation_analysis.py         # K-NN imputation analysis
    └── streamlit_dashboard.py             # Existing dashboard (reference)
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

6. **Data Analysis**
   - ✅ Distribution comparisons
   - ✅ Column-level analysis
   - ✅ Multi-panel visualizations
   - ✅ K-NN imputation with MAR pattern

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

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: Backend complete, Frontend pending
**Next Steps**: Begin frontend implementation using this reference

