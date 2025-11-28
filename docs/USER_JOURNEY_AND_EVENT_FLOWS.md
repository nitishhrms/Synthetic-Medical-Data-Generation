# 👥 USER JOURNEY & EVENT FLOWS
## Complete End-User Guide for Clinical Trial Platform

**Document Version**: 1.0
**Analysis Date**: 2025-11-17
**Status**: Comprehensive User Journey Mapping

---

## 📊 EXECUTIVE SUMMARY

### Your Platform's Users (Actually 6+ Roles, Not Just 2!)

Based on your platform's capabilities, here are the **real user personas**:

| Role | Primary Goal | Platform Features Used | Frequency |
|------|--------------|------------------------|-----------|
| **1. Clinical Data Manager** | Oversee trial data quality | EDC, Quality, RBQM | Daily |
| **2. Site Coordinator (CRC)** | Enter patient data | EDC, Visit Management | Daily |
| **3. Biostatistician** | Analyze trial results | Analytics, Daft, Synthetic Data | Weekly |
| **4. Regulatory Affairs** | Ensure compliance | LinkUp, Evidence Packs, SDTM | Weekly |
| **5. Study Manager** | Monitor trial progress | RBQM, Site Risk Dashboard | Daily |
| **6. Protocol Developer** | Design trial protocols | Protocol Intelligence (NEW!) | Pre-trial |

**You mentioned 2 roles:**
- **Data Analyst** = Biostatistician + Clinical Data Manager
- **Clinical Technician** = Site Coordinator (CRC - Clinical Research Coordinator)

**Reality**: You actually have a **multi-persona platform** serving the entire trial team!

---

## 🎯 CORE USER PERSONAS (DETAILED)

### Persona 1: **Site Coordinator (CRC)** - The "Clinical Technician"

**Who They Are**:
- Works at hospital/clinic site
- Responsible for patient visits
- Enters data into EDC system
- First point of contact with patients
- Typically: Nurses, medical assistants, clinical research coordinators

**Pain Points**:
- Manual data entry is time-consuming
- Validation errors delay patient visits
- Need to look up normal ranges constantly
- Afraid of making mistakes (audit findings)
- Paper forms are error-prone

**How Your Platform Helps**:
- ✅ EDC with real-time validation
- ✅ Edit checks show errors immediately
- ✅ YAML rules pre-configured (no memorization)
- ✅ Mobile-friendly data entry (future)
- ✅ Auto-repair functionality (fixes common mistakes)

**Daily Workflow** (See Section 3 for detailed flow)

---

### Persona 2: **Clinical Data Manager** - The "Data Analyst" (Part 1)

**Who They Are**:
- Oversees data quality for entire trial
- Reviews queries and discrepancies
- Ensures database lock readiness
- Works for sponsor or CRO
- Manages site coordinators

**Pain Points**:
- Sites enter bad data constantly
- Chasing sites for query resolution
- Manual quality checks take hours
- Regulatory audits are stressful
- No visibility into real-time quality

**How Your Platform Helps**:
- ✅ Automated edit checks (YAML engine)
- ✅ Real-time quality metrics dashboard
- ✅ RBQM site risk monitoring
- ✅ Query tracking and resolution
- ✅ Audit trail (21 CFR Part 11 compliant)

**Daily Workflow** (See Section 4 for detailed flow)

---

### Persona 3: **Biostatistician** - The "Data Analyst" (Part 2)

**Who They Are**:
- Designs statistical analysis plan
- Analyzes trial results
- Generates CSR (Clinical Study Report)
- Creates SDTM datasets for FDA
- Works for sponsor or CRO

**Pain Points**:
- Need to validate synthetic data quality
- Statistical programming is slow (SAS)
- Generating SDTM datasets is tedious
- CSR takes weeks to write
- Need to cite methodologies (FDA requirement)

**How Your Platform Helps**:
- ✅ Synthetic data generation (4 methods)
- ✅ Daft analytics (10-100x faster than SAS/Spark)
- ✅ Automated CSR generation
- ✅ One-click SDTM export
- ✅ LinkUp evidence packs (auto-citations)

**Weekly Workflow** (See Section 5 for detailed flow)

---

### Persona 4: **Study Manager** - The "Trial Overseer"

**Who They Are**:
- Manages entire clinical trial
- Monitors site performance
- Reports to sponsor/executive team
- Identifies risks early
- Coordinates with sites, vendors, sponsors

**Pain Points**:
- No real-time trial visibility
- Sites underperform silently
- Quality issues discovered too late
- Manual reporting to stakeholders
- Can't predict which sites need help

**How Your Platform Helps**:
- ✅ RBQM dashboard (ICH E6(R2) compliant)
- ✅ Site risk heatmaps (real-time)
- ✅ Automated KRI calculations
- ✅ Portfolio dashboard (multi-study)
- ✅ Alerts for threshold breaches

**Daily Workflow** (See Section 6 for detailed flow)

---

### Persona 5: **Regulatory Affairs** - The "Compliance Gatekeeper"

**Who They Are**:
- Ensures FDA/EMA compliance
- Prepares regulatory submissions
- Manages document control
- Responds to audit findings
- Keeps up with guidance updates

**Pain Points**:
- Regulatory guidance changes constantly
- Citations required for every methodology
- Submission packages take months
- Audit findings are career-threatening
- Manual compliance tracking

**How Your Platform Helps**:
- ✅ LinkUp compliance watcher (auto-monitors FDA, ICH, CDISC)
- ✅ Evidence pack generation (auto-citations)
- ✅ SDTM export (FDA-ready)
- ✅ Audit trail (immutable logs)
- ✅ 21 CFR Part 11 / HIPAA compliance

**Weekly Workflow** (See Section 7 for detailed flow)

---

### Persona 6: **Protocol Developer** - The "Trial Designer" (NEW!)

**Who They Are**:
- Designs clinical trial protocols
- Medical directors, clinical scientists
- Works pre-trial (before patient enrollment)
- Writes inclusion/exclusion criteria
- Defines endpoints and visit schedules

**Pain Points**:
- Protocol amendments are expensive ($500K+)
- Don't know if enrollment targets are realistic
- Need to benchmark against similar trials
- FDA guidance is hard to interpret
- Manual protocol writing takes weeks

**How Your Platform COULD Help** (with protocol intelligence):
- 🚧 Upload protocol PDF → AI extracts key elements
- 🚧 Validate against FDA guidance (LinkUp)
- 🚧 Benchmark against similar trials (ClinicalTrials.gov)
- 🚧 Simulate enrollment feasibility (synthetic data)
- 🚧 Auto-generate edit checks from protocol

**Pre-Trial Workflow** (See Section 8 for detailed flow - NEW!)

---

## 🔄 COMPLETE EVENT FLOWS (REALISTIC SCENARIOS)

### EVENT FLOW 1: **Site Coordinator (CRC) - Daily Data Entry**

#### Scenario: "Sarah enters vitals for a Week 4 patient visit"

**Sarah's Role**: CRC at Memorial Hospital (Site 001)
**Patient**: Subject RA001-023 (Active treatment arm)
**Visit**: Week 4 (scheduled today)

---

**8:00 AM - Patient Arrives**
```
Sarah logs into platform
  ↓
Dashboard shows:
  - Today's scheduled visits (5 patients)
  - Outstanding queries (2 from yesterday)
  - Recent alerts (1 abnormal BP from last visit)
```

**8:15 AM - Prepare for Visit**
```
Click on "RA001-023 - Week 4 Visit"
  ↓
Platform shows:
  - Patient history (last visit: Screening)
  - Required procedures today:
    ✅ Vitals
    ✅ Adverse event check
    ✅ Concomitant medication review
  - Previous values (for reference):
    - Screening SBP: 145 mmHg
    - Screening DBP: 88 mmHg
```

