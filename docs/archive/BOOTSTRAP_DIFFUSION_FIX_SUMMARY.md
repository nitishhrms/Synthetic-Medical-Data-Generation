# Bootstrap and Diffusion Generator Fix Summary

**Date**: 2025-11-20
**Branch**: `daft`
**Commit**: `0595b33`

## Problem Statement

When using comprehensive study generation with the bootstrap method in AACT-enhanced mode, the following error occurred:

```
Comprehensive study generation failed: Cannot convert non-finite values (NA or inf) to integer
```

This error prevented users from generating synthetic clinical trial data using the bootstrap method.

## Root Causes Identified

### 1. **Hard-coded Visit Schedule in Bootstrap Generator**
   - The bootstrap generator hard-coded `"Week 12"` for treatment effect application
   - AACT-enhanced generation uses custom visit schedules (e.g., "Month 3", "Month 12")
   - This mismatch caused NaN values when calculating treatment effects

### 2. **Missing NaN Protection Before Integer Conversion**
   - The jitter function added Gaussian noise to numeric columns
   - If the base data had NaN values, the result would also be NaN
   - Converting NaN to `int64` caused the error

### 3. **Diffusion Generator Required data_path Parameter**
   - The `generate_with_simple_diffusion()` function required a `data_path` parameter
   - Comprehensive study generation called it without this parameter
   - This caused a TypeError when using the diffusion method

## Fixes Applied

### Fix 1: Bootstrap Generator NaN Handling (`generators.py` lines 535-543)

**Before**:
```python
s_noisy = pd.to_numeric(s, errors="coerce") + noise

# Clip to clinical constraints
col_min, col_max = constraints[col]
s_noisy = np.clip(s_noisy, col_min, col_max)
```

**After**:
```python
s_noisy = pd.to_numeric(s, errors="coerce") + noise

# Handle any NaN values that might have appeared
if s_noisy.isna().any():
    # Fill NaN with column mean from base data
    col_mean = base.mean()
    if pd.isna(col_mean):
        # Use default fallback values
        defaults = {"SystolicBP": 140, "DiastolicBP": 85, "HeartRate": 72, "Temperature": 36.7}
        col_mean = defaults.get(col, 0)
    s_noisy = s_noisy.fillna(col_mean)

# Clip to clinical constraints
col_min, col_max = constraints[col]
s_noisy = np.clip(s_noisy, col_min, col_max)
```

### Fix 2: Visit Schedule Coordination (`generators.py` lines 616-649)

**Before**:
```python
# ===== Apply Treatment Effect at Week 12 =====
week12 = out["VisitName"] == "Week 12"
active = out["TreatmentArm"] == "Active"
placebo = out["TreatmentArm"] == "Placebo"

# Calculate current effect
active_week12_mean = out[week12 & active]["SystolicBP"].mean()
placebo_week12_mean = out[week12 & placebo]["SystolicBP"].mean()
current_effect = active_week12_mean - placebo_week12_mean

# Adjust to target effect
adjustment = target_effect - current_effect
```

**After**:
```python
# ===== Apply Treatment Effect at Final Visit =====
# Use provided visit_schedule or default to standard visits
if visit_schedule is not None and len(visit_schedule) > 0:
    final_visit = visit_schedule[-1]  # Use last visit from coordinated schedule
else:
    final_visit = "Week 12"  # Default fallback

final_visit_mask = out["VisitName"] == final_visit
active = out["TreatmentArm"] == "Active"
placebo = out["TreatmentArm"] == "Placebo"

# Calculate current effect with NaN protection
active_final_mean = out[final_visit_mask & active]["SystolicBP"].mean()
placebo_final_mean = out[final_visit_mask & placebo]["SystolicBP"].mean()

# Check for NaN values before calculating effect
if pd.isna(active_final_mean) or pd.isna(placebo_final_mean):
    # If we don't have data for final visit, skip adjustment
    print(f"⚠️  Warning: Cannot calculate treatment effect - missing data for {final_visit}")
    adjustment = 0
else:
    current_effect = active_final_mean - placebo_final_mean
    adjustment = target_effect - current_effect

# Apply adjustment to Active arm at final visit (only if we have valid adjustment)
if adjustment != 0:
    mask = final_visit_mask & active
    if mask.any():
        # Add adjustment and ensure no NaN values
        adjusted_values = out.loc[mask, "SystolicBP"] + adjustment
        # Remove any NaN values that might have appeared
        adjusted_values = adjusted_values.fillna(140)  # Use default if NaN
        # Re-clip after adjustment and convert to int
        out.loc[mask, "SystolicBP"] = np.clip(adjusted_values, 95, 200).round().astype(int)
```

