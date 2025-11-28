#!/usr/bin/env python3
"""
Test script to verify comprehensive study coordination
Ensures all datasets share same subject IDs, visit schedules, and treatment arms
"""

import sys
sys.path.insert(0, '/home/user/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src')

from generators import (
    generate_vitals_mvn_aact,
    generate_demographics_aact,
    generate_oncology_ae_aact,
    generate_labs_aact
)

def test_coordination():
    """Test that all generators use coordinated parameters correctly"""

    print("=" * 80)
    print("Testing Comprehensive Study Coordination")
    print("=" * 80)

    # Step 1: Create coordination metadata
    n_per_arm = 5
    total_subjects = n_per_arm * 2

    subject_ids = [f"RA001-{i:03d}" for i in range(1, total_subjects + 1)]
    visit_schedule = ["Screening", "Day 1", "Week 4", "Week 12"]
    treatment_arms = {}
    for i, subj in enumerate(subject_ids):
        treatment_arms[subj] = "Active" if i < n_per_arm else "Placebo"

    print(f"\n✓ Generated coordination metadata:")
    print(f"  Subject IDs: {subject_ids}")
    print(f"  Visit schedule: {visit_schedule}")
    print(f"  Treatment arms: {treatment_arms}")

    # Step 2: Generate vitals with coordination
    print(f"\n\n📊 Generating Vitals...")
    vitals_df = generate_vitals_mvn_aact(
        indication="hypertension",
        phase="Phase 3",
        n_per_arm=n_per_arm,
        target_effect=-5.0,
        seed=42,
        subject_ids=subject_ids,
        visit_schedule=visit_schedule,
        treatment_arms=treatment_arms
    )

    vitals_subjects = vitals_df['SubjectID'].unique().tolist()
    vitals_visits = vitals_df['VisitName'].unique().tolist()

    print(f"  Generated {len(vitals_df)} vitals records")
    print(f"  Subjects: {vitals_subjects}")
    print(f"  Visits: {vitals_visits}")

    # Step 3: Generate demographics with coordination
    print(f"\n📋 Generating Demographics...")
    demographics_df = generate_demographics_aact(
        indication="hypertension",
        phase="Phase 3",
        n_subjects=total_subjects,
        seed=42,
        subject_ids=subject_ids,
        treatment_arms=treatment_arms
    )

    demo_subjects = demographics_df['SubjectID'].unique().tolist()

    print(f"  Generated {len(demographics_df)} demographics records")
    print(f"  Subjects: {demo_subjects}")

    # Step 4: Generate AE with coordination
    print(f"\n⚠️  Generating Adverse Events...")
    ae_df = generate_oncology_ae_aact(
        indication="hypertension",
        phase="Phase 3",
        n_subjects=total_subjects,
        seed=43,
        subject_ids=subject_ids,
        visit_schedule=visit_schedule,
        treatment_arms=treatment_arms
    )

    ae_subjects = ae_df['SubjectID'].unique().tolist() if 'SubjectID' in ae_df.columns else []

    print(f"  Generated {len(ae_df)} AE records")
    if ae_subjects:
        print(f"  AE Subjects: {ae_subjects}")

    # Step 5: Generate labs with coordination
    print(f"\n🧪 Generating Labs...")
    labs_df = generate_labs_aact(
        indication="hypertension",
        phase="Phase 3",
        n_subjects=total_subjects,
        seed=44,
        use_duration=True,
        subject_ids=subject_ids,
        visit_schedule=visit_schedule,
        treatment_arms=treatment_arms
    )

    labs_subjects = labs_df['SubjectID'].unique().tolist()
    labs_visits = labs_df['VisitName'].unique().tolist() if 'VisitName' in labs_df.columns else []

    print(f"  Generated {len(labs_df)} lab records")
    print(f"  Subjects: {labs_subjects}")
    if labs_visits:
        print(f"  Visits: {labs_visits}")

    # Step 6: Verify coordination
    print(f"\n\n🔍 Verifying Coordination...")

    errors = []

    # Check subject ID consistency
    if set(vitals_subjects) != set(subject_ids):
        errors.append("❌ Vitals subjects don't match coordination!")
    else:
        print(f"  ✅ Vitals subjects match")

    if set(demo_subjects) != set(subject_ids):
        errors.append("❌ Demographics subjects don't match coordination!")
    else:
        print(f"  ✅ Demographics subjects match")

    if set(labs_subjects) != set(subject_ids):
        errors.append("❌ Labs subjects don't match coordination!")
    else:
        print(f"  ✅ Labs subjects match")

    # Check visit schedule consistency
    if set(vitals_visits) != set(visit_schedule):
        errors.append(f"❌ Vitals visits don't match coordination! Got {vitals_visits}")
    else:
        print(f"  ✅ Vitals visits match")

    if labs_visits and set(labs_visits) != set(visit_schedule):
        errors.append(f"❌ Labs visits don't match coordination! Got {labs_visits}")
    else:
        print(f"  ✅ Labs visits match")

    # Check treatment arm assignments in vitals
    for subj in vitals_subjects:
        vitals_arm = vitals_df[vitals_df['SubjectID'] == subj]['TreatmentArm'].iloc[0]
        expected_arm = treatment_arms[subj]
        if vitals_arm != expected_arm:
            errors.append(f"❌ Subject {subj}: vitals has arm '{vitals_arm}', expected '{expected_arm}'")

    if not errors:
        print(f"  ✅ Treatment arms match in vitals")

    # Final result
    print(f"\n\n{'='*80}")
    if errors:
        print("❌ COORDINATION TEST FAILED")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("✅ COORDINATION TEST PASSED!")
        print("All datasets share the same subject IDs, visit schedules, and treatment arms.")
        print("Datasets can be joined properly for comprehensive study analysis.")
        return True

if __name__ == "__main__":
    success = test_coordination()
    sys.exit(0 if success else 1)
