#!/usr/bin/env python3
"""
Process CDISC pilot data into the format expected by the generators.

Expected output format:
SubjectID, VisitName, TreatmentArm, SystolicBP, DiastolicBP, HeartRate, Temperature
"""
import pandas as pd
import numpy as np
from pathlib import Path

def process_cdisc_data():
    """Process CDISC vital signs and demographics into generator format."""

    data_dir = Path(__file__).parent

    # Load data
    print("Loading CDISC data...")
    vs_df = pd.read_csv(data_dir / "vital_signs.csv")
    dm_df = pd.read_csv(data_dir / "demographics.csv")

    print(f"Loaded {len(vs_df)} vital signs records and {len(dm_df)} demographic records")

    # Extract treatment arms from demographics
    # CDISC uses ACTARM (Actual Treatment Arm)
    subject_arms = dm_df[["USUBJID", "ACTARM"]].dropna()

    # Filter out screen failures and keep only actual treatment arms
    valid_arms = ["Placebo", "Xanomeline Low Dose", "Xanomeline High Dose"]
    subject_arms = subject_arms[subject_arms["ACTARM"].isin(valid_arms)]

    print(f"Found {len(subject_arms)} subjects with valid treatment arms")

    # Process vital signs
    # Pivot VS data so each row has all vitals for one subject/visit
    # VSTESTCD values: DIABP, SYSBP, PULSE, TEMP

    # Filter to relevant test codes
    test_codes = {
        "SYSBP": "SystolicBP",
        "DIABP": "DiastolicBP",
        "PULSE": "HeartRate",
        "TEMP": "Temperature"
    }

    vs_filtered = vs_df[vs_df["VSTESTCD"].isin(test_codes.keys())].copy()

    # Keep only relevant columns
    vs_filtered = vs_filtered[["USUBJID", "VISIT", "VSTESTCD", "VSSTRESN"]]

    # For each subject/visit, take the mean if multiple measurements
    vs_agg = vs_filtered.groupby(["USUBJID", "VISIT", "VSTESTCD"])["VSSTRESN"].mean().reset_index()

    # Pivot to wide format
    vs_wide = vs_agg.pivot_table(
        index=["USUBJID", "VISIT"],
        columns="VSTESTCD",
        values="VSSTRESN"
    ).reset_index()

    # Rename columns
    vs_wide = vs_wide.rename(columns=test_codes)

    # Merge with treatment arms
    result = vs_wide.merge(subject_arms, on="USUBJID", how="inner")

    # Rename columns to match expected format
    result = result.rename(columns={
        "USUBJID": "SubjectID",
        "VISIT": "VisitName",
        "ACTARM": "TreatmentArm"
    })

    # Map CDISC treatment arms to Active/Placebo format
    # For simplicity, we'll map both Xanomeline doses as "Active"
    arm_mapping = {
        "Placebo": "Placebo",
        "Xanomeline Low Dose": "Active",
        "Xanomeline High Dose": "Active"
    }
    result["TreatmentArm"] = result["TreatmentArm"].map(arm_mapping)

    # Standardize visit names to match our system
    # CDISC uses: SCREENING 1, SCREENING 2, BASELINE, WEEK 2, WEEK 4, WEEK 8, WEEK 12, etc.
    visit_mapping = {
        "SCREENING 1": "Screening",
        "SCREENING 2": "Screening",
        "BASELINE": "Day 1",
        "WEEK 2": "Week 4",  # Map to closest visit in our system
        "WEEK 4": "Week 4",
        "WEEK 8": "Week 12",  # Map to closest visit
        "WEEK 12": "Week 12",
        "WEEK 16": "Week 12",
        "WEEK 20": "Week 12",
        "WEEK 24": "Week 12",
        "WEEK 26": "Week 12"
    }

    # Apply visit mapping
    result["VisitName"] = result["VisitName"].str.upper()
    result["VisitName"] = result["VisitName"].replace(visit_mapping)

    # Keep only the visits in our standard set
    standard_visits = ["Screening", "Day 1", "Week 4", "Week 12"]
    result = result[result["VisitName"].isin(standard_visits)]

    # Select final columns in correct order
    final_cols = ["SubjectID", "VisitName", "TreatmentArm",
                  "SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]

    result = result[final_cols]

    # Remove any rows with missing vital signs
    result = result.dropna()

    # Ensure proper data types
    result["SystolicBP"] = result["SystolicBP"].round().astype(int)
    result["DiastolicBP"] = result["DiastolicBP"].round().astype(int)
    result["HeartRate"] = result["HeartRate"].round().astype(int)
    result["Temperature"] = result["Temperature"].round(1).astype(float)

    # Sort by subject and visit
    visit_order = {v: i for i, v in enumerate(standard_visits)}
    result["_visit_order"] = result["VisitName"].map(visit_order)
    result = result.sort_values(["SubjectID", "_visit_order"]).drop(columns=["_visit_order"])
    result = result.reset_index(drop=True)

    # Save processed data
    output_path = data_dir / "pilot_trial.csv"
    result.to_csv(output_path, index=False)

    print(f"\nProcessed data saved to: {output_path}")
    print(f"Total records: {len(result)}")
    print(f"Unique subjects: {result['SubjectID'].nunique()}")
    print(f"\nTreatment arm distribution:")
    print(result.groupby("TreatmentArm")["SubjectID"].nunique())
    print(f"\nVisit distribution:")
    print(result["VisitName"].value_counts().sort_index())
    print(f"\nSample data (first 10 rows):")
    print(result.head(10).to_string())

    return result

if __name__ == "__main__":
    process_cdisc_data()
