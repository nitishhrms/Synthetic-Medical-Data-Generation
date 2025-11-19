"""
SyntheticTrial SDK - Quick Start Example

This example demonstrates the basic usage of the SyntheticTrial SDK
"""

from synthetictrial import SyntheticTrial
import pandas as pd


def main():
    # Initialize the client
    print("🚀 Initializing SyntheticTrial client...")
    client = SyntheticTrial(base_url="http://localhost:8002")

    # Generate a realistic trial
    print("\n📊 Generating realistic trial with 50 subjects per arm...")
    trial = client.trials.generate(
        indication="Hypertension",
        n_per_arm=50,
        method="realistic",
        site_heterogeneity=0.4,
        dropout_rate=0.18,
        missing_data_rate=0.10,
        enrollment_pattern="exponential",
        seed=42
    )

    # Display results
    print(f"\n✅ Trial generated successfully!")
    print(f"   Total subjects: {trial.n_subjects}")
    print(f"   Total vitals records: {trial.n_records}")
    print(f"   Adverse events: {len(trial.adverse_events)}")
    print(f"   Protocol deviations: {len(trial.protocol_deviations)}")
    print(f"   Realism score: {trial.realism_score:.1f}/100")

    # Show sample data
    print(f"\n📋 Sample vitals data:")
    print(trial.vitals.head(10))

    # Analyze Week-12 efficacy
    print("\n📈 Analyzing Week-12 efficacy endpoint...")
    stats = client.analytics.week12_statistics(trial.vitals)

    print(f"\n📊 Statistical Results:")
    print(f"   Treatment effect: {stats.treatment_effect['difference']:.2f} mmHg")
    print(f"   95% CI: [{stats.treatment_effect['ci_95_lower']:.2f}, {stats.treatment_effect['ci_95_upper']:.2f}]")
    print(f"   P-value: {stats.p_value:.4f}")
    print(f"   Statistically significant: {'Yes ✓' if stats.is_significant else 'No ✗'}")

    # Export data
    print("\n💾 Exporting data to CSV...")
    trial.to_csv(prefix="example_trial")
    print("   Files created:")
    print("   - example_trial_vitals.csv")
    print("   - example_trial_adverse_events.csv")
    print("   - example_trial_deviations.csv")

    print("\n✨ Complete! Check the generated CSV files.")


if __name__ == "__main__":
    main()
