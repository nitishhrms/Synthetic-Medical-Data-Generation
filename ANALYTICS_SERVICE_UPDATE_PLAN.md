# Analytics Service Update Plan
## Comprehensive Overhaul to Match Data Generation Service (Daft Branch)

**Date**: 2025-11-20
**Current Branch**: `daft`
**Analytics Service Port**: 8003
**Current Status**: ⚠️ Requires Major Update
**Target Version**: 2.0.0

---

## Executive Summary

The **Data Generation Service** (Port 8002) on the `daft` branch has undergone massive expansion with:
- **35+ endpoints** (up from ~10)
- **10+ generation methods** (Rules, MVN, LLM, Bootstrap, Bayesian, MICE, Diffusion, AACT-based)
- **New data types**: Demographics, Labs, Comprehensive Studies
- **AACT integration**: Real-world clinical trial data from ClinicalTrials.gov
- **Million-scale generation**: Async processing for large datasets
- **Benchmarking & stress testing**: Performance monitoring

The **Analytics Service** (Port 8003) currently supports:
- ✅ Basic vitals statistics (Week 12, RECIST)
- ✅ RBQM, CSR, SDTM export (vitals only)
- ✅ Quality assessment (PCA, comprehensive)
- ✅ DAFT integration (distributed analytics)
- ✅ Trial planning features

**Gap**: Analytics service lacks support for new data types, generation methods, and AACT integration.

---

## 1. Current State Analysis

### Data Generation Service Endpoints (Daft Branch)

#### A. **Vitals Generation Methods** (10 methods)
| Method | Endpoint | Status | Analytics Support |
|--------|----------|--------|-------------------|
| Rules-based | `POST /generate/rules` | ✅ Complete | ✅ Supported |
| MVN (Pilot) | `POST /generate/mvn` | ✅ Complete | ✅ Supported |
| LLM | `POST /generate/llm` | ✅ Complete | ✅ Supported |
| Bootstrap | `POST /generate/bootstrap` | ✅ Complete | ✅ Supported |
| MVN (AACT) | `POST /generate/mvn-aact` | ✅ Complete | ❌ **Not Supported** |
| Bootstrap (AACT) | `POST /generate/bootstrap-aact` | ✅ Complete | ❌ **Not Supported** |
| Rules (AACT) | `POST /generate/rules-aact` | ✅ Complete | ❌ **Not Supported** |
| Bayesian | `POST /generate/bayesian` | ✅ Complete | ❌ **Not Supported** |
| Bayesian (AACT) | `POST /generate/bayesian-aact` | ✅ Complete | ❌ **Not Supported** |
| MICE Imputation | `POST /generate/mice` | ✅ Complete | ❌ **Not Supported** |
| MICE (AACT) | `POST /generate/mice-aact` | ✅ Complete | ❌ **Not Supported** |
| Diffusion | `POST /generate/diffusion` | ✅ Complete | ❌ **Not Supported** |

#### B. **Additional Data Types**
| Data Type | Generation Endpoints | Analytics Support |
|-----------|---------------------|-------------------|
| Demographics | `POST /generate/demographics`<br>`POST /generate/demographics-aact` | ❌ **Not Supported** |
| Lab Results | `POST /generate/labs`<br>`POST /generate/labs-aact` | ❌ **Not Supported** |
| Adverse Events | `POST /generate/ae`<br>`POST /generate/ae-aact` | ⚠️ **Partial** (only RECIST) |

#### C. **Comprehensive Generation**
| Feature | Endpoint | Analytics Support |
|---------|----------|-------------------|
| Realistic Trial | `POST /generate/realistic-trial` | ❌ **Not Supported** |
| Comprehensive Study | `POST /generate/comprehensive-study` | ❌ **Not Supported** |
| Million-Scale | `POST /generate/million-scale` | ❌ **Not Supported** |

