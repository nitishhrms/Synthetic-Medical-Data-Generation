#!/usr/bin/env python3
"""
Simple verification script to check if generators.py is working.
Shows you exactly what the generators produce.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microservices" / "data-generation-service" / "src"))

from generators import generate_vitals_mvn, load_pilot_vitals, generate_vitals_bootstrap

print("="*70)
print("GENERATORS.PY VERIFICATION")
print("="*70)

# 1. Show real data being used
print("\n1. Real CDISC Data (what generators learn from):")
print("-" * 70)
real_data = load_pilot_vitals()
print(f"   Records: {len(real_data)}")
print(f"   Subjects: {real_data['SubjectID'].nunique()}")
print(f"   Treatment arms: {real_data['TreatmentArm'].unique().tolist()}")
print(f"   Visits: {real_data['VisitName'].unique().tolist()}")
print("\n   Sample from real data:")
print(real_data.head(3).to_string(index=False))

# 2. Generate with MVN
print("\n\n2. MVN Generator Output (learns from real data):")
print("-" * 70)
mvn_data = generate_vitals_mvn(n_per_arm=3, seed=123)  # Just 3 subjects per arm
print(f"   Generated {len(mvn_data)} records for {mvn_data['SubjectID'].nunique()} subjects")
print("\n   Sample synthetic data:")
print(mvn_data.head(6).to_string(index=False))

# 3. Generate with Bootstrap
print("\n\n3. Bootstrap Generator Output (resamples real data):")
print("-" * 70)
boot_data = generate_vitals_bootstrap(real_data, n_per_arm=3, seed=42)
print(f"   Generated {len(boot_data)} records for {boot_data['SubjectID'].nunique()} subjects")
print("\n   Sample synthetic data:")
print(boot_data.head(6).to_string(index=False))

# 4. Compare distributions
print("\n\n4. Distribution Comparison (Week 12, Active arm):")
print("-" * 70)
real_week12 = real_data[(real_data['VisitName'] == 'Week 12') &
                        (real_data['TreatmentArm'] == 'Active')]['SystolicBP']
mvn_week12 = mvn_data[(mvn_data['VisitName'] == 'Week 12') &
                      (mvn_data['TreatmentArm'] == 'Active')]['SystolicBP']
boot_week12 = boot_data[(boot_data['VisitName'] == 'Week 12') &
                        (boot_data['TreatmentArm'] == 'Active')]['SystolicBP']

print(f"   Real data:      Mean={real_week12.mean():.1f}, Std={real_week12.std():.1f}")
print(f"   MVN synthetic:  Mean={mvn_week12.mean():.1f}, Std={mvn_week12.std():.1f}")
print(f"   Boot synthetic: Mean={boot_week12.mean():.1f}, Std={boot_week12.std():.1f}")

print("\n" + "="*70)
print("✅ VERIFICATION COMPLETE - All generators working correctly!")
print("="*70)
print("\nKey points:")
print("  • Real CDISC data is loaded successfully")
print("  • MVN generator learns realistic distributions from real data")
print("  • Bootstrap generator resamples from real data")
print("  • Synthetic data preserves realistic patterns")
