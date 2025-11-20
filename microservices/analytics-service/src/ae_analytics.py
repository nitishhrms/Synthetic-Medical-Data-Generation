"""
Adverse Events (AE) Analytics Module
Comprehensive adverse event analysis for clinical trials

Functions:
1. calculate_ae_summary() - AE frequency tables by SOC, PT, severity, relationship
2. analyze_treatment_emergent_aes() - Treatment-emergent AE analysis
3. analyze_soc_distribution() - System Organ Class (SOC) analysis per MedDRA
4. compare_ae_quality() - Real vs synthetic AE data quality assessment

Statistical Methods:
- Frequency tables (SOC, PT, severity)
- Fisher's exact test for treatment comparisons
- Time-to-first-AE analysis
- Chi-square tests for distribution similarity
- Incidence rate calculations

MedDRA Terminology:
- SOC: System Organ Class (primary classification)
- PT: Preferred Term (specific AE term)
- SAE: Serious Adverse Event
- Related: Relationship to study treatment
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from scipy import stats
from datetime import datetime, timedelta


# MedDRA System Organ Class (SOC) - Common categories
MEDDRA_SOC_EXAMPLES = {
    "Gastrointestinal disorders": ["Nausea", "Vomiting", "Diarrhea", "Constipation", "Abdominal pain"],
    "Nervous system disorders": ["Headache", "Dizziness", "Somnolence", "Tremor", "Seizure"],
    "Skin and subcutaneous tissue disorders": ["Rash", "Pruritus", "Urticaria", "Dermatitis", "Photosensitivity"],
    "General disorders and administration site conditions": ["Fatigue", "Pyrexia", "Edema", "Chest pain", "Pain"],
    "Infections and infestations": ["Upper respiratory tract infection", "Urinary tract infection", "Nasopharyngitis", "Influenza"],
    "Cardiac disorders": ["Palpitations", "Tachycardia", "Bradycardia", "Atrial fibrillation", "Chest discomfort"],
    "Respiratory, thoracic and mediastinal disorders": ["Cough", "Dyspnea", "Nasal congestion", "Wheezing", "Throat irritation"],
    "Musculoskeletal and connective tissue disorders": ["Back pain", "Arthralgia", "Myalgia", "Muscle spasms", "Joint swelling"],
    "Psychiatric disorders": ["Insomnia", "Anxiety", "Depression", "Confusional state", "Agitation"],
    "Blood and lymphatic system disorders": ["Anemia", "Thrombocytopenia", "Leukopenia", "Neutropenia", "Lymphadenopathy"],
    "Metabolism and nutrition disorders": ["Decreased appetite", "Hyperglycemia", "Hypoglycemia", "Hypokalemia", "Dehydration"],
    "Eye disorders": ["Vision blurred", "Dry eye", "Eye pain", "Conjunctivitis", "Photophobia"],
    "Ear and labyrinth disorders": ["Vertigo", "Tinnitus", "Ear pain", "Hearing impaired"],
    "Vascular disorders": ["Hypertension", "Hypotension", "Flushing", "Hot flush", "Hematoma"],
    "Renal and urinary disorders": ["Dysuria", "Hematuria", "Urinary frequency", "Urinary retention", "Proteinuria"],
    "Hepatobiliary disorders": ["Hepatic enzyme increased", "Hyperbilirubinemia", "Jaundice", "Hepatitis"],
    "Reproductive system and breast disorders": ["Erectile dysfunction", "Menstrual disorder", "Breast pain", "Dysmenorrhea"]
}


def infer_soc_from_pt(pt: str) -> str:
    """
    Infer System Organ Class (SOC) from Preferred Term (PT)

    Uses a simple lookup based on common MedDRA mappings.
    In production, this would use official MedDRA dictionary.
    """
    pt_lower = pt.lower()

    for soc, pts in MEDDRA_SOC_EXAMPLES.items():
        for example_pt in pts:
            if example_pt.lower() in pt_lower or pt_lower in example_pt.lower():
                return soc

    # Default to General disorders if no match
    return "General disorders and administration site conditions"


def calculate_ae_summary(ae_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate AE frequency tables by SOC, PT, severity, relationship

    Args:
        ae_df: DataFrame with columns:
            - SubjectID
            - PreferredTerm (PT): Specific AE term
            - SystemOrganClass (SOC): MedDRA SOC (optional, will infer if missing)
            - Severity: "Mild", "Moderate", or "Severe"
            - Serious: Boolean (SAE flag)
            - RelatedToTreatment: "Related", "Not Related", "Possibly Related"
            - TreatmentArm (optional)
            - OnsetDate (optional)

    Returns:
        Dictionary with:
        - overall_summary: Total AEs, subjects with AEs, AE rate
        - by_soc: Frequency by System Organ Class
        - by_pt: Frequency by Preferred Term (top 20)
        - by_severity: Distribution by severity
        - by_relationship: Distribution by relationship to treatment
        - sae_summary: Serious AE statistics
        - by_arm: Comparisons by treatment arm (if available)
    """
    result = {
        "overall_summary": {},
        "by_soc": {},
        "by_pt": {},
        "by_severity": {},
        "by_relationship": {},
        "sae_summary": {},
        "by_arm": {}
    }

    # Infer SOC if not provided
    if "SystemOrganClass" not in ae_df.columns or ae_df["SystemOrganClass"].isna().all():
        ae_df["SystemOrganClass"] = ae_df["PreferredTerm"].apply(infer_soc_from_pt)

    # Overall summary
    total_aes = len(ae_df)
    subjects_with_aes = ae_df["SubjectID"].nunique()

    result["overall_summary"] = {
        "total_aes": total_aes,
        "subjects_with_aes": subjects_with_aes,
        "unique_pts": ae_df["PreferredTerm"].nunique(),
        "unique_socs": ae_df["SystemOrganClass"].nunique()
    }

    # By SOC
    soc_counts = ae_df["SystemOrganClass"].value_counts()
    soc_subject_counts = ae_df.groupby("SystemOrganClass")["SubjectID"].nunique()

    for soc in soc_counts.index:
        result["by_soc"][soc] = {
            "ae_count": int(soc_counts[soc]),
            "subject_count": int(soc_subject_counts[soc]),
            "ae_rate": round(float(soc_counts[soc] / total_aes * 100), 1)
        }

    # Sort by AE count descending
    result["by_soc"] = dict(sorted(result["by_soc"].items(),
                                   key=lambda x: x[1]["ae_count"],
                                   reverse=True))

    # By PT (top 20)
    pt_counts = ae_df["PreferredTerm"].value_counts().head(20)
    pt_subject_counts = ae_df.groupby("PreferredTerm")["SubjectID"].nunique()

    for pt in pt_counts.index:
        result["by_pt"][pt] = {
            "ae_count": int(pt_counts[pt]),
            "subject_count": int(pt_subject_counts[pt]),
            "incidence_rate": round(float(pt_subject_counts[pt] / subjects_with_aes * 100), 1)
        }

    # By severity
    if "Severity" in ae_df.columns:
        severity_counts = ae_df["Severity"].value_counts()
        result["by_severity"] = {
            severity: {
                "count": int(count),
                "percentage": round(float(count / total_aes * 100), 1)
            }
            for severity, count in severity_counts.items()
        }

    # By relationship
    if "RelatedToTreatment" in ae_df.columns:
        rel_counts = ae_df["RelatedToTreatment"].value_counts()
        result["by_relationship"] = {
            rel: {
                "count": int(count),
                "percentage": round(float(count / total_aes * 100), 1)
            }
            for rel, count in rel_counts.items()
        }

    # SAE summary
    if "Serious" in ae_df.columns:
        saes = ae_df[ae_df["Serious"] == True]
        result["sae_summary"] = {
            "total_saes": len(saes),
            "subjects_with_saes": saes["SubjectID"].nunique() if len(saes) > 0 else 0,
            "sae_rate": round(len(saes) / total_aes * 100, 1) if total_aes > 0 else 0,
            "sae_by_soc": saes["SystemOrganClass"].value_counts().to_dict() if len(saes) > 0 else {}
        }

    # By treatment arm
    if "TreatmentArm" in ae_df.columns:
        for arm in ae_df["TreatmentArm"].unique():
            arm_data = ae_df[ae_df["TreatmentArm"] == arm]

            result["by_arm"][arm] = {
                "total_aes": len(arm_data),
                "subjects_with_aes": arm_data["SubjectID"].nunique(),
                "top_5_pts": arm_data["PreferredTerm"].value_counts().head(5).to_dict()
            }

    return result