#### D. **Real Data & AACT**
| Feature | Endpoint | Analytics Support |
|---------|----------|-------------------|
| Pilot Data | `GET /data/pilot` | ✅ Supported |
| Real Vitals | `GET /data/real-vitals` | ⚠️ **Needs enhancement** |
| Real Demographics | `GET /data/real-demographics` | ❌ **Not Supported** |
| Real AE | `GET /data/real-ae` | ❌ **Not Supported** |
| AACT Indications | `GET /aact/indications` | ❌ **Not Supported** |
| AACT Stats | `GET /aact/stats/{indication}` | ❌ **Not Supported** |

#### E. **Utility & Benchmarking**
| Feature | Endpoint | Analytics Support |
|---------|----------|-------------------|
| Method Comparison | `GET /compare` | ⚠️ **Needs expansion** |
| Performance Benchmark | `GET /benchmark/performance` | ❌ **Not Supported** |
| Concurrent Stress Test | `POST /stress-test/concurrent` | ❌ **Not Supported** |
| Portfolio Analytics | `GET /analytics/portfolio` | ⚠️ **Limited** |

---

### Current Analytics Service Endpoints

#### ✅ **Working Endpoints** (15 endpoints)
1. `GET /health` - Service health check
2. `GET /` - Service info
3. `POST /stats/week12` - Week-12 vitals statistics
4. `POST /stats/recist` - RECIST/ORR analysis
5. `POST /rbqm/summary` - RBQM quality management
6. `POST /csr/draft` - Clinical Study Report draft
7. `POST /sdtm/export` - SDTM VS export (vitals only)
8. `POST /quality/pca-comparison` - PCA visualization
9. `POST /quality/comprehensive` - Comprehensive quality assessment
10. `POST /quality/compare-methods` - Compare generation methods
11. `GET /daft/status` - DAFT service status
12. `POST /daft/aggregate/by-treatment-arm` - Treatment arm aggregation
13. `POST /daft/aggregate/by-visit` - Visit aggregation
14. `POST /daft/treatment-effect` - Treatment effect analysis
15. `POST /daft/change-from-baseline` - Baseline change analysis
16. `POST /daft/responder-analysis` - Responder analysis
17. `POST /daft/longitudinal-summary` - Longitudinal summary
18. `POST /daft/outlier-detection` - Outlier detection
19. `POST /daft/add-medical-features` - Medical feature engineering
20. `POST /daft/correlation-matrix` - Correlation analysis
21. `POST /trial-planning/virtual-control-arm` - Virtual control arm
22. `POST /trial-planning/augment-control-arm` - Augment control
23. `POST /trial-planning/what-if/enrollment` - Enrollment simulation
24. `POST /trial-planning/what-if/patient-mix` - Patient mix simulation
25. `POST /trial-planning/feasibility` - Feasibility analysis

---

## 2. Gap Analysis

### 🔴 **Critical Gaps** (Blocking Frontend Features)

1. **Demographics Analysis** ❌
   - No baseline characteristics table
   - No demographic summary statistics
   - No quality assessment for demographics
   - No SDTM DM export

2. **Lab Results Analysis** ❌
   - No safety lab analysis
   - No abnormal value detection (high/low/critical)
   - No shift tables (baseline → endpoint)
   - No SDTM LB export

3. **Enhanced AE Analysis** ⚠️
   - Current: Only RECIST/ORR for oncology
   - Missing: Treatment-emergent AEs, severity analysis, SAE tracking
   - Missing: AE frequency tables, system organ class (SOC) analysis

4. **AACT Data Analytics** ❌
   - No comparison with real-world AACT data
   - No benchmark statistics from ClinicalTrials.gov
   - No indication-specific analytics

5. **Comprehensive Study Analytics** ❌
   - No multi-domain analysis (vitals + demographics + labs + AE)
   - No integrated CSR for comprehensive studies

### 🟡 **Important Gaps** (Nice-to-Have)