**8:30 AM - Take Vital Signs**
```
Patient measured:
  - SBP: 138 mmHg ✅ (↓ from 145 - good trend!)
  - DBP: 84 mmHg ✅
  - HR: 72 bpm ✅
  - Temp: 36.7°C ✅
```

**8:35 AM - Enter Data into EDC**
```
Sarah opens "Vitals" eCRF form
  ↓
Enters measurements:
  - Systolic BP: 138
  - Diastolic BP: 84
  - Heart Rate: 72
  - Temperature: 36.7

Platform validates in REAL-TIME:
  ✅ Range checks pass (all within normal limits)
  ✅ BP differential check pass (SBP > DBP + 5)
  ✅ No duplicates detected
  ✅ All required fields populated

[SAVE BUTTON - Green checkmark]
```

**What if Sarah makes a mistake?**
```
Sarah accidentally types:
  - Systolic BP: 84  ❌ (typo - swapped SBP and DBP)
  - Diastolic BP: 138 ❌

Platform IMMEDIATELY shows edit check error:
  🔴 EDIT CHECK FAILED: "SBP must be greater than DBP by at least 5 mmHg"

  Suggested fix: "Did you mean SBP: 138, DBP: 84?"

  [AUTO-REPAIR] button

Sarah clicks AUTO-REPAIR → values corrected ✅
Sarah clicks SAVE → data accepted ✅
```

**8:40 AM - Review Adverse Events**
```
Platform prompts: "Any new adverse events since last visit?"

Sarah asks patient → Patient reports mild headache (Day 10)

Sarah enters AE:
  - Term: "Headache"
  - Severity: Mild
  - Onset Date: Day 10
  - Outcome: Ongoing
  - Related to study drug: Possibly

Platform auto-flags:
  ⚠️ "Common AE for this indication - no action needed"
  ✅ "Not serious - continue monitoring"
```

**8:45 AM - Visit Complete**
```
Platform shows:
  ✅ All required procedures completed
  ✅ No outstanding queries
  ✅ Visit status: COMPLETE

Sarah clicks "Mark Visit as Complete"
  ↓
Data auto-saved to database
Audit trail created:
  - User: sarah.jones@memorialhospital.com
  - Action: Visit completed
  - Timestamp: 2025-11-17 08:45:23 UTC
  - IP: 192.168.1.45
```

**9:00 AM - Check Query Dashboard**
```
Sarah sees 2 outstanding queries from yesterday:

Query #1:
  Subject: RA001-018
  Field: Systolic BP (Week 2)
  Issue: "Value seems high (182 mmHg). Please confirm or correct."

Sarah reviews source document → confirms value is correct
Sarah clicks "Respond to Query": "Confirmed. Patient had white coat syndrome."
Sarah attaches photo of source document
Sarah clicks "Mark as Answered"
  ↓
Query auto-routed to Clinical Data Manager for closure
```

**End Result**:
- ✅ 1 patient visit completed (5 minutes)
- ✅ Data validated in real-time (0 errors)
- ✅ 1 AE reported
- ✅ 1 query resolved
- ✅ Total time: 30 minutes (vs. 60 minutes with paper forms)

**Value to Sarah**:
- 50% faster data entry
- No validation errors (edit checks prevent mistakes)
- Real-time feedback (not waiting days for query resolution)
- Mobile-friendly (future: iPad at bedside)
- Less stress (auto-repair fixes common mistakes)

---

### EVENT FLOW 2: **Clinical Data Manager - Daily Quality Review**

#### Scenario: "Michael reviews data quality across all sites"

**Michael's Role**: Clinical Data Manager at PharmaCo Inc
**Trial**: Hypertension Phase 3 Trial (STU001)
**Sites**: 10 sites, 100 subjects enrolled

---

**8:30 AM - Login and Dashboard Review**
```
Michael logs into platform
  ↓
Dashboard shows:

📊 Trial Overview:
  - Subjects enrolled: 100 / 200 (50%)
  - Visits completed: 387 / 800 (48%)
  - Queries outstanding: 23 (↓ from 31 yesterday - good!)
  - Data entry lag: 2.3 days average (⚠️ above target of 2.0)

🔴 ALERTS (3):
  - Site 003: Query rate exceeded threshold (8.2 per 100 CRFs - limit: 6.0)
  - Site 007: 1 serious AE reported yesterday (requires review)
  - Site 009: Data entry lag = 5.1 days (⚠️ needs follow-up)
```

**8:35 AM - Review Site 003 (High Query Rate)**
```
Michael clicks "Site 003 Alert"
  ↓
Platform shows Site 003 details:

📈 Site 003 (Boston General Hospital):
  - Query rate: 8.2 per 100 CRFs (🔴 above threshold)
  - Most common query types:
    1. BP values out of range (40%)
    2. Missing concomitant medications (30%)
    3. AE dates inconsistent (20%)

  - Top 3 fields with errors:
    1. Systolic BP (12 queries)
    2. Concomitant meds (8 queries)
    3. AE onset date (5 queries)

Michael's action:
  - Email Site 003 coordinator: "Please review BP measurement technique"
  - Schedule retraining call for Friday
  - Add note to site file: "Monitoring closely for next 2 weeks"
```

**8:45 AM - Review Serious AE (Site 007)**
```
Michael clicks "Site 007 - Serious AE"
  ↓
Platform shows SAE details:

Subject: RA001-067
Event: Hospitalization
Term: Chest pain
Severity: Moderate
Related to study drug: Unlikely (investigator assessment)
Outcome: Resolved
Hospitalized: Yes (2 days - discharged yesterday)

Platform auto-generated SAE report:
  ✅ Reported within 24 hours (protocol compliant)
  ✅ All required fields populated
  ✅ Source documents attached
  ✅ Investigator signature present

Michael's action:
  - Review narrative: "Patient had pre-existing coronary artery disease..."
  - Confirm relatedness: "Unlikely related" ✅
  - Forward to Medical Monitor for final adjudication
  - Mark as "Under Review"
  - Set reminder: "Follow-up in 3 days"
```

**9:00 AM - Run Quality Metrics Report**
```
Michael clicks "Quality Dashboard"
  ↓
Platform shows (Daft-powered analytics - generated in 2 seconds!):

📊 Data Quality Metrics (All Sites):

Completeness:
  - Overall: 97.3% ✅
  - By site:
    - Site 001: 99.1% ✅ (best)
    - Site 009: 93.2% ⚠️ (needs improvement)

Edit Check Failures:
  - Total: 487 checks run
  - Failures: 23 (4.7% failure rate) ✅
  - Most common failures:
    1. BP differential (8 failures)
    2. Duplicate visit dates (5 failures)
    3. Missing temperature (4 failures)

Timeliness:
  - Data entry lag: 2.3 days average
  - Sites above target (> 3 days):
    - Site 009: 5.1 days 🔴
    - Site 006: 3.8 days ⚠️

Michael's action:
  - Download report as PDF (for weekly sponsor call)
  - Email Site 009: "Please improve data entry timeliness"
  - Add to RBQM report: "Site 009 under monitoring"
```

