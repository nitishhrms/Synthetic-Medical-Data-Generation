"""
Data generation functions for clinical trial data
Extracted from existing monolithic app.py
"""
import pandas as pd
import numpy as np
import re
import os
from io import StringIO
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

# Constants
NUM_COLS = ["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]
VISITS = ["Screening", "Day 1", "Week 4", "Week 12"]
ARMS = ["Active", "Placebo"]

# Import validation functions (assuming they're available in EDC service)
# For now, we'll include a simplified version here
def validate_vitals(df: pd.DataFrame) -> Dict[str, Any]:
    """Simplified validation for generation service"""
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

    required = ["SubjectID", "VisitName", "TreatmentArm", "SystolicBP",
                "DiastolicBP", "HeartRate", "Temperature"]
    report["checks"].append(("columns_present", all(c in df.columns for c in required)))

    in_range = (
        pd.to_numeric(df["SystolicBP"], errors="coerce").between(95, 200).all() and
        pd.to_numeric(df["DiastolicBP"], errors="coerce").between(55, 130).all() and
        pd.to_numeric(df["HeartRate"], errors="coerce").between(50, 120).all() and
        pd.to_numeric(df["Temperature"], errors="coerce").between(35.0, 40.0).all()
    )
    report["checks"].append(("ranges_ok", bool(in_range)))

    fevers = int((pd.to_numeric(df["Temperature"], errors="coerce") > 38.0).sum())
    report["checks"].append(("fever_count_1_to_2", 1 <= fevers <= 2))

    fever_hr_ok = True
    if fevers > 0:
        fever_rows = df.loc[pd.to_numeric(df["Temperature"], errors="coerce") > 38.0, "HeartRate"]
        fever_hr_ok = bool(pd.to_numeric(fever_rows, errors="coerce").ge(67).all())
    report["checks"].append(("fever_hr_link_ok", fever_hr_ok))

    wk12 = df[df["VisitName"] == "Week 12"].copy()
    effect_ok, effect = True, None
    if not wk12.empty:
        wk12["SystolicBP"] = pd.to_numeric(wk12["SystolicBP"], errors="coerce")
        means = wk12.groupby("TreatmentArm")["SystolicBP"].mean().to_dict()
        if "Active" in means and "Placebo" in means:
            effect = float(means["Active"] - means["Placebo"])
            effect_ok = (-7 <= effect <= -3)
    report["checks"].append(("week12_sbp_effect_approx_-5mmHg", effect_ok))
    report["week12_effect"] = effect
    report["fever_count"] = fevers
    return report


def generate_vitals_rules(n_per_arm=50, target_effect=-5.0, seed=42) -> pd.DataFrame:
    """
    Generate synthetic vitals using rules-based approach

    Args:
        n_per_arm: Number of subjects per arm
        target_effect: Target treatment effect for Week 12 SBP (Active - Placebo)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic vitals data
    """
    rng = np.random.default_rng(seed)
    visits = ["Screening", "Day 1", "Week 4", "Week 12"]
    arms = (["Active"] * n_per_arm) + (["Placebo"] * n_per_arm)
    subs = [f"RA001-{i:03d}" for i in range(1, 2 * n_per_arm + 1)]

    rows = []
    for sid, arm in zip(subs, arms):
        base_val = rng.normal(130, 10)
        for v in visits:
            sbp = rng.normal(base_val, 6)
            if v == "Week 12" and arm == "Active":
                sbp += target_effect  # negative lowers Active
            dbp = rng.normal(80, 8)
            hr = int(rng.integers(60, 101))
            temp = rng.normal(36.8, 0.3)
            rows.append([
                sid, v, arm,
                int(np.clip(round(sbp), 95, 200)),
                int(np.clip(round(dbp), 55, 130)),
                int(np.clip(hr, 50, 120)),
                float(np.clip(temp, 35.0, 40.0)),
            ])

    df = pd.DataFrame(rows, columns=[
        "SubjectID", "VisitName", "TreatmentArm", "SystolicBP",
        "DiastolicBP", "HeartRate", "Temperature"
    ])

    # Add 1–2 fever rows w/ HR ≥ 67
    k = int(rng.integers(1, 3))
    idx = rng.choice(df.index, size=k, replace=False)
    df.loc[idx, "Temperature"] = rng.uniform(38.1, 38.8, size=k)
    df.loc[idx, "HeartRate"] = np.maximum(df.loc[idx, "HeartRate"], 67)

    # Snap Week-12 effect precisely
    df["SystolicBP"] = pd.to_numeric(df["SystolicBP"], errors="coerce")
    wk12 = df["VisitName"] == "Week 12"
    means = df.loc[wk12].groupby("TreatmentArm")["SystolicBP"].mean().to_dict()
    if "Active" in means and "Placebo" in means:
        current = means["Active"] - means["Placebo"]
        adjust = target_effect - current
        mask = wk12 & (df["TreatmentArm"] == "Active")
        df.loc[mask, "SystolicBP"] = (
            df.loc[mask, "SystolicBP"] + adjust
        ).round().astype(int).clip(95, 200)

    return df


def _to_num_block(df_block: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns to float, dropping NaNs"""
    X = df_block[NUM_COLS].apply(pd.to_numeric, errors="coerce").dropna()
    return X


def fit_mvn_models(train_df: pd.DataFrame) -> Dict:
    """
    Fit mean + covariance for each (VisitName, TreatmentArm) block

    Returns:
        dict[(visit, arm)] = {"mu": np.array(4,), "cov": np.array(4x4)}
    """
    models = {}
    for v in VISITS:
        for a in ARMS:
            blk = train_df[(train_df["VisitName"] == v) & (train_df["TreatmentArm"] == a)]
            X = _to_num_block(blk)
            if len(X) >= 8:
                mu = X.mean().to_numpy()
                cov = np.cov(X.to_numpy(), rowvar=False)
            else:
                # Fallback priors
                mu = np.array([130, 80, 75, 36.8], dtype=float)
                cov = np.diag(np.array([10**2, 8**2, 8**2, 0.3**2], dtype=float))
            # Stabilize covariance
            cov = cov + 1e-6 * np.eye(len(NUM_COLS))
            models[(v, a)] = {"mu": mu, "cov": cov}
    return models


def load_pilot_vitals() -> pd.DataFrame:
    """Load pilot vitals data from the existing-app directory"""
    # Correctly locate the pilot data relative to the microservices directory
    base_path = Path(__file__).resolve().parents[3]
    pilot_data_path = base_path / "existing-app" / "data" / "pilot" / "vitals.csv"

    if not pilot_data_path.exists():
        raise FileNotFoundError(
            f"Pilot data not found at the expected path: {pilot_data_path}. "
            "Ensure the 'existing-app' directory is at the root of the repository."
        )

    return pd.read_csv(pilot_data_path)


def generate_vitals_mvn(n_per_arm=50, target_effect=-5.0, seed=123,
                        train_source: str = "pilot",
                        current_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Generate vitals using Multivariate Normal learned from training data

    Args:
        n_per_arm: Number of subjects per arm
        target_effect: Target treatment effect
        seed: Random seed
        train_source: 'pilot' or 'current'
        current_df: Current dataframe if train_source='current'

    Returns:
        DataFrame with synthetic vitals
    """
    rng = np.random.default_rng(seed)

    if train_source == "current" and isinstance(current_df, pd.DataFrame) and not current_df.empty:
        train_df = current_df.copy()
    else:
        train_df = load_pilot_vitals()

    models = fit_mvn_models(train_df)

    rows = []
    subj_active = [f"RA001-{i:03d}" for i in range(1, n_per_arm + 1)]
    subj_placebo = [f"RA001-{i:03d}" for i in range(n_per_arm + 1, 2 * n_per_arm + 1)]

    for arm, subjects in [("Active", subj_active), ("Placebo", subj_placebo)]:
        for sid in subjects:
            for visit in VISITS:
                m = models[(visit, arm)]
                x = np.random.default_rng(rng.integers(0, 2**31 - 1)).multivariate_normal(
                    mean=m["mu"], cov=m["cov"], size=1
                )[0]
                sbp, dbp, hr, temp = x.tolist()
                rows.append([
                    sid, visit, arm,
                    int(np.clip(round(sbp), 95, 200)),
                    int(np.clip(round(dbp), 55, 130)),
                    int(np.clip(round(hr), 50, 120)),
                    float(np.clip(temp, 35.0, 40.0)),
                ])

    df = pd.DataFrame(rows, columns=["SubjectID", "VisitName", "TreatmentArm"] + NUM_COLS)

    # Add 1–2 fever rows with HR >= 67
    k = int(rng.integers(1, 3))
    idx = rng.choice(df.index, size=k, replace=False)
    df.loc[idx, "Temperature"] = rng.uniform(38.1, 38.8, size=k)
    df.loc[idx, "HeartRate"] = np.maximum(df.loc[idx, "HeartRate"], 67)

    # Snap Week-12 effect exactly to target
    wk12 = df["VisitName"] == "Week 12"
    means = df.loc[wk12].groupby("TreatmentArm")["SystolicBP"].mean().to_dict()
    if "Active" in means and "Placebo" in means:
        current = means["Active"] - means["Placebo"]
        adjust = target_effect - current
        mask = wk12 & (df["TreatmentArm"] == "Active")
        df.loc[mask, "SystolicBP"] = (
            df.loc[mask, "SystolicBP"] + adjust
        ).round().astype(int).clip(95, 200)

    return df


# ======================== LLM Generation ========================
def _openai_chat(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    """Call OpenAI API"""
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not installed. `pip install openai`") from e

    if not api_key:
        raise RuntimeError("Missing OpenAI API key.")

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def call_llm(prompt: str, provider: str = "openai",
             api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> str:
    """Call LLM provider"""
    if provider == "openai":
        return _openai_chat(prompt, api_key=api_key or os.environ.get("OPENAI_API_KEY"), model=model)
    raise RuntimeError(f"LLM provider '{provider}' not supported.")


LLM_SYSTEM_PREFIX = """You are a meticulous biostatistician. You MUST obey the following output rules:
1) Output ONLY a single CSV code block (markdown fenced), nothing else.
2) Include EXACT headers: SubjectID,VisitName,TreatmentArm,SystolicBP,DiastolicBP,HeartRate,Temperature
3) Do NOT add commentary, units in cells, or extra columns.
"""

DEFAULT_CSV_PROMPT_TEMPLATE = """Generate a VITALS CSV for a Phase 3 {indication} trial.
Arms: Active vs Placebo. Subjects per arm: {n_per_arm}.
Visits: Screening, Day 1, Week 4, Week 12.

Constraints:
- SystolicBP ~ N(130,10), clamp [95,200], integers
- DiastolicBP ~ N(80,8), clamp [55,130], integers
- HeartRate in [60,100], integers
- Temperature ~ N(36.8,0.3); include 1–2 rows with Temp > 38.0°C; for those rows, HeartRate >= 67
- Week 12 treatment effect: mean(SBP, Active) - mean(SBP, Placebo) ≈ {target_effect} mmHg (acceptable range -7..-3 if target is -5)
"""


def build_llm_prompt(indication: str, n_per_arm: int, target_effect: float,
                     prompt_template: Optional[str] = None,
                     extra_instructions: str = "") -> str:
    """Build LLM prompt for data generation"""
    tpl = prompt_template or DEFAULT_CSV_PROMPT_TEMPLATE
    body = tpl.format(indication=indication, n_per_arm=n_per_arm, target_effect=target_effect)
    if extra_instructions:
        body += "\n\nAdditional instructions (must still obey schema & CSV-only):\n" + extra_instructions.strip()
    body += "\n\nOutput: ONLY a single CSV code block with headers and no prose."
    return LLM_SYSTEM_PREFIX + "\n\n" + body


def extract_csv_block(text: str) -> str:
    """Extract CSV from markdown code block"""
    m = re.search(r"```(?:csv)?\s*(.*?)```", text, re.S | re.I)
    return m.group(1).strip() if m else text.strip()


def generate_vitals_llm(indication: str, n_per_arm: int, target_effect: float,
                        api_key: Optional[str] = None, model: str = "gpt-4o-mini",
                        prompt_template: Optional[str] = None,
                        extra_instructions: str = "") -> Tuple[pd.DataFrame, str]:
    """Generate vitals using LLM"""
    prompt = build_llm_prompt(indication, n_per_arm, target_effect,
                              prompt_template, extra_instructions)
    content = call_llm(prompt, api_key=api_key, model=model)
    csv_text = extract_csv_block(content)
    df = pd.read_csv(StringIO(csv_text))
    return df, prompt


def generate_vitals_llm_with_repair(indication: str, n_per_arm: int, target_effect: float,
                                     api_key: Optional[str] = None, model: str = "gpt-4o-mini",
                                     prompt_template: Optional[str] = None,
                                     extra_instructions: str = "",
                                     max_iters: int = 2) -> Tuple[pd.DataFrame, Dict, str]:
    """
    Generate vitals using LLM with automatic repair loop

    Returns:
        (dataframe, validation_report, prompt_used)
    """
    df, used_prompt = generate_vitals_llm(indication, n_per_arm, target_effect,
                                          api_key, model, prompt_template, extra_instructions)
    rep = validate_vitals(df)

    for _ in range(max_iters):
        if all(bool(v) for _, v in rep["checks"]):
            break
        fail_notes = [name for name, ok in rep["checks"] if not bool(ok)]
        fb = f"\nRegenerate. The following checks failed: {fail_notes}. Keep schema EXACT. Keep N per arm {n_per_arm}. Target effect {target_effect}."
        content = call_llm(used_prompt + fb, api_key=api_key, model=model)
        df = pd.read_csv(StringIO(extract_csv_block(content)))
        rep = validate_vitals(df)

    return df, rep, used_prompt


def generate_oncology_ae(n_subjects=30, seed=7) -> pd.DataFrame:
    """
    Generate synthetic oncology adverse events

    Returns:
        DataFrame with SDTM AE domain structure
    """
    rng = np.random.default_rng(seed)
    subjects = [f"ONC{idx:03d}" for idx in range(1, n_subjects + 1)]
    terms = [
        ("Neutropenia", "Blood and lymphatic system disorders"),
        ("Nausea", "Gastrointestinal disorders"),
        ("Anemia", "Blood and lymphatic system disorders"),
        ("Fatigue", "General disorders and administration site conditions"),
        ("Elevated ALT", "Hepatobiliary disorders"),
    ]
    rows = []

    # Guarantee 2 serious+related and 1 fatal
    rows.append([rng.choice(subjects), "Myelosuppression",
                 "Blood and lymphatic system disorders", "Y", "Y", "ONGOING"])
    rows.append([rng.choice(subjects), "Hepatic failure",
                 "Hepatobiliary disorders", "Y", "Y", "FATAL"])

    for _ in range(max(20, n_subjects)):
        subj = rng.choice(subjects)
        term, bod = terms[rng.integers(0, len(terms))]
        ser = "Y" if term in ("Neutropenia", "Anemia") and rng.random() < 0.2 else "N"
        rel = "Y" if rng.random() < 0.6 else "N"
        out = "RESOLVED" if rng.random() < 0.8 else "ONGOING"
        rows.append([subj, term, bod, ser, rel, out])

    return pd.DataFrame(rows, columns=["USUBJID", "AETERM", "AEBODSYS", "AESER", "AEREL", "AEOUT"])


def generate_vitals_bootstrap(
    training_df: pd.DataFrame,
    n_per_arm: int = 50,
    target_effect: float = -5.0,
    jitter_frac: float = 0.05,
    cat_flip_prob: float = 0.05,
    seed: int = 42
) -> pd.DataFrame:
    """
    Bootstrap-based synthetic data generation with clinical trial enhancements

    Uses row sampling with intelligent augmentation, fine-tuned for clinical trials:
    - Bootstrap sampling with replacement
    - Gaussian jitter on vitals (scaled by column std)
    - Respects clinical constraints (BP, HR, Temp ranges)
    - Maintains integer types for appropriate fields
    - Generates proper SubjectIDs (RA###-###)
    - Ensures complete visit sequences per subject
    - Applies treatment effect at Week 12

    Best for: Quick augmentation from pilot study data or existing datasets

    Args:
        training_df: Training data (pilot study or existing dataset)
                    Must contain: SubjectID, VisitName, TreatmentArm, SystolicBP,
                                  DiastolicBP, HeartRate, Temperature
        n_per_arm: Number of subjects per treatment arm
        target_effect: Target SystolicBP reduction (Active - Placebo) at Week 12
        jitter_frac: Fraction of std for numeric noise (0.05 = 5% of std)
        cat_flip_prob: Probability of flipping categorical values for diversity
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic vitals data
    """
    from pandas.api.types import is_integer_dtype

    rng = np.random.default_rng(seed)
    np.random.seed(seed)

    # Validate input
    required_cols = ["SubjectID", "VisitName", "TreatmentArm", "SystolicBP",
                     "DiastolicBP", "HeartRate", "Temperature"]
    missing = [c for c in required_cols if c not in training_df.columns]
    if missing:
        raise ValueError(f"Training data missing required columns: {missing}")

    # Calculate target total rows (subjects × visits × arms)
    target_n = n_per_arm * len(VISITS) * len(ARMS)
    n0 = len(training_df)

    if n0 == 0:
        raise ValueError("Training data is empty")

    # Sample complete rows with replacement
    needed = max(target_n - n0, 0)
    if needed > 0:
        syn = training_df.sample(n=needed, replace=True, random_state=seed).reset_index(drop=True)
    else:
        syn = training_df.sample(n=target_n, replace=False, random_state=seed).reset_index(drop=True)

    # ===== Numeric Jitter with Clinical Constraints =====
    num_cols = ["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]
    constraints = {
        "SystolicBP": (95, 200),
        "DiastolicBP": (55, 130),
        "HeartRate": (50, 120),
        "Temperature": (35.0, 40.0)
    }

    for col in num_cols:
        s = syn[col].copy()
        base = pd.to_numeric(training_df[col], errors="coerce")
        std = base.std()

        if pd.isna(std) or std == 0:
            continue

        # Add Gaussian noise scaled by std
        scale = max(std * jitter_frac, 1e-12)
        noise = rng.normal(0.0, scale, size=len(s))
        s_noisy = pd.to_numeric(s, errors="coerce") + noise

        # Clip to clinical constraints
        col_min, col_max = constraints[col]
        s_noisy = np.clip(s_noisy, col_min, col_max)

        # Integer columns (BP, HR)
        if col in ["SystolicBP", "DiastolicBP", "HeartRate"]:
            s_noisy = np.round(s_noisy).astype(np.int64)
        else:
            s_noisy = s_noisy.astype(float)

        syn[col] = s_noisy

    # ===== Ensure SystolicBP > DiastolicBP by at least 5 mmHg =====
    mask = syn["SystolicBP"] <= syn["DiastolicBP"] + 5
    if mask.any():
        syn.loc[mask, "SystolicBP"] = syn.loc[mask, "DiastolicBP"] + rng.integers(5, 20, size=mask.sum())
        # Re-clip to max
        syn.loc[mask, "SystolicBP"] = np.clip(syn.loc[mask, "SystolicBP"], 95, 200)

    # ===== Categorical Flip (VisitName and TreatmentArm - low probability) =====
    if cat_flip_prob > 0:
        # Flip VisitName occasionally for diversity
        mask = rng.random(len(syn)) < cat_flip_prob
        if mask.any():
            syn.loc[mask, "VisitName"] = rng.choice(VISITS, size=mask.sum())

        # Flip TreatmentArm occasionally
        mask = rng.random(len(syn)) < cat_flip_prob
        if mask.any():
            syn.loc[mask, "TreatmentArm"] = rng.choice(ARMS, size=mask.sum())

    # ===== Combine original + synthetic =====
    out = pd.concat([training_df, syn], ignore_index=True)

    # ===== Ensure complete visit sequences per subject =====
    # Group by subject and ensure all 4 visits present
    subjects_visits = out.groupby("SubjectID")["VisitName"].apply(set)
    incomplete_subjects = subjects_visits[subjects_visits.apply(lambda x: len(x) < len(VISITS))].index

    # Fill missing visits by duplicating existing rows
    rows_to_add = []
    for subj in incomplete_subjects:
        subj_data = out[out["SubjectID"] == subj]
        missing_visits = set(VISITS) - set(subj_data["VisitName"])

        for visit in missing_visits:
            # Use a random existing row from this subject as template
            template = subj_data.sample(n=1, random_state=seed).iloc[0].copy()
            template["VisitName"] = visit
            rows_to_add.append(template)

    if rows_to_add:
        out = pd.concat([out, pd.DataFrame(rows_to_add)], ignore_index=True)

    # ===== Regenerate SubjectIDs in proper format (RA###-###) =====
    unique_subjects = out["SubjectID"].unique()
    subject_mapping = {}
    counter = 1

    for old_subj in unique_subjects:
        subject_mapping[old_subj] = f"RA001-{counter:03d}"
        counter += 1

    out["SubjectID"] = out["SubjectID"].map(subject_mapping)

    # ===== Apply Treatment Effect at Week 12 =====
    week12 = out["VisitName"] == "Week 12"
    active = out["TreatmentArm"] == "Active"
    placebo = out["TreatmentArm"] == "Placebo"

    # Calculate current effect
    active_week12_mean = out[week12 & active]["SystolicBP"].mean()
    placebo_week12_mean = out[week12 & placebo]["SystolicBP"].mean()
    current_effect = active_week12_mean - placebo_week12_mean

    # Adjust to target effect
    adjustment = target_effect - current_effect

    # Apply adjustment to Active arm at Week 12
    mask = week12 & active
    out.loc[mask, "SystolicBP"] = out.loc[mask, "SystolicBP"] + adjustment

    # Re-clip after adjustment
    out.loc[mask, "SystolicBP"] = np.clip(out.loc[mask, "SystolicBP"], 95, 200).astype(int)

    # ===== Sample to exact target size =====
    # Group by treatment arm and ensure balanced
    active_df = out[out["TreatmentArm"] == "Active"]
    placebo_df = out[out["TreatmentArm"] == "Placebo"]

    # Get unique subjects per arm
    active_subjects = active_df["SubjectID"].unique()
    placebo_subjects = placebo_df["SubjectID"].unique()

    # Sample subjects
    if len(active_subjects) > n_per_arm:
        active_subjects = rng.choice(active_subjects, size=n_per_arm, replace=False)
    if len(placebo_subjects) > n_per_arm:
        placebo_subjects = rng.choice(placebo_subjects, size=n_per_arm, replace=False)

    # Filter to selected subjects
    out = out[
        out["SubjectID"].isin(active_subjects) | out["SubjectID"].isin(placebo_subjects)
    ].reset_index(drop=True)

    # ===== Add 1-2 fever rows (Temperature > 38°C) =====
    fever_mask = out["Temperature"] > 38.0
    current_fever_count = fever_mask.sum()

    if current_fever_count < 1:
        # Add 1 fever
        idx = rng.choice(out.index, size=1)
        out.loc[idx, "Temperature"] = rng.uniform(38.1, 39.5, size=1)
    elif current_fever_count > 2:
        # Remove excess fevers
        fever_indices = out[fever_mask].index
        to_fix = rng.choice(fever_indices, size=current_fever_count - 2, replace=False)
        out.loc[to_fix, "Temperature"] = rng.uniform(36.5, 37.8, size=len(to_fix))

    # Ensure fever rows have HR >= 67
    fever_mask = out["Temperature"] > 38.0
    low_hr = out["HeartRate"] < 67
    to_fix = fever_mask & low_hr
    if to_fix.any():
        out.loc[to_fix, "HeartRate"] = rng.integers(67, 100, size=to_fix.sum())

    # Sort by SubjectID and VisitName for clean output
    visit_order = {v: i for i, v in enumerate(VISITS)}
    out["_visit_order"] = out["VisitName"].map(visit_order)
    out = out.sort_values(["SubjectID", "_visit_order"]).drop(columns=["_visit_order"])

    return out.reset_index(drop=True)