6. **New Generation Methods Comparison** ⚠️
   - Bayesian method quality assessment
   - MICE imputation validation
   - Diffusion model comparison

7. **Million-Scale Analytics** ❌
   - No support for analyzing million-record datasets
   - No async analytics processing

8. **Benchmarking & Performance** ❌
   - No performance metrics dashboard
   - No quality score tracking over time

9. **Portfolio Analytics** ⚠️
   - Limited cross-study analysis
   - No meta-analysis capabilities

---

## 3. Proposed Solution Architecture

### A. **Modular Expansion Strategy**

Instead of monolithic changes, we'll expand the analytics service in **6 modules**:

```
analytics-service/src/
├── main.py                          # FastAPI app (existing)
├── stats.py                         # Vitals statistics (existing)
├── rbqm.py                          # RBQM (existing)
├── csr.py                           # CSR generation (existing)
├── sdtm.py                          # SDTM export (existing + expand)
├── daft_processor.py                # DAFT integration (existing)
├── daft_aggregations.py             # DAFT aggregations (existing)
├── daft_udfs.py                     # DAFT UDFs (existing)
│
├── demographics_analytics.py        # 📦 NEW - Demographics analysis
├── labs_analytics.py                # 📦 NEW - Lab results analysis
├── ae_analytics.py                  # 📦 NEW - Enhanced AE analysis
├── comprehensive_analytics.py       # 📦 NEW - Multi-domain analysis
├── aact_analytics.py                # 📦 NEW - AACT comparison
├── quality_extended.py              # 📦 NEW - Extended quality for all data types
├── benchmarking.py                  # 📦 NEW - Performance & benchmarking
└── portfolio.py                     # 📦 NEW - Portfolio analytics
```

### B. **New Endpoints to Add** (26 new endpoints)

#### **Demographics Analytics** (5 endpoints)
1. `POST /stats/demographics/baseline` - Baseline characteristics table
2. `POST /stats/demographics/summary` - Demographic summary (age, gender, race distribution)
3. `POST /quality/demographics/compare` - Compare real vs synthetic demographics
4. `POST /sdtm/demographics/export` - Export to SDTM DM domain
5. `POST /stats/demographics/balance` - Treatment arm balance check

#### **Lab Results Analytics** (7 endpoints)
6. `POST /stats/labs/summary` - Lab results summary statistics
7. `POST /stats/labs/abnormal` - Abnormal value detection
8. `POST /stats/labs/shift-table` - Shift table (normal → abnormal)
9. `POST /stats/labs/trends` - Longitudinal trends
10. `POST /stats/labs/safety-signals` - Safety signal detection
11. `POST /quality/labs/compare` - Compare real vs synthetic labs
12. `POST /sdtm/labs/export` - Export to SDTM LB domain

#### **Enhanced AE Analytics** (5 endpoints)
13. `POST /stats/ae/frequency` - AE frequency table
14. `POST /stats/ae/treatment-emergent` - Treatment-emergent AEs
15. `POST /stats/ae/soc-analysis` - System Organ Class analysis
16. `POST /stats/ae/severity` - Severity distribution
17. `POST /sdtm/ae/export` - Export to SDTM AE domain

#### **Comprehensive Study Analytics** (3 endpoints)
18. `POST /stats/comprehensive/summary` - Multi-domain summary
19. `POST /csr/comprehensive/draft` - Integrated CSR for all domains
20. `POST /quality/comprehensive/assess` - Quality assessment across all domains

#### **AACT Integration** (3 endpoints)
21. `POST /aact/compare-indication` - Compare with AACT benchmark
22. `POST /aact/quality-score` - AACT-based quality score
23. `POST /aact/similarity-analysis` - Similarity to real-world trials

#### **Quality Extensions** (2 endpoints)
24. `POST /quality/method-comparison/extended` - Compare all generation methods
25. `POST /quality/privacy/assessment` - Privacy metrics (K-anonymity, etc.)