**9:15 AM - Review and Close Queries**
```
Michael clicks "Query Management"
  ↓
Platform shows 23 outstanding queries:

Queries by status:
  - Open (awaiting site response): 12
  - Answered (awaiting closure): 8
  - Escalated (requiring sponsor review): 3

Michael reviews answered queries:

Query #14:
  Subject: RA001-032
  Field: Heart Rate (Week 4)
  Original value: 120 bpm
  Issue: "Value seems high. Confirm or correct."
  Site response: "Confirmed. Patient had just walked up stairs."

Michael's action:
  - Review source document (attached photo) ✅
  - Accept response: "Confirmed" ✅
  - Click "Close Query"
  ↓
  Platform auto-marks query as CLOSED
  Audit trail created

Michael closes 8 queries in 10 minutes (vs. 30 minutes manually)
```

**9:30 AM - Generate RBQM Report for Sponsor**
```
Michael clicks "RBQM Summary"
  ↓
Platform auto-generates (using analytics-service/src/rbqm.py):

# RBQM Summary - Week 12
## Key Risk Indicators

| Site | Query Rate | Missing Data | Screen Fail | Risk Level |
|------|------------|--------------|-------------|------------|
| Site 001 | 3.2 | 0.9% | 28% | 🟢 Low |
| Site 002 | 4.1 | 1.2% | 32% | 🟢 Low |
| Site 003 | 8.2 | 2.3% | 45% | 🔴 High |
| Site 007 | 5.1 | 1.8% | 35% | 🟡 Medium |
| Site 009 | 6.8 | 4.2% | 52% | 🔴 High |

## Recommended Actions:
- Site 003: Retraining on BP measurement
- Site 009: Improve data entry timeliness + enrollment strategy

Michael's action:
  - Click "Export to PDF"
  - Email to sponsor with note: "2 sites require intervention"
  - Schedule monitoring visit to Site 003 (on-site audit)
```

**End Result**:
- ✅ 3 alerts triaged
- ✅ 1 SAE reviewed and escalated
- ✅ 8 queries closed
- ✅ RBQM report generated (auto!)
- ✅ Total time: 60 minutes (vs. 3 hours manually)

**Value to Michael**:
- 70% time savings on quality review
- Real-time alerts (not discovering issues weeks later)
- Automated reports (RBQM, quality metrics)
- Data-driven site monitoring decisions
- Audit-ready documentation (21 CFR Part 11)

---

### EVENT FLOW 3: **Biostatistician - Weekly Analysis**

#### Scenario: "Dr. Chen analyzes Week 12 efficacy data"

**Dr. Chen's Role**: Senior Biostatistician at PharmaCo Inc
**Trial**: Hypertension Phase 3 Trial (STU001)
**Analysis**: Week 12 primary endpoint (change in SBP from baseline)

---

**Monday 9:00 AM - Extract Data for Analysis**
```
Dr. Chen logs into platform
  ↓
Clicks "Analytics" → "Data Export"
  ↓
Platform shows:

Export Options:
  - Format: CSV ✓ / Parquet / SDTM / JSON
  - Data cut-off: 2025-11-17
  - Subjects: All (100 enrolled)
  - Visits: All visits ✓ / Specific visits
  - Domains: Vitals ✓ / AE / Meds / Labs

Dr. Chen selects:
  - Format: Parquet (10x smaller than CSV!)
  - Visits: Screening, Week 12
  - Domains: Vitals only

Click "Export" → Download starts
  ↓
File downloaded: vitals_2025-11-17.parquet (2.3 MB vs. 23 MB CSV)
```

**9:10 AM - Load Data into Daft**
```
Dr. Chen uses Daft Analytics Service (Port 8007)

Option 1: Via UI (frontend dashboard - if implemented):
  - Upload Parquet file
  - Click "Load into Daft"
  - See preview (first 100 rows)

Option 2: Via API (Dr. Chen prefers this - she's technical):

import httpx

# Load data
response = httpx.post(
    "http://localhost:8007/daft/load",
    json={"file_path": "vitals_2025-11-17.parquet"}
)

dataframe_id = response.json()["dataframe_id"]
# Returns in 12ms (vs. 2 seconds with Pandas!)
```

**9:15 AM - Calculate Treatment Effect**
```
Dr. Chen clicks "Calculate Treatment Effect" (or via API)

POST /daft/treatment-effect
{
  "dataframe_id": "df_12345",
  "treatment_column": "TreatmentArm",
  "outcome_column": "SystolicBP",
  "visit_column": "VisitName",
  "baseline_visit": "Screening",
  "followup_visit": "Week 12"
}

Platform returns (in 28ms! Daft advantage):

{
  "treatment_groups": {
    "Active": {
      "n": 50,
      "baseline_mean": 145.2,
      "followup_mean": 135.8,
      "change_from_baseline": -9.4,
      "std": 10.2,
      "se": 1.44
    },
    "Placebo": {
      "n": 50,
      "baseline_mean": 144.8,
      "followup_mean": 140.3,
      "change_from_baseline": -4.5,
      "std": 9.8,
      "se": 1.39
    }
  },
  "treatment_effect": {
    "difference": -4.9,  // Active is 4.9 mmHg better than Placebo!
    "se_difference": 2.01,
    "t_statistic": -2.44,
    "p_value": 0.016,  // 🎉 SIGNIFICANT! (p < 0.05)
    "ci_95_lower": -8.8,
    "ci_95_upper": -1.0
  },
  "interpretation": {
    "significant": true,
    "effect_size": "moderate",
    "clinical_relevance": "Clinically meaningful reduction in systolic BP"
  }
}
```

**9:20 AM - Dr. Chen Reviews Results**
```
✅ Primary endpoint MET!
  - Active arm: -9.4 mmHg reduction from baseline
  - Placebo arm: -4.5 mmHg reduction
  - Treatment effect: -4.9 mmHg (p = 0.016)
  - 95% CI: [-8.8, -1.0] (excludes zero - good!)

Dr. Chen's reaction:
  "Excellent! This is statistically significant AND clinically meaningful.
   The -4.9 mmHg reduction exceeds our target of -5 mmHg (close enough!)."
```

**9:30 AM - Generate Visualizations**
```
Dr. Chen uses Daft to create plots (via API or frontend):

POST /daft/visualize/treatment-effect
{
  "dataframe_id": "df_12345",
  "plot_type": "box_plot"
}

Platform generates:
  1. Box plot: Baseline vs. Week 12 (by treatment arm)
  2. Forest plot: Treatment effect with 95% CI
  3. Histogram: Distribution of SBP changes

Dr. Chen downloads plots for slide deck ✅
```

**9:45 AM - Validate with Synthetic Data**
```
Dr. Chen wants to ensure results aren't due to data errors.

She generates synthetic data to compare:

POST /generate/mvn
{
  "n_per_arm": 50,
  "target_effect": -5.0,
  "seed": 12345
}

Platform returns 400 synthetic records in 28ms

Dr. Chen runs same analysis on synthetic data:
  - Treatment effect (synthetic): -5.1 mmHg
  - Treatment effect (real): -4.9 mmHg
  - ✅ Results are consistent! Data quality looks good.

POST /quality/comprehensive
{
  "original_data": [real vitals],
  "synthetic_data": [synthetic vitals]
}

Platform returns:
  - Quality score: 0.89 ✅ (Excellent)
  - Wasserstein distance: 2.1 (low - distributions match)
  - Correlation preservation: 0.94 (high - relationships preserved)

Dr. Chen's conclusion:
  "Real data quality is excellent. Results are trustworthy."
```

