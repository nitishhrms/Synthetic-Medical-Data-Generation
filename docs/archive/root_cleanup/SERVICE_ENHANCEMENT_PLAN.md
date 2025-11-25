# Comprehensive Enhancement Plan: Data Generation & Analytics Services
## Leveraging AACT Phase 1 Enhancements

**Date:** 2025-11-22  
**Context:** Post-AACT extraction improvements (dropout variance, arm-specific rates, treatment effects, etc.)

---

## 🎯 **EXECUTIVE SUMMARY**

The AACT enhancements provide **realistic variance data** that your current services aren't utilizing. This plan addresses:

1. **Data Generation Service:** Add variance simulation to make synthetic trials indistinguishable from real ones
2. **Analytics Service:** Add variance validation to detect unrealistic synthetic data

**Expected Impact:** Synthetic trials will vary realistically (0-30% dropout) instead of all having identical 5.24% dropout.

---

## 📊 **PART 1: DATA GENERATION SERVICE ENHANCEMENTS**

### **Current State Assessment**

**Strengths:**
- ✅ Multiple generator methods (MVN, Bootstrap, MICE, Bayesian, Diffusion)
- ✅ AACT statistics integration
- ✅ Treatment arm generation

**Critical Gaps:**
- ❌ All trials have identical dropout rates (no variance)
- ❌ No arm-specific differential dropout
- ❌ No age-based baseline vital adjustments
- ❌ Study duration not utilized
- ❌ Treatment effects sometimes ignored

---

### **Enhancement 1: Realistic Dropout Variance**

**Priority:** 🔴 CRITICAL  
**Complexity:** Medium  
**Impact:** Transforms identical trials → realistic variation

#### **Implementation:**

**File:** `microservices/data-generation-service/src/generators.py`

**Current Code:**
```python
# Static dropout rate
dropout_rate = 0.0524  # 5.24% for all trials
```

**Enhanced Code:**
```python
def sample_dropout_rate(indication: str, phase: str, aact_stats: dict) -> float:
    """Sample realistic dropout rate from trial-level variance"""
    variance = aact_stats['indications'][indication]['dropout_patterns'][phase]['trial_variance']
    
    # Sample from normal distribution
    mean_rate = aact_stats['indications'][indication]['dropout_patterns'][phase]['dropout_rate']
    std_dev = variance['std_dev']
    
    # Sample with realistic bounds
    sampled_rate = np.random.normal(mean_rate, std_dev)
    
    # Clip to realistic range (0% to max observed)
    return np.clip(sampled_rate, 0, variance['max_rate'])
```

**Usage:**
```python
# In generate_vitals_mvn():
dropout_rate = sample_dropout_rate(indication, phase, aact_stats)
```

**Expected Output:** Trials now vary: Trial A has 2% dropout, Trial B has 18%, Trial C has 5%, etc.

---

### **Enhancement 2: Arm-Specific Dropout Rates**

**Priority:** 🔴 CRITICAL  
**Complexity:** Medium  
**Impact:** Active arms have higher dropout than placebo (realistic)

#### **Implementation:**

**File:** `microservices/data-generation-service/src/generators.py`

**New Function:**
```python
def assign_arm_specific_dropouts(
    df: pd.DataFrame, 
    arm_rates: dict,
    overall_rate: float
) -> pd.DataFrame:
    """
    Assign differential dropout by treatment arm
    
    Args:
        df: Trial data with 'arm' column
        arm_rates: {arm_code: dropout_rate} from AACT
        overall_rate: Fallback if arm not in cache
    
    Returns:
        df with 'dropout' column (boolean)
    """
    df['dropout_prob'] = df['arm'].map(arm_rates).fillna(overall_rate)
    df['dropout'] = np.random.random(len(df)) < df['dropout_prob']
    return df
```

**Usage:**
```python
# After generating baseline data
arm_rates = aact_stats['indications'][indication]['dropout_patterns'][phase]['arm_specific_rates']
df = assign_arm_specific_dropouts(df, arm_rates, overall_dropout_rate)
```

**Expected Output:** Active arm (FG000) has 12% dropout, Placebo (FG001) has 5% dropout