#### **Benchmarking** (1 endpoint)
26. `POST /benchmark/quality-dashboard` - Quality metrics dashboard

---

## 4. Detailed Implementation Plan

### **Phase 1: Demographics Analytics** (Priority: 🔴 Critical)

**Files to Create/Modify:**
- ✅ Create `demographics_analytics.py`
- ✅ Update `main.py` (add 5 endpoints)
- ✅ Update `sdtm.py` (add DM export function)

**Implementation:**
```python
# demographics_analytics.py

def calculate_baseline_characteristics(demographics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate baseline characteristics table (Table 1 in papers)

    Returns:
        - Continuous variables: Mean ± SD, Median (IQR)
        - Categorical variables: N (%)
        - By treatment arm comparison
    """
    pass

def calculate_demographic_summary(demographics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Demographic distribution summary

    Returns:
        - Age distribution (histogram bins)
        - Gender distribution
        - Race/ethnicity distribution
        - BMI categories
    """
    pass

def assess_treatment_arm_balance(demographics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if randomization produced balanced treatment arms

    Uses:
        - Chi-square tests for categorical variables
        - T-tests for continuous variables
        - Standardized differences
    """
    pass

def compare_demographics_quality(real_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Quality assessment for demographics

    Metrics:
        - Wasserstein distance (age, BMI)
        - Chi-square (gender, race, ethnicity)
        - Correlation preservation
    """
    pass
```

**Endpoints:**
```python
# main.py

@app.post("/stats/demographics/baseline")
async def demographics_baseline(request: DemographicsRequest):
    """Generate baseline characteristics table"""
    df = pd.DataFrame(request.demographics_data)
    result = calculate_baseline_characteristics(df)
    return result

@app.post("/stats/demographics/summary")
async def demographics_summary(request: DemographicsRequest):
    """Demographic distribution summary"""
    df = pd.DataFrame(request.demographics_data)
    result = calculate_demographic_summary(df)
    return result

@app.post("/stats/demographics/balance")
async def demographics_balance(request: DemographicsRequest):
    """Check treatment arm balance"""
    df = pd.DataFrame(request.demographics_data)
    result = assess_treatment_arm_balance(df)
    return result

@app.post("/quality/demographics/compare")
async def demographics_quality(request: DemographicsCompareRequest):
    """Compare real vs synthetic demographics"""
    real_df = pd.DataFrame(request.real_data)
    syn_df = pd.DataFrame(request.synthetic_data)
    result = compare_demographics_quality(real_df, syn_df)
    return result

@app.post("/sdtm/demographics/export")
async def demographics_sdtm_export(request: DemographicsRequest):
    """Export demographics to SDTM DM domain"""
    df = pd.DataFrame(request.demographics_data)
    sdtm_dm = export_to_sdtm_dm(df)
    return {"sdtm_data": sdtm_dm.to_dict(orient="records")}
```

**Testing:**
```bash
# Test baseline characteristics
curl -X POST http://localhost:8003/stats/demographics/baseline \
  -H "Content-Type: application/json" \
  -d '{"demographics_data": [...]}'
```

---

### **Phase 2: Lab Results Analytics** (Priority: 🔴 Critical)

**Files to Create:**
- ✅ Create `labs_analytics.py`
- ✅ Update `main.py` (add 7 endpoints)
- ✅ Update `sdtm.py` (add LB export function)