**10:00 AM - Generate CSR Draft**
```
Dr. Chen clicks "Generate CSR" (or via API)

POST /csr/draft
{
  "statistics": {treatment_effect_results},
  "ae_data": [adverse_events],
  "n_rows": 400
}

Platform auto-generates (in 5 seconds!):

# Clinical Study Report - STU001
## Hypertension Phase 3 Trial

### Efficacy Results

**Primary Endpoint**: Change in systolic blood pressure from baseline to Week 12

**Results**:
- Active arm (n=50): -9.4 mmHg (SD: 10.2)
- Placebo arm (n=50): -4.5 mmHg (SD: 9.8)
- Treatment difference: -4.9 mmHg (95% CI: -8.8 to -1.0)
- Statistical significance: p = 0.016 (t = -2.44)

**Interpretation**:
The active treatment demonstrated a statistically significant and clinically
meaningful reduction in systolic blood pressure compared to placebo...

[Full 20-page CSR draft continues...]

Dr. Chen's action:
  - Download CSR draft as Markdown
  - Convert to Word (for medical writer review)
  - Share with team: "First draft ready - please review!"
  - Time saved: 40 hours (vs. manual CSR writing)
```

**10:30 AM - Export to SDTM for FDA Submission**
```
Dr. Chen prepares data for FDA submission

POST /sdtm/export
{
  "vitals_data": [all vitals records]
}

Platform transforms data to CDISC SDTM format:

From:
{
  "SubjectID": "RA001-001",
  "VisitName": "Week 12",
  "SystolicBP": 135
}

To SDTM:
{
  "USUBJID": "RA001-001",
  "VSTESTCD": "SYSBP",
  "VSORRES": "135",
  "VSORRESU": "mmHg",
  "VISITNUM": 4,
  "VISIT": "Week 12"
}

Platform exports:
  - vs.xpt (SAS transport file)
  - define.xml (metadata)
  - Reviewer's guide

Dr. Chen's action:
  - Download SDTM package
  - Validate with Pinnacle 21 (external tool)
  - Upload to FDA ESG (Electronic Submissions Gateway)
  - Time saved: 20 hours (vs. manual SDTM programming)
```

**End Result**:
- ✅ Primary endpoint analyzed (significant result!)
- ✅ Data quality validated (synthetic data comparison)
- ✅ CSR draft generated (auto!)
- ✅ SDTM datasets created (FDA-ready)
- ✅ Total time: 90 minutes (vs. 2 weeks manually!)

**Value to Dr. Chen**:
- 95% time savings on statistical analysis
- Daft = 10-100x faster than SAS/Spark
- Automated CSR generation (weeks → hours)
- One-click SDTM export
- Evidence packs for regulatory submissions (LinkUp citations)

---

### EVENT FLOW 4: **Study Manager - Daily Monitoring**

#### Scenario: "Jessica monitors trial progress across all sites"

**Jessica's Role**: Study Manager at PharmaCo Inc
**Trial**: Hypertension Phase 3 Trial (STU001)
**Sites**: 10 sites, 100 subjects enrolled (target: 200)

---

**7:30 AM - Morning Dashboard Review**
```
Jessica logs into platform (mobile app while commuting)
  ↓
Dashboard shows (mobile-optimized):

📊 Trial Status (STU001):
  - Enrollment: 100 / 200 (50%) - ⚠️ Behind schedule
  - Enrollment rate: 2.1 subjects/week (target: 4.0) - 🔴 ALERT
  - Data completeness: 97.3% ✅
  - Query rate: 5.1 per 100 CRFs ✅ (below threshold)
  - Outstanding SAEs: 1 (under review)

🔴 CRITICAL ALERTS (2):
  - Enrollment lag: 15 weeks behind schedule
  - Site 003: High query rate (8.2) - intervention needed
```

**8:00 AM - Open RBQM Dashboard (Desktop)**
```
Jessica arrives at office, opens full RBQM dashboard

Click "Site Risk Heatmap"
  ↓
Platform shows (Daft-powered - real-time!):

SITE RISK HEATMAP:

|        | Query | Missing | Screen | Enroll | Overall |
|        | Rate  | Data    | Fail   | Rate   | Risk    |
|--------|-------|---------|--------|--------|---------|
| Site001| 🟢 3.2| 🟢 0.9% | 🟢 28% | 🟡 0.8 | 🟢 Low  |
| Site002| 🟢 4.1| 🟢 1.2% | 🟢 32% | 🟢 1.2 | 🟢 Low  |
| Site003| 🔴 8.2| 🟡 2.3% | 🔴 45% | 🔴 0.3 | 🔴 High |
| Site004| 🟢 3.8| 🟢 1.1% | 🟢 30% | 🟢 1.1 | 🟢 Low  |
| Site005| 🟡 5.9| 🟢 1.5% | 🟡 38% | 🟡 0.9 | 🟡 Med  |
| Site006| 🟢 3.9| 🟡 2.1% | 🟢 31% | 🟢 1.0 | 🟢 Low  |
| Site007| 🟡 5.1| 🟢 1.8% | 🟢 35% | 🟢 1.3 | 🟡 Med  |
| Site008| 🟢 4.3| 🟢 1.0% | 🟢 29% | 🟢 1.2 | 🟢 Low  |
| Site009| 🔴 6.8| 🔴 4.2% | 🔴 52% | 🔴 0.4 | 🔴 High |
| Site010| 🟢 4.0| 🟢 1.3% | 🟢 33% | 🟡 0.8 | 🟢 Low  |

Jessica's immediate actions:
  1. Site 003: Schedule monitoring visit (next week)
  2. Site 009: Call PI today (discuss enrollment challenges)
  3. Sites 001, 010: Increase enrollment targets (capable sites)
```

**8:30 AM - Drill Down into Site 009**
```
Jessica clicks "Site 009" in heatmap
  ↓
Platform shows detailed KRI trends:

📈 Site 009 - City Medical Center (Dr. Anderson, PI)

Enrollment Performance:
  - Screened: 25 patients (last 3 months)
  - Screen failures: 13 (52%) - 🔴 Very high!
  - Enrolled: 12 patients
  - Enrollment rate: 0.4 subjects/week - 🔴 Slow

  Top screen failure reasons:
    1. BP not in range (6 failures) - 46%
    2. Concomitant meds prohibited (4 failures) - 31%
    3. Patient declined (3 failures) - 23%

Data Quality:
  - Query rate: 6.8 per 100 CRFs - 🟡 Borderline
  - Missing data: 4.2% - 🔴 High
  - Data entry lag: 5.1 days - 🔴 Slow

Jessica's hypothesis:
  "Site 009 is struggling with I/E criteria interpretation.
   High BP screen failures suggest they're screening wrong patients."

Jessica's action:
  - Call Dr. Anderson: "Let's review inclusion/exclusion criteria"
  - Send recruitment strategies email
  - Consider additional site training
  - Monitor for 2 weeks → If no improvement, reduce enrollment target
```

**9:00 AM - Weekly Sponsor Call Prep**
```
Jessica clicks "Generate Executive Report"
  ↓
Platform auto-generates (Daft analytics):

# STU001 - Weekly Executive Summary
## Week 12 Status Report

### Enrollment Status
- **Current**: 100 / 200 subjects (50%)
- **Timeline**: 15 weeks behind schedule ⚠️
- **Projection**: Study completion delayed by 4 months at current rate

### Site Performance
- **High Performers** (5 sites): On track
- **Medium Performers** (3 sites): Acceptable
- **Low Performers** (2 sites): Require intervention
  - Site 003: Quality issues (high query rate)
  - Site 009: Enrollment issues (high screen fail)

### Recommended Actions
1. Increase enrollment targets at top 5 sites (+50% capacity)
2. Conduct monitoring visit to Site 003 (quality improvement)
3. Retrain Site 009 on I/E criteria (enrollment optimization)
4. Consider adding 2 new sites to recover timeline

Jessica's action:
  - Download report as PowerPoint (auto-generated charts!)
  - Add 2 slides with commentary
  - Email to sponsor 30 minutes before call
  - Time saved: 2 hours (vs. manual report creation)
```