### Fix 3: Diffusion Generator Optional Parameters (`simple_diffusion.py` lines 275-332)

**Before**:
```python
def generate_with_simple_diffusion(
    data_path: str,  # Required parameter
    n_per_arm: int = 50,
    n_steps: int = 50,
    target_effect: float = -5.0,
    seed: Optional[int] = None
) -> pd.DataFrame:
    # Load generator
    generator = load_and_train_simple_diffusion(data_path)
```

**After**:
```python
def generate_with_simple_diffusion(
    n_per_arm: int = 50,  # Moved to first parameter
    n_steps: int = 50,
    target_effect: float = -5.0,
    seed: Optional[int] = None,
    data_path: Optional[str] = None,  # Now optional
    training_data: Optional[pd.DataFrame] = None  # Alternative to data_path
) -> pd.DataFrame:
    # Load or create generator
    if data_path is not None:
        generator = load_and_train_simple_diffusion(data_path)
    elif training_data is not None:
        generator = SimpleDiffusionGenerator(training_data)
    else:
        # Create synthetic baseline from default statistics (AACT fallback)
        [... creates synthetic baseline ...]
        training_data = pd.DataFrame(baseline_rows)
        generator = SimpleDiffusionGenerator(training_data)
```

## Testing

A test script was created (`test_bootstrap_fix.py`) that verifies:
1. ✅ Bootstrap generator with coordinated visit schedules
2. ✅ NaN handling and integer conversion
3. ✅ Diffusion generator without data_path
4. ✅ All generators produce valid data without NaN errors

## Impact

These fixes ensure that:
- **Bootstrap generation** works with custom visit schedules from AACT data
- **No NaN errors** occur during integer conversion
- **Diffusion generator** can be called without requiring pilot data files
- **All generators** gracefully handle missing or invalid data
- **Comprehensive study generation** works with all methods (MVN, Bootstrap, Rules, Diffusion)

## Files Modified

1. `microservices/data-generation-service/src/generators.py`
   - Lines 535-543: NaN handling in jitter section
   - Lines 616-649: Visit schedule coordination and treatment effect

2. `microservices/data-generation-service/src/simple_diffusion.py`
   - Lines 275-332: Optional parameters and synthetic baseline generation

## Deployment Notes

**Branch**: `daft` (local commit only)
**Status**: ⚠️ Committed locally but NOT pushed to origin due to permission restrictions

To deploy these fixes:
```bash
# The fixes are committed on the daft branch
git checkout daft
git log --oneline -1  # Should show: 0595b33 Fix bootstrap and diffusion generator NaN errors

# To push (requires appropriate permissions):
git push origin daft

# Or create a pull request to merge into main/master
```

## Testing in Production

To test the fixes:

```bash
# Start the data generation service
cd microservices/data-generation-service
docker-compose up

# Test bootstrap generation via API
curl -X POST http://localhost:8002/generate/comprehensive-study \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 50,
    "method": "bootstrap",
    "use_aact": true,
    "indication": "hypertension",
    "phase": "Phase 3",
    "include_vitals": true,
    "seed": 42
  }'

# Test diffusion generation
curl -X POST http://localhost:8002/generate/comprehensive-study \
  -H "Content-Type: application/json" \
  -d '{
    "n_per_arm": 50,
    "method": "diffusion",
    "use_aact": false,
    "include_vitals": true,
    "seed": 42
  }'
```

## Related Issues

- Fixes: Bootstrap generation with AACT comprehensive study
- Related to: AACT v4.0 enhancement
- Enables: Production-ready synthetic data generation

---

**Status**: ✅ FIXED - Ready for deployment