**Implementation:**
```python
# labs_analytics.py

def calculate_lab_summary(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Lab results summary statistics

    For each lab parameter (Hemoglobin, Glucose, Creatinine, etc.):
        - Mean ± SD by visit
        - Reference range comparisons
        - Change from baseline
    """
    pass

def detect_abnormal_values(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Abnormal value detection

    Categories:
        - Low: Below reference range
        - High: Above reference range
        - Critical: Dangerously abnormal (e.g., Hemoglobin < 7 g/dL)

    Returns:
        - Frequency of abnormal values by parameter
        - List of critical values requiring clinical attention
    """
    pass

def generate_shift_table(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Shift table (Baseline → Endpoint)

    Shows movement between:
        - Normal → Normal
        - Normal → Low/High
        - Low/High → Normal
        - Low/High → Worse
    """
    pass

def analyze_lab_trends(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Longitudinal trends

    For each subject:
        - Trajectory over time (Screening → Week 4 → Week 12)
        - Slope of change
        - Pattern detection (improving, worsening, stable)
    """
    pass

def detect_safety_signals(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Safety signal detection

    Identifies:
        - Potential liver toxicity (ALT/AST > 3x ULN)
        - Renal impairment (Creatinine elevation)
        - Hematologic toxicity (WBC/Platelet drop)

    Returns:
        - Flagged subjects
        - Signal severity
        - Frequency by treatment arm
    """
    pass

def compare_labs_quality(real_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Quality assessment for lab results

    Metrics:
        - Distribution similarity (Wasserstein)
        - Correlation preservation
        - Reference range compliance
    """
    pass
```

**Reference Ranges** (used for abnormal detection):
```python
REFERENCE_RANGES = {
    "Hemoglobin": {"low": 12.0, "high": 17.0, "critical_low": 7.0, "critical_high": 20.0},
    "Hematocrit": {"low": 36.0, "high": 50.0, "critical_low": 25.0, "critical_high": 60.0},
    "WBC": {"low": 4.0, "high": 11.0, "critical_low": 2.0, "critical_high": 30.0},
    "Platelets": {"low": 150, "high": 400, "critical_low": 50, "critical_high": 1000},
    "Glucose": {"low": 70, "high": 100, "critical_low": 40, "critical_high": 400},
    "Creatinine": {"low": 0.6, "high": 1.2, "critical_low": 0.3, "critical_high": 10.0},
    "BUN": {"low": 7, "high": 20, "critical_low": 5, "critical_high": 100},
    "ALT": {"low": 7, "high": 55, "critical_low": 0, "critical_high": 300},
    "AST": {"low": 8, "high": 48, "critical_low": 0, "critical_high": 300},
    "Bilirubin": {"low": 0.1, "high": 1.2, "critical_low": 0, "critical_high": 10.0},
}
```

---

### **Phase 3: Enhanced AE Analytics** (Priority: 🟡 Important)

**Files to Create:**
- ✅ Create `ae_analytics.py`
- ✅ Update `main.py` (add 5 endpoints)
- ✅ Update `sdtm.py` (add AE export function)

**Implementation:**
```python
# ae_analytics.py

def calculate_ae_frequency(ae_df: pd.DataFrame) -> Dict[str, Any]:
    """
    AE frequency table

    Returns:
        - Most common AEs by preferred term
        - Frequency by treatment arm
        - Incidence rates
    """
    pass

def analyze_treatment_emergent_aes(ae_df: pd.DataFrame, demographics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Treatment-emergent adverse events (TEAEs)

    Definition: AEs occurring after first dose

    Returns:
        - TEAE count by arm
        - Time to first TEAE
        - AE duration
    """
    pass

def analyze_soc(ae_df: pd.DataFrame) -> Dict[str, Any]:
    """
    System Organ Class (SOC) analysis

    Groups AEs by body system:
        - Gastrointestinal disorders
        - Nervous system disorders
        - Skin and subcutaneous tissue disorders
        - etc.
    """
    pass

def analyze_severity(ae_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Severity distribution

    CTCAE Grades:
        - Grade 1 (Mild)
        - Grade 2 (Moderate)
        - Grade 3 (Severe)
        - Grade 4 (Life-threatening)
        - Grade 5 (Death)
    """
    pass
```

---

### **Phase 4: AACT Integration** (Priority: 🟡 Important)

**Files to Create:**
- ✅ Create `aact_analytics.py`
- ✅ Update `main.py` (add 3 endpoints)

