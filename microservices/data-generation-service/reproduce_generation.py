
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

# Mocking the generator function from generators.py
def generate_vitals_mvn_aact_mock(
    n_per_arm: int = 50,
    subject_ids: Optional[List[str]] = None,
    treatment_arms: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    
    if subject_ids is not None:
        all_subjects = subject_ids
    else:
        subj_active = [f"RA001-{i:03d}" for i in range(1, n_per_arm + 1)]
        subj_placebo = [f"RA001-{i:03d}" for i in range(n_per_arm + 1, 2 * n_per_arm + 1)]
        all_subjects = subj_active + subj_placebo

    if treatment_arms is None:
        treatment_arms = {}
        for i, subj in enumerate(all_subjects):
            treatment_arms[subj] = "Active" if i < n_per_arm else "Placebo"

    rows = []
    visit_names = ["Screening", "Day 1"] # Simplified
    
    print(f"DEBUG: Generating for {len(all_subjects)} subjects")
    active_count = 0
    placebo_count = 0
    
    for sid in all_subjects:
        arm = treatment_arms[sid]
        if arm == "Active": active_count += 1
        if arm == "Placebo": placebo_count += 1
        
        for visit in visit_names:
            rows.append([sid, visit, arm])

    print(f"DEBUG: Generator Internal Counts - Active: {active_count}, Placebo: {placebo_count}")
    
    df = pd.DataFrame(rows, columns=["SubjectID", "VisitName", "TreatmentArm"])
    return df

# Mocking the main.py logic
def run_simulation(n_per_arm: int):
    print(f"\n--- Running Simulation with n_per_arm={n_per_arm} ---")
    total_subjects = n_per_arm * 2
    print(f"Total Subjects: {total_subjects}")

    # 1.1 Generate Subject IDs
    subject_ids = [f"RA001-{i:03d}" for i in range(1, total_subjects + 1)]
    print(f"Subject IDs generated: {len(subject_ids)}")

    # 1.2 Assign Treatment Arms
    treatment_arms = {}
    for i, subj in enumerate(subject_ids):
        treatment_arms[subj] = "Active" if i < n_per_arm else "Placebo"
    
    # Verify treatment arms distribution
    active_arms = sum(1 for v in treatment_arms.values() if v == "Active")
    placebo_arms = sum(1 for v in treatment_arms.values() if v == "Placebo")
    print(f"Treatment Arms Map: Active={active_arms}, Placebo={placebo_arms}")

    # Call generator
    df = generate_vitals_mvn_aact_mock(
        n_per_arm=n_per_arm,
        subject_ids=subject_ids,
        treatment_arms=treatment_arms
    )
    
    # Analyze output
    print("Output DataFrame Stats:")
    print(df.groupby(["VisitName", "TreatmentArm"]).size())

# Test cases
run_simulation(50)
run_simulation(202)