def analyze_treatment_emergent_aes(ae_df: pd.DataFrame,
                                   treatment_start_date: str = None) -> Dict[str, Any]:
    """
    Analyze treatment-emergent adverse events (TEAEs)

    TEAEs are AEs that:
    - Start on or after first dose of study treatment
    - Were not present at baseline, or worsened after treatment start

    Args:
        ae_df: DataFrame with columns:
            - SubjectID
            - PreferredTerm
            - OnsetDate: Date AE started (YYYY-MM-DD format)
            - TreatmentArm
            - Severity
            - Serious (optional)

        treatment_start_date: Reference start date (default: earliest OnsetDate)

    Returns:
        Dictionary with:
        - teae_summary: Overall TEAE statistics
        - time_to_first_ae: Distribution of time to first AE
        - teae_by_arm: TEAE comparison by treatment arm
        - early_vs_late: Early (≤30 days) vs late (>30 days) AEs
    """
    result = {
        "teae_summary": {},
        "time_to_first_ae": {},
        "teae_by_arm": {},
        "early_vs_late": {}
    }

    # Convert OnsetDate to datetime
    if "OnsetDate" in ae_df.columns:
        ae_df["OnsetDate"] = pd.to_datetime(ae_df["OnsetDate"], errors="coerce")

        # Determine treatment start date
        if treatment_start_date:
            ref_date = pd.to_datetime(treatment_start_date)
        else:
            ref_date = ae_df["OnsetDate"].min()

        # Calculate days from treatment start
        ae_df["DaysFromStart"] = (ae_df["OnsetDate"] - ref_date).dt.days

        # Filter for TEAEs (onset on or after treatment start)
        teaes = ae_df[ae_df["DaysFromStart"] >= 0].copy()

        # Overall TEAE summary
        result["teae_summary"] = {
            "total_teaes": len(teaes),
            "subjects_with_teaes": teaes["SubjectID"].nunique(),
            "teae_rate": round(len(teaes) / len(ae_df) * 100, 1) if len(ae_df) > 0 else 0,
            "median_onset_day": float(teaes["DaysFromStart"].median()) if len(teaes) > 0 else 0
        }

        # Time to first AE per subject
        first_ae_per_subject = teaes.groupby("SubjectID")["DaysFromStart"].min()

        result["time_to_first_ae"] = {
            "mean_days": round(float(first_ae_per_subject.mean()), 1),
            "median_days": round(float(first_ae_per_subject.median()), 1),
            "min_days": int(first_ae_per_subject.min()),
            "max_days": int(first_ae_per_subject.max()),
            "distribution": {
                "0-7_days": int((first_ae_per_subject <= 7).sum()),
                "8-30_days": int(((first_ae_per_subject > 7) & (first_ae_per_subject <= 30)).sum()),
                "31-90_days": int(((first_ae_per_subject > 30) & (first_ae_per_subject <= 90)).sum()),
                ">90_days": int((first_ae_per_subject > 90).sum())
            }
        }

        # TEAE by treatment arm
        if "TreatmentArm" in teaes.columns:
            for arm in teaes["TreatmentArm"].unique():
                arm_teaes = teaes[teaes["TreatmentArm"] == arm]
                arm_first_ae = arm_teaes.groupby("SubjectID")["DaysFromStart"].min()

                result["teae_by_arm"][arm] = {
                    "total_teaes": len(arm_teaes),
                    "subjects_with_teaes": arm_teaes["SubjectID"].nunique(),
                    "median_onset_day": round(float(arm_first_ae.median()), 1) if len(arm_first_ae) > 0 else 0,
                    "top_5_teaes": arm_teaes["PreferredTerm"].value_counts().head(5).to_dict()
                }

        # Early vs late TEAEs
        early_teaes = teaes[teaes["DaysFromStart"] <= 30]
        late_teaes = teaes[teaes["DaysFromStart"] > 30]

        result["early_vs_late"] = {
            "early_teaes": {
                "count": len(early_teaes),
                "percentage": round(len(early_teaes) / len(teaes) * 100, 1) if len(teaes) > 0 else 0,
                "top_3_pts": early_teaes["PreferredTerm"].value_counts().head(3).to_dict()
            },
            "late_teaes": {
                "count": len(late_teaes),
                "percentage": round(len(late_teaes) / len(teaes) * 100, 1) if len(teaes) > 0 else 0,
                "top_3_pts": late_teaes["PreferredTerm"].value_counts().head(3).to_dict()
            }
        }
    else:
        result["error"] = "OnsetDate column required for TEAE analysis"

    return result