**10:00 AM - Sponsor Call**
```
Jessica presents dashboard (screen share):
  - Shows real-time RBQM heatmap
  - Demonstrates drill-down into Site 009
  - Discusses intervention plan

Sponsor asks: "What's your confidence in hitting timeline?"

Jessica clicks "Enrollment Projection" (Daft analytics):
  ↓
  Platform shows:

  Current rate: 2.1 subjects/week
  Target rate: 4.0 subjects/week

  Scenarios:
    - Current pace: Completion in 48 weeks (🔴 4 months late)
    - With interventions: Completion in 40 weeks (🟡 2 months late)
    - Add 2 new sites: Completion in 36 weeks (✅ On time!)

Sponsor approves:
  - Add 2 new sites (approved!)
  - Jessica to identify candidates this week
```

**End Result**:
- ✅ RBQM dashboard reviewed (real-time insights)
- ✅ 2 high-risk sites identified
- ✅ Intervention plan created
- ✅ Executive report generated (auto!)
- ✅ Sponsor alignment achieved
- ✅ Total time: 90 minutes (vs. 4 hours manually)

**Value to Jessica**:
- Real-time trial visibility (not waiting for monthly reports)
- Data-driven decisions (RBQM heatmaps)
- Proactive risk mitigation (identify issues early)
- Automated reporting (weekly sponsor updates)
- Mobile access (monitor trial anywhere)

---

### EVENT FLOW 5: **Regulatory Affairs - Submission Prep**

#### Scenario: "David prepares evidence pack for FDA submission"

**David's Role**: Regulatory Affairs Associate at PharmaCo Inc
**Trial**: Hypertension Phase 3 Trial (STU001)
**Task**: Prepare data quality evidence pack for IND submission

---

**Monday 9:00 AM - Quality Assessment**
```
David logs into platform
  ↓
Clicks "Quality" → "Comprehensive Assessment"
  ↓
Uploads real trial data + compares to synthetic benchmark

POST /quality/comprehensive
{
  "original_data": [100 subjects, 400 records],
  "synthetic_data": [MVN-generated benchmark]
}

Platform returns (in 3 seconds via Daft):

{
  "wasserstein_distances": {
    "SystolicBP": 2.34,
    "DiastolicBP": 1.87,
    "HeartRate": 3.12
  },
  "correlation_preservation": 0.94,
  "overall_quality_score": 0.87,  // ✅ Excellent!
  "summary": "✅ EXCELLENT - Quality score: 0.87. Data suitable for regulatory submission."
}
```

**9:10 AM - Generate Evidence Pack with Citations**
```
David clicks "Generate Evidence Pack" (LinkUp-powered!)

POST /linkup/evidence/fetch-citations
{
  "metrics": [
    {"name": "Wasserstein distance", "value": 2.34},
    {"name": "RMSE", "value": 8.45},
    {"name": "Correlation preservation", "value": 0.94}
  ],
  "context": "clinical trial data quality validation"
}

Platform searches (LinkUp deep search - costs €0.15 total):
  - fda.gov (FDA guidance)
  - ich.org (ICH guidelines)
  - cdisc.org (CDISC standards)
  - ema.europa.eu (EMA regulations)

Returns in 45 seconds:

{
  "citations": [
    {
      "metric": "Wasserstein distance",
      "sources": [
        {
          "title": "FDA Guidance: Use of Electronic Health Record Data in Clinical Investigations",
          "url": "https://www.fda.gov/regulatory-information/...",
          "excerpt": "Wasserstein distance is an appropriate metric for assessing distributional similarity...",
          "relevance": 0.92,
          "date": "2023-05-15"
        },
        {
          "title": "ICH E9: Statistical Principles for Clinical Trials",
          "url": "https://www.ich.org/page/efficacy-guidelines",
          "excerpt": "Quality metrics should demonstrate preservation of statistical properties...",
          "relevance": 0.88,
          "date": "2023-02-01"
        }
      ]
    },
    {
      "metric": "RMSE",
      "sources": [...]
    }
  ]
}
```

**9:30 AM - Generate PDF Evidence Pack**
```
David clicks "Generate PDF Report"

POST /linkup/evidence/generate-pdf
{
  "quality_assessment_id": "qa_12345",
  "include_visualizations": true,
  "include_citations": true
}

Platform auto-generates (using ReportLab):

📄 Evidence_Pack_STU001_20251117.pdf (24 pages):

  Page 1: Cover Page
    - Study: STU001 - Hypertension Phase 3
    - Date: 2025-11-17
    - Prepared by: David Chen, Regulatory Affairs

  Page 2-3: Table of Contents

  Page 4-5: Executive Summary
    - Overall quality score: 0.87 (Excellent)
    - All metrics meet FDA standards
    - Recommendation: Suitable for regulatory submission

  Page 6-10: Quality Metrics
    - Wasserstein Distance: 2.34
      ✅ Citation [1]: FDA Guidance (2023)
      ✅ Citation [2]: ICH E9 (2023)

    - RMSE: 8.45 mmHg
      ✅ Citation [3]: FDA Technical Conformance Guide

    - Correlation Preservation: 0.94
      ✅ Citation [4]: CDISC Data Quality Guidelines

  Page 11-15: Visualizations
    - PCA scatter plots (real vs. synthetic)
    - Distribution histograms (by variable)
    - QQ plots (normality assessment)

  Page 16-18: Methodology
    - Data collection procedures
    - Validation algorithms
    - Statistical methods

  Page 19-22: References (12 citations)
    [1] FDA (2023). Use of Electronic Health Record Data...
    [2] ICH (2023). E9: Statistical Principles...
    [3] FDA (2022). Technical Conformance Guide...
    ... (all auto-generated by LinkUp!)

  Page 23-24: Appendix
    - Raw data summary tables

David's action:
  - Download PDF ✅
  - Review citations (all look authoritative!) ✅
  - Share with Medical Writer for final review
  - Time saved: 40 hours (vs. manual citation hunting!)
```

**10:00 AM - Monitor Regulatory Updates**
```
David checks "Compliance Watcher" dashboard

LinkUp auto-scanned last night (2 AM UTC CronJob):
  - FDA.gov
  - ICH.org
  - CDISC.org
  - TransCelerate.org
  - EMA.europa.eu

Results:

🔔 NEW REGULATORY UPDATE DETECTED:

Update #1:
  Source: FDA
  Title: "Revised Guidance: Data Integrity and Compliance"
  Date: 2025-11-15
  URL: https://www.fda.gov/regulatory-information/...
  Impact: HIGH ⚠️

  Affected Rules:
    - EDIT_CHECK_VITAL_SIGNS_001
    - RBQM_QUERY_RATE_THRESHOLD

  Summary:
    "New requirements for electronic data validation. Edit check
     severity levels must align with FDA risk-based approach..."

  Recommended Action:
    "Update edit check YAML rules to match new FDA requirements"

GitHub PR Auto-Generated: PR #42
  Title: "[AUTO] Update edit checks per FDA guidance 2025-11-15"
  Files changed: 3
  Status: Ready for review

David's action:
  - Review GitHub PR
  - Approve changes: "LGTM - FDA compliant" ✅
  - Merge to main branch
  - Deploy to production (tonight)
  - Time saved: 20 hours (vs. manual guidance monitoring!)
```

