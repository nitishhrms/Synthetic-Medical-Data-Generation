# End-to-End Testing Guide

## 🎯 Overview

This guide provides step-by-step instructions for performing end-to-end testing of the Synthetic Medical Data Generation platform, including all newly implemented features.

## ✅ What's Ready to Test

### Frontend Features (All Complete ✅)
1. **Data Generation** - 6 methods (MVN, Bootstrap, Rules, Bayesian, MICE, LLM)
2. **Analytics Dashboard** - Statistical analysis, quality metrics, visualizations
3. **Quality Dashboard** - SYNDATA metrics (CI coverage 88-98%), automated reports
4. **Trial Planning** - 5 advanced features (Virtual Control, Augmentation, What-If scenarios)
5. **Studies Management** - EDC integration, subject enrollment
6. **RBQM Dashboard** - Risk-based quality management
7. **Data Entry** - Forms and validation

### Backend Services Required
- **PostgreSQL**: Port 5433
- **Redis**: Port 6379
- **API Gateway**: Port 8000
- **Security Service**: Port 8005
- **Data Generation Service**: Port 8002
- **Analytics Service**: Port 8003
- **Quality Service**: Port 8004 (renamed from Quality Service port 8006 in CLAUDE.md)
- **EDC Service**: Port 8001

---

## 🚀 Starting Backend Services

### Option 1: Docker Compose (Recommended)

```bash
cd /home/user/Synthetic-Medical-Data-Generation

# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option 2: Individual Services (Manual)

If Docker is not available, start each service manually:

#### 1. Start PostgreSQL and Redis
```bash
# Install and start PostgreSQL
sudo service postgresql start

# Install and start Redis
sudo service redis-server start
```

#### 2. Start Microservices

Each service needs to be started in a separate terminal:

```bash
# Security Service (Port 8005)
cd microservices/security-service/src
uvicorn main:app --reload --port 8005

# Data Generation Service (Port 8002)
cd microservices/data-generation-service/src
uvicorn main:app --reload --port 8002

# Analytics Service (Port 8003)
cd microservices/analytics-service/src
uvicorn main:app --reload --port 8003

# Quality Service (Port 8004)
cd microservices/quality-service/src
uvicorn main:app --reload --port 8004

# EDC Service (Port 8001)
cd microservices/edc-service/src
uvicorn main:app --reload --port 8001

# API Gateway (Port 8000)
cd microservices/api-gateway/src
uvicorn main:app --reload --port 8000
```

#### 3. Verify Services Are Running

```bash
# Check health endpoints
curl http://localhost:8005/health  # Security
curl http://localhost:8002/health  # Data Generation
curl http://localhost:8003/health  # Analytics
curl http://localhost:8004/health  # Quality
curl http://localhost:8001/health  # EDC
curl http://localhost:8000/health  # API Gateway

# All should return: {"status": "healthy"}
```

---

## 🎨 Starting Frontend

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev

# Frontend will be available at: http://localhost:5173
```

---

## 🧪 E2E Testing Checklist

### 1. Authentication Testing

**Test Login:**
1. Navigate to http://localhost:5173
2. Login with test credentials (or register new user)
3. Verify successful authentication and redirect to Dashboard

**Expected Result:** Dashboard loads with navigation rail visible

---

### 2. Data Generation Testing

**Test Case: Generate Synthetic Data with MVN Method**
1. Click "Generate" in navigation
2. Select "MVN" method
3. Set parameters:
   - N per arm: 50
   - Target effect: -5.0
   - Seed: 42
4. Click "Generate Data"

**Expected Results:**
- ✅ Loading indicator appears
- ✅ Data generated successfully (400 records)
- ✅ Success message displayed
- ✅ Data preview table shows records
- ✅ Download button appears

**Test Case: Generate with All 6 Methods**
1. Repeat for each method: Bootstrap, Rules, Bayesian, MICE, LLM
2. Verify each generates data successfully
3. Compare metadata (generation time, record counts)