**Implementation:**
```python
# aact_analytics.py

def compare_with_aact_benchmark(
    synthetic_df: pd.DataFrame,
    indication: str
) -> Dict[str, Any]:
    """
    Compare synthetic data with AACT benchmark for indication

    Process:
        1. Fetch AACT stats for indication (via Data Gen Service)
        2. Compare distributions
        3. Calculate similarity score

    Returns:
        - Wasserstein distance vs AACT
        - Demographic alignment
        - Efficacy alignment
    """
    pass

def calculate_aact_quality_score(
    synthetic_df: pd.DataFrame,
    indication: str
) -> float:
    """
    Quality score based on AACT similarity

    Score components:
        - 30% - Demographic similarity
        - 40% - Efficacy measure similarity
        - 30% - Safety profile similarity

    Returns:
        - Quality score 0-1 (higher = more realistic)
    """
    pass

def analyze_aact_similarity(
    synthetic_df: pd.DataFrame,
    indication: str
) -> Dict[str, Any]:
    """
    Detailed similarity analysis

    Returns:
        - How synthetic data compares to real-world trials
        - Strengths and weaknesses
        - Recommendations for parameter adjustment
    """
    pass
```

---

### **Phase 5: Comprehensive Study Analytics** (Priority: 🟡 Important)

**Files to Create:**
- ✅ Create `comprehensive_analytics.py`
- ✅ Update `main.py` (add 3 endpoints)
- ✅ Update `csr.py` (add comprehensive CSR function)

**Implementation:**
```python
# comprehensive_analytics.py

def analyze_comprehensive_study(
    vitals_df: pd.DataFrame,
    demographics_df: pd.DataFrame,
    labs_df: pd.DataFrame,
    ae_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Multi-domain analysis for comprehensive studies

    Integrates:
        - Baseline characteristics (demographics)
        - Efficacy analysis (vitals)
        - Safety analysis (labs + AE)
        - Quality metrics across all domains

    Returns:
        - Integrated summary
        - Cross-domain correlations
        - Holistic quality score
    """
    pass

def generate_comprehensive_csr(
    vitals_df: pd.DataFrame,
    demographics_df: pd.DataFrame,
    labs_df: pd.DataFrame,
    ae_df: pd.DataFrame,
    study_metadata: Dict[str, Any]
) -> str:
    """
    Generate integrated CSR for all domains

    Sections:
        1. Study Design & Objectives
        2. Baseline Demographics
        3. Efficacy Results (vitals)
        4. Safety Results (labs + AE)
        5. Discussion & Conclusions

    Returns:
        - Markdown formatted CSR
    """
    pass

def assess_comprehensive_quality(
    real_vitals: pd.DataFrame,
    real_demographics: pd.DataFrame,
    real_labs: pd.DataFrame,
    real_ae: pd.DataFrame,
    syn_vitals: pd.DataFrame,
    syn_demographics: pd.DataFrame,
    syn_labs: pd.DataFrame,
    syn_ae: pd.DataFrame
) -> Dict[str, Any]:
    """
    Quality assessment across all domains

    Returns:
        - Overall quality score
        - Domain-specific scores
        - Weakest domain identification
        - Improvement recommendations
    """
    pass
```

---

### **Phase 6: Benchmarking & Extensions** (Priority: 🟢 Nice-to-Have)

**Files to Create:**
- ✅ Create `benchmarking.py`
- ✅ Update `quality_extended.py`
- ✅ Update `main.py` (add 2 endpoints)

