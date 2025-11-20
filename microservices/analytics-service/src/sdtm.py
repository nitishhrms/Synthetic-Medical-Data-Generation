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


def export_to_sdtm_lb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Export laboratory data to SDTM LB (Laboratory) domain

    Converts lab data to CDISC SDTM LB domain format following SDTM-IG v3.4.

    Args:
        df: Laboratory DataFrame with columns:
            - SubjectID: Unique subject identifier
            - VisitName: Visit name
            - TestName: Laboratory test name (e.g., "ALT", "Creatinine")
            - TestValue: Numeric test result
            - TestUnit: Unit of measurement
            - TreatmentArm (optional): Treatment arm assignment

    Returns:
        SDTM LB DataFrame with standard variables
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # CDISC SDTM LBTESTCD mapping (standardized test codes)
    test_code_mapping = {
        "ALT": ("ALT", "Alanine Aminotransferase"),
        "AST": ("AST", "Aspartate Aminotransferase"),
        "Bilirubin": ("BILI", "Bilirubin"),
        "Creatinine": ("CREAT", "Creatinine"),
        "eGFR": ("EGFR", "Estimated Glomerular Filtration Rate"),
        "Hemoglobin": ("HGB", "Hemoglobin"),
        "WBC": ("WBC", "White Blood Cell Count"),
        "Platelets": ("PLAT", "Platelet Count"),
        "Glucose": ("GLUC", "Glucose"),
        "Sodium": ("SODIUM", "Sodium"),
        "Potassium": ("K", "Potassium"),
        "Chloride": ("CL", "Chloride"),
        "BUN": ("BUN", "Blood Urea Nitrogen"),
        "Albumin": ("ALB", "Albumin"),
        "Alkaline Phosphatase": ("ALP", "Alkaline Phosphatase")
    }

    # Initialize result list
    rows = []

    # Visit number mapping (assume visits are ordered chronologically)
    visits = sorted(df["VisitName"].unique())
    visit_num_mapping = {visit: idx + 1 for idx, visit in enumerate(visits)}

    for _, r in df.iterrows():
        # Convert SubjectID to USUBJID format
        usubjid = str(r["SubjectID"]).replace("RA001", "RASTUDY")
        subjid = str(r["SubjectID"]).split("-")[-1] if "-" in str(r["SubjectID"]) else str(r["SubjectID"])

        # Get test code and test name
        test_name = r.get("TestName", "")
        if test_name in test_code_mapping:
            lbtestcd, lbtest = test_code_mapping[test_name]
        else:
            # If not in mapping, use the original test name
            lbtestcd = test_name.upper().replace(" ", "")[:8]  # Max 8 chars per SDTM
            lbtest = test_name

        # Get visit information
        visit_name = r.get("VisitName", "")
        visitnum = visit_num_mapping.get(visit_name, 0)

        # Build SDTM LB record
        lb_record = {
            "STUDYID": "RASTUDY",
            "DOMAIN": "LB",
            "USUBJID": usubjid,
            "SUBJID": subjid,
            "LBSEQ": None,  # Sequence number (would be assigned sequentially in production)
            "LBTESTCD": lbtestcd,
            "LBTEST": lbtest,
            "LBCAT": "CHEMISTRY" if lbtestcd in ["ALT", "AST", "BILI", "CREAT", "GLUC", "BUN", "ALB", "ALP"]
                     else "HEMATOLOGY" if lbtestcd in ["HGB", "WBC", "PLAT"]
                     else "URINALYSIS" if lbtestcd == "EGFR"
                     else "CHEMISTRY",
            "LBORRES": str(r.get("TestValue", "")),
            "LBORRESU": r.get("TestUnit", ""),
            "LBSTRESC": str(r.get("TestValue", "")),  # Standardized result (same as LBORRES for numeric)
            "LBSTRESN": float(r.get("TestValue", 0)) if pd.notna(r.get("TestValue")) else None,
            "LBSTRESU": r.get("TestUnit", ""),
            "VISITNUM": visitnum,
            "VISIT": visit_name,
            "LBDTC": "",  # Lab collection date (would come from actual collection dates)
            "LBDY": None  # Study day (would be calculated from RFSTDTC)
        }

        rows.append(lb_record)

    # Create DataFrame with proper column order per SDTM-IG
    columns = [
        "STUDYID", "DOMAIN", "USUBJID", "SUBJID", "LBSEQ",
        "LBTESTCD", "LBTEST", "LBCAT",
        "LBORRES", "LBORRESU", "LBSTRESC", "LBSTRESN", "LBSTRESU",
        "VISITNUM", "VISIT", "LBDTC", "LBDY"
    ]

    sdtm_df = pd.DataFrame(rows, columns=columns)

    # Assign sequence numbers
    sdtm_df["LBSEQ"] = range(1, len(sdtm_df) + 1)

    return sdtm_df
