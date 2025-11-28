#!/usr/bin/env python3
"""
Test script to verify bootstrap and diffusion generator fixes

This script tests:
1. Bootstrap generator with NaN protection
2. Diffusion generator without data_path
3. Visit schedule coordination
"""

import sys
import os
sys.path.insert(0, '/home/user/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src')

import pandas as pd
import numpy as np
from generators import generate_vitals_bootstrap, generate_vitals_bootstrap_aact

def test_bootstrap_with_coordination():
    """Test bootstrap generator with coordinated parameters"""
    print("=" * 60)
    print("TEST 1: Bootstrap with Visit Schedule Coordination")
    print("=" * 60)

    # Create a small baseline dataset
    baseline_rows = []
    for i in range(10):
        sid = f"BASE-{i+1:03d}"
        arm = "Active" if i < 5 else "Placebo"
        for visit in ["Screening", "Day 1", "Month 3", "Month 12"]:
            baseline_rows.append({
                'SubjectID': sid,
                'VisitName': visit,
                'TreatmentArm': arm,
                'SystolicBP': int(np.clip(np.random.normal(140, 15), 95, 200)),
                'DiastolicBP': int(np.clip(np.random.normal(85, 10), 55, 130)),
                'HeartRate': int(np.clip(np.random.normal(72, 10), 50, 120)),
                'Temperature': float(np.clip(np.random.normal(36.7, 0.3), 35.0, 40.0))
            })

    baseline_df = pd.DataFrame(baseline_rows)

    # Setup coordination parameters
    subject_ids = [f"RA001-{i:03d}" for i in range(1, 21)]
    visit_schedule = ["Screening", "Day 1", "Month 3", "Month 12"]
    treatment_arms = {subj: "Active" if i < 10 else "Placebo"
                     for i, subj in enumerate(subject_ids)}

    try:
        result = generate_vitals_bootstrap(
            training_df=baseline_df,
            n_per_arm=10,
            target_effect=-5.0,
            seed=42,
            subject_ids=subject_ids,
            visit_schedule=visit_schedule,
            treatment_arms=treatment_arms
        )

        print(f"✓ Generated {len(result)} records successfully")
        print(f"✓ Subjects: {result['SubjectID'].nunique()}")
        print(f"✓ Visits: {result['VisitName'].unique().tolist()}")
        print(f"✓ Treatment Arms: {result['TreatmentArm'].value_counts().to_dict()}")

        # Check for NaN values
        nan_counts = result.isna().sum()
        if nan_counts.any():
            print(f"✗ Found NaN values:")
            print(nan_counts[nan_counts > 0])
            return False
        else:
            print("✓ No NaN values found")

        # Check data types
        if result['SystolicBP'].dtype != np.int64:
            print(f"✗ SystolicBP has wrong dtype: {result['SystolicBP'].dtype}")
            return False
        else:
            print("✓ SystolicBP has correct dtype (int64)")

        print("\n✅ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"\n✗ Test 1 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_bootstrap_aact():
    """Test AACT-enhanced bootstrap generator"""
    print("=" * 60)
    print("TEST 2: AACT-Enhanced Bootstrap Generator")
    print("=" * 60)

    try:
        # This should create a synthetic baseline from AACT statistics (or defaults)
        result = generate_vitals_bootstrap_aact(
            indication="hypertension",
            phase="Phase 3",
            n_per_arm=10,
            target_effect=-5.0,
            seed=42
        )

        print(f"✓ Generated {len(result)} records successfully")
        print(f"✓ Subjects: {result['SubjectID'].nunique()}")

        # Check for NaN values
        nan_counts = result.isna().sum()
        if nan_counts.any():
            print(f"✗ Found NaN values:")
            print(nan_counts[nan_counts > 0])
            return False
        else:
            print("✓ No NaN values found")

        # Check data types
        int_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate']
        for col in int_cols:
            if result[col].dtype != np.int64:
                print(f"✗ {col} has wrong dtype: {result[col].dtype}")
                return False
        print(f"✓ All integer columns have correct dtypes")

        print("\n✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"\n✗ Test 2 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_diffusion_without_data_path():
    """Test diffusion generator without data_path"""
    print("=" * 60)
    print("TEST 3: Diffusion Generator Without data_path")
    print("=" * 60)

    try:
        from simple_diffusion import generate_with_simple_diffusion

        result = generate_with_simple_diffusion(
            n_per_arm=10,
            n_steps=10,  # Use fewer steps for faster testing
            target_effect=-5.0,
            seed=42
        )

        print(f"✓ Generated {len(result)} records successfully")
        print(f"✓ Subjects: {result['SubjectID'].nunique()}")

        # Check for NaN values
        nan_counts = result.isna().sum()
        if nan_counts.any():
            print(f"✗ Found NaN values:")
            print(nan_counts[nan_counts > 0])
            return False
        else:
            print("✓ No NaN values found")

        print("\n✅ Test 3 PASSED\n")
        return True

    except Exception as e:
        print(f"\n✗ Test 3 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BOOTSTRAP AND DIFFUSION GENERATOR FIX VERIFICATION")
    print("=" * 60 + "\n")

    tests = [
        test_bootstrap_with_coordination,
        test_bootstrap_aact,
        test_diffusion_without_data_path
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n🎉 ALL TESTS PASSED! 🎉")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