**10:30 AM - Prepare SDTM Datasets**
```
David works with biostatistician to finalize SDTM

Biostatistician already exported:
  - vs.xpt (vitals dataset)
  - define.xml (metadata)

David's checklist:
  ✅ Run Pinnacle 21 validation (external tool)
  ✅ Check CDISC controlled terminology version
  ✅ Verify define.xml completeness
  ✅ Generate reviewer's guide

Platform helps:
  - One-click SDTM export (already done!)
  - Auto-generated define.xml (compliant!)
  - Links to CDISC standards (up-to-date!)

David's final action:
  - Package datasets into submission folder
  - Upload to FDA ESG (Electronic Submissions Gateway)
  - Mark task as complete: "SDTM datasets submitted" ✅
```

**End Result**:
- ✅ Quality assessment completed (3 seconds!)
- ✅ Evidence pack with FDA/ICH citations (auto-generated!)
- ✅ Regulatory update detected and addressed (proactive!)
- ✅ SDTM datasets validated and submitted
- ✅ Total time: 90 minutes (vs. 3 weeks manually!)

**Value to David**:
- LinkUp auto-citations save 40+ hours per submission
- Proactive compliance monitoring (never miss FDA updates)
- Audit-ready documentation (immutable citations)
- Reduced regulatory risk (FDA-backed quality metrics)
- Faster submission timelines (weeks → days)

---

## 🚧 NEW EVENT FLOW: **Protocol Developer (WITH PROTOCOL INTELLIGENCE)**

### Scenario: "Dr. Martinez designs a new diabetes trial protocol"

**Dr. Martinez's Role**: Medical Director at PharmaCo Inc
**Task**: Design Phase 3 trial protocol for novel diabetes drug
**Current Problem**: Manual protocol writing takes 6-8 weeks

---

### **WHERE PROTOCOL INTELLIGENCE FITS IN YOUR PROJECT:**

This is a **NEW capability** inspired by Trialscope-AI. Here's how it would work:

---

**Monday 8:00 AM - Upload Draft Protocol**
```
Dr. Martinez has a 50-page protocol draft (PDF)

She logs into your platform
  ↓
Clicks "Protocol Intelligence" (NEW MODULE!)
  ↓
Uploads protocol PDF: "Protocol_Diabetes_v1.0.pdf"
  ↓
Platform processes (using GPT-4o or Claude):
  - Extracts text from PDF (PyMuPDF)
  - LLM parses key sections
  - LinkUp validates against FDA guidance
```

**8:05 AM - AI Extracts Protocol Elements**
```
Platform shows (in 3-5 minutes):

📋 PROTOCOL ANALYSIS RESULTS:

Endpoints Detected:
  ✅ Primary: HbA1c reduction from baseline to Week 24
  ✅ Secondary: Fasting glucose, body weight, hypoglycemia events

Inclusion Criteria:
  ✅ Age 18-75 years
  ✅ Type 2 Diabetes Mellitus diagnosis
  ✅ HbA1c 7.5-10.5%
  ✅ BMI 25-40 kg/m²

Exclusion Criteria:
  ✅ Type 1 Diabetes
  ✅ Severe renal impairment (eGFR < 30)
  ✅ Recent cardiovascular event (< 6 months)

Visit Schedule:
  ✅ Screening
  ✅ Baseline (Day 1)
  ✅ Week 4, 8, 12, 16, 20, 24
  ✅ Follow-up (Week 28)

Sample Size:
  ✅ 300 subjects (150 per arm)
  ✅ Power: 90%
  ✅ Alpha: 0.05
  ✅ Assumed effect: -0.8% HbA1c reduction
```

**8:10 AM - LinkUp Validates Against FDA Guidance**
```
Platform auto-searches (LinkUp deep search):

Query 1: "HbA1c primary endpoint FDA diabetes trial guidance"
  ↓
Returns:
  ✅ FDA Guidance: Diabetes Mellitus - Developing Drugs (2020)
  ✅ ICH E9: Statistical Principles
  ✅ ADA Standards of Care (2024)

Validation Result:
  ✅ HbA1c is acceptable primary endpoint
  ✅ -0.8% reduction is clinically meaningful
  ✅ 24-week duration meets FDA requirements

Query 2: "hypoglycemia safety assessment diabetes trials FDA"
  ↓
Returns:
  ⚠️ WARNING: FDA requires adjudicated hypoglycemia events

Platform flags:
  🔴 ISSUE: "Protocol does not mention adjudication committee for
              hypoglycemia events. This is required per FDA guidance."

  Suggested Fix: "Add Adjudication Committee section to protocol"

  Citation: FDA Guidance (2020), Section 4.3
```

**8:20 AM - Benchmark Against Similar Trials**
```
Platform searches ClinicalTrials.gov (450K trials):

Semantic match: "Type 2 Diabetes, HbA1c, Phase 3"
  ↓
Returns 127 similar completed trials

Top 5 matches:
  1. NCT03456789 - Similar drug class, same endpoint
     - Enrolled: 320 subjects
     - Duration: 26 weeks
     - Primary endpoint: HbA1c reduction
     - Enrollment rate: 8 subjects/week/site

  2. NCT02987654 - Different class, same population
     - Enrolled: 450 subjects
     - Duration: 52 weeks
     - Screen failure rate: 38%

Platform analyzes and warns:

⚠️ ENROLLMENT FEASIBILITY:
  - Your target: 300 subjects
  - Planned sites: 10
  - Expected enrollment rate: 8 subjects/week/site (based on NCT03456789)
  - Estimated timeline: 9-12 months enrollment

  ✅ FEASIBLE - timeline is realistic

⚠️ SCREEN FAILURE PREDICTION:
  - Based on similar trials: 35-40% screen failure expected
  - To enroll 300, you'll need to screen ~460 patients

  Recommendation: "Budget for 460 screens, not 300"
```

**8:30 AM - Simulate Trial with Synthetic Data**
```
Dr. Martinez wants to test if sample size is adequate.

She clicks "Simulate Trial Outcomes"
  ↓
Platform uses synthetic data generation:

POST /generate/diabetes-patients (NEW ENDPOINT - planned)
{
  "indication": "Type 2 Diabetes",
  "n_per_arm": 150,
  "primary_endpoint": "HbA1c",
  "target_effect": -0.8,
  "baseline_hba1c_mean": 8.5,
  "baseline_hba1c_sd": 1.0
}

Platform generates 300 synthetic patients in 2 seconds
  ↓
Runs 1,000 trial simulations (Daft-powered - fast!)
  ↓
Returns:

📊 TRIAL SIMULATION RESULTS:

Power Analysis:
  - Achieved power: 92% ✅ (target: 90%)
  - Probability of success: 87%
  - Type I error rate: 4.8% ✅ (target: < 5%)

Enrollment Scenarios:
  - Best case (fast enrollment): 8 months
  - Expected case: 11 months
  - Worst case (slow enrollment): 16 months

Sensitivity Analysis:
  - If true effect is -0.6% (weaker than assumed):
    Power drops to 78% ⚠️ (below 80% threshold)

  Recommendation: "Consider increasing sample size to 350 to maintain
                   power even if effect is smaller than expected"
```

**8:45 AM - Auto-Generate Edit Checks**
```
Platform asks: "Would you like to auto-generate edit checks for this protocol?"

Dr. Martinez clicks "Yes"
  ↓
Platform uses LinkUp to create edit check rules:

For each variable in protocol:
  - HbA1c → POST /linkup/edit-checks/generate-rule
  - Fasting Glucose → POST /linkup/edit-checks/generate-rule
  - Body Weight → POST /linkup/edit-checks/generate-rule
  - eGFR → POST /linkup/edit-checks/generate-rule

Returns 25 YAML rules in 30 seconds:

Example rule (auto-generated):
```yaml
rules:
  - id: AUTO_HBA1C_20251117
    name: HbA1c Clinical Range Check
    type: range
    field: hba1c
    min: 4.0
    max: 14.0
    severity: Major
    message: "HbA1c out of clinical range [4.0, 14.0]%"
    evidence:
      - source: "ADA Standards of Care 2024"
        url: "https://diabetesjournals.org/care/..."
        excerpt: "Normal HbA1c: 4-6%. Diabetic range typically 7-14%."
    generated_at: "2025-11-17T08:45:00Z"
    confidence: high
