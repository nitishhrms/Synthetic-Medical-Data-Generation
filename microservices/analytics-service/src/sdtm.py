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
