"""
YAML Edit Check Engine for clinical trial data quality
Extracted from existing monolithic app.py
"""
import pandas as pd
import numpy as np
import yaml
import re
from typing import List, Dict


DEFAULT_RULES_YAML = """
rules:
  - id: VS001
    severity: Major
    type: range
    field: SystolicBP
    min: 95
    max: 200
    message: "SystolicBP out of [95,200] mmHg"

  - id: VS002
    severity: Major
    type: range
    field: DiastolicBP
    min: 55
    max: 130
    message: "DiastolicBP out of [55,130] mmHg"

  - id: VS003
    severity: Major
    type: range
    field: HeartRate
    min: 50
    max: 120
    message: "HeartRate out of [50,120] bpm"

  - id: VS004
    severity: Major
    type: range
    field: Temperature
    min: 35.0
    max: 40.0
    message: "Temperature out of [35.0,40.0] °C (check °F vs °C)"

  - id: VS005
    severity: Major
    type: diff_at_least
    larger: SystolicBP
    smaller: DiastolicBP
    delta: 5
    message: "SystolicBP should exceed DiastolicBP by ≥5 mmHg"

  - id: VS007
    severity: Major
    type: allowed_values
    field: VisitName
    values: ["Screening","Day 1","Week 4","Week 12"]
    message: "VisitName not allowed"

  - id: VS008
    severity: Major
    type: allowed_values
    field: TreatmentArm
    values: ["Active","Placebo"]
    message: "TreatmentArm must be Active or Placebo"

  - id: VS009
    severity: Minor
    type: regex
    field: SubjectID
    pattern: '^RA\\d{3}-\\d{3}$'
    message: "SubjectID format should be RA###-###"

  - id: VS010
    severity: Critical
    type: constant_within_subject
    field: TreatmentArm
    message: "TreatmentArm changes across visits"

  - id: VS011
    severity: Major
    type: required_visits
    visits: ["Screening","Day 1","Week 4","Week 12"]
    message: "Missing required visits"

  - id: VS012
    severity: Major
    type: unique_combo
    fields: ["SubjectID","VisitName"]
    message: "Duplicate SubjectID+VisitName row"
"""


def load_default_rules() -> str:
    """Load default YAML edit check rules"""
    return DEFAULT_RULES_YAML