**Implementation:**
```python
# benchmarking.py

def generate_quality_dashboard() -> Dict[str, Any]:
    """
    Quality metrics dashboard

    Shows:
        - Quality score trends over time
        - Comparison across generation methods
        - Best/worst performing methods by metric
    """
    pass

# quality_extended.py

def compare_all_generation_methods(
    pilot_df: pd.DataFrame,
    n_per_arm: int = 50
) -> Dict[str, Any]:
    """
    Compare ALL generation methods

    Methods tested:
        - Rules, MVN, Bootstrap, Bayesian, MICE, Diffusion
        - With and without AACT data

    Returns:
        - Quality scores for each method
        - Performance metrics (speed, memory)
        - Recommendation: which method to use when
    """
    pass
```

---

## 5. Implementation Timeline

### **Sprint 1** (Week 1): Demographics + Labs Analytics
- ✅ Day 1-2: Create `demographics_analytics.py` + endpoints
- ✅ Day 3-4: Create `labs_analytics.py` + endpoints
- ✅ Day 5: Update `sdtm.py` for DM + LB export
- ✅ Day 6-7: Testing + documentation

**Deliverables:**
- 12 new endpoints (5 demographics + 7 labs)
- SDTM DM & LB export
- Unit tests

---

### **Sprint 2** (Week 2): Enhanced AE + AACT Analytics
- ✅ Day 1-2: Create `ae_analytics.py` + endpoints
- ✅ Day 3-4: Create `aact_analytics.py` + endpoints
- ✅ Day 5: Update `sdtm.py` for AE export
- ✅ Day 6-7: Testing + integration

**Deliverables:**
- 8 new endpoints (5 AE + 3 AACT)
- SDTM AE export
- AACT integration

---

### **Sprint 3** (Week 3): Comprehensive Analytics + Quality Extensions
- ✅ Day 1-3: Create `comprehensive_analytics.py` + endpoints
- ✅ Day 4-5: Update `quality_extended.py` for method comparison
- ✅ Day 6-7: Create `benchmarking.py` + dashboard

**Deliverables:**
- 6 new endpoints (3 comprehensive + 2 quality + 1 benchmark)
- Comprehensive CSR generation
- Method comparison dashboard

---

### **Sprint 4** (Week 4): Testing, Documentation, Frontend Integration
- ✅ Day 1-3: Comprehensive testing (unit + integration)
- ✅ Day 4-5: API documentation (OpenAPI/Swagger)
- ✅ Day 6-7: Frontend integration guide + examples

**Deliverables:**
- 100% test coverage
- Complete API documentation
- Frontend integration examples

---

## 6. Testing Strategy

### A. **Unit Tests** (per module)
```python
# test_demographics_analytics.py
def test_baseline_characteristics():
    """Test baseline characteristics calculation"""
    pass

def test_demographic_summary():
    """Test demographic summary stats"""
    pass

def test_treatment_arm_balance():
    """Test balance assessment"""
    pass

# test_labs_analytics.py
def test_abnormal_value_detection():
    """Test abnormal value detection with known cases"""
    # Test case: Hemoglobin = 6.5 g/dL should be flagged as critical
    pass

def test_shift_table_generation():
    """Test shift table calculation"""
    pass

# ... similar for all modules
```

### B. **Integration Tests**
```python
# test_integration.py
def test_comprehensive_study_analysis():
    """
    Test end-to-end comprehensive study analysis

    Flow:
        1. Generate vitals, demographics, labs, AE
        2. Analyze each domain
        3. Generate comprehensive CSR
        4. Validate outputs
    """
    pass

def test_aact_integration():
    """Test AACT data fetching and comparison"""
    pass
```

### C. **API Tests** (via `pytest` + `httpx`)
```python
@pytest.mark.asyncio
async def test_demographics_baseline_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/stats/demographics/baseline", json={
            "demographics_data": [...]
        })
        assert response.status_code == 200
        assert "baseline_characteristics" in response.json()
```

---

## 7. Documentation Updates

### A. **Update CLAUDE.md**
- Add new analytics endpoints
- Update data flow diagrams
- Add examples for demographics/labs analytics

