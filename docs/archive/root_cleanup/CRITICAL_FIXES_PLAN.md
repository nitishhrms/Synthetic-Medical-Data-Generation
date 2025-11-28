# CRITICAL FIXES IMPLEMENTATION PLAN
## Addressing Expert Assessment Findings

**Priority:** Fix the 3 critical flaws that drop quality from 85% → 60%  
**Timeline:** Week 1 (5-7 days of work)  
**Goal:** Raise platform grade from B- (77) to A (85)

---

## 🔴 **FIX #1: TEMPORAL CORRELATION (CRITICAL)**

### Problem:
```python
# Current: Each visit is independent
# Week 4 SBP has NO correlation with Baseline SBP
for visit in visits:
    sample_independent()  # WRONG!
```

### Solution: AR(1) Model (Autoregressive Order 1)
```python
# Correct: Future measurements depend on previous ones
SBP_week4 = α * SBP_baseline + β * treatment + ε
where ε ~ N(0, σ²)
```

### Implementation:
**File:** `microservices/data-generation-service/src/temporal_generators.py` (NEW)

**Functions:**
1. `generate_vitals_with_temporal_correlation()` - Main function
2. `fit_ar1_parameters()` - Learn α from AACT data
3. `sample_ar1_trajectory()` - Generate time series

**Parameters:**
- `rho`: Autocorrelation coefficient (0.6-0.8 for vital signs)
- `innovation_std`: Noise term standard deviation

**Example:**
```python
# Instead of:
visits = [generate_independent_visit(v) for v in [0, 4, 12]]

# Use:
visits = generate_ar1_trajectory(
    baseline=generate_baseline(),
    visits=[0, 4, 12],
    rho=0.7,  # 70% correlation with previous visit
    treatment_effect=-5.0
)
```

**Estimated effort:** 4 hours  
**Files to modify:**
- Create `temporal_generators.py` 
- Update `generators.py` to import and use temporal functions
- Add AR(1) test in `test_temporal_correlation.py`

---

## 🔴 **FIX #2: HETEROGENEOUS TREATMENT EFFECTS (CRITICAL)**

### Problem:
```python
# Current: Everyone gets exactly -5 mmHg
df['sbp_week12'] = df['sbp_baseline'] + target_effect
```

### Solution: Subject-Level Treatment Effect Sampling
```python
# Correct: Treatment effects vary by subject
treatment_effects = sample_heterogeneous_effects(
    baseline_sbp=df['sbp_baseline'],
    mean_effect=-5.0,
    std_effect=3.0  # Some get -10, others get 0
)
```

### Implementation:
**File:** `microservices/data-generation-service/src/treatment_effect_sampler.py` (NEW)

**Functions:**
1. `sample_heterogeneous_effects()` - Main sampler
2. `correlation_with_baseline()` - Higher baseline → bigger effect
3. `add_placebo_responders()` - 30% of placebo shows improvement

**Distribution:**
```python
# Treatment effect ~ N(μ, σ²) with baseline correlation
effect = np.random.normal(mean_effect, std_effect)
# Severity adjustment: worse patients respond better
effect *= (1 + 0.15 * (baseline_sbp - 140) / 20)
```

**Estimated effort:** 3 hours  
**Files to modify:**
- Create `treatment_effect_sampler.py`
- Update `generate_vitals_mvn()` to use heterogeneous effects
- Add test in `test_treatment_heterogeneity.py`

---

## 🔴 **FIX #3: REALISTIC MISSING DATA MECHANISM (CRITICAL)**

### Problem:
```python
# Current: Random dropout (MCAR)
dropout_mask = np.random.random(n) < dropout_rate
```

### Solution: MAR/MNAR Missingness
```python
# MAR: Dropout depends on OBSERVED data (AEs, high BP)
dropout_prob = base_rate + 0.2 * (sbp > 160) + 0.15 * has_ae

# MNAR: Dropout depends on UNOBSERVED factors
dropout_prob += 0.1 * latent_frailty
```

### Implementation:
**File:** `microservices/data-generation-service/src/missingness_mechanisms.py` (NEW)

**Functions:**
1. `apply_mar_dropout()` - Missing At Random
2. `apply_mnar_dropout()` - Missing Not At Random  
3. `generate_latent_frailty()` - Unobserved confounders