def run_edit_checks_yaml(df: pd.DataFrame, rules_yaml: str) -> pd.DataFrame:
    """
    Run YAML-based edit checks on DataFrame

    Args:
        df: DataFrame to validate
        rules_yaml: YAML string with edit check rules

    Returns:
        DataFrame with queries (violations)
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "CheckID", "Severity", "Message", "SubjectID", "VisitName", "Field", "Value"
        ])

    spec = yaml.safe_load(rules_yaml)

    # Handle both formats: direct list or wrapped in "rules:" key
    if isinstance(spec, list):
        rules = spec
    elif isinstance(spec, dict):
        rules = spec.get("rules", [])
    else:
        rules = []
    queries = []

    def add_q(rid, sev, msg, subj, visit, field, value):
        """Add a query to the list"""
        queries.append({
            "CheckID": rid,
            "Severity": sev,
            "Message": msg,
            "SubjectID": subj,
            "VisitName": visit,
            "Field": field,
            "Value": value
        })

    # Check if required columns exist for grouping
    has_subject_id = "SubjectID" in df.columns
    per_subj = df.groupby("SubjectID") if has_subject_id else None

    for rule in rules:
        t = rule.get("type")
        # Support both "id" and "name" for rule identifier
        rid = rule.get("id") or rule.get("name", "RULE")
        sev = rule.get("severity", "Major")
        msg = rule.get("message", "")

        if t == "range":
            # Check if value is within [min, max]
            # Support both "field" and "column" keys
            f = rule.get("field") or rule.get("column")
            if not f:
                continue
            lo, hi = rule["min"], rule["max"]
            if f not in df.columns:
                continue
            x = pd.to_numeric(df[f], errors="coerce")
            mask = ~x.between(lo, hi)
            for _, r in df[mask].iterrows():
                subj = r.get("SubjectID", "")
                visit = r.get("VisitName", "")
                add_q(rid, sev, msg, subj, visit, f, r[f])

        elif t == "diff_at_least":
            # Check if larger >= smaller + delta
            a, b, d = rule["larger"], rule["smaller"], float(rule["delta"])
            if a not in df.columns or b not in df.columns:
                continue
            xa = pd.to_numeric(df[a], errors="coerce")
            xb = pd.to_numeric(df[b], errors="coerce")
            mask = (xa < xb + d)
            for _, r in df[mask].iterrows():
                subj = r.get("SubjectID", "")
                visit = r.get("VisitName", "")
                add_q(rid, sev, msg, subj, visit, f"{a}/{b}", f"{r[a]}/{r[b]}")

        elif t == "allowed_values":
            # Check if value is in allowed set
            f = rule.get("field") or rule.get("column")
            if not f:
                continue
            vals = set(rule["values"])
            if f not in df.columns:
                continue
            mask = ~df[f].isin(vals)
            for _, r in df[mask].iterrows():
                subj = r.get("SubjectID", "")
                visit = r.get("VisitName", "")
                add_q(rid, sev, msg, subj, visit, f, r[f])

        elif t == "regex":
            # Check if value matches regex pattern
            f = rule.get("field") or rule.get("column")
            if not f:
                continue
            pat = re.compile(rule["pattern"])
            if f not in df.columns:
                continue
            mask = ~df[f].astype(str).str.match(pat)
            for _, r in df[mask].iterrows():
                subj = r.get("SubjectID", "")
                visit = r.get("VisitName", "")
                add_q(rid, sev, msg, subj, visit, f, r[f])

        elif t == "constant_within_subject":
            # Check if field is constant per subject
            if per_subj is None:
                continue
            f = rule.get("field") or rule.get("column")
            if not f or f not in df.columns:
                continue
            bad = per_subj[f].nunique()
            bad = bad[bad > 1].index
            for subj in bad:
                add_q(rid, sev, msg, subj, "", f, "")

        elif t == "required_visits":
            # Check if all required visits are present per subject
            if per_subj is None or "VisitName" not in df.columns:
                continue
            visits = set(rule["visits"])
            seen = per_subj["VisitName"].apply(set)
            for subj, s in seen.items():
                missing = sorted(list(visits - s))
                if missing:
                    add_q(rid, sev, f"{msg}: {', '.join(missing)}", subj, "", "VisitName", "")

        elif t == "unique_combo":
            # Check if field combination is unique
            fields = rule["fields"]
            # Check if all fields exist
            if not all(f in df.columns for f in fields):
                continue
            dup_mask = df.duplicated(subset=fields, keep=False)
            for _, r in df[dup_mask].iterrows():
                subj = r.get("SubjectID", "")
                visit = r.get("VisitName", "")
                add_q(rid, sev, msg, subj, visit, "+".join(fields), "")

    return pd.DataFrame(queries)


def simulate_entry_noise(df: pd.DataFrame, typo_rate: float = 0.02,
                         temp_unit_flip_rate: float = 0.01, seed: int = 123) -> pd.DataFrame:
    """
    Simulate data entry errors (noise)

    Args:
        df: Clean DataFrame
        typo_rate: Probability of typo per value
        temp_unit_flip_rate: Probability of C→F unit error
        seed: Random seed

    Returns:
        DataFrame with simulated errors
    """
    rng = np.random.default_rng(seed)
    out = df.copy()

    # Random ±1 jitter on vitals
    for col in ["SystolicBP", "DiastolicBP", "HeartRate"]:
        if col in out.columns:
            mask = rng.random(len(out)) < float(typo_rate)
            jitter = np.where(rng.random(len(out)) < 0.5, 1, -1)
            out.loc[mask, col] = (
                pd.to_numeric(out.loc[mask, col], errors="coerce")
                .fillna(0).astype(int) + jitter[mask]
            )

    # Scaling errors (±10-90%)
    for col in ["SystolicBP", "DiastolicBP"]:
        if col in out.columns:
            mask = rng.random(len(out)) < float(typo_rate / 2.0)
            scale = np.where(rng.random(len(out)) < 0.5, 1.10, 0.90)
            out.loc[mask, col] = (
                np.rint(pd.to_numeric(out.loc[mask, col], errors="coerce")
                .fillna(0) * scale[mask]).astype(int)
            )

    # Temperature unit conversion errors (C→F)
    if temp_unit_flip_rate > 0 and "Temperature" in out.columns:
        mask = rng.random(len(out)) < float(temp_unit_flip_rate)
        out.loc[mask, "Temperature"] = (
            pd.to_numeric(out.loc[mask, "Temperature"], errors="coerce")
            .fillna(36.8) * 9.0 / 5.0 + 32.0
        )

    return out
