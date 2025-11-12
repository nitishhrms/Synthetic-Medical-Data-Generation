"""
Risk-Based Quality Management (RBQM) functions
Extracted from existing monolithic app.py
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, Optional


def subject_to_site(subject_id: str, site_size: int = 20) -> str:
    """
    Derive pseudo SiteID from SubjectID by bucketing

    Args:
        subject_id: Subject ID (e.g., RA001-050)
        site_size: Number of subjects per site

    Returns:
        Site ID (e.g., S03)
    """
    try:
        num = int(str(subject_id).split("-")[-1])
        idx = (num - 1) // site_size + 1
        return f"S{idx:02d}"
    except Exception:
        return "S00"


def generate_rbqm_summary(queries_df: pd.DataFrame, vitals_df: pd.DataFrame,
                          ae_df: Optional[pd.DataFrame],
                          thresholds: Dict[str, float],
                          site_size: int) -> Tuple[str, pd.DataFrame, Dict]:
    """
    Generate RBQM summary with KRIs and site-level quality metrics

    Args:
        queries_df: Edit check queries DataFrame
        vitals_df: Vitals data DataFrame
        ae_df: Adverse events DataFrame (optional)
        thresholds: Quality tolerance limit thresholds
        site_size: Number of subjects per site

    Returns:
        Tuple of (markdown_summary, site_summary_df, kris_dict)
    """
    # Overall counters
    total_rows = len(vitals_df) if isinstance(vitals_df, pd.DataFrame) else 0
    total_q = len(queries_df) if isinstance(queries_df, pd.DataFrame) else 0
    q_rate = (100.0 * total_q / total_rows) if total_rows else 0.0

    # Count specific check types
    def count_check(prefix):
        if queries_df is None or queries_df.empty:
            return 0
        return int(queries_df["CheckID"].astype(str).str.startswith(prefix).sum())

    out_of_range = sum(count_check(cid) for cid in ["VS001", "VS002", "VS003", "VS004"])

    missing_visit_subjects = 0
    arm_change_subjects = 0
    duplicates = 0
    if isinstance(queries_df, pd.DataFrame) and not queries_df.empty:
        missing_visit_subjects = queries_df.loc[queries_df["CheckID"] == "VS011", "SubjectID"].nunique()
        arm_change_subjects = queries_df.loc[queries_df["CheckID"] == "VS010", "SubjectID"].nunique()
        duplicates = int((queries_df["CheckID"] == "VS012").sum())

    # AE KRIs
    fatal = 0
    sr = 0
    if isinstance(ae_df, pd.DataFrame) and not ae_df.empty:
        if "AEOUT" in ae_df.columns:
            fatal = int((ae_df["AEOUT"] == "FATAL").sum())
        if set(["AESER", "AEREL"]).issubset(ae_df.columns):
            sr = int(((ae_df["AESER"] == "Y") & (ae_df["AEREL"] == "Y")).sum())

    # Site roll-up
    v = vitals_df.copy()
    v["SiteID"] = v["SubjectID"].apply(lambda s: subject_to_site(s, site_size=site_size))

    if queries_df is not None and not queries_df.empty:
        q_df = queries_df.copy()
        q_df["SiteID"] = q_df["SubjectID"].apply(lambda s: subject_to_site(s, site_size=site_size))
        site_q = q_df.groupby("SiteID").size().rename("queries").reset_index()
    else:
        site_q = pd.DataFrame(columns=["SiteID", "queries"])

    site_rows = v.groupby("SiteID").size().rename("rows").reset_index()
    site_summary = site_rows.merge(site_q, on="SiteID", how="left").fillna({"queries": 0})
    site_summary["queries_per_100"] = site_summary.apply(
        lambda r: (100.0 * r["queries"] / r["rows"]) if r["rows"] else 0.0, axis=1
    )
    site_summary["QTL_flag"] = site_summary["queries_per_100"] > float(thresholds.get("q_rate_site", 6.0))

    # Build markdown summary
    lines = []
    lines.append(f"# RBQM Summary — {datetime.utcnow().date().isoformat()}")
    lines.append("")
    lines.append("## Key Risk Indicators (KRIs)")
    lines.append(f"- Total edit queries: **{total_q}**  ({q_rate:.1f} per 100 rows)")
    lines.append(f"- Out-of-range values (VS001–VS004): **{out_of_range}**")
    lines.append(f"- Subjects missing required visits (VS011): **{missing_visit_subjects}**")
    lines.append(f"- Treatment arm changes (VS010): **{arm_change_subjects}**")
    lines.append(f"- Duplicate SubjectID+VisitName (VS012): **{duplicates}**")
    lines.append(f"- Serious+related AEs: **{sr}**   |   Fatal AEs: **{fatal}**")
    lines.append("")
    lines.append("## Quality Tolerance Limits (QTL) — Example thresholds")
    lines.append(f"- Site query rate > **{float(thresholds.get('q_rate_site', 6.0)):.1f}** per 100 rows → Flag")
    lines.append(f"- Missing visits subjects > **{int(thresholds.get('missing_subj', 3))}** → Flag")
    lines.append(f"- Serious+related AEs > **{int(thresholds.get('serious_related', 5))}** → Flag")
    lines.append("")

    # Oncology notes
    lines.append("### Oncology QTL notes (demo)")
    lines.append("- Example: **Site rate of serious+related AEs > 3** → review")
    lines.append("- Example: Grade ≥3 neutropenia > 15% or ALT >3×ULN incidence > 10% → flag (if labs tracked).")
    lines.append("")

    over = site_summary[site_summary["QTL_flag"]]
    if not over.empty:
        lines.append("### Sites exceeding QTL (queries per 100 rows)")
        for _, r in over.sort_values("queries_per_100", ascending=False).iterrows():
            lines.append(f"- {r['SiteID']}: {r['queries_per_100']:.1f}")
    else:
        lines.append("No sites exceed the site-level QTL in this run.")
    lines.append("")
    lines.append("_Note: RBQM signals computed on synthetic demo data using YAML edit checks. For production, integrate with live EDC feeds and monitoring._")

    # KRIs dict for API response
    kris = {
        "total_queries": total_q,
        "query_rate_per_100": q_rate,
        "out_of_range": out_of_range,
        "missing_visit_subjects": missing_visit_subjects,
        "arm_change_subjects": arm_change_subjects,
        "duplicates": duplicates,
        "serious_related_aes": sr,
        "fatal_aes": fatal
    }

    return "\n".join(lines), site_summary, kris
