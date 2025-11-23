# AACT Data Extraction Gap Analysis
## Critical Missing Features for Synthetic Data Variance

**Generated:** 2025-11-22  
**Purpose:** Identify gaps in current AACT extraction to improve synthetic data realism

---

## 1. DROPOUT PATTERNS - Currently Missing

### **What We Extract:**
✅ Overall dropout rate by phase (e.g., 5.24% for Hypertension Phase 3)  
✅ Top 5 dropout reasons with percentages  
✅ Total subjects and total dropouts

### **What We're MISSING:**

#### **A. Treatment Arm-Specific Dropouts**
- **Impact:** Active arms often have DIFFERENT dropout rates than placebo
- **Data Available:** `ctgov_group_code` column in drop_withdrawals.txt
- **Example:** Active arm: 8% dropout, Placebo: 3% dropout
- **Why Critical:** Generates unrealistic data if we assume same dropout rate across arms

#### **B. Time-Based Dropout Distribution**
- **Impact:** Dropouts aren't uniform - most occur early (weeks 1-4) or late (>12 weeks)
- **Data Available:** `period` column (e.g., "Treatment Period", "Week 12", "Follow-up")
- **Why Critical:** Need to simulate realistic dropout timing curves

#### **C. Trial-Level Variance**
- **Impact:** Some trials have 0% dropout, others 30%
- **Current:** We only extract aggregated mean (5.24%)
- **What We Need:** Standard deviation and distribution of dropout rates across trials
- **Why Critical:** Synthetic trials all look identical without this variance

---

## 2. BASELINE VITAL SIGNS - Partial Extraction

### **What We Extract:**
✅ Mean, median, std, Q25, Q75 for SBP/DBP/HR/Temp  
✅ Phase-specific values

### **What We're MISSING:**

#### **A. Age-Stratified Vitals**
- **Impact:** 25-year-olds have different BP than 65-year-olds
- **Data Available:** Can cross-reference baseline_measurements with eligibilities (age criteria)
- **Why Critical:** Current generator produces same vitals regardless of age

#### **B. Gender-Stratified Vitals**
- **Impact:** Males have higher SBP than females (5-10 mmHg difference)
- **Data Available:** demographic data in baseline_measurements
- **Why Critical:** Ignoring this creates unrealistic correlations

#### **C. Visit-to-Visit Variability**
- **Impact:** Same patient's BP varies ±5-10 mmHg visit-to-visit
- **Data Available:** outcome_measurements.txt has longitudinal data
- **Why Critical:** Our diffusion model needs realistic noise patterns

---

## 3. ADVERSE EVENTS - Good Extraction, Minor Gaps

### **What We Extract:**
✅ Top 20 AEs by phase with frequencies  
✅ Subjects affected and trial counts

### **What We're MISSING:**

#### **A. AE Severity Distribution**
- **Impact:** Not all AEs are equal - Grade 1 headache vs Grade 4 MI
- **Data Available:** reported_events.txt has severity columns
- **Why Critical:** Need to simulate realistic SAE (Serious Adverse Event) rates

#### **B. AE Timing**
- **Impact:** Some AEs occur early (infusion reactions), others late (cumulative toxicity)
- **Data Available:** Temporal data in reported_events.txt
- **Why Critical:** Realistic trial simulations need time-based AE patterns

---

## 4. TREATMENT EFFECTS - Major Gap

### **What We Extract:**
✅ Median effect and trial counts  
❌ **BUT median_effect is NULL in output**

### **Investigation Needed:**
- The script processes 4.6M outcome_measurements but isn't calculating effects correctly
- Need to extract:
  - Mean treatment effect (Active - Placebo)
  - Standard deviation of effects across trials
  - Responder rates (% subjects achieving >10 mmHg reduction)
  - Time to effect (when does separation occur?)

---

## 5. MISSING CATEGORIES (Empty in Cache)

### **A. Study Duration**
- **Current:** Zero data extracted
- **Available:** milestones.txt (start/completion dates)
- **Why Critical:** Trials vary 4 weeks to 52 weeks - affects dropout, costs, everything

### **B. Age Distribution**
- **Current:** Zero data extracted  
- **Available:** eligibilities.txt (minimum_age, maximum_age)
- **Why Critical:** Need to generate realistic age demographics

### **C. Common Drugs**
- **Current:** Zero data extracted
- **Available:** interventions.txt
- **Why Critical:** Drug names add realism to generated trials

---

## PRIORITY RECOMMENDATIONS

### **Immediate (High Impact):**
1. ✅ Treatment arm-specific dropout rates
2. ✅ Trial-level dropout variance (std dev)
3. ✅ Fix treatment_effects null values
4. ✅ Extract study duration from milestones
5. ✅ Age distribution from eligibilities

### **Medium Priority:**
6. Time-based dropout curves
7. AE severity distributions
8. Age-stratified baseline vitals
9. Visit-to-visit vital sign variability

### **Nice-to-Have:**
10. Gender-stratified vitals
11. AE timing patterns
12. Responder rate distributions

---

## PROPOSED SOLUTION

Create enhanced extraction logic that captures:
- **Distributions** (not just means) → enables variance
- **Stratifications** (by arm, age, gender) → enables correlations
- **Temporal patterns** (time-based) → enables realistic dynamics

This will transform synthetic data from "statistically accurate" to "indistinguishable from real trials."
