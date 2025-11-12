"""
Validation module for clinical trial vitals data
Extracted from existing monolithic app.py
"""
import pandas as pd
from typing import Dict, Any


def validate_vitals(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate vitals data against clinical constraints

    Checks:
    - Required columns present
    - Value ranges (BP, HR, Temperature)
    - Fever count (1-2 rows with temp > 38°C)
    - Fever rows have HR >= 67
    - Week-12 effect approximately -5 mmHg (Active - Placebo)

    Args:
        df: DataFrame with vitals data

    Returns:
        Dict with validation report including:
        - rows: number of rows
        - checks: list of (check_name, passed) tuples
        - week12_effect: calculated effect size
        - fever_count: number of fever rows
    """
    report = {"rows": int(len(df) if df is not None else 0), "checks": []}

    if df is None or df.empty:
        report["checks"] = [
            ("columns_present", False),
            ("ranges_ok", False),
            ("fever_count_1_to_2", False),
            ("fever_hr_link_ok", False),
            ("week12_sbp_effect_approx_-5mmHg", False),
        ]
        report["week12_effect"] = None
        report["fever_count"] = 0
        return report

    # Check 1: Required columns present
    required = ["SubjectID", "VisitName", "TreatmentArm", "SystolicBP",
                "DiastolicBP", "HeartRate", "Temperature"]
    report["checks"].append(("columns_present", all(c in df.columns for c in required)))

    # Check 2: Values in valid ranges
    in_range = (
        pd.to_numeric(df["SystolicBP"], errors="coerce").between(95, 200).all() and
        pd.to_numeric(df["DiastolicBP"], errors="coerce").between(55, 130).all() and
        pd.to_numeric(df["HeartRate"], errors="coerce").between(50, 120).all() and
        pd.to_numeric(df["Temperature"], errors="coerce").between(35.0, 40.0).all()
    )
    report["checks"].append(("ranges_ok", bool(in_range)))

    # Check 3: Fever count (1-2 rows)
    fevers = int((pd.to_numeric(df["Temperature"], errors="coerce") > 38.0).sum())
    report["checks"].append(("fever_count_1_to_2", 1 <= fevers <= 2))

    # Check 4: Fever rows have HR >= 67
    fever_hr_ok = True
    if fevers > 0:
        fever_rows = df.loc[pd.to_numeric(df["Temperature"], errors="coerce") > 38.0, "HeartRate"]
        fever_hr_ok = bool(pd.to_numeric(fever_rows, errors="coerce").ge(67).all())
    report["checks"].append(("fever_hr_link_ok", fever_hr_ok))

    # Check 5: Week-12 effect approximately -5 mmHg
    wk12 = df[df["VisitName"] == "Week 12"].copy()
    effect_ok, effect = True, None
    if not wk12.empty:
        wk12["SystolicBP"] = pd.to_numeric(wk12["SystolicBP"], errors="coerce")
        means = wk12.groupby("TreatmentArm")["SystolicBP"].mean().to_dict()
        if "Active" in means and "Placebo" in means:
            effect = float(means["Active"] - means["Placebo"])
            effect_ok = (-7 <= effect <= -3)  # target ≈ -5
    report["checks"].append(("week12_sbp_effect_approx_-5mmHg", effect_ok))
    report["week12_effect"] = effect
    report["fever_count"] = fevers

    return report
