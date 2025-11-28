# AACT Data Extraction - Comprehensive Enhancement Plan
## Beyond the Basics: Advanced Features for Production-Grade Synthetic Data

---

## TIER 1: Critical Variance Features (Implement Now)

### 1. **Dropout Patterns Enhancement**
- ✅ Treatment arm-specific dropout rates
- ✅ Trial-level variance (std dev, min, max)
- ✅ Time-based dropout curves (early vs late)
- **NEW:** Cumulative dropout over time (survival curves)

### 2. **Treatment Effects (Currently Broken)**
- ✅ Fix null median_effect calculation
- ✅ Extract effect size variance across trials
- **NEW:** Effect size by baseline severity (responder analysis)
- **NEW:** Time-to-maximal-effect (when does treatment separate from placebo?)

### 3. **Missing Critical Categories**
- ✅ Study duration (from milestones.txt)
- ✅ Age distribution (from eligibilities.txt)  
- ✅ Common drug names (from interventions.txt)

---

## TIER 2: Advanced Realism Features

### 4. **Baseline Characteristics Stratification**
- Age-stratified vital signs (young vs elderly patients)
- Gender-stratified measurements
- BMI correlations with BP (heavier patients → higher BP)
- **Why:** Current generator ignores patient heterogeneity

### 5. **Visit-to-Visit Variability**
- Intra-subject variation (same patient, different visits)
- White-coat effect (first visit higher BP)
- Regression to the mean
- **Why:** Synthetic data looks too "clean" without measurement noise

### 6. **Enrollment Dynamics**
- Enrollment rate curves (slow at start, peak mid-trial, slow at end)
- Screen failure rates (how many screened vs randomized?)
- Site-level enrollment variance (some sites enroll 10%, others 1%)
- **Why:** Realistic trial timelines require this

### 7. **Protocol Deviations**
- Visit window compliance (±7 days is typical)
- Missing visit patterns (which visits get skipped most?)
- Per-protocol vs ITT population ratios
- **Why:** Real trials are messy - we need realistic messiness

---

## TIER 3: Expert-Level Features

### 8. **Missing Data Patterns**
- MCAR (Missing Completely At Random): random dropouts
- MAR (Missing At Random): correlated with observed data
- MNAR (Missing Not At Random): related to unobserved outcome
- **Why:** Imputation methods need realistic missingness

### 9. **Subgroup Effects**
- Age subgroups (e.g., treatment works better in >65 years)
- Baseline severity (works better in stage 2 vs stage 1)
- Gender interactions
- **Why:** Regulatory submissions require subgroup analyses

### 10. **Endpoint Hierarchies**
- Primary vs secondary endpoints
- Exploratory endpoints
- Success rates per endpoint type
- **Why:** Multi-endpoint trials need realistic correlations

### 11. **Cost & Site Variance**
- Geographic cost variations (US sites cost 3x vs Asia)
- Site performance metrics (quality, enrollment speed)
- Investigator experience levels
- **Why:** Budget planning and site selection optimization

### 12. **Adaptive Design Features**
- Interim analysis triggers
- Sample size re-estimation patterns
- Futility stopping boundaries
- **Why:** Modern trials use adaptive designs

---

## PROPOSED IMPLEMENTATION ORDER

### **Phase 1: Foundation (This Session)**
1. ✅ Treatment arm-specific dropouts
2. ✅ Trial-level dropout variance
3. ✅ Fix treatment effects
4. ✅ Study duration extraction
5. ✅ Age distribution
6. ✅ Drug names

**Estimated Time:** 30-45 minutes  
**Impact:** High - addresses immediate gaps

### **Phase 2: Correlations (Next Session)**
7. Age-stratified vitals
8. Visit-to-visit variability
9. BMI-BP correlations
10. Enrollment curves

**Estimated Time:** 1-2 hours  
**Impact:** Medium-High - adds realistic heterogeneity

### **Phase 3: Advanced (Future)**
11. Missing data patterns
12. Subgroup effects
13. Protocol deviations
14. Endpoint hierarchies

**Estimated Time:** 2-3 hours  
**Impact:** Expert-level realism

---

## ADDITIONAL QUICK WINS

### **A. Data Quality Improvements**
- Add data validation checks (flag suspicious values)
- Extract confidence intervals for all statistics
- Add sample size tracking (how many trials contributed to each statistic?)

### **B. Metadata Enhancements**
- Track data freshness (when was AACT last updated?)
- Version control for cache (track what changed between runs)
- Add data lineage (which AACT file → which cache field)

### **C. Performance Optimizations**
- Cache intermediate results (don't re-process unchanged files)
- Parallel processing for independent file processing
- Incremental updates (only process new trials)

---

## RECOMMENDATION

**Start with Phase 1 (6 enhancements) NOW**, then assess if Phase 2 is needed based on your synthetic data quality testing.

The biggest impact items are:
1. **Treatment arm-specific dropouts** (different rates for active vs placebo)
2. **Trial-level variance** (some trials 0%, others 30%)
3. **Fix treatment effects** (currently null - broken calculation)