### B. **Create API Documentation**
```markdown
# Analytics Service API Documentation

## Demographics Analytics

### POST /stats/demographics/baseline
Generate baseline characteristics table (Table 1)

**Request:**
```json
{
  "demographics_data": [
    {
      "SubjectID": "RA001-001",
      "Age": 45,
      "Gender": "Male",
      "Race": "White",
      "BMI": 28.5,
      "TreatmentArm": "Active"
    }
  ]
}
```

**Response:**
```json
{
  "overall": {
    "n": 100,
    "age_mean": 54.2,
    "age_sd": 12.3,
    "gender_male_pct": 52.0
  },
  "by_arm": {
    "Active": {...},
    "Placebo": {...}
  },
  "p_values": {
    "age": 0.342,
    "gender": 0.518
  }
}
```
```

### C. **Create Frontend Integration Guide**
```typescript
// Example: Fetch baseline characteristics
const fetchBaselineCharacteristics = async (demographicsData: any[]) => {
  const response = await fetch('http://localhost:8003/stats/demographics/baseline', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ demographics_data: demographicsData })
  });

  const result = await response.json();
  return result;
};
```

---

## 8. Success Criteria

### A. **Functional Requirements**
- ✅ All 26 new endpoints functional
- ✅ Demographics, labs, AE analytics working
- ✅ AACT integration complete
- ✅ Comprehensive study analysis working
- ✅ SDTM export for all domains (VS, DM, LB, AE)

### B. **Quality Requirements**
- ✅ 90%+ test coverage
- ✅ API response time < 500ms (for standard datasets)
- ✅ No breaking changes to existing endpoints
- ✅ Comprehensive documentation

### C. **Integration Requirements**
- ✅ Frontend can consume all new endpoints
- ✅ Data generation service outputs compatible
- ✅ AACT data properly integrated

---

## 9. Risks & Mitigation

### Risk 1: **Backward Compatibility**
**Risk**: New changes break existing frontend
**Mitigation**:
- Keep all existing endpoints unchanged
- Add new endpoints without modifying old ones
- Version API if needed (`/v2/stats/...`)

### Risk 2: **Performance Degradation**
**Risk**: New analytics slow for large datasets
**Mitigation**:
- Use DAFT for distributed processing where possible
- Implement caching for expensive calculations
- Add pagination for large result sets

### Risk 3: **AACT API Availability**
**Risk**: AACT service may be unavailable
**Mitigation**:
- Cache AACT responses
- Graceful degradation (skip AACT comparison if unavailable)
- Provide fallback to pilot data

---

## 10. Next Steps

### Immediate Actions (Today):
1. ✅ **Get approval** on this plan
2. ✅ **Create feature branch**: `feature/analytics-service-update`
3. ✅ **Set up project structure** (create new files)
4. ✅ **Start Sprint 1**: Demographics analytics

### This Week:
- Complete demographics analytics module
- Complete labs analytics module
- Update SDTM export

### Next Week:
- AE analytics enhancement
- AACT integration
- Comprehensive study analytics

---

## 11. Questions for Clarification

Before starting implementation, please confirm:

1. **Priority**: Should we focus on any specific data type first (demographics vs labs vs AE)?
2. **AACT Access**: Do we have API credentials for ClinicalTrials.gov AACT database?
3. **Frontend Timeline**: When does frontend need these new endpoints?
4. **Performance**: Are there any specific performance requirements (response time, dataset size)?
5. **SDTM Compliance**: Do we need full CDISC SDTM compliance or simplified export?

---

## 12. Summary

**Current State**: Analytics service supports vitals analysis only
**Target State**: Full multi-domain analytics (vitals + demographics + labs + AE)
**New Endpoints**: 26
**New Modules**: 6
**Timeline**: 4 weeks
**Complexity**: 🔴 High (major overhaul)

**Recommended Approach**: Incremental development with weekly sprints, thorough testing at each phase.

---

**Ready to proceed?** Please review and approve this plan, and I'll start implementation immediately! 🚀
