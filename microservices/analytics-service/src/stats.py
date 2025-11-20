"""
Statistical analysis functions for clinical trials
Extracted from existing monolithic app.py
"""
import pandas as pd
import numpy as np
from math import erf
from typing import Dict, Any, Tuple

# Try to import scipy for exact t-test
try:
    from scipy.stats import ttest_ind
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False


def _phi(x: float) -> float:
    """Standard normal CDF"""
    return 0.5 * (1.0 + erf(x / np.sqrt(2.0)))


def calculate_week12_statistics(df: pd.DataFrame, visit_name: str = "Week 12") -> Dict[str, Any]:
    """
    Calculate final visit statistics (Active vs Placebo)

    Performs Welch's t-test on SystolicBP at the specified final visit

    Args:
        df: DataFrame with vitals data
        visit_name: Name of the visit to analyze (default: "Week 12")
                   Can be "Week 12", "Month 6", "Month 12", "Week 16", etc.

    Returns:
        Dict with statistical test results in nested format
    """
    # Filter to specified visit only
    wk12 = df[df["VisitName"] == visit_name].copy()

    if wk12.empty:
        # List available visits to help user
        available_visits = sorted(df["VisitName"].unique().tolist())
        raise ValueError(f"No '{visit_name}' data found. Available visits: {available_visits}")

    # Split by treatment arm
    wk12["SystolicBP"] = pd.to_numeric(wk12["SystolicBP"], errors="coerce")
    active = wk12[wk12["TreatmentArm"] == "Active"]["SystolicBP"].dropna().values
    placebo = wk12[wk12["TreatmentArm"] == "Placebo"]["SystolicBP"].dropna().values

    if len(active) == 0 or len(placebo) == 0:
        raise ValueError(f"Insufficient data for both arms at {visit_name}")

    # Calculate basic statistics
    x_active = np.asarray(active, dtype=float)
    x_placebo = np.asarray(placebo, dtype=float)

    n1, n2 = x_active.size, x_placebo.size
    m1 = x_active.mean() if n1 else np.nan
    m2 = x_placebo.mean() if n2 else np.nan
    s1 = x_active.std(ddof=1) if n1 > 1 else np.nan
    s2 = x_placebo.std(ddof=1) if n2 > 1 else np.nan
    se1 = s1 / np.sqrt(n1) if n1 > 1 else np.nan
    se2 = s2 / np.sqrt(n2) if n2 > 1 else np.nan

    diff = m1 - m2
    se_diff = np.sqrt((s1**2) / n1 + (s2**2) / n2) if (n1 > 1 and n2 > 1) else np.nan

    # Calculate p-value and t-statistic
    t_stat = diff / se_diff if (se_diff and np.isfinite(se_diff) and se_diff > 0) else np.nan

    if HAS_SCIPY and n1 > 1 and n2 > 1:
        p = float(ttest_ind(x_active, x_placebo, equal_var=False).pvalue)
    else:
        # Fallback to normal approximation
        z = diff / se_diff if (se_diff and np.isfinite(se_diff)) else np.nan
        p = 2.0 * (1.0 - _phi(abs(z))) if np.isfinite(z) else np.nan

    # Calculate 95% confidence interval (t-distribution approximation)
    # Using z=1.96 for 95% CI (normal approximation)
    ci_95_lower = diff - 1.96 * se_diff if np.isfinite(se_diff) else np.nan
    ci_95_upper = diff + 1.96 * se_diff if np.isfinite(se_diff) else np.nan

    # Interpretation
    significant = p < 0.05 if np.isfinite(p) else False

    # Cohen's d for effect size
    pooled_sd = np.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1 + n2 - 2)) if (n1 > 1 and n2 > 1) else np.nan
    cohens_d = abs(diff) / pooled_sd if np.isfinite(pooled_sd) and pooled_sd > 0 else 0

    if cohens_d < 0.2:
        effect_size = "negligible"
    elif cohens_d < 0.5:
        effect_size = "small"
    elif cohens_d < 0.8:
        effect_size = "medium"
    else:
        effect_size = "large"

    # Clinical relevance (5+ mmHg reduction is clinically meaningful)
    if abs(diff) >= 5 and significant:
        clinical_relevance = "clinically significant"
    elif abs(diff) >= 5:
        clinical_relevance = "borderline"
    else:
        clinical_relevance = "not clinically meaningful"

    return {
        "treatment_groups": {
            "Active": {
                "n": int(n1),
                "mean_systolic": round(float(m1), 1),
                "std_systolic": round(float(s1), 1) if np.isfinite(s1) else 0.0,
                "se_systolic": round(float(se1), 1) if np.isfinite(se1) else 0.0
            },
            "Placebo": {
                "n": int(n2),
                "mean_systolic": round(float(m2), 1),
                "std_systolic": round(float(s2), 1) if np.isfinite(s2) else 0.0,
                "se_systolic": round(float(se2), 1) if np.isfinite(se2) else 0.0
            }
        },
        "treatment_effect": {
            "difference": round(float(diff), 1),
            "se_difference": round(float(se_diff), 1) if np.isfinite(se_diff) else 0.0,
            "t_statistic": round(float(t_stat), 2) if np.isfinite(t_stat) else 0.0,
            "p_value": round(float(p), 3) if np.isfinite(p) else 1.0,
            "ci_95_lower": round(float(ci_95_lower), 1) if np.isfinite(ci_95_lower) else 0.0,
            "ci_95_upper": round(float(ci_95_upper), 1) if np.isfinite(ci_95_upper) else 0.0
        },
        "interpretation": {
            "significant": bool(significant),
            "effect_size": effect_size,
            "clinical_relevance": clinical_relevance
        }
    }


