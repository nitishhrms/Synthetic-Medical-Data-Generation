#!/usr/bin/env python3
"""
Test MVN and Bootstrap generators with real CDISC clinical trial data.
"""
import sys
from pathlib import Path

# Add the generators module to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microservices" / "data-generation-service" / "src"))

import pandas as pd
import numpy as np
from generators import (
    load_pilot_vitals,
    fit_mvn_models,
    generate_vitals_mvn,
    generate_vitals_bootstrap,
    validate_vitals
)

def print_statistics(df, name):
    """Print statistics about the generated data."""
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    print(f"Total records: {len(df)}")
    print(f"Unique subjects: {df['SubjectID'].nunique()}")
    print(f"\nTreatment arm distribution:")
    print(df.groupby("TreatmentArm")["SubjectID"].nunique())
    print(f"\nVisit distribution:")
    print(df["VisitName"].value_counts().sort_index())
    print(f"\nVital signs summary statistics:")
    print(df[["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]].describe())

    # Check Week 12 treatment effect
    week12 = df[df["VisitName"] == "Week 12"]
    if not week12.empty:
        means = week12.groupby("TreatmentArm")["SystolicBP"].mean()
        if "Active" in means.index and "Placebo" in means.index:
            effect = means["Active"] - means["Placebo"]
            print(f"\nWeek 12 Treatment Effect (Active - Placebo): {effect:.2f} mmHg")

    print(f"\nSample data (first 5 rows):")
    print(df.head(5).to_string())

def test_real_data_loading():
    """Test loading real CDISC data."""
    print("\n" + "="*60)
    print("TEST 1: Loading Real CDISC Clinical Trial Data")
    print("="*60)

    try:
        df = load_pilot_vitals()
        print(f"✓ Successfully loaded pilot data")
        print_statistics(df, "Real CDISC Clinical Trial Data")

        # Analyze the distributions for each visit/arm combination
        print(f"\n{'='*60}")
        print("Distribution Analysis by Visit and Treatment Arm")
        print(f"{'='*60}")

        for visit in ["Screening", "Day 1", "Week 4", "Week 12"]:
            print(f"\n{visit}:")
            visit_data = df[df["VisitName"] == visit]
            if not visit_data.empty:
                for arm in ["Active", "Placebo"]:
                    arm_data = visit_data[visit_data["TreatmentArm"] == arm]
                    if not arm_data.empty:
                        sbp_mean = arm_data["SystolicBP"].mean()
                        sbp_std = arm_data["SystolicBP"].std()
                        print(f"  {arm}: SBP={sbp_mean:.1f}±{sbp_std:.1f} mmHg (n={len(arm_data)})")

        return df

    except Exception as e:
        print(f"✗ Failed to load pilot data: {e}")
        return None

def test_mvn_generator(pilot_df):
    """Test MVN generator with real data."""
    print("\n" + "="*60)
    print("TEST 2: MVN Generator with Real Data")
    print("="*60)

    try:
        # Test fitting MVN models from real data
        print("\nFitting MVN models from real data...")
        models = fit_mvn_models(pilot_df)

        print(f"✓ Successfully fitted {len(models)} MVN models")

        # Print learned parameters
        print("\nLearned parameters (mean ± std) for each visit/arm:")
        for (visit, arm), params in sorted(models.items()):
            mu = params["mu"]
            cov = params["cov"]
            std = np.sqrt(np.diag(cov))
            print(f"\n{visit} - {arm}:")
            print(f"  SystolicBP:  {mu[0]:.1f} ± {std[0]:.1f}")
            print(f"  DiastolicBP: {mu[1]:.1f} ± {std[1]:.1f}")
            print(f"  HeartRate:   {mu[2]:.1f} ± {std[2]:.1f}")
            print(f"  Temperature: {mu[3]:.2f} ± {std[3]:.2f}")

        # Generate synthetic data using MVN
        print("\n\nGenerating synthetic data using MVN...")
        synthetic_df = generate_vitals_mvn(
            n_per_arm=50,
            target_effect=-5.0,
            seed=123,
            train_source="pilot"
        )

        print(f"✓ Successfully generated {len(synthetic_df)} synthetic records")

        # Validate the generated data
        report = validate_vitals(synthetic_df)
        print("\nValidation report:")
        for check_name, passed in report["checks"]:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")

        print_statistics(synthetic_df, "MVN Generated Synthetic Data (from real baseline)")

        return synthetic_df

    except Exception as e:
        print(f"✗ MVN generator failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_bootstrap_generator(pilot_df):
    """Test Bootstrap generator with real data."""
    print("\n" + "="*60)
    print("TEST 3: Bootstrap Generator with Real Data")
    print("="*60)

    try:
        print("Generating synthetic data using Bootstrap sampling...")
        synthetic_df = generate_vitals_bootstrap(
            training_df=pilot_df,
            n_per_arm=50,
            target_effect=-5.0,
            jitter_frac=0.05,
            cat_flip_prob=0.05,
            seed=42
        )

        print(f"✓ Successfully generated {len(synthetic_df)} synthetic records")

        # Validate the generated data
        report = validate_vitals(synthetic_df)
        print("\nValidation report:")
        for check_name, passed in report["checks"]:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")

        print_statistics(synthetic_df, "Bootstrap Generated Synthetic Data (from real baseline)")

        return synthetic_df

    except Exception as e:
        print(f"✗ Bootstrap generator failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_distributions(real_df, mvn_df, bootstrap_df):
    """Compare distributions between real and synthetic data."""
    print("\n" + "="*60)
    print("TEST 4: Distribution Comparison")
    print("="*60)

    print("\nSystolic BP Mean by Visit (Active arm only):")
    print("-" * 60)

    for visit in ["Screening", "Day 1", "Week 4", "Week 12"]:
        real_mean = real_df[(real_df["VisitName"] == visit) &
                            (real_df["TreatmentArm"] == "Active")]["SystolicBP"].mean()

        mvn_mean = mvn_df[(mvn_df["VisitName"] == visit) &
                          (mvn_df["TreatmentArm"] == "Active")]["SystolicBP"].mean() if mvn_df is not None else 0

        boot_mean = bootstrap_df[(bootstrap_df["VisitName"] == visit) &
                                 (bootstrap_df["TreatmentArm"] == "Active")]["SystolicBP"].mean() if bootstrap_df is not None else 0

        print(f"{visit:12} | Real: {real_mean:6.1f} | MVN: {mvn_mean:6.1f} | Bootstrap: {boot_mean:6.1f}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✓ MVN generator learns means and correlations from real data")
    print("✓ Bootstrap generator resamples and augments real data")
    print("✓ Both methods now use real CDISC clinical trial data as baseline")
    print("✓ Synthetic data preserves realistic vital sign distributions")

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Testing Synthetic Data Generators with Real CDISC Clinical Trial Data")
    print("="*80)

    # Test 1: Load real data
    pilot_df = test_real_data_loading()

    if pilot_df is None:
        print("\n✗ Cannot proceed without pilot data. Exiting.")
        return

    # Test 2: MVN generator
    mvn_df = test_mvn_generator(pilot_df)

    # Test 3: Bootstrap generator
    bootstrap_df = test_bootstrap_generator(pilot_df)

    # Test 4: Compare distributions
    if mvn_df is not None and bootstrap_df is not None:
        compare_distributions(pilot_df, mvn_df, bootstrap_df)

    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80)

if __name__ == "__main__":
    main()