**Expected Results:**
- ✅ MVN: ~29,000 records/sec
- ✅ Bootstrap: ~140,000 records/sec
- ✅ Rules: ~80,000 records/sec
- ✅ Bayesian: Preserves causal structure
- ✅ MICE: Realistic missing data handling
- ✅ LLM: Requires OpenAI API key (or shows error)

---

### 3. Analytics Testing

**Test Case: Run Statistical Analysis**
1. First generate data using any method (see above)
2. Click "Analytics" in navigation
3. Click "Run Analysis"

**Expected Results:**
- ✅ Week-12 statistics displayed
- ✅ Treatment effect shown with confidence intervals
- ✅ P-value calculated
- ✅ Statistical significance indicated
- ✅ Scatter plot shows Active vs Placebo
- ✅ Distribution comparisons for all vitals
- ✅ PCA visualization shows data quality
- ✅ Quality metrics: Wasserstein distance, correlation preservation
- ✅ Overall quality score displayed

**Key Metrics to Verify:**
- Treatment difference: ~-5 mmHg (target effect)
- P-value: < 0.05 for significant results
- Quality score: > 0.85 (Excellent)

---

### 4. Quality Dashboard Testing (PROFESSOR'S KEY FEATURE)

**Test Case: SYNDATA Metrics Assessment**
1. Navigate to "Quality" (Quality Dashboard)
2. Click "Load Real Data" (pilot data)
3. Generate synthetic data if not already done
4. Click "Run SYNDATA Assessment"

**Expected Results - CI Coverage Tab:**
- ✅ Overall coverage percentage displayed (88-98% target)
- ✅ CART Standard badge shows "✅ CART Standard" if in range
- ✅ Per-variable breakdown shown:
  - SystolicBP: ~92%
  - DiastolicBP: ~91%
  - HeartRate: ~90%
  - Temperature: ~93%
- ✅ Color-coded progress bars (green for good, yellow for borderline)

**Expected Results - Other SYNDATA Metrics:**
- ✅ Support Coverage: Value range matching
- ✅ Cross-Classification: Joint distribution similarity
- ✅ Membership Disclosure: Privacy risk assessment
- ✅ Attribute Disclosure: Privacy risk assessment

**Test Case: Generate Quality Report**
1. After running SYNDATA assessment
2. Click "Generate Quality Report"

**Expected Results:**
- ✅ Comprehensive markdown report generated
- ✅ Summary statistics included
- ✅ SYNDATA metrics detailed
- ✅ Recommendations provided
- ✅ Conclusion states data quality level

---

### 5. Trial Planning Testing (NEW FEATURE - PROFESSOR'S REQUIREMENT)

#### 5.1 Virtual Control Arm

**Test Case: Generate Virtual Control Arm**
1. Navigate to "Planning" (Trial Planning)
2. Stay on "Virtual Control" tab
3. Set parameters:
   - Control Arm Size: 50
   - Target Effect: -5.0 mmHg
   - Baseline Mean SBP: 140
   - Baseline Std Dev: 10
4. Click "Generate Virtual Control"

**Expected Results:**
- ✅ Virtual control data generated (200 records for 50 subjects × 4 visits)
- ✅ Summary cards show:
  - Total Records: 200
  - Mean SBP: ~140 mmHg
  - Quality Score: >85%
- ✅ Quality metrics displayed:
  - Wasserstein Distance: Low value (good similarity)
  - Correlation Preservation: >80%
- ✅ Use case description displayed
- ✅ Success message appears

#### 5.2 Augment Control Arm

**Test Case: Augment Small Control Group**
1. Click "Augment Arm" tab
2. Set parameters:
   - Real Control: 20
   - Synthetic Add: 30
   - Target Effect: -5.0
3. Click "Augment Control Arm"

**Expected Results:**
- ✅ Combined dataset created
- ✅ Summary cards show:
  - Real Patients: 20
  - Synthetic Added: 30
  - Total Combined: 50
  - Similarity: >85%
- ✅ Before/After comparison displayed:
  - Real Only (N=20): Mean SBP, Std Dev
  - Combined (N=50): Mean SBP, Std Dev
- ✅ Benefit message explains 150% increase
- ✅ Success indicator appears