def ks_distance(x, y) -> float:
    """
    Calculate Kolmogorov-Smirnov distance between two distributions

    Args:
        x: First sample
        y: Second sample

    Returns:
        KS distance (max difference between CDFs)
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)

    if len(x) == 0 or len(y) == 0:
        return np.nan

    xs = np.sort(np.concatenate([x, y]))
    fx = np.searchsorted(np.sort(x), xs, side="right") / len(x)
    fy = np.searchsorted(np.sort(y), xs, side="right") / len(y)

    return float(np.max(np.abs(fx - fy)))


def simulate_recist_from_vitals(df: pd.DataFrame, p_active: float = 0.35,
                                 p_placebo: float = 0.20, seed: int = 777) -> pd.DataFrame:
    """
    Simulate RECIST responses for oncology trials

    CR/PR are 'responders'; SD/PD are 'non-responders'

    Args:
        df: Vitals DataFrame
        p_active: Response probability for Active arm
        p_placebo: Response probability for Placebo arm
        seed: Random seed

    Returns:
        DataFrame with RECIST responses
    """
    rng = np.random.default_rng(seed)
    wk12 = df[df["VisitName"] == "Week 12"].copy()

    if wk12.empty or wk12["TreatmentArm"].nunique() < 2:
        return pd.DataFrame(columns=["SubjectID", "TreatmentArm", "RECIST"])

    def draw_label(p):
        # responders split CR:PR ≈ 1:3 for variety
        if rng.random() < p:
            return "CR" if rng.random() < 0.25 else "PR"
        return "SD" if rng.random() < 0.5 else "PD"

    rows = []
    for _, r in wk12.iterrows():
        p = p_active if r["TreatmentArm"] == "Active" else p_placebo
        rows.append([r["SubjectID"], r["TreatmentArm"], draw_label(p)])

    return pd.DataFrame(rows, columns=["SubjectID", "TreatmentArm", "RECIST"])


def two_prop_ztest(x1: int, n1: int, x2: int, n2: int) -> float:
    """
    Two-proportion z-test (two-sided)

    Args:
        x1: Number of successes in group 1
        n1: Total in group 1
        x2: Number of successes in group 2
        n2: Total in group 2

    Returns:
        p-value (two-sided)
    """
    p1 = x1 / max(n1, 1e-9)
    p2 = x2 / max(n2, 1e-9)
    p = (x1 + x2) / max(n1 + n2, 1e-9)
    se = np.sqrt(p * (1 - p) * (1.0 / n1 + 1.0 / n2)) if n1 and n2 else np.nan

    if not np.isfinite(se) or se == 0:
        return np.nan

    z = (p1 - p2) / se
    return 2.0 * (1.0 - _phi(abs(z)))


def calculate_recist_orr(df: pd.DataFrame, p_active: float = 0.35,
                         p_placebo: float = 0.20, seed: int = 777) -> Dict[str, Any]:
    """
    Calculate Objective Response Rate (ORR) from RECIST data

    Args:
        df: Vitals DataFrame
        p_active: Response probability for Active
        p_placebo: Response probability for Placebo
        seed: Random seed

    Returns:
        Dict with ORR statistics and p-value
    """
    recist_df = simulate_recist_from_vitals(df, p_active, p_placebo, seed)

    if recist_df.empty:
        raise ValueError("No RECIST data generated")

    # Calculate ORR (CR + PR = responders)
    recist_df["responder"] = recist_df["RECIST"].isin(["CR", "PR"])

    active_df = recist_df[recist_df["TreatmentArm"] == "Active"]
    placebo_df = recist_df[recist_df["TreatmentArm"] == "Placebo"]

    orr_active = active_df["responder"].mean() if not active_df.empty else 0.0
    orr_placebo = placebo_df["responder"].mean() if not placebo_df.empty else 0.0

    # Two-proportion z-test
    x1 = int(active_df["responder"].sum())
    n1 = len(active_df)
    x2 = int(placebo_df["responder"].sum())
    n2 = len(placebo_df)

    p_value = two_prop_ztest(x1, n1, x2, n2)

    return {
        "recist_data": recist_df.to_dict(orient="records"),
        "orr_active": float(orr_active),
        "orr_placebo": float(orr_placebo),
        "orr_difference": float(orr_active - orr_placebo),
        "p_value": float(p_value) if np.isfinite(p_value) else 1.0
    }