---

### **Enhancement 3: Age-Stratified Baseline Vitals**

**Priority:** 🟡 HIGH  
**Complexity:** Medium  
**Impact:** Realistic correlation between age and vital signs

#### **Implementation:**

**File:** `microservices/data-generation-service/src/generators.py`

**New Function:**
```python
def adjust_vitals_by_age(vitals: pd.DataFrame, ages: np.ndarray) -> pd.DataFrame:
    """
    Adjust baseline vitals based on patient age
    
    Age effects (per decade):
    - SBP: +5 mmHg per decade after age 40
    - DBP: +2 mmHg per decade after age 40
    - HR: -2 bpm per decade after age 30
    """
    age_decades = (ages - 40) / 10
    
    vitals['sbp'] += age_decades * 5 * (ages > 40)
    vitals['dbp'] += age_decades * 2 * (ages > 40)
    vitals['hr'] -= ((ages - 30) / 10) * 2 * (ages > 30)
    
    # Ensure physiological bounds
    vitals['sbp'] = vitals['sbp'].clip(90, 200)
    vitals['dbp'] = vitals['dbp'].clip(60, 120)
    vitals['hr'] = vitals['hr'].clip(50, 120)
    
    return vitals
```

**Integration:**
```python
# In generate_vitals_mvn():
ages = generate_ages(aact_stats, indication, phase, n_subjects)
vitals_df = generate_baseline_vitals(aact_stats, n_subjects)
vitals_df = adjust_vitals_by_age(vitals_df, ages)
```

---

### **Enhancement 4: Study Duration Utilization**

**Priority:** 🟡 HIGH  
**Complexity:** Low  
**Impact:** Accurate trial timelines and costs

#### **Implementation:**

**File:** `microservices/data-generation-service/src/realistic_trial.py`

**New Function:**
```python
def sample_study_duration(indication: str, phase: str, aact_stats: dict) -> int:
    """Sample realistic study duration in days"""
    duration_stats = aact_stats['indications'][indication].get('study_duration', {}).get(phase)
    
    if not duration_stats:
        # Fallback defaults
        defaults = {'Phase 1': 90, 'Phase 2': 180, 'Phase 3': 365, 'Phase 4': 180}
        return defaults.get(phase, 180)
    
    # Sample from distribution
    mean = duration_stats['median_days']
    std = duration_stats['std_days']
    
    sampled = int(np.random.normal(mean, std))
    
    # Clip to observed range
    return np.clip(sampled, duration_stats['min_days'], duration_stats['max_days'])
```

**Usage:**
```python
# In realistic_trial_design():
study_duration_days = sample_study_duration(indication, phase, aact_stats)
visit_schedule = generate_visit_schedule(study_duration_days)
```

---

### **Enhancement 5: Treatment Effect Application**

**Priority:** 🟡 HIGH  
**Complexity:** Medium  
**Impact:** Realistic primary endpoint results

#### **Implementation:**

**File:** `microservices/data-generation-service/src/generators.py`

**New Function:**
```python
def apply_treatment_effect(
    vitals_df: pd.DataFrame,
    arm: str,
    indication: str,
    phase: str,
    aact_stats: dict
) -> pd.DataFrame:
    """Apply realistic treatment effect to endpoint measurements"""
    
    effect_stats = aact_stats['indications'][indication]['treatment_effects'].get(phase)
    
    if not effect_stats or arm != 'active':
        return vitals_df  # No effect for placebo
    
    # Sample treatment effect from distribution
    median_effect = effect_stats['median']
    std_effect = effect_stats['std']
    
    sampled_effect = np.random.normal(median_effect, std_effect / 10)
    
    # Apply to primary endpoint (SBP for hypertension)
    vitals_df['sbp_week12'] = vitals_df['sbp_baseline'] + sampled_effect
    
    return vitals_df
```

---

### **Enhancement 6: Visit-to-Visit Variability**

**Priority:** 🟢 MEDIUM  
**Complexity:** Low  
**Impact:** Realistic measurement noise

#### **Implementation:**

