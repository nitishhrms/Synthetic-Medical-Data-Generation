# Data Generation Service Enhancements

## Overview

The Data Generation Service has been significantly revamped to leverage real-world clinical trial data from the AACT (Aggregate Analysis of ClinicalTrials.gov) database. These enhancements ensure that synthetic data is not just statistically valid but indistinguishable from real clinical trials.

## Key Enhancements

### 1. Realistic Dropout Variance
- **Before:** Static dropout rate (e.g., 5%) for all trials.
- **After:** Dropout rates are sampled from real-world distributions specific to the indication and phase.
- **Impact:** Trials now exhibit realistic variability (e.g., one trial has 2% dropout, another has 12%).

### 2. Arm-Specific Dropout Rates
- **Before:** Identical dropout rates for Active and Placebo arms.
- **After:** Differential dropout rates based on real trial data (e.g., higher dropout in Active arms due to adverse events).
- **Impact:** More realistic simulation of treatment tolerability.

### 3. Age-Stratified Baseline Vitals
- **Before:** Generic baseline vitals (e.g., 140/85 mmHg) for all subjects.
- **After:** Baseline vitals are adjusted based on patient age using physiological models.
- **Impact:** Realistic correlations between age and vital signs (e.g., higher SBP in older patients).

### 4. Real Treatment Effects
- **Before:** User-specified fixed treatment effect (e.g., -5 mmHg).
- **After:** Treatment effects can be sampled from real trial outcomes for the specific indication.
- **Impact:** Effect sizes match historical data for the drug class.

### 5. Visit-to-Visit Variability
- **Before:** Smooth trajectories.
- **After:** Realistic noise added to visit measurements, including "white-coat" effects at the first visit.
- **Impact:** Data looks like real electronic health record (EHR) data.

## Usage

These enhancements are automatically applied when using the "Enhanced" or "AACT" generation methods.

```http
POST /generate/mvn-aact
{
  "indication": "Hypertension",
  "phase": "Phase 3",
  "n_per_arm": 100,
  "use_enhanced_variance": true
}
```

## Validation

These enhancements are validated by the Analytics Service's new validators:
- **Variance Validation:** Checks if trial-level variance matches AACT distributions.
- **Arm-Specific Validation:** Checks for differential dropout.
- **Age-Vital Correlation:** Verifies physiological relationships.
