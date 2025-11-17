# Comprehensive Testing Guide - Synthetic Medical Data Generation Platform

**Last Updated**: 2025-11-16
**Platform Version**: 2.0 (Frontend + Backend Microservices)
**Status**: Production Ready ✅

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start Testing](#quick-start-testing)
3. [Backend Services Testing](#backend-services-testing)
4. [Frontend Application Testing](#frontend-application-testing)
5. [Analytics Dashboard Testing](#analytics-dashboard-testing) ⭐
6. [End-to-End Workflows](#end-to-end-workflows)
7. [Performance Testing](#performance-testing)
8. [Troubleshooting](#troubleshooting)
9. [Expected Results Reference](#expected-results-reference)

---

## Prerequisites

### Required Services Running

Before testing, ensure all services are running:

**Backend Services** (running on localhost):
- ✅ Data Generation Service: Port 8002
- ✅ Analytics Service: Port 8003
- ✅ EDC Service: Port 8004
- ✅ Security Service: Port 8005
- ✅ Quality Service: Port 8006

**Frontend**:
- ✅ React/Vite Dev Server: Port 3000

### Verify Services Are Running

```bash
# Check backend services
for port in 8002 8003 8004 8005 8006; do
  echo "Port $port: $(curl -s http://localhost:$port/health 2>/dev/null || echo 'NOT RUNNING')"
done

# Check frontend
curl -s http://localhost:3000 > /dev/null && echo "Frontend: RUNNING" || echo "Frontend: NOT RUNNING"
```

**Expected Output**:
```
Port 8002: {"status":"healthy","service":"data-generation-service"...}
Port 8003: {"status":"healthy","service":"analytics-service"...}
Port 8004: {"status":"healthy","service":"edc-service"...}
Port 8005: {"status":"healthy","service":"security-service"...}
Port 8006: {"status":"healthy","service":"quality-service"...}
Frontend: RUNNING
```

---

## Quick Start Testing

### 1. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

**What to Expect**:
- Login/Registration screen appears
- Clean, modern UI with purple branding (#6750A4)
- No console errors in browser DevTools

### 2. Register a Test User

Click **"Sign up"** and create a test account:

```
Username: test_researcher
Email: researcher@example.com
Password: TestPass123!
Role: researcher
```

**What to Expect**:
- Registration succeeds
- Automatic login after registration
- Redirected to Dashboard

### 3. Navigate to Data Generation

Click **"Data Generation"** in the sidebar.

**What to Expect**:
- Four generation method tabs: MVN, Bootstrap, Rules, LLM
- Form fields for configuration (n_per_arm, target_effect, etc.)
- "Generate Data" button

### 4. Generate Test Data (MVN Method)

**Steps**:
1. Select **MVN** tab
2. Set `n_per_arm`: 10
3. Set `target_effect`: -5.0
4. Click **"Generate Data"**

**What to Expect**:
- Progress indicator appears
- Generation completes in < 1 second
- Success message: "✅ Successfully generated 40 records"
- Data preview table shows 40 rows
- Columns: SubjectID, VisitName, TreatmentArm, SystolicBP, DiastolicBP, HeartRate, Temperature

**Sample Data Row**:
```json
{
  "SubjectID": "RA001-001",
  "VisitName": "Screening",
  "TreatmentArm": "Active",
  "SystolicBP": 142,
  "DiastolicBP": 88,
  "HeartRate": 72,
  "Temperature": 36.7
}
```

---

## Backend Services Testing

### Data Generation Service (Port 8002)

#### Test 1: MVN Generation

```bash
curl -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 5,
    "target_effect": -5.0,
    "seed": 123
  }'
```

**What to Expect**:
- HTTP 200 OK
- JSON array of VitalsRecords
- Total records: 40 (5 subjects/arm × 2 arms × 4 visits)
- SystolicBP values: 95-200 mmHg
- DiastolicBP values: 55-130 mmHg
- HeartRate values: 50-120 bpm
- Temperature values: 35.0-40.0 °C

**Validation**:
```bash
# Save response and validate
curl -s -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 5, "target_effect": -5.0, "seed": 123}' | \
  python3 -c "import sys, json; data = json.load(sys.stdin); \
  print(f'✅ Total records: {len(data)}'); \
  print(f'✅ Unique subjects: {len(set(r[\"SubjectID\"] for r in data))}'); \
  print(f'✅ Treatment arms: {set(r[\"TreatmentArm\"] for r in data)}'); \
  print(f'✅ Visits: {set(r[\"VisitName\"] for r in data)}')"
```

**Expected Output**:
```
✅ Total records: 40
✅ Unique subjects: 10
✅ Treatment arms: {'Active', 'Placebo'}
✅ Visits: {'Screening', 'Day 1', 'Week 4', 'Week 12'}
```

#### Test 2: Pilot Data Endpoint

```bash
curl -s http://localhost:8002/data/pilot | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'✅ Pilot data records: {len(data)}')"
```

**Expected Output**:
```
✅ Pilot data records: 945
```

#### Test 3: Bootstrap Generation

```bash
# First get pilot data, then use it for bootstrap
curl -s http://localhost:8002/data/pilot > /tmp/pilot.json

curl -X POST http://localhost:8002/generate/bootstrap \
  -H "Content-Type: application/json" \
  -d "{
    \"training_data\": $(cat /tmp/pilot.json),
    \"n_per_arm\": 10,
    \"target_effect\": -5.0,
    \"jitter_frac\": 0.05,
    \"seed\": 456
  }" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'✅ Bootstrap records: {len(data)}')"
```

**Expected Output**:
```
✅ Bootstrap records: 40-80 (variable due to resampling)
```

---

### Analytics Service (Port 8003)

#### Test 1: Week-12 Statistics

```bash
# Generate data first
curl -s -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 50, "target_effect": -5.0, "seed": 123}' > /tmp/vitals.json

# Run Week-12 analysis
curl -X POST http://localhost:8003/stats/week12 \
  -H "Content-Type: application/json" \
  -d "{\"vitals_data\": $(cat /tmp/vitals.json)}" | jq '.'
```

**What to Expect**:
```json
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

**Key Metrics to Validate**:
- ✅ `p_value` should be < 0.05 (statistically significant)
- ✅ `difference` should be close to target_effect (-5.0 mmHg)
- ✅ `significant` should be `true`
- ✅ Both groups should have n=50

#### Test 2: Quality Assessment

```bash
# Get real and synthetic data
curl -s http://localhost:8002/data/pilot > /tmp/real.json
curl -s -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 50, "target_effect": -5.0}' > /tmp/synthetic.json

# Run comprehensive quality assessment
curl -X POST http://localhost:8003/quality/comprehensive \
  -H "Content-Type: application/json" \
  -d "{
    \"original_data\": $(cat /tmp/real.json),
    \"synthetic_data\": $(cat /tmp/synthetic.json),
    \"k\": 5
  }" | jq '.'
```

**What to Expect**:
```json
{
  "wasserstein_distances": {
    "SystolicBP": 2.34,
    "DiastolicBP": 1.87,
    "HeartRate": 3.12,
    "Temperature": 0.15
  },
  "correlation_preservation": 0.94,
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

**Quality Score Interpretation**:
- ✅ **≥ 0.85**: EXCELLENT - Production ready
- ⚠️ **0.70-0.85**: GOOD - Minor adjustments needed
- ❌ **< 0.70**: NEEDS IMPROVEMENT - Review parameters

---

## Frontend Application Testing

### Test 1: Data Generation Workflow

**Steps**:
1. Navigate to **Data Generation** page
2. Select **MVN** tab
3. Configure:
   - n_per_arm: 25
   - target_effect: -5.0
   - seed: 777
4. Click **"Generate Data"**

**What to Expect**:
- Loading spinner appears
- Success toast notification
- Data preview table loads with 100 records (25 × 2 × 4)
- **Download CSV** button appears
- Click **Download CSV** → file downloads as `generated_vitals_mvn.csv`

**CSV Validation**:
- Open downloaded CSV in Excel/Numbers
- Header row: SubjectID, VisitName, TreatmentArm, SystolicBP, DiastolicBP, HeartRate, Temperature
- 100 data rows
- No missing values

---

### Test 2: Bootstrap Generation

**Steps**:
1. Select **Bootstrap** tab
2. Configure:
   - n_per_arm: 30
   - target_effect: -5.0
   - jitter_frac: 0.05
3. Click **"Generate Data"**

**What to Expect**:
- First, pilot data is fetched (may take 1-2 seconds for 945 records)
- Progress indicator shows "Loading pilot data..."
- Then generation starts
- Success message shows variable record count (60-120 records typical)
- Bootstrap data should resemble pilot data characteristics

---

### Test 3: Analytics Dashboard Navigation

**Steps**:
1. After generating data (MVN or Bootstrap), click **"View Analytics"** button
2. OR navigate to **Analytics** from sidebar

**What to Expect**:
- Redirected to Analytics & Quality page
- Three main tabs:
  - **Statistics** - Week-12 analysis results
  - **Quality Metrics** - Comprehensive quality assessment
  - **Visualizations** - Distribution comparisons

---

## Analytics Dashboard Testing ⭐

**This is the CORE functionality for comprehensive data validation.**

### Prerequisites

Generate three datasets for complete analytics testing:

```bash
# Option A: Use frontend to generate all three
# Navigate to Data Generation → MVN → Generate
# Navigate to Data Generation → Bootstrap → Generate
# Navigate to Data Generation → Rules → Generate

# Option B: Use API directly
# Real data
curl -s http://localhost:8002/data/pilot > /tmp/real_data.json

# MVN synthetic
curl -s -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 50, "target_effect": -5.0, "seed": 123}' > /tmp/mvn_data.json

# Bootstrap synthetic
curl -s -X POST http://localhost:8002/generate/bootstrap \
  -H "Content-Type: application/json" \
  -d "{\"training_data\": $(cat /tmp/real_data.json), \"n_per_arm\": 50}" > /tmp/bootstrap_data.json
```

---

### Test 1: Distribution Comparisons

**Navigate**: Analytics → Visualizations → Real vs MVN

**What to Look For**:

#### Panel 1-4: Overlaid Density Histograms

**Systolic BP Histogram**:
- ✅ **Green curve** (Real Data): Smooth bell-shaped distribution
  - Peak around 130-140 mmHg
  - Range: 95-200 mmHg
- ✅ **Purple curve** (MVN): Should closely match real data shape
  - Similar peak location
  - Similar spread
  - Slightly smoother (less noise)

**Validation Checklist**:
- [ ] Curves overlay properly (aligned bin edges)
- [ ] Peak values within 10% of each other
- [ ] Both curves integrate to ≈ 1.0 (density mode)
- [ ] Tooltip shows bin range, density value, and cohort name
- [ ] Export PNG button works

**Diastolic BP, Heart Rate, Temperature**:
- Same validation criteria as Systolic BP
- Expected ranges:
  - DBP: 55-130 mmHg
  - HR: 50-120 bpm
  - Temp: 35.0-40.0 °C

#### Panel 5: Records per Visit

**What to Expect**:
- Grouped bar chart
- X-axis: Visit names (Screening, Day 1, Week 4, Week 12)
- Y-axis: Record count
- Two bars per visit (Real vs MVN)
- All bars should be approximately equal height
  - Real: ~236 records/visit (945 total / 4 visits)
  - MVN: ~100 records/visit (400 total / 4 visits for n_per_arm=50)

**Validation**:
- [ ] All visits have equal representation
- [ ] No missing visits
- [ ] Tooltip shows exact counts

#### Panel 6: Treatment Arm Balance

**What to Expect**:
- Grouped bar chart
- X-axis: Treatment arms (Active, Placebo)
- Y-axis: Subject count
- Two bars (Real vs MVN)
- Bars should be equal height (balanced randomization)
  - Real Active: ~473 records
  - Real Placebo: ~472 records
  - MVN Active: 200 records (50 subjects × 4 visits)
  - MVN Placebo: 200 records

**Validation**:
- [ ] Active and Placebo counts are equal (±1 for real data)
- [ ] Perfect balance for synthetic data

#### Panel 7: Visit Sequence Completeness

**What to Expect**:
- Stacked bar chart (percentage mode)
- Shows % of subjects with complete visit sequences
- Real data: May have incomplete sequences (dropouts)
  - Complete: ~85-95%
  - Incomplete: ~5-15%
- Synthetic data: 100% complete (by design)

**Validation**:
- [ ] Synthetic shows 100% complete
- [ ] Real shows realistic dropout rate
- [ ] Colors: Green (complete), Orange (incomplete)

#### Panel 8: Pulse Pressure Distribution

**What to Expect**:
- Calculated as: Systolic BP - Diastolic BP
- Overlaid histogram (Real vs MVN)
- Expected range: 20-80 mmHg
- Peak around 40-50 mmHg

**Validation**:
- [ ] Both distributions peak at similar values
- [ ] MVN distribution matches real distribution shape
- [ ] No negative values
- [ ] No outliers > 100 mmHg

#### Panel 9: Summary Statistics Table

**What to Expect**:

| Metric | Real Data | MVN Synthetic | Diff % |
|--------|-----------|---------------|--------|
| **Systolic BP** |  |  |  |
| Mean | 135.4 | 134.8 | -0.4% 🟢 |
| Std Dev | 14.2 | 13.9 | -2.1% 🟢 |
| Min | 96 | 98 | +2.1% 🟢 |
| Max | 198 | 195 | -1.5% 🟢 |
| **Diastolic BP** |  |  |  |
| Mean | 82.3 | 82.0 | -0.4% 🟢 |
| Std Dev | 9.8 | 9.5 | -3.1% 🟢 |
| **Heart Rate** |  |  |  |
| Mean | 72.1 | 71.8 | -0.4% 🟢 |
| Std Dev | 11.2 | 11.0 | -1.8% 🟢 |
| **Temperature** |  |  |  |
| Mean | 36.6 | 36.6 | 0.0% 🟢 |
| Std Dev | 0.4 | 0.4 | 0.0% 🟢 |

**Validation Criteria**:
- [ ] Diff % for means: < 5% (Excellent) 🟢
- [ ] Diff % for std devs: < 10% (Good) 🟡
- [ ] Diff % for extremes: < 15% (Acceptable) 🟠
- [ ] CSV export button works
- [ ] Downloaded CSV matches table data

---

### Test 2: Three-Way Comparison

**Navigate**: Analytics → Visualizations → Three-Way Comparison

**What to Expect**:
- Comparison of Real, MVN, and Bootstrap datasets
- 12 panels total

#### Box Plots (Panels 7-9)

**Systolic BP Box Plot**:
- Three box plots side-by-side (Real, MVN, Bootstrap)
- Each box shows:
  - **Box**: Q1 to Q3 (Interquartile Range)
  - **Line inside box**: Median
  - **Whiskers**: Q1 - 1.5×IQR to Q3 + 1.5×IQR
  - **Dots**: Outliers beyond whiskers

**What to Look For**:
- [ ] **Medians** (horizontal line in box) are similar across all three
  - Real: ~135 mmHg
  - MVN: ~134 mmHg
  - Bootstrap: ~135 mmHg
- [ ] **IQR** (box height) is similar
  - Real: ~18 mmHg (Q1: 126, Q3: 144)
  - MVN: ~17 mmHg
  - Bootstrap: ~18 mmHg
- [ ] **Whiskers** extend to similar ranges
- [ ] **Outliers** are present in real data, fewer in synthetic

**Interpretation**:
- ✅ **Good match**: Medians within 3%, IQR within 10%
- ⚠️ **Acceptable**: Medians within 5%, IQR within 20%
- ❌ **Poor**: Medians differ > 5%

**Box Plots for DBP and HR**:
- Same validation criteria
- Expected medians:
  - DBP: ~82 mmHg
  - HR: ~72 bpm

---

### Test 3: Quality Metrics Dashboard

**Navigate**: Analytics → Quality Metrics

**What to Look For**:

#### Wasserstein Distances Card

**Definition**: Measures the "cost" of transforming one distribution into another. Lower is better.

**Expected Values**:
```
SystolicBP:    2-5 mmHg    (Excellent < 5, Good < 10, Poor > 10)
DiastolicBP:   1-3 mmHg    (Excellent < 3, Good < 6, Poor > 6)
HeartRate:     2-5 bpm     (Excellent < 5, Good < 10, Poor > 10)
Temperature:   0.1-0.3 °C  (Excellent < 0.5, Good < 1, Poor > 1)
```

**Validation**:
- [ ] All values in "Excellent" or "Good" range
- [ ] Temperature has lowest distance (smallest range)
- [ ] Systolic BP has highest distance (largest range)

**What It Means**:
- **Low values** (green): Distributions are very similar
- **Medium values** (orange): Distributions somewhat similar
- **High values** (red): Distributions differ significantly

#### RMSE (Root Mean Square Error) Card

**Definition**: Average prediction error if using synthetic data mean to predict real data values.

**Expected Values**:
```
SystolicBP:    5-10 mmHg   (Excellent < 10, Good < 15, Poor > 15)
DiastolicBP:   3-8 mmHg    (Excellent < 8, Good < 12, Poor > 12)
HeartRate:     4-10 bpm    (Excellent < 10, Good < 15, Poor > 15)
Temperature:   0.2-0.5 °C  (Excellent < 0.5, Good < 1, Poor > 1)
```

**Validation**:
- [ ] All RMSE values < 1 standard deviation of original data
- [ ] Temperature has lowest RMSE
- [ ] Values decrease over multiple generation attempts (learning)

#### Correlation Preservation Score

**Definition**: How well the synthetic data preserves correlations between variables (e.g., SBP vs DBP).

**Expected Value**: 0.85 - 0.98

**Interpretation**:
- ✅ **≥ 0.90**: Excellent - Correlations well preserved
- ⚠️ **0.80-0.90**: Good - Minor correlation differences
- ❌ **< 0.80**: Poor - Correlations not preserved

**Validation**:
- [ ] Score > 0.85
- [ ] Known correlations (SBP-DBP, HR-Temperature) are preserved

#### K-NN Imputation Score

**Definition**: Can synthetic data be used to impute missing values in real data using K-Nearest Neighbors?

**Expected Value**: 0.80 - 0.95

**Interpretation**:
- ✅ **≥ 0.85**: Excellent - Synthetic data captures real data patterns
- ⚠️ **0.70-0.85**: Good - Some pattern loss
- ❌ **< 0.70**: Poor - Patterns not captured

**Validation**:
- [ ] Score > 0.80
- [ ] Hover over (i) icon to see methodology

#### Overall Quality Score

**Displayed as Badge**:
- 🟢 **EXCELLENT** (≥ 0.85): Production ready
- 🟡 **GOOD** (0.70-0.85): Usable with minor caveats
- 🔴 **NEEDS IMPROVEMENT** (< 0.70): Not recommended

**What to Expect**:
- MVN generation: 0.85-0.95 (Excellent)
- Bootstrap generation: 0.88-0.96 (Excellent, often higher than MVN)
- Rules generation: 0.75-0.85 (Good to Excellent)

**Validation**:
- [ ] Badge color matches score range
- [ ] Summary text explains quality level
- [ ] Recommendations provided if score < 0.85

---

### Test 4: Week-12 Statistical Analysis

**Navigate**: Analytics → Statistics

**What to Expect**:

#### Treatment Group Summary Card

```
Active Arm (n=50):
- Mean Systolic BP: 134.2 ± 10.4 mmHg
- SE: 1.47 mmHg
- 95% CI: [131.3, 137.1]

Placebo Arm (n=50):
- Mean Systolic BP: 139.1 ± 9.8 mmHg
- SE: 1.39 mmHg
- 95% CI: [136.3, 141.9]
```

**Validation**:
- [ ] Both groups have equal n (balanced randomization)
- [ ] Mean Active < Mean Placebo (due to target_effect = -5.0)
- [ ] Standard deviations are realistic (8-15 mmHg)
- [ ] Standard errors calculated correctly: SE = SD / √n

#### Treatment Effect Card

```
Difference (Active - Placebo): -4.9 mmHg
SE of Difference: 2.03 mmHg
95% CI: [-8.9, -0.9] mmHg

t-statistic: -2.41
p-value: 0.018
```

**Validation**:
- [ ] Difference is close to target_effect (-5.0)
- [ ] p-value < 0.05 (statistically significant)
- [ ] 95% CI does not include 0 (significant effect)
- [ ] t-statistic magnitude > 2 (significant)

**Interpretation**:
- ✅ **p < 0.05**: Statistically significant effect
- ✅ **|Difference| ≥ 3 mmHg**: Clinically meaningful
- ✅ **CI excludes 0**: Robust evidence of effect

#### Interpretation Card

**What to Expect**:
```
✅ Statistically Significant: Yes (p=0.018)
✅ Effect Size: Moderate (-4.9 mmHg, ~3.5% reduction)
✅ Clinical Relevance: Clinically meaningful reduction
✅ Conclusion: The active treatment demonstrates a statistically
   significant and clinically meaningful reduction in systolic BP
   compared to placebo.
```

**Validation**:
- [ ] All three criteria (significant, effect size, clinical relevance) are "Yes"
- [ ] Conclusion is clear and actionable
- [ ] Effect size percentage calculated correctly

---

## End-to-End Workflows

### Workflow 1: Complete Data Generation → Analytics Pipeline

**Objective**: Generate synthetic data, validate quality, and analyze efficacy.

**Steps**:
1. **Generate MVN Data**
   - Data Generation → MVN tab
   - n_per_arm: 100
   - target_effect: -5.0
   - Generate → Should produce 400 records in ~0.5 seconds

2. **Download and Inspect**
   - Click "Download CSV"
   - Open in Excel/Numbers
   - Verify 400 rows, 7 columns
   - Check for missing values (should be none)

3. **View Quality Assessment**
   - Click "View Analytics" button
   - Navigate to Quality Metrics tab
   - **Expected**: Overall Quality Score ≥ 0.85 (Excellent)
   - **Check**: All Wasserstein distances in "Excellent" range

4. **Analyze Efficacy**
   - Navigate to Statistics tab
   - **Expected**: p-value < 0.05
   - **Expected**: Difference ≈ -5.0 mmHg
   - **Expected**: Interpretation = "Clinically meaningful"

5. **Compare Distributions**
   - Navigate to Visualizations tab
   - Select "Real vs MVN"
   - **Check**: All 4 vital sign histograms align well
   - **Check**: Summary table shows Diff % < 5% for all means

**Success Criteria**:
- [ ] All 400 records generated successfully
- [ ] Quality score ≥ 0.85
- [ ] p-value < 0.05
- [ ] Treatment effect within 10% of target (-4.5 to -5.5 mmHg)
- [ ] All distribution overlays match well

---

### Workflow 2: Bootstrap vs MVN Comparison

**Objective**: Compare two synthetic data generation methods.

**Steps**:
1. **Generate MVN Data** (n_per_arm=50, seed=123)
2. **Generate Bootstrap Data** (n_per_arm=50, same parameters)
3. **Navigate to Three-Way Comparison**
4. **Compare Box Plots**:
   - Bootstrap median should match Real median more closely than MVN
   - Bootstrap IQR should match Real IQR more closely
5. **Compare Quality Scores**:
   - Bootstrap score often 2-5% higher than MVN
   - Bootstrap preserves extremes better (min/max closer to real data)

**What to Expect**:
```
Quality Scores:
- MVN: 0.86 (Excellent)
- Bootstrap: 0.91 (Excellent) ← Higher

Wasserstein Distances:
- MVN SystolicBP: 3.2 mmHg
- Bootstrap SystolicBP: 2.1 mmHg ← Lower is better

Correlation Preservation:
- MVN: 0.89
- Bootstrap: 0.94 ← Better
```

**Interpretation**:
- **Bootstrap** better preserves:
  - Original data distribution shape
  - Correlations between variables
  - Extreme values (min/max)
- **MVN** is:
  - Faster (29K records/sec vs 140K records/sec)
  - More parametric (smoother distributions)
  - Better for large-scale generation

---

## Performance Testing

### Backend Performance Benchmarks

**Expected Generation Speeds** (n_per_arm=1000):

```bash
# MVN: ~29,000 records/second
time curl -s -X POST http://localhost:8002/generate/mvn \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 1000}' > /dev/null

# Expected: ~0.14 seconds for 4000 records

# Bootstrap: ~140,000 records/second
time curl -s -X POST http://localhost:8002/generate/bootstrap \
  -H "Content-Type: application/json" \
  -d "{\"training_data\": $(cat /tmp/real_data.json), \"n_per_arm\": 1000}" > /dev/null

# Expected: ~0.03 seconds for 4000 records

# Rules: ~80,000 records/second
time curl -s -X POST http://localhost:8002/generate/rules \
  -H "Content-Type: application/json" \
  -d '{"n_per_arm": 1000}' > /dev/null

# Expected: ~0.05 seconds for 4000 records
```

**Validation**:
- [ ] MVN completes in < 1 second for 10K records
- [ ] Bootstrap completes in < 0.5 seconds for 10K records
- [ ] Rules completes in < 0.5 seconds for 10K records

---

### Frontend Performance

**Expected Load Times**:
- Initial page load: < 2 seconds
- Data generation (n=50): < 1 second (including API round-trip)
- Analytics dashboard load: < 1 second
- Chart rendering (9 panels): < 0.5 seconds
- CSV download: Instant (client-side)

**Test with Chrome DevTools**:
1. Open DevTools (F12)
2. Go to Performance tab
3. Record while generating data and viewing analytics
4. Analyze:
   - **Total Time**: Should be < 2 seconds from click to render
   - **API Call Time**: Should be < 500ms
   - **Rendering Time**: Should be < 300ms

**Validation**:
- [ ] No memory leaks (check Memory tab)
- [ ] No console errors
- [ ] Lighthouse score > 90 for Performance

---

## Troubleshooting

### Issue 1: "Failed to fetch" errors

**Symptoms**: Red toast notification "Error: Failed to fetch" when generating data.

**Diagnosis**:
```bash
# Check if backend service is running
curl http://localhost:8002/health
```

**Solutions**:
1. Start the backend service:
   ```bash
   cd microservices/data-generation-service/src
   python3 -m uvicorn main:app --reload --port 8002
   ```

2. Check for port conflicts:
   ```bash
   lsof -i:8002
   ```

3. Verify CORS settings in backend (should allow `localhost:3000`)

---

### Issue 2: Quality Score is Low (< 0.70)

**Symptoms**: Overall Quality Score shows "NEEDS IMPROVEMENT".

**Diagnosis**:
- Check Wasserstein distances - which vitals have high distances?
- Check RMSE - are errors too large?
- Check correlation preservation - are correlations broken?

**Solutions**:
1. **High Wasserstein Distance for SystolicBP**:
   - Increase `n_per_arm` (more data = better distribution fit)
   - Try Bootstrap method instead of MVN

2. **Low Correlation Preservation**:
   - MVN method better preserves correlations than Rules
   - Bootstrap best preserves correlations (uses real data)

3. **High RMSE**:
   - Check if target_effect is too large (> 15 mmHg)
   - Verify seed is set for reproducibility

---

### Issue 3: Analytics Dashboard Shows Empty Charts

**Symptoms**: Charts render but show no data or "No data available".

**Diagnosis**:
```javascript
// Open browser console and check
console.log(vitalsData);  // Should show array of records
```

**Solutions**:
1. **No data in state**:
   - Re-generate data from Data Generation page
   - Ensure data is successfully fetched before navigating to Analytics

2. **Wrong data format**:
   - Ensure data has fields: SubjectID, VisitName, TreatmentArm, SystolicBP, DiastolicBP, HeartRate, Temperature
   - Check browser console for parsing errors

3. **Filter issues**:
   - Ensure Week 12 visit exists in data
   - Check that both Active and Placebo arms have data

---

### Issue 4: p-value is Not Significant (> 0.05)

**Symptoms**: Week-12 analysis shows p > 0.05, interpretation says "Not significant".

**Diagnosis**:
- This is **expected** for small sample sizes or small target effects
- Not a bug, but a statistical reality

**Solutions**:
1. **Increase sample size**:
   - Try `n_per_arm: 100` or `n_per_arm: 200`
   - Larger n = more statistical power

2. **Increase target effect**:
   - Try `target_effect: -10.0` (larger effect easier to detect)

3. **Change seed**:
   - Random variation can affect p-value
   - Try multiple seeds (123, 456, 789) and average results

**Expected p-values** (target_effect = -5.0):
- n_per_arm = 10: p ≈ 0.10-0.30 (often not significant)
- n_per_arm = 50: p ≈ 0.01-0.05 (usually significant)
- n_per_arm = 100: p < 0.01 (almost always significant)

---

## Expected Results Reference

### Typical MVN Generation Results (n_per_arm=50)

**Data Characteristics**:
```
Total Records: 400 (50 × 2 × 4)
Subjects: 100 (50 Active, 50 Placebo)
Visits: 4 (Screening, Day 1, Week 4, Week 12)

Systolic BP:
- Range: 95-200 mmHg
- Mean Active: 134±10 mmHg
- Mean Placebo: 139±10 mmHg
- Difference: -5±2 mmHg

Diastolic BP:
- Range: 55-130 mmHg
- Mean Active: 81±9 mmHg
- Mean Placebo: 82±9 mmHg

Heart Rate:
- Range: 50-120 bpm
- Mean: 72±11 bpm

Temperature:
- Range: 35.0-40.0 °C
- Mean: 36.6±0.4 °C
```

**Quality Metrics**:
```
Overall Quality Score: 0.87 (EXCELLENT)

Wasserstein Distances:
- SystolicBP: 2.3 mmHg ✅
- DiastolicBP: 1.9 mmHg ✅
- HeartRate: 3.1 bpm ✅
- Temperature: 0.15 °C ✅

RMSE:
- SystolicBP: 8.5 mmHg ✅
- DiastolicBP: 5.2 mmHg ✅
- HeartRate: 6.8 bpm ✅
- Temperature: 0.32 °C ✅

Correlation Preservation: 0.94 ✅
K-NN Imputation Score: 0.88 ✅
```

**Statistical Analysis**:
```
Treatment Effect:
- Difference: -4.9 mmHg
- 95% CI: [-8.9, -0.9]
- p-value: 0.018 ✅ (significant)
- Effect Size: Moderate
- Clinical Relevance: Meaningful reduction ✅
```

---

### Typical Bootstrap Generation Results (n_per_arm=50)

**Data Characteristics**:
```
Total Records: Variable (450-600, depends on resampling)
Subjects: 100
Visits: 4

Systolic BP:
- Closely matches real data distribution
- Preserves outliers and extremes
- Mean difference: < 1% from real data
```

**Quality Metrics** (Often Higher than MVN):
```
Overall Quality Score: 0.91 (EXCELLENT)

Wasserstein Distances: (Lower = Better)
- SystolicBP: 1.8 mmHg ✅
- DiastolicBP: 1.5 mmHg ✅
- HeartRate: 2.4 bpm ✅
- Temperature: 0.12 °C ✅

Correlation Preservation: 0.96 ✅ (Better than MVN)
K-NN Imputation Score: 0.92 ✅
```

---

## Summary Checklist

**Before Deployment**:
- [ ] All backend services running (ports 8002-8006)
- [ ] Frontend running on port 3000
- [ ] No console errors in browser
- [ ] All health endpoints return 200 OK

**Core Functionality**:
- [ ] User can register and login
- [ ] MVN generation works (< 1 second for n=50)
- [ ] Bootstrap generation works (fetches pilot data)
- [ ] Rules generation works
- [ ] CSV download works
- [ ] Analytics dashboard loads

**Analytics Validation**:
- [ ] All 9 panels render in Real vs MVN
- [ ] Overlaid histograms align properly
- [ ] Box plots show correct quartiles
- [ ] Summary table shows realistic statistics
- [ ] Quality score ≥ 0.85 for MVN
- [ ] Quality score ≥ 0.88 for Bootstrap
- [ ] Week-12 analysis shows p < 0.05 (for n≥50)
- [ ] Treatment effect within 10% of target

**Performance**:
- [ ] MVN generation: < 1 second for 400 records
- [ ] Analytics load: < 2 seconds total
- [ ] No memory leaks in browser
- [ ] Charts render in < 500ms

---

## Next Steps

1. **Run through all workflows** in this guide
2. **Document any deviations** from expected results
3. **Test with different parameters**:
   - Try n_per_arm: 10, 50, 100, 200
   - Try target_effect: -3, -5, -10
   - Try different seeds: 123, 456, 789
4. **Export and share results**:
   - Download CSVs for further analysis
   - Export charts as PNG for reports
5. **Scale testing**:
   - Test with n_per_arm=1000 (4000 records)
   - Verify performance remains good

---

## Additional Resources

- **Backend API Reference**: See `CLAUDE.md`
- **Analytics Component Docs**: See `frontend/ANALYTICS_DASHBOARD_README.md`
- **Frontend README**: See `frontend/README.md`
- **Swagger API Docs**:
  - Data Generation: http://localhost:8002/docs
  - Analytics: http://localhost:8003/docs

---

**Happy Testing! 🚀**

**Questions or Issues?** Check the Troubleshooting section or open an issue in the project repository.