**New Function:**
```python
def add_visit_variability(vitals: pd.DataFrame, visit_num: int) -> pd.DataFrame:
    """Add realistic visit-to-visit noise"""
    
    # White-coat effect (first visit has +5 mmHg SBP)
    if visit_num == 1:
        vitals['sbp'] += 5
    
    # Random daily variation (±5 mmHg)
    vitals['sbp'] += np.random.normal(0, 5, len(vitals))
    vitals['dbp'] += np.random.normal(0, 3, len(vitals))
    vitals['hr'] += np.random.normal(0, 5, len(vitals))
    
    return vitals
```

---

## 📈 **PART 2: ANALYTICS SERVICE ENHANCEMENTS**

### **Current State Assessment**

**Strengths:**
- ✅ KS test, T-test implementations
- ✅ PCA comparison
- ✅ Correlation analysis

**Critical Gaps:**
- ❌ No variance validation (all trials looking identical passes)
- ❌ No arm-specific checks
- ❌ No age-vital correlation checks

---

### **Enhancement 7: Variance Validation**

**Priority:** 🔴 CRITICAL  
**Complexity:** Medium  
**Impact:** Detect unrealistic lack of variance

#### **Implementation:**

**File:** `microservices/analytics-service/src/quality_checks.py`

**New Check:**
```python
def validate_dropout_variance(
    synthetic_trials: List[pd.DataFrame],
    indication: str,
    phase: str,
    aact_stats: dict
) -> dict:
    """
    Validate that synthetic trials have realistic variance
    
    Returns:
        {
            'pass': bool,
            'synthetic_std': float,
            'expected_std': float,
            'variance_ratio': float  # Should be ~1.0
        }
    """
    # Calculate dropout rate for each synthetic trial
    synthetic_rates = [
        (trial['dropout'].sum() / len(trial)) 
        for trial in synthetic_trials
    ]
    
    synthetic_std = np.std(synthetic_rates)
    
    # Get expected variance from AACT
    expected_std = aact_stats['indications'][indication]['dropout_patterns'][phase]['trial_variance']['std_dev']
    
    # Variance should be within 50% of expected
    variance_ratio = synthetic_std / expected_std
    passed = 0.5 < variance_ratio < 1.5
    
    return {
        'pass': passed,
        'synthetic_std': synthetic_std,
        'expected_std': expected_std,
        'variance_ratio': variance_ratio,
        'message': f"Synthetic variance is {variance_ratio:.2f}x expected"
    }
```

---

### **Enhancement 8: Arm-Specific Validation**

**Priority:** 🔴 CRITICAL  
**Complexity:** Low  
**Impact:** Detect unrealistic equal dropout across arms

#### **Implementation:**

**New Check:**
```python
def validate_arm_specific_dropout(
    df: pd.DataFrame,
    arm_rates_expected: dict
) -> dict:
    """Validate differential dropout by arm"""
    
    actual_rates = df.groupby('arm')['dropout'].mean().to_dict()
    
    # Check if active arm has higher dropout than placebo
    active_rate = actual_rates.get('active', 0)
    placebo_rate = actual_rates.get('placebo', 0)
    
    differential_exists = active_rate > placebo_rate
    
    return {
        'pass': differential_exists,
        'active_dropout': active_rate,
        'placebo_dropout': placebo_rate,
        'differential': active_rate - placebo_rate,
        'message': f"Active dropout ({active_rate:.1%}) {'>' if differential_exists else '<='} Placebo ({placebo_rate:.1%})"
    }
```

---

### **Enhancement 9: Age-Vital Correlation Check**

**Priority:** 🟡 HIGH  
**Complexity:** Low  
**Impact:** Validate realistic physiological correlations

#### **Implementation:**
```python
def validate_age_vital_correlation(df: pd.DataFrame) -> dict:
    """Validate that SBP increases with age"""
    
    correlation = df['age'].corr(df['sbp_baseline'])
    
    # Correlation should be positive (>0.3)
    passed = correlation > 0.3
    
    return {
        'pass': passed,
        'correlation': correlation,
        'message': f"Age-SBP correlation: {correlation:.3f} (expected >0.3)"
    }
```

---