```

Dr. Martinez's action:
  - Review rules (all look reasonable!)
  - Click "Import to EDC" ✅
  - Edit checks now ready for trial execution
  - Time saved: 10 hours (vs. manual rule creation!)
```

**9:00 AM - Protocol Optimization Suggestions**
```
Platform provides AI-powered recommendations:

💡 OPTIMIZATION SUGGESTIONS:

1. Visit Schedule:
   Current: 8 visits (Screening → Week 28)
   Suggestion: Add Week 2 visit
   Rationale: "73% of similar diabetes trials include early safety
               assessment at Week 2 per FDA guidance"
   Impact: "Detect safety signals earlier, improve retention"

2. Inclusion Criteria:
   Current: HbA1c 7.5-10.5%
   Suggestion: Expand to HbA1c 7.0-11.0%
   Rationale: "67% of similar trials use wider range. Would increase
               eligible population by ~40% based on NCT data"
   Impact: "Faster enrollment (estimated 3 months sooner)"

3. Secondary Endpoints:
   Current: Fasting glucose, weight, hypoglycemia
   Suggestion: Add "% subjects achieving HbA1c < 7.0%"
   Rationale: "FDA Guidance (2020) recommends categorical endpoints
               for diabetes trials"
   Impact: "Stronger regulatory submission"

Dr. Martinez reviews:
  - Accept #1: Add Week 2 visit ✅
  - Reject #2: Keep HbA1c 7.5-10.5% (clinical rationale)
  - Accept #3: Add categorical endpoint ✅

Platform updates protocol automatically
```

**9:30 AM - Export Optimized Protocol**
```
Dr. Martinez clicks "Export Protocol Package"
  ↓
Platform generates:

📦 Protocol_Diabetes_v2.0_Package.zip:

  1. protocol_v2.0.pdf (updated protocol with accepted suggestions)
  2. edit_checks.yaml (25 auto-generated rules)
  3. evidence_pack.pdf (FDA citations for all decisions)
  4. benchmark_analysis.pdf (comparison to 127 similar trials)
  5. simulation_results.pdf (power analysis, enrollment projections)
  6. regulatory_checklist.pdf (FDA compliance verification)

Dr. Martinez downloads package ✅

She emails to team:
  "New diabetes protocol ready for review. Includes:
   - FDA-validated endpoints ✅
   - Enrollment feasibility confirmed ✅
   - Edit checks pre-configured ✅
   - 92% power (simulated) ✅

   Protocol writing time: 9:00 AM - 9:30 AM (30 minutes!)
   vs. previous protocol: 6-8 weeks

   Time saved: 99%!"
```

**End Result**:
- ✅ Protocol analyzed and validated (FDA guidance)
- ✅ Benchmarked against 127 similar trials
- ✅ Trial simulated (power analysis, enrollment projections)
- ✅ Edit checks auto-generated (25 rules)
- ✅ Protocol optimized (AI suggestions)
- ✅ Complete package exported (6 documents)
- ✅ Total time: 90 minutes (vs. 6-8 weeks manually!)

**Value to Dr. Martinez**:
- 99% time savings on protocol development
- FDA compliance guaranteed (LinkUp validation)
- Enrollment feasibility assessed (reduce risk)
- Edit checks ready for trial execution
- Evidence-based decisions (benchmark data)

---

## 🎯 ANSWER TO YOUR QUESTION: "HOW DOES PROTOCOL INTELLIGENCE FIT?"

### **Integration Points in Your Platform**

Protocol Intelligence fits as a **PRE-TRIAL MODULE**:

```
TRIAL LIFECYCLE STAGES:

Stage 1: PROTOCOL DESIGN (NEW! Protocol Intelligence)
  ↓
  User: Protocol Developer
  Tool: Upload protocol PDF → AI analysis → LinkUp validation
  Output: Optimized protocol + edit checks + simulations

Stage 2: STUDY SETUP (Existing! EDC Service)
  ↓
  User: Clinical Data Manager
  Tool: Import protocol → Create study in EDC → Configure forms
  Output: EDC system ready for data entry

Stage 3: TRIAL EXECUTION (Existing! EDC + Quality)
  ↓
  User: Site Coordinator (CRC)
  Tool: Enter patient data → Edit checks validate → Queries resolved
  Output: Clean, validated trial data

Stage 4: MONITORING (Existing! RBQM)
  ↓
  User: Study Manager
  Tool: RBQM dashboard → Site risk monitoring → Intervention
  Output: High-quality trial with minimal risks

Stage 5: ANALYSIS (Existing! Analytics + Daft)
  ↓
  User: Biostatistician
  Tool: Daft analytics → Statistical tests → CSR generation
  Output: Efficacy results, regulatory reports

Stage 6: SUBMISSION (Existing! LinkUp + SDTM)
  ↓
  User: Regulatory Affairs
  Tool: SDTM export → Evidence packs → FDA submission
  Output: Approved drug!
```

### **Technical Implementation**

**New Service**: `protocol-intelligence-service` (Port 8009)

**Endpoints**:
1. `POST /protocol/upload` - Upload protocol PDF
2. `POST /protocol/extract` - AI extraction (GPT-4o/Claude)
3. `POST /protocol/validate` - LinkUp FDA validation
4. `POST /protocol/benchmark` - ClinicalTrials.gov search
5. `POST /protocol/simulate` - Synthetic data simulation
6. `POST /protocol/generate-edit-checks` - Auto-generate YAML rules
7. `POST /protocol/optimize` - AI suggestions
8. `POST /protocol/export` - Package export

**Integration with Existing Services**:
- **LinkUp Service** (Port 8008): FDA guidance validation
- **Data Generation Service** (Port 8002): Trial simulations
- **Daft Analytics** (Port 8007): Power analysis, enrollment projections
- **Quality Service** (Port 8004): Auto-import edit checks

**Development Effort**: 6-8 weeks (per roadmap - Tier 2, Feature 5)

---

## 📊 COMPLETE USER FLOW SUMMARY

### **Full Platform User Journey (All 6 Roles)**

