"""
SDTM (Study Data Tabulation Model) export functions
Extracted from existing monolithic app.py
"""
import pandas as pd
from typing import List, Dict


def export_to_sdtm_vs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Export vitals to SDTM VS (Vital Signs) domain

    CDISC SDTM standard format for regulatory submission

    Args:
        df: Vitals DataFrame

    Returns:
        SDTM VS DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame()

    rows = []
    for _, r in df.iterrows():
        usubjid = str(r["SubjectID"]).replace("RA001", "RASTUDY")

        # Map each vital sign to SDTM format
        vitals_mapping = [
            ("SystolicBP", "SYSBP", "mmHg"),
            ("DiastolicBP", "DIABP", "mmHg"),
            ("HeartRate", "HR", "bpm"),
            ("Temperature", "TEMP", "C")
        ]

        for src_col, test_code, unit in vitals_mapping:
            rows.append({
                "STUDYID": "RASTUDY",
                "USUBJID": usubjid,
                "VISIT": r["VisitName"],
                "VSTESTCD": test_code,
                "VSORRES": r[src_col],
                "VSORRESU": unit
            })

    return pd.DataFrame(rows, columns=[
        "STUDYID", "USUBJID", "VISIT", "VSTESTCD", "VSORRES", "VSORRESU"
    ])


def export_to_sdtm_dm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Export demographics to SDTM DM (Demographics) domain

    Converts demographics data to CDISC SDTM DM domain format following SDTM-IG v3.4.

    Args:
        df: Demographics DataFrame with columns:
            - SubjectID: Unique subject identifier
            - Age: Age in years
            - Gender: "Male" or "Female"
            - Race: Race category
            - Ethnicity: Ethnicity category
            - TreatmentArm: Treatment arm assignment

    Returns:
        SDTM DM DataFrame with standard variables
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Initialize result list
    rows = []

    for _, r in df.iterrows():
        # Convert SubjectID to USUBJID format
        usubjid = str(r["SubjectID"]).replace("RA001", "RASTUDY")
        subjid = str(r["SubjectID"]).split("-")[-1] if "-" in str(r["SubjectID"]) else str(r["SubjectID"])

        # Map Gender to SEX (M/F/U)
        gender = r.get("Gender", "")
        if gender == "Male":
            sex = "M"
        elif gender == "Female":
            sex = "F"
        else:
            sex = "U"  # Unknown

        # Get treatment arm codes
        treatment_arm = r.get("TreatmentArm", "")
        if treatment_arm == "Active":
            armcd = "ACT"
            arm = "Active Treatment"
        elif treatment_arm == "Placebo":
            armcd = "PBO"
            arm = "Placebo"
        else:
            armcd = "UNK"
            arm = "Unknown"

        # Build SDTM DM record
        dm_record = {
            "STUDYID": "RASTUDY",
            "DOMAIN": "DM",
            "USUBJID": usubjid,
            "SUBJID": subjid,
            "RFSTDTC": "",  # Reference start date (would come from trial data)
            "RFENDTC": "",  # Reference end date (would come from trial data)
            "SITEID": str(r["SubjectID"]).split("-")[0] if "-" in str(r["SubjectID"]) else "SITE001",
            "AGE": int(r.get("Age", 0)) if pd.notna(r.get("Age")) else None,
            "AGEU": "YEARS",
            "SEX": sex,
            "RACE": r.get("Race", ""),
            "ETHNIC": r.get("Ethnicity", ""),
            "ARMCD": armcd,
            "ARM": arm,
            "ACTARMCD": armcd,  # Actual arm (same as planned for this use case)
            "ACTARM": arm
        }

        rows.append(dm_record)

    # Create DataFrame with proper column order per SDTM-IG
    columns = [
        "STUDYID", "DOMAIN", "USUBJID", "SUBJID", "RFSTDTC", "RFENDTC",
        "SITEID", "AGE", "AGEU", "SEX", "RACE", "ETHNIC",
        "ARMCD", "ARM", "ACTARMCD", "ACTARM"
    ]

    return pd.DataFrame(rows, columns=columns)