**Mechanism Types:**
```python
def apply_mar_dropout(df, arm_rates):
    """MAR: Dropout probability depends on observed vitals/AEs"""
    base_prob = arm_rates[df['arm']]
    
    # Increase dropout for adverse events
    base_prob += 0.20 * df['has_severe_ae']
    
    # Increase dropout for uncontrolled BP
    base_prob += 0.15 * (df['sbp_week4'] > 160)
    
    return np.random.random(len(df)) < base_prob
```

**Estimated effort:** 4 hours  
**Files to modify:**
- Create `missingness_mechanisms.py`
- Update `generators.py` to use MAR/MNAR
- Add test in `test_missingness.py`

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Day 1-2: Temporal Correlation**
- [ ] Create `temporal_generators.py`
- [ ] Implement AR(1) sampler
- [ ] Estimate `rho` from AACT (if duration data available)
- [ ] Add unit tests
- [ ] Integrate into `generate_vitals_mvn()`
- [ ] Verify: `corr(Week4, Baseline) > 0.6`

### **Day 3: Treatment Heterogeneity**
- [ ] Create `treatment_effect_sampler.py`
- [ ] Implement heterogeneous sampler
- [ ] Add baseline correlation
- [ ] Add placebo responders
- [ ] Unit tests
- [ ] Verify: `std(treatment_effects) > 2.0`

### **Day 4-5: Missing Data**
- [ ] Create `missingness_mechanisms.py`
- [ ] Implement MAR dropout
- [ ] Implement MNAR dropout (with latent frailty)
- [ ] Unit tests  
- [ ] Verify: Dropout rate higher for AEs

### **Day 6-7: Integration & Testing**
- [ ] Update all generator methods (MVN, Bootstrap, etc.)
- [ ] End-to-end integration test
- [ ] Compare before/after data quality
- [ ] Update analytics service validators
- [ ] Documentation

---

## 🎯 **SUCCESS METRICS**

### **Before Fixes:**
- Temporal correlation: 0.0 (independent visits)
- Treatment effect variance: 0.0 (all same)
- Missing data: MCAR only
- **Overall Grade: B- (77/100)**

### **After Fixes:**
- Temporal correlation: 0.6-0.8 (realistic)
- Treatment effect variance: 3-5 mmHg std
- Missing data: MAR + MNAR
- **Overall Grade: A (85/100)**

### **Validation:**
```python
# Test 1: Temporal correlation
assert df.groupby('subject_id')['sbp'].corr() > 0.6

# Test 2: Treatment heterogeneity  
active_effects = df[df['arm']=='active']['sbp_change']
assert active_effects.std() > 2.0

# Test 3: MAR missingness
dropout_with_ae = df[df['has_ae']==True]['dropout'].mean()
dropout_no_ae = df[df['has_ae']==False]['dropout'].mean()
assert dropout_with_ae > dropout_no_ae
```

---

## 📁 **NEW FILES TO CREATE**

1. `temporal_generators.py` (~200 lines)
2. `treatment_effect_sampler.py` (~150 lines)
3. `missingness_mechanisms.py` (~180 lines)
4. `test_temporal_correlation.py` (~100 lines)
5. `test_treatment_heterogeneity.py` (~80 lines)
6. `test_missingness.py` (~90 lines)

**Total:** ~800 lines of high-quality, tested code

---

## 🚀 **EXECUTION ORDER**

1. **Start:** Temporal correlation (biggest impact)
2. **Then:** Treatment heterogeneity (enables subgroup analysis)
3. **Finally:** Missingness (completes realism)

**Rationale:** Temporal correlation affects ALL downstream analyses, so fix it first.

---

## 💡 **QUICK WINS (Optional but Recommended)**

After the 3 critical fixes, these are high-value, low-effort:

1. **Validate against AACT hold-out** (1 day)
   - Hold out 10% of trials, generate synthetic, compare

2. **Add uncertainty quantification** (0.5 day)
   - Generate 10 datasets → measure variance in conclusions

3. **Document statistical assumptions** (0.5 day)
   - Critical for FDA/regulatory review

---

Let's start implementation! 🚀