def analyze_soc_distribution(ae_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze System Organ Class (SOC) distribution per MedDRA

    Provides detailed SOC-level analysis including:
    - Most frequent SOCs by treatment arm
    - SAE distribution by SOC
    - PT distribution within each SOC
    - Fisher's exact test for arm comparisons

    Args:
        ae_df: DataFrame with columns:
            - SubjectID
            - PreferredTerm
            - SystemOrganClass
            - TreatmentArm
            - Serious (optional)

    Returns:
        Dictionary with:
        - soc_ranking: SOCs ranked by frequency
        - soc_by_arm: SOC distribution by treatment arm
        - soc_details: Detailed PT breakdown within each SOC
        - sae_by_soc: SAE distribution by SOC
        - statistical_tests: Fisher's exact test results
    """
    result = {
        "soc_ranking": [],
        "soc_by_arm": {},
        "soc_details": {},
        "sae_by_soc": {},
        "statistical_tests": {}
    }

    # Infer SOC if not provided
    if "SystemOrganClass" not in ae_df.columns or ae_df["SystemOrganClass"].isna().all():
        ae_df["SystemOrganClass"] = ae_df["PreferredTerm"].apply(infer_soc_from_pt)

    # SOC ranking
    soc_counts = ae_df.groupby("SystemOrganClass").agg({
        "SubjectID": "nunique",
        "PreferredTerm": "count"
    }).rename(columns={"SubjectID": "subject_count", "PreferredTerm": "ae_count"})

    soc_counts = soc_counts.sort_values("ae_count", ascending=False)

    result["soc_ranking"] = [
        {
            "soc": soc,
            "ae_count": int(row["ae_count"]),
            "subject_count": int(row["subject_count"]),
            "incidence_rate": round(row["subject_count"] / ae_df["SubjectID"].nunique() * 100, 1)
        }
        for soc, row in soc_counts.iterrows()
    ]

    # SOC by treatment arm
    if "TreatmentArm" in ae_df.columns:
        for arm in ae_df["TreatmentArm"].unique():
            arm_data = ae_df[ae_df["TreatmentArm"] == arm]
            arm_soc_counts = arm_data["SystemOrganClass"].value_counts()

            result["soc_by_arm"][arm] = {
                soc: {
                    "count": int(count),
                    "subjects": int(arm_data[arm_data["SystemOrganClass"] == soc]["SubjectID"].nunique())
                }
                for soc, count in arm_soc_counts.items()
            }

        # Fisher's exact test for most common SOCs (Active vs Placebo)
        if len(ae_df["TreatmentArm"].unique()) == 2:
            arms = list(ae_df["TreatmentArm"].unique())
            arm1, arm2 = arms[0], arms[1]

            arm1_subjects = ae_df[ae_df["TreatmentArm"] == arm1]["SubjectID"].nunique()
            arm2_subjects = ae_df[ae_df["TreatmentArm"] == arm2]["SubjectID"].nunique()

            for soc in soc_counts.head(10).index:
                arm1_with_soc = ae_df[(ae_df["TreatmentArm"] == arm1) &
                                      (ae_df["SystemOrganClass"] == soc)]["SubjectID"].nunique()
                arm2_with_soc = ae_df[(ae_df["TreatmentArm"] == arm2) &
                                      (ae_df["SystemOrganClass"] == soc)]["SubjectID"].nunique()

                # 2x2 contingency table
                table = [
                    [arm1_with_soc, arm1_subjects - arm1_with_soc],
                    [arm2_with_soc, arm2_subjects - arm2_with_soc]
                ]

                # Fisher's exact test
                odds_ratio, p_value = stats.fisher_exact(table)

                result["statistical_tests"][soc] = {
                    "arm1": arm1,
                    "arm1_subjects_with_soc": arm1_with_soc,
                    "arm1_incidence": round(arm1_with_soc / arm1_subjects * 100, 1),
                    "arm2": arm2,
                    "arm2_subjects_with_soc": arm2_with_soc,
                    "arm2_incidence": round(arm2_with_soc / arm2_subjects * 100, 1),
                    "odds_ratio": round(float(odds_ratio), 3),
                    "p_value": round(float(p_value), 4),
                    "significant": p_value < 0.05
                }

    # SOC details (top 5 PTs within each SOC)
    for soc in soc_counts.head(10).index:
        soc_aes = ae_df[ae_df["SystemOrganClass"] == soc]
        pt_counts = soc_aes["PreferredTerm"].value_counts().head(5)

        result["soc_details"][soc] = {
            "total_aes": len(soc_aes),
            "top_pts": [
                {
                    "pt": pt,
                    "count": int(count),
                    "percentage": round(count / len(soc_aes) * 100, 1)
                }
                for pt, count in pt_counts.items()
            ]
        }

    # SAE by SOC
    if "Serious" in ae_df.columns:
        saes = ae_df[ae_df["Serious"] == True]
        sae_soc_counts = saes["SystemOrganClass"].value_counts()

        result["sae_by_soc"] = {
            soc: {
                "sae_count": int(count),
                "subjects_with_sae": int(saes[saes["SystemOrganClass"] == soc]["SubjectID"].nunique())
            }
            for soc, count in sae_soc_counts.items()
        }

    return result


def compare_ae_quality(real_ae: pd.DataFrame, synthetic_ae: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare real vs synthetic AE data quality

    Validates that synthetic AE data matches real-world clinical trial AE patterns
    using distribution similarity metrics.

    Args:
        real_ae: Real AE data DataFrame
        synthetic_ae: Synthetic AE data DataFrame
        Both must have: PreferredTerm, SystemOrganClass, Severity, RelatedToTreatment

    Returns:
        Dictionary with:
        - soc_distribution_similarity: Chi-square test for SOC distribution
        - pt_distribution_similarity: Top 20 PT distribution comparison
        - severity_distribution: Chi-square test for severity
        - relationship_distribution: Chi-square test for relationship
        - overall_quality_score: Aggregate quality (0-1)
        - interpretation: Quality assessment
    """
    result = {
        "soc_distribution_similarity": {},
        "pt_distribution_similarity": {},
        "severity_distribution": {},
        "relationship_distribution": {},
        "overall_quality_score": 0.0,
        "interpretation": ""
    }

    # Infer SOC if not provided
    for df in [real_ae, synthetic_ae]:
        if "SystemOrganClass" not in df.columns or df["SystemOrganClass"].isna().all():
            df["SystemOrganClass"] = df["PreferredTerm"].apply(infer_soc_from_pt)

    quality_scores = []

    # SOC distribution similarity
    real_soc = real_ae["SystemOrganClass"].value_counts(normalize=True)
    synthetic_soc = synthetic_ae["SystemOrganClass"].value_counts(normalize=True)

    # Align distributions
    all_socs = list(set(real_soc.index) | set(synthetic_soc.index))
    real_soc_aligned = [real_soc.get(soc, 0) for soc in all_socs]
    synthetic_soc_aligned = [synthetic_soc.get(soc, 0) for soc in all_socs]

    # Convert proportions to counts for chi-square
    n_real = len(real_ae)
    n_synthetic = len(synthetic_ae)
    real_counts = [int(p * n_real) for p in real_soc_aligned]
    synthetic_counts = [int(p * n_synthetic) for p in synthetic_soc_aligned]

    if sum(real_counts) > 0 and sum(synthetic_counts) > 0:
        chi2, p_value = stats.chisquare(synthetic_counts, real_counts)

        result["soc_distribution_similarity"] = {
            "chi_square": round(float(chi2), 3),
            "p_value": round(float(p_value), 4),
            "distributions_similar": p_value > 0.05
        }

        quality_scores.append(1.0 if p_value > 0.05 else 0.5)

    # PT distribution (top 20)
    real_pt = real_ae["PreferredTerm"].value_counts(normalize=True).head(20)
    synthetic_pt = synthetic_ae["PreferredTerm"].value_counts(normalize=True).head(20)

    # Jaccard similarity for PT overlap
    real_pt_set = set(real_pt.index)
    synthetic_pt_set = set(synthetic_pt.index)
    jaccard = len(real_pt_set & synthetic_pt_set) / len(real_pt_set | synthetic_pt_set) if len(real_pt_set | synthetic_pt_set) > 0 else 0

    result["pt_distribution_similarity"] = {
        "top_20_overlap": len(real_pt_set & synthetic_pt_set),
        "jaccard_similarity": round(float(jaccard), 3),
        "interpretation": "Good" if jaccard > 0.6 else "Fair" if jaccard > 0.4 else "Poor"
    }

    quality_scores.append(jaccard)

    # Severity distribution
    if "Severity" in real_ae.columns and "Severity" in synthetic_ae.columns:
        real_sev = real_ae["Severity"].value_counts()
        synthetic_sev = synthetic_ae["Severity"].value_counts()

        all_sevs = list(set(real_sev.index) | set(synthetic_sev.index))
        real_sev_counts = [real_sev.get(sev, 0) for sev in all_sevs]
        synthetic_sev_counts = [synthetic_sev.get(sev, 0) for sev in all_sevs]

        if sum(real_sev_counts) > 0 and sum(synthetic_sev_counts) > 0:
            chi2, p_value = stats.chisquare(synthetic_sev_counts, real_sev_counts)

            result["severity_distribution"] = {
                "chi_square": round(float(chi2), 3),
                "p_value": round(float(p_value), 4),
                "distributions_similar": p_value > 0.05
            }

            quality_scores.append(1.0 if p_value > 0.05 else 0.5)

    # Relationship distribution
    if "RelatedToTreatment" in real_ae.columns and "RelatedToTreatment" in synthetic_ae.columns:
        real_rel = real_ae["RelatedToTreatment"].value_counts()
        synthetic_rel = synthetic_ae["RelatedToTreatment"].value_counts()

        all_rels = list(set(real_rel.index) | set(synthetic_rel.index))
        real_rel_counts = [real_rel.get(rel, 0) for rel in all_rels]
        synthetic_rel_counts = [synthetic_rel.get(rel, 0) for rel in all_rels]

        if sum(real_rel_counts) > 0 and sum(synthetic_rel_counts) > 0:
            chi2, p_value = stats.chisquare(synthetic_rel_counts, real_rel_counts)

            result["relationship_distribution"] = {
                "chi_square": round(float(chi2), 3),
                "p_value": round(float(p_value), 4),
                "distributions_similar": p_value > 0.05
            }

            quality_scores.append(1.0 if p_value > 0.05 else 0.5)

    # Overall quality score
    if quality_scores:
        overall_quality = np.mean(quality_scores)
        result["overall_quality_score"] = round(float(overall_quality), 3)

        if overall_quality >= 0.85:
            result["interpretation"] = "Excellent - Synthetic AE data closely matches real patterns"
        elif overall_quality >= 0.70:
            result["interpretation"] = "Good - Synthetic data is usable with minor differences"
        else:
            result["interpretation"] = "Needs improvement - Review generation parameters"

    return result
