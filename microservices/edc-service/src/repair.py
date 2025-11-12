"""
Auto-repair module for clinical trial vitals data
Extracted from existing monolithic app.py
"""
import pandas as pd
from typing import Optional


def auto_repair_vitals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Auto-repair vitals data to fix constraint violations

    Repair actions:
    - Clip values to valid ranges
    - Ensure at least 1 fever row (temp > 38°C)
    - Ensure fever rows have HR >= 67
    - Adjust Week-12 effect to target -5 mmHg

    Args:
        df: DataFrame with vitals data

    Returns:
        Repaired DataFrame
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    # Repair ranges
    df["SystolicBP"] = pd.to_numeric(df["SystolicBP"], errors="coerce").clip(95, 200).round().astype(int)
    df["DiastolicBP"] = pd.to_numeric(df["DiastolicBP"], errors="coerce").clip(55, 130).round().astype(int)
    df["HeartRate"] = pd.to_numeric(df["HeartRate"], errors="coerce").clip(50, 120).round().astype(int)
    df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce").clip(35.0, 40.0)

    # Ensure at least 1 fever row
    if (df["Temperature"] > 38.0).sum() == 0:
        idx = df.index[(df["VisitName"].eq("Week 4")) & (df["TreatmentArm"].eq("Active"))]
        if len(idx) == 0:
            idx = df.index[:1]
        df.loc[idx[0], "Temperature"] = 38.2
        if df.loc[idx[0], "HeartRate"] < 67:
            df.loc[idx[0], "HeartRate"] = 67

    # Fever rows must have HR >= 67
    fever_idx = df.index[df["Temperature"] > 38.0]
    df.loc[fever_idx, "HeartRate"] = df.loc[fever_idx, "HeartRate"].clip(lower=67)

    # Enforce Week-12 effect ≈ -5 on Active
    wk12 = df["VisitName"] == "Week 12"
    if wk12.any():
        means = df.loc[wk12].groupby("TreatmentArm")["SystolicBP"].mean().to_dict()
        if "Active" in means and "Placebo" in means:
            current = means["Active"] - means["Placebo"]
            adjust = -5.0 - current
            mask = wk12 & (df["TreatmentArm"] == "Active")
            df.loc[mask, "SystolicBP"] = (
                df.loc[mask, "SystolicBP"] + adjust
            ).round().astype(int).clip(95, 200)

    return df


def effect_shift(df: pd.DataFrame, target_effect: float) -> pd.DataFrame:
    """
    Shift Week-12 effect to a specific target value

    Args:
        df: DataFrame with vitals data
        target_effect: Target effect size (Active - Placebo)

    Returns:
        DataFrame with adjusted Week-12 SBP values
    """
    if df is None or df.empty:
        return df

    out = df.copy()
    out["SystolicBP"] = pd.to_numeric(out["SystolicBP"], errors="coerce")
    wk12 = out["VisitName"] == "Week 12"

    if not wk12.any():
        return out

    means = out.loc[wk12].groupby("TreatmentArm")["SystolicBP"].mean().to_dict()
    if "Active" in means and "Placebo" in means:
        current = means["Active"] - means["Placebo"]
        adjust = target_effect - current
        mask = wk12 & (out["TreatmentArm"] == "Active")
        out.loc[mask, "SystolicBP"] = (
            out.loc[mask, "SystolicBP"] + adjust
        ).round().astype(int).clip(95, 200)

    return out