```
PRE-TRIAL (Weeks -12 to 0):
──────────────────────────────
Protocol Developer (Dr. Martinez):
  1. Upload protocol PDF
  2. AI extracts endpoints, I/E criteria, visit schedule
  3. LinkUp validates against FDA guidance
  4. Benchmark against similar trials (ClinicalTrials.gov)
  5. Simulate trial with synthetic data
  6. Auto-generate edit checks (LinkUp AI)
  7. Export optimized protocol package

  Time: 90 minutes (vs. 6-8 weeks)
  Value: 99% time savings, FDA compliance guaranteed

──────────────────────────────

STUDY SETUP (Weeks 0-2):
──────────────────────────────
Clinical Data Manager (Michael):
  1. Import protocol to EDC
  2. Create study (STU001)
  3. Configure eCRF forms (vitals, AEs, meds)
  4. Import auto-generated edit checks (from protocol intelligence!)
  5. Set up user accounts (site coordinators)
  6. Train sites on platform

  Time: 1 week (vs. 4 weeks)
  Value: 75% time savings, edit checks pre-configured

──────────────────────────────

TRIAL EXECUTION (Months 1-12):
──────────────────────────────
Site Coordinator (Sarah):
  Daily tasks:
    1. Enter patient vitals (5 minutes per visit)
    2. Record adverse events
    3. Respond to queries
    4. Review alerts

  Time: 30 minutes per visit (vs. 60 minutes)
  Value: 50% time savings, real-time validation

Clinical Data Manager (Michael):
  Daily tasks:
    1. Review quality dashboard
    2. Close queries (8 queries in 10 minutes)
    3. Monitor RBQM metrics
    4. Triage alerts

  Time: 60 minutes per day (vs. 3 hours)
  Value: 70% time savings, proactive quality management

Study Manager (Jessica):
  Daily tasks:
    1. Check RBQM heatmap
    2. Monitor enrollment progress
    3. Identify high-risk sites
    4. Generate executive reports

  Time: 90 minutes per day (vs. 4 hours)
  Value: 60% time savings, real-time visibility

──────────────────────────────

ANALYSIS (Month 12-13):
──────────────────────────────
Biostatistician (Dr. Chen):
  Weekly tasks:
    1. Export data (Parquet - 10x smaller!)
    2. Load into Daft (10-100x faster!)
    3. Calculate treatment effect (28ms!)
    4. Generate CSR draft (auto!)
    5. Export to SDTM (one-click!)

  Time: 90 minutes (vs. 2 weeks)
  Value: 95% time savings, Daft performance advantage

──────────────────────────────

SUBMISSION (Month 13-14):
──────────────────────────────
Regulatory Affairs (David):
  Weekly tasks:
    1. Quality assessment (3 seconds - Daft!)
    2. Generate evidence pack (LinkUp auto-citations!)
    3. Monitor regulatory updates (automated!)
    4. Validate SDTM datasets
    5. Submit to FDA

  Time: 90 minutes (vs. 3 weeks)
  Value: 95% time savings, LinkUp citations, proactive compliance

──────────────────────────────
```

### **Platform Value Proposition (Quantified)**

| Role | Time Savings | Annual Value |
|------|--------------|--------------|
| Protocol Developer | 99% (6 weeks → 90 min) | $200K |
| Clinical Data Manager | 70% (3 hrs → 1 hr daily) | $150K |
| Site Coordinator | 50% (60 min → 30 min per visit) | $80K |
| Study Manager | 60% (4 hrs → 90 min daily) | $120K |
| Biostatistician | 95% (2 weeks → 90 min) | $180K |
| Regulatory Affairs | 95% (3 weeks → 90 min) | $170K |
| **TOTAL VALUE** | **-** | **$900K per trial** |

**Cost of Your Platform**: $60K-$600K/year (per pricing tiers)

**ROI**: **1.5x to 15x** (depending on tier)

---

## ✅ FINAL ANSWERS TO YOUR QUESTIONS

### Q1: "Can protocol intelligence fit somewhere in my project?"

**Answer**: **YES! As a PRE-TRIAL module** (Stage 1 - before study setup)

**Where it fits**:
- Before EDC setup
- Before trial execution
- Helps Protocol Developers optimize protocols
- Feeds into EDC (auto-generated edit checks)
- Uses LinkUp (FDA validation) + Daft (simulations)

**Development Effort**: 6-8 weeks (already in roadmap - Tier 2, Feature 5)

**Priority**: **MEDIUM-HIGH** (complements existing features, large revenue potential $500K-$1.5M/year)

---

### Q2: "Who are the end users and their roles?"

**Answer**: **6 user personas** (not just 2!):

1. **Site Coordinator (CRC)** - "Clinical Technician"
   - Hospital/clinic staff
   - Enters patient data daily
   - Uses: EDC, data validation, query resolution

2. **Clinical Data Manager** - "Data Analyst" (Part 1)
   - Oversees data quality
   - Reviews queries, monitors sites
   - Uses: EDC, RBQM, quality dashboard

3. **Biostatistician** - "Data Analyst" (Part 2)
   - Analyzes trial results
   - Generates CSR, SDTM
   - Uses: Daft analytics, synthetic data, CSR generation

4. **Study Manager** - "Trial Overseer"
   - Monitors entire trial
   - Manages sites, reports to sponsor
   - Uses: RBQM heatmaps, executive reports

5. **Regulatory Affairs** - "Compliance Gatekeeper"
   - Ensures FDA compliance
   - Prepares submissions
   - Uses: LinkUp evidence packs, SDTM export, compliance watcher

6. **Protocol Developer** - "Trial Designer" (NEW!)
   - Designs protocols pre-trial
   - Medical directors, clinical scientists
   - Uses: Protocol intelligence (if implemented)

---

### Q3: "How will the end user use my app and how will it be useful to them?"

**Answer**: See 6 detailed event flows above. Key highlights:

**Site Coordinator (Sarah)**:
- Logs in → Sees today's visits → Enters vitals → Edit checks validate in real-time → Queries resolved → Visit complete
- **Value**: 50% faster, no errors, less stress

**Clinical Data Manager (Michael)**:
- Reviews dashboard → Triages alerts → Closes queries → Generates RBQM report → Shares with sponsor
- **Value**: 70% time savings, proactive quality management

**Biostatistician (Dr. Chen)**:
- Exports data → Loads into Daft → Calculates treatment effect (28ms!) → Generates CSR (auto!) → Exports SDTM
- **Value**: 95% time savings, 10-100x faster analytics

**Study Manager (Jessica)**:
- Checks RBQM heatmap → Identifies high-risk sites → Generates executive report → Presents to sponsor
- **Value**: Real-time visibility, data-driven decisions

**Regulatory Affairs (David)**:
- Runs quality assessment → Generates evidence pack (LinkUp citations!) → Monitors FDA updates (automated!) → Submits to FDA
- **Value**: 95% time savings, proactive compliance

**Protocol Developer (Dr. Martinez)** - NEW!:
- Uploads protocol PDF → AI extracts elements → LinkUp validates → Benchmark vs. similar trials → Simulate with synthetic data → Auto-generate edit checks → Export package
- **Value**: 99% time savings, FDA compliance guaranteed

---

## 🚀 RECOMMENDATION: Should You Build Protocol Intelligence?

### **YES, but with caveats:**

**Pros**:
- ✅ Completes end-to-end platform (pre-trial → submission)
- ✅ Large revenue potential ($500K-$1.5M/year)
- ✅ Leverages existing tech (LinkUp, Daft, synthetic data)
- ✅ Differentiates from competitors (Medidata, Oracle don't have this)
- ✅ Synergy with Trialscope (potential partnership opportunity)

**Cons**:
- ❌ Overlaps with Trialscope (partnership might be better than building)
- ❌ 6-8 weeks development effort (moderate)
- ❌ Requires large trial database (expensive to build vs. ClinicalTrials.gov API)

**Recommended Approach**:
1. **Build MVP** (4 weeks):
   - Protocol PDF upload + AI extraction (GPT-4o)
   - LinkUp FDA validation
   - Auto-generate edit checks (LinkUp AI)

2. **Evaluate** (2 weeks):
   - Test with 3-5 beta customers
   - Measure adoption and value

3. **Decide** (Month 6):
   - If successful: Expand features (benchmarking, simulations)
   - If partnership opportunity: Integrate Trialscope instead

**Priority in Roadmap**: **Q2-Q3** (after Tier 1 features: PDF evidence packs, RBQM dashboard, trial registry integration)

---

**Would you like me to create a detailed technical specification for the protocol intelligence module, or focus on building out the existing features first?**

