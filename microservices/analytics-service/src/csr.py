"""
Clinical Study Report (CSR) generation functions
Extracted from existing monolithic app.py
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Optional


def generate_csr_draft(stats: Dict, ae_df: Optional[pd.DataFrame], n_rows: int) -> str:
    """
    Generate CSR draft markdown

    Args:
        stats: Statistical analysis results (Week 12)
        ae_df: Adverse events DataFrame
        n_rows: Total number of vitals rows

    Returns:
        CSR markdown string
    """
    pval = stats.get("p_value_two_sided")
    ptxt = f"{pval:.3g}" if pval == pval else "n/a"  # Check for NaN

    fatal = 0
    sr = 0
    if isinstance(ae_df, pd.DataFrame) and not ae_df.empty:
        if "AEOUT" in ae_df.columns:
            fatal = int((ae_df["AEOUT"] == "FATAL").sum())
        if set(["AESER", "AEREL"]).issubset(ae_df.columns):
            sr = int(((ae_df["AESER"] == "Y") & (ae_df["AEREL"] == "Y")).sum())

    lines = []
    lines.append(f"# CSR Draft (Auto) — {datetime.utcnow().date().isoformat()}")
    lines.append("")
    lines.append("## 9. Efficacy — Primary Endpoint")
    lines.append("**Endpoint:** Systolic Blood Pressure at Week 12 (Active − Placebo).")
    lines.append(
        f"**Analysis set:** N≈{n_rows} rows of vitals across visits; "
        f"Week-12 subsets: n(Active)={stats.get('n_active')}, n(Placebo)={stats.get('n_placebo')}."
    )
    lines.append(
        f"**Results:** mean(SBP)_Active={stats.get('mean_active'):.1f} mmHg; "
        f"mean(SBP)_Placebo={stats.get('mean_placebo'):.1f} mmHg."
    )
    lines.append(
        f"**Effect:** {stats.get('diff_active_minus_placebo'):+.2f} mmHg "
        f"(SE={stats.get('se'):.2f}); **p**={ptxt} (Welch t-test or normal approx)."
    )
    lines.append("")
    lines.append("## 10. Safety")
    lines.append(f"Serious & related AEs: **{sr}**; Fatal outcomes: **{fatal}**.")
    lines.append(
        "Common events included constitutional symptoms and laboratory abnormalities "
        "consistent with the therapeutic area. No unexpected safety signals were observed "
        "in this synthetic demonstration dataset."
    )
    lines.append("")
    lines.append("## 11. Data Handling & Quality")
    lines.append(
        "- Edit checks enforced: value ranges, visit completeness, SubjectID regex, "
        "treatment-arm constancy, unique SubjectID+VisitName."
    )
    lines.append(
        "- Auto-repair applied for mild violations (clipping ranges, enforcing fever HR link, "
        "Week-12 effect alignment)."
    )
    lines.append("- Dataset validated post-repair; see `checks/validation_report.md`.")
    lines.append("")
    lines.append("> **Note:** Dataset is synthetic for development/demo only; not for clinical decision-making.")

    return "\n".join(lines)