#### 5.3 Enrollment What-If Scenarios

**Test Case: Sample Size Power Analysis**
1. Click "Enrollment" tab
2. Set parameters:
   - Baseline N per Arm: 50
   - Target Effect: -5.0
   - Scenarios: 25, 50, 75, 100, 150, 200
3. Click "Run Enrollment What-If"

**Expected Results:**
- ✅ 6 scenarios analyzed
- ✅ Power by Sample Size chart displayed
- ✅ Line chart shows power increasing with N
- ✅ Scenario details list shows:
  - Each N value with corresponding power
  - P-value for each scenario
  - Badge indicates if power ≥ 80%
  - "Significant" badge if p < 0.05
- ✅ Recommendation provided (e.g., "Use N=75 per arm for 80% power")

**Key Check:**
- Power should increase with sample size
- Larger N → Higher power
- N=25 might have low power (<50%)
- N=150+ should have very high power (>95%)

#### 5.4 Patient Mix What-If Scenarios

**Test Case: Baseline Severity Analysis**
1. Click "Patient Mix" tab
2. Set parameters:
   - N per Scenario: 50
   - Baseline SBP Scenarios: 130, 140, 150, 160
   - Target Effect: -5.0
3. Click "Run Patient Mix What-If"

**Expected Results:**
- ✅ 4 scenarios analyzed (mild to severe hypertension)
- ✅ Bar chart shows treatment effect by baseline
- ✅ Scenario comparison cards show:
  - 130 mmHg: "Mild hypertension"
  - 140 mmHg: "Moderate hypertension"
  - 150 mmHg: "Moderate-severe hypertension"
  - 160 mmHg: "Severe hypertension"
- ✅ Effect size and significance for each
- ✅ Color coding: Green bars for significant, Gray for non-significant
- ✅ Insight recommendation displayed

**Key Check:**
- Effect sizes should be consistent across populations
- P-values vary by baseline severity
- Higher baseline might show stronger effects

#### 5.5 Trial Feasibility Assessment

**Test Case: Sample Size Calculation**
1. Click "Feasibility" tab
2. Set parameters:
   - Expected Effect Size: -5.0 mmHg
   - Expected Std Dev: 10 mmHg
   - Significance Level (α): 0.05
   - Desired Power: 0.8
   - Allocation Ratio: 1.0
3. Click "Assess Feasibility"

**Expected Results:**
- ✅ Required sample size calculated
- ✅ Large display shows N per arm (e.g., 63 per arm)
- ✅ Total patients shown (e.g., 126 total)
- ✅ Study parameters displayed:
  - Effect Size: -5.0 mmHg
  - Cohen's d: ~0.5
  - Power: 80%
  - Alpha: 0.05
  - Allocation: 1:1
- ✅ Feasibility assessment shown:
  - Badge: "Highly Feasible" (green) or "Feasible" (yellow)
  - Interpretation text
  - Assumptions listed
- ✅ Recommendation provided

**Key Check:**
- Larger effect size → Smaller required N
- Higher power requirement → Larger required N
- Feasibility ratings:
  - Cohen's d > 0.8: "Highly Feasible"
  - Cohen's d 0.5-0.8: "Feasible"
  - Cohen's d < 0.5: "Challenging"

---

### 6. Cross-Feature Integration Testing

**Test Case: Full Workflow - Generation → Analysis → Quality → Planning**
1. **Generate** data using Bayesian method (N=50 per arm)
2. **Analyze** the data (Week-12 statistics)
3. **Assess** quality (SYNDATA metrics, CI coverage)
4. **Plan** trial using What-If scenarios
5. **Verify** consistency across all screens

**Expected Results:**
- ✅ Same dataset used across all screens
- ✅ Statistics consistent everywhere
- ✅ Quality score >0.85
- ✅ CI coverage 88-98%
- ✅ All visualizations render correctly
- ✅ No errors or crashes

---

## 📊 Testing Summary Template

Use this template to document your testing results:

```markdown
## E2E Testing Results - [Date]

### Environment
- Frontend URL: http://localhost:5173
- Backend Services: All running ✅

### Test Results

| Feature | Status | Notes |
|---------|--------|-------|
| Authentication | ✅ | Login successful |
| Data Generation (MVN) | ✅ | 400 records in 14ms |
| Data Generation (Bayesian) | ✅ | Causal structure preserved |
| Analytics Dashboard | ✅ | P-value: 0.018, significant |
| Quality Dashboard | ✅ | CI Coverage: 92.5% (CART standard) |
| SYNDATA Metrics | ✅ | All 5 metrics calculated |
| Trial Planning - Virtual Control | ✅ | Quality score: 89% |
| Trial Planning - Augmentation | ✅ | Combined N: 50 (20+30) |
| Trial Planning - Enrollment What-If | ✅ | 6 scenarios, power chart |
| Trial Planning - Patient Mix | ✅ | 4 populations tested |
| Trial Planning - Feasibility | ✅ | Required N: 63 per arm |

### Issues Found
- [List any bugs or issues]

### Performance
- Page Load Time: [X] seconds
- Data Generation Time: [X] ms
- Analysis Time: [X] seconds
- Overall Responsiveness: Good/Fair/Poor

### Professor Demo Readiness
- ✅ SYNDATA CI Coverage (88-98%) - KEY FEATURE
- ✅ Trial Planning Features - KEY FEATURE
- ✅ Quality Reports - KEY FEATURE
- ✅ All 6 Generation Methods Working
- ✅ Professional UI/UX
```

---

## 🎓 Demonstrating to Professor

### Key Features to Highlight

1. **SYNDATA Metrics (Professor's Specific Request)**
   - Navigate to Quality Dashboard
   - Show CI Coverage tab with 88-98% range (CART study standard)
   - Explain: "This shows what percentage of synthetic data falls within real data confidence intervals"
   - Point out: Per-variable breakdown and color-coded results

2. **Trial Planning (Industry-Inspired)**
   - Navigate to Trial Planning screen
   - Demo Virtual Control Arm: "Similar to Medidata's product"
   - Show What-If scenarios: "Trial feasibility without recruiting patients"
   - Explain use case: "Reduce placebo patients, optimize study design"

3. **Quality Assessment**
   - Show comprehensive quality report
   - Highlight: Wasserstein distance, correlation preservation
   - Explain: "Multiple metrics ensure synthetic data reliability"

4. **Real-World Application**
   - Demonstrate full workflow: Generate → Analyze → Quality Check → Plan
   - Show how it addresses real pharmaceutical needs
   - Mention: "Ready for regulatory submissions with CDISC compliance"

---

## 🐛 Troubleshooting

### Backend Not Starting

```bash
# Check if ports are in use
sudo lsof -i :8000  # API Gateway
sudo lsof -i :8002  # Data Generation
sudo lsof -i :8003  # Analytics

# Kill process if needed
sudo kill -9 <PID>
```

### Frontend Build Errors

```bash
cd frontend
npm install
npm run build

# If errors persist, clear cache
rm -rf node_modules
rm package-lock.json
npm install
```

### Database Connection Issues

```bash
# Check PostgreSQL status
sudo service postgresql status

# Restart if needed
sudo service postgresql restart

# Check Redis
redis-cli ping
# Should return: PONG
```

### CORS Errors

If you see CORS errors in browser console:
1. Check backend services have `ALLOWED_ORIGINS=*` (or specific origin)
2. Verify all services are running on correct ports
3. Clear browser cache and hard reload (Ctrl+Shift+R)

---

## 📝 Notes

- **OpenAI API Key**: Required only for LLM generation method
- **Data Persistence**: Real pilot data loaded from `data/pilot_trial_cleaned.csv`
- **Session Persistence**: Generated data stored in React context (lost on refresh)
- **Production Deployment**: Update ALLOWED_ORIGINS to specific domain

---

## ✅ Testing Completed By

**Tester Name:** _______________
**Date:** _______________
**Overall Status:** ✅ Pass / ⚠️ Issues Found / ❌ Fail
**Professor Demo Ready:** ✅ Yes / ❌ No

**Signature:** _______________