## 🚀 **IMPLEMENTATION ROADMAP**

### **Phase 1: Critical Variance Features (Week 1)**
1. ✅ Enhancement 1: Dropout Variance Sampling
2. ✅ Enhancement 2: Arm-Specific Dropouts
3. ✅ Enhancement 7: Variance Validation
4. ✅ Enhancement 8: Arm-Specific Validation

**Deliverable:** Synthetic trials with realistic dropout variation

---

### **Phase 2: Physiological Realism (Week 2)**
5. ✅ Enhancement 3: Age-Stratified Vitals
6. ✅ Enhancement 5: Treatment Effects
7. ✅ Enhancement 9: Age-Vital Correlation Check

**Deliverable:** Age-appropriate vital signs and realistic treatment effects

---

### **Phase 3: Timeline & Noise (Week 3)**
8. ✅ Enhancement 4: Study Duration
9. ✅ Enhancement 6: Visit-to-Visit Variability

**Deliverable:** Realistic study timelines and measurement noise

---

## 📋 **TESTING PLAN**

### **Unit Tests:**
```python
def test_dropout_variance():
    """Test that 1000 synthetic trials have realistic variance"""
    trials = [generate_trial() for _ in range(1000)]
    dropout_rates = [calc_dropout_rate(t) for t in trials]
    std = np.std(dropout_rates)
    
    assert 0.10 < std < 0.25  # Expected range for Phase 3 hypertension
    
def test_arm_differential():
    """Test active arm has higher dropout"""
    trial = generate_trial_with_arms()
    active_dropout = trial[trial['arm']=='active']['dropout'].mean()
    placebo_dropout = trial[trial['arm']=='placebo']['dropout'].mean()
    
    assert active_dropout > placebo_dropout
```

---

## 📊 **SUCCESS METRICS**

| Metric | Before | After (Target) |
|--------|--------|----------------|
| **Dropout Variance (Std Dev)** | 0.0% (all identical) | 15-20% |
| **Active vs Placebo Differential** | None | 5-10% higher |
| **Age-SBP Correlation** | ~0 | >0.3 |
| **Treatment Effect Accuracy** | Fixed | Sampled from real distribution |
| **Variance Validation Pass Rate** | N/A | >90% |

---

## 🎯 **EXPECTED OUTCOMES**

1. **Regulatory Readiness:** Synthetic data will pass FDA scrutiny for variance
2. **ML Training:** Better training data for predictive models
3. **Cost Estimation:** Accurate trial duration → accurate budgets
4. **Realistic Simulations:** Dropout patterns match real trials

---

## 📁 **FILES TO MODIFY**

### **Data Generation Service:**
- `src/generators.py` (all 6 enhancements)
- `src/realistic_trial.py` (study duration)
- `src/simple_diffusion.py` (variance sampling)

### **Analytics Service:**
- `src/quality_checks.py` (3 new validations)
- `src/validators.py` (variance validators)

### **Supporting:**
- `src/aact_utils.py` (helper functions for AACT access)
- `tests/test_variance.py` (new test suite)

---

## ⚠️ **RISKS & MITIGATION**

| Risk | Mitigation |
|------|-----------|
| Over-variance (unrealistic extremes) | Add clipping to observed min/max from AACT |
| Performance impact | Cache AACT stats in memory, pre-sample distributions |
| Breaking existing tests | Update test expectations to account for variance |
| Backwards compatibility | Add `enable_variance=True` flag to generators |

---

## 💡 **QUICK WINS**

Want to see immediate impact? Implement **just Enhancement 1 & 7** (dropout variance + validation):

**Effort:** 2-3 hours  
**Impact:** Massive - transforms all trials from identical to realistic

```python
# 30 lines of code:
def sample_dropout_rate(...): # 10 lines
def validate_dropout_variance(...): # 20 lines
```

---

## 🎉 **CONCLUSION**

Your AACT enhancements extracted the "DNA" of real trials. Now you need to inject that DNA into your synthetic data generators. This plan provides a clear roadmap from "statistically accurate" to "indistinguishable from real trials."

**Recommended Start:** Phase 1 (Variance Features) - highest impact, medium effort.
