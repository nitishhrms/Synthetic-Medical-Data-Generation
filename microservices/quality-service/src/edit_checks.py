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

    spec = yaml.safe_load(rules_yaml) or {}
    rules = spec.get("rules", [])
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

    per_subj = df.groupby("SubjectID")

    for rule in rules:
        t = rule.get("type")
        rid = rule.get("id", "RULE")
        sev = rule.get("severity", "Major")
        msg = rule.get("message", "")

        if t == "range":
            # Check if value is within [min, max]
            f, lo, hi = rule["field"], rule["min"], rule["max"]
            x = pd.to_numeric(df[f], errors="coerce")
            mask = ~x.between(lo, hi)
            for _, r in df[mask].iterrows():
                add_q(rid, sev, msg, r.SubjectID, r.VisitName, f, r[f])

        elif t == "diff_at_least":
            # Check if larger >= smaller + delta
            a, b, d = rule["larger"], rule["smaller"], float(rule["delta"])
            xa = pd.to_numeric(df[a], errors="coerce")
            xb = pd.to_numeric(df[b], errors="coerce")
            mask = (xa < xb + d)
            for _, r in df[mask].iterrows():
                add_q(rid, sev, msg, r.SubjectID, r.VisitName, f"{a}/{b}", f"{r[a]}/{r[b]}")

        elif t == "allowed_values":
            # Check if value is in allowed set
            f, vals = rule["field"], set(rule["values"])
            mask = ~df[f].isin(vals)
            for _, r in df[mask].iterrows():
                add_q(rid, sev, msg, r.SubjectID, r.VisitName, f, r[f])

        elif t == "regex":
            # Check if value matches regex pattern
            f, pat = rule["field"], re.compile(rule["pattern"])
            mask = ~df[f].astype(str).str.match(pat)
            for _, r in df[mask].iterrows():
                add_q(rid, sev, msg, r.SubjectID, r.VisitName, f, r[f])

        elif t == "constant_within_subject":
            # Check if field is constant per subject
            f = rule["field"]
            bad = per_subj[f].nunique()
            bad = bad[bad > 1].index
            for subj in bad:
                add_q(rid, sev, msg, subj, "", f, "")

        elif t == "required_visits":
            # Check if all required visits are present per subject
            visits = set(rule["visits"])
            seen = per_subj["VisitName"].apply(set)
            for subj, s in seen.items():
                missing = sorted(list(visits - s))
                if missing:
                    add_q(rid, sev, f"{msg}: {', '.join(missing)}", subj, "", "VisitName", "")

        elif t == "unique_combo":
            # Check if field combination is unique
            fields = rule["fields"]
            dup_mask = df.duplicated(subset=fields, keep=False)
            for _, r in df[dup_mask].iterrows():
                add_q(rid, sev, msg, r.SubjectID, r.VisitName, "+".join(fields), "")

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
