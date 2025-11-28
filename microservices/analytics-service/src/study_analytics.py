"""
Comprehensive Study Analytics Module
Integrates all domains for holistic trial assessment

This module provides comprehensive study-level analytics by integrating:
- Demographics analytics
- Vitals analytics
- Laboratory analytics
- Adverse events analytics
- AACT benchmarking

Key Features:
- Cross-domain summary generation
- Inter-domain correlation analysis
- Executive trial dashboard with KPIs
- Integrated quality assessment
- AACT context for regulatory readiness
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from collections import Counter
from datetime import datetime

# Import analytics modules
from demographics_analytics import (
    calculate_baseline_characteristics,
    assess_treatment_arm_balance
)
from labs_analytics import (
    calculate_labs_summary,
    detect_abnormal_labs,
    detect_safety_signals
)
from ae_analytics import (
    calculate_ae_summary,
    analyze_soc_distribution
)
from aact_integration import (
    compare_study_to_aact,
    benchmark_adverse_events
)


def generate_comprehensive_summary(
    demographics_data: Optional[pd.DataFrame] = None,
    vitals_data: Optional[pd.DataFrame] = None,
    labs_data: Optional[pd.DataFrame] = None,
    ae_data: Optional[pd.DataFrame] = None,
    indication: str = "hypertension",
    phase: str = "Phase 3"
) -> Dict[str, Any]:
    """
    Generate comprehensive study summary across all domains

    Integrates demographics, vitals, labs, and AEs into a unified
    study summary suitable for clinical study reports and regulatory submissions.

    Args:
        demographics_data: Demographics DataFrame (optional)
        vitals_data: Vitals DataFrame (optional)
        labs_data: Labs DataFrame (optional)
        ae_data: Adverse events DataFrame (optional)
        indication: Disease indication for AACT benchmarking
        phase: Trial phase

    Returns:
        Dict containing:
        - study_overview: Basic study statistics
        - demographics_summary: Key demographic metrics
        - efficacy_summary: Vitals-based efficacy assessment
        - safety_summary: Labs + AEs safety assessment
        - aact_benchmark: Comparison with real-world trials
        - data_quality: Completeness and quality metrics
        - regulatory_readiness: Assessment for submission
    """
    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "indication": indication,
        "phase": phase
    }

    # ========== STUDY OVERVIEW ==========
    study_overview = {
        "data_domains_available": [],
        "total_subjects": 0,
        "total_observations": 0
    }

    if demographics_data is not None and not demographics_data.empty:
        study_overview["data_domains_available"].append("Demographics")
        study_overview["total_subjects"] = demographics_data["SubjectID"].nunique()

    if vitals_data is not None and not vitals_data.empty:
        study_overview["data_domains_available"].append("Vitals")
        study_overview["total_observations"] += len(vitals_data)
        if study_overview["total_subjects"] == 0:
            study_overview["total_subjects"] = vitals_data["SubjectID"].nunique()

    if labs_data is not None and not labs_data.empty:
        study_overview["data_domains_available"].append("Labs")
        study_overview["total_observations"] += len(labs_data)
        if study_overview["total_subjects"] == 0:
            study_overview["total_subjects"] = labs_data["SubjectID"].nunique()

    if ae_data is not None and not ae_data.empty:
        study_overview["data_domains_available"].append("Adverse Events")
        study_overview["total_observations"] += len(ae_data)
        if study_overview["total_subjects"] == 0:
            study_overview["total_subjects"] = ae_data["SubjectID"].nunique()

    summary["study_overview"] = study_overview

    # ========== DEMOGRAPHICS SUMMARY ==========
    if demographics_data is not None and not demographics_data.empty:
        try:
            baseline = calculate_baseline_characteristics(demographics_data)
            balance = assess_treatment_arm_balance(demographics_data)

            summary["demographics_summary"] = {
                "n_subjects": len(demographics_data),
                "mean_age": baseline.get("overall", {}).get("Age", {}).get("mean"),
                "gender_distribution": baseline.get("overall", {}).get("Gender", {}),
                "treatment_arms": list(baseline.get("by_arm", {}).keys()),
                "randomization_balance": balance.get("overall_balance", "Unknown"),
                "imbalanced_variables": balance.get("imbalanced_variables", [])
            }
        except Exception as e:
            summary["demographics_summary"] = {"error": str(e)}
    else:
        summary["demographics_summary"] = {"status": "No demographics data provided"}

    # ========== EFFICACY SUMMARY (Vitals-based) ==========
    if vitals_data is not None and not vitals_data.empty:
        try:
            # Calculate Week 12 / endpoint efficacy
            # Check if we have treatment arms
            if "TreatmentArm" in vitals_data.columns:
                # Get last visit per subject (endpoint)
                visits = sorted(vitals_data["VisitName"].unique())
                if len(visits) > 0:
                    endpoint_visit = visits[-1]
                    endpoint_data = vitals_data[vitals_data["VisitName"] == endpoint_visit]

                    # Calculate by arm
                    efficacy_by_arm = {}
                    for arm in endpoint_data["TreatmentArm"].unique():
                        arm_data = endpoint_data[endpoint_data["TreatmentArm"] == arm]
                        efficacy_by_arm[arm] = {
                            "n": len(arm_data),
                            "mean_sbp": float(arm_data["SystolicBP"].mean()) if "SystolicBP" in arm_data.columns else None,
                            "mean_dbp": float(arm_data["DiastolicBP"].mean()) if "DiastolicBP" in arm_data.columns else None,
                            "mean_hr": float(arm_data["HeartRate"].mean()) if "HeartRate" in arm_data.columns else None
                        }

                    # Calculate treatment effect (if Active vs Placebo)
                    if "Active" in efficacy_by_arm and "Placebo" in efficacy_by_arm:
                        treatment_effect_sbp = (efficacy_by_arm["Active"]["mean_sbp"] or 0) - (efficacy_by_arm["Placebo"]["mean_sbp"] or 0)
                    else:
                        treatment_effect_sbp = None

                    summary["efficacy_summary"] = {
                        "endpoint_visit": endpoint_visit,
                        "by_arm": efficacy_by_arm,
                        "treatment_effect_sbp": treatment_effect_sbp,
                        "status": "Calculated from endpoint data"
                    }
                else:
                    summary["efficacy_summary"] = {"status": "No visits found"}
            else:
                summary["efficacy_summary"] = {"status": "No treatment arm data"}
        except Exception as e:
            summary["efficacy_summary"] = {"error": str(e)}
    else:
        summary["efficacy_summary"] = {"status": "No vitals data provided"}

    # ========== SAFETY SUMMARY (Labs + AEs) ==========
    safety_summary = {
        "labs_safety": {},
        "ae_safety": {},
        "overall_safety_assessment": ""
    }

    # Labs safety
    if labs_data is not None and not labs_data.empty:
        try:
            abnormal_labs = detect_abnormal_labs(labs_data)
            safety_signals = detect_safety_signals(labs_data)

            safety_summary["labs_safety"] = {
                "total_lab_observations": len(labs_data),
                "abnormal_rate": abnormal_labs.get("abnormal_rate", 0),
                "grade_3_4_count": abnormal_labs.get("summary_by_grade", {}).get("Grade 3", 0) +
                                   abnormal_labs.get("summary_by_grade", {}).get("Grade 4", 0),
                "hys_law_cases": len(safety_signals.get("hys_law_cases", [])),
                "kidney_decline_cases": len(safety_signals.get("kidney_decline_cases", [])),
                "bone_marrow_cases": len(safety_signals.get("bone_marrow_cases", []))
            }
        except Exception as e:
            safety_summary["labs_safety"] = {"error": str(e)}
    else:
        safety_summary["labs_safety"] = {"status": "No labs data provided"}

    # AE safety
    if ae_data is not None and not ae_data.empty:
        try:
            ae_summary_result = calculate_ae_summary(ae_data)
            soc_analysis = analyze_soc_distribution(ae_data)

            safety_summary["ae_safety"] = {
                "total_aes": ae_summary_result.get("overall_summary", {}).get("total_aes", 0),
                "subjects_with_aes": ae_summary_result.get("overall_summary", {}).get("subjects_with_any_ae", 0),
                "ae_rate": ae_summary_result.get("overall_summary", {}).get("subjects_with_any_ae_pct", 0),
                "serious_aes": ae_summary_result.get("sae_summary", {}).get("total_saes", 0),
                "sae_rate": ae_summary_result.get("sae_summary", {}).get("sae_rate", 0),
                "most_common_soc": soc_analysis.get("soc_ranking", [{}])[0].get("soc", "Unknown") if soc_analysis.get("soc_ranking") else "Unknown",
                "top_3_aes": list(ae_summary_result.get("by_pt", {}).keys())[:3]
            }
        except Exception as e:
            safety_summary["ae_safety"] = {"error": str(e)}
    else:
        safety_summary["ae_safety"] = {"status": "No AE data provided"}

    # Overall safety assessment
    safety_flags = []
    if safety_summary["labs_safety"].get("hys_law_cases", 0) > 0:
        safety_flags.append(f"⚠ {safety_summary['labs_safety']['hys_law_cases']} Hy's Law cases detected")
    if safety_summary["labs_safety"].get("grade_3_4_count", 0) > 0:
        safety_flags.append(f"⚠ {safety_summary['labs_safety']['grade_3_4_count']} Grade 3-4 lab abnormalities")
    if safety_summary["ae_safety"].get("sae_rate", 0) > 10:
        safety_flags.append(f"⚠ High SAE rate: {safety_summary['ae_safety']['sae_rate']:.1f}%")

    if len(safety_flags) == 0:
        safety_summary["overall_safety_assessment"] = "✅ No significant safety signals detected"
    else:
        safety_summary["overall_safety_assessment"] = "; ".join(safety_flags)

    summary["safety_summary"] = safety_summary

    # ========== AACT BENCHMARK ==========
    if vitals_data is not None and not vitals_data.empty and study_overview["total_subjects"] > 0:
        try:
            # Use treatment effect if available
            treatment_effect = summary.get("efficacy_summary", {}).get("treatment_effect_sbp", -5.0)
            if treatment_effect is None:
                treatment_effect = -5.0  # Default

            aact_comparison = compare_study_to_aact(
                n_subjects=study_overview["total_subjects"],
                indication=indication,
                phase=phase,
                treatment_effect=treatment_effect
            )

            summary["aact_benchmark"] = {
                "similarity_score": aact_comparison.get("similarity_score"),
                "enrollment_percentile": aact_comparison.get("enrollment_benchmark", {}).get("percentile"),
                "treatment_effect_percentile": aact_comparison.get("treatment_effect_benchmark", {}).get("percentile"),
                "overall_assessment": aact_comparison.get("interpretation", {}).get("overall_assessment"),
                "recommendation": aact_comparison.get("interpretation", {}).get("recommendation")
            }

            # Add AE benchmark if available
            if ae_data is not None and not ae_data.empty:
                ae_benchmark = benchmark_adverse_events(ae_data, indication, phase)
                summary["aact_benchmark"]["ae_similarity_score"] = ae_benchmark.get("similarity_score")
                summary["aact_benchmark"]["ae_assessment"] = ae_benchmark.get("interpretation", {}).get("overall_assessment")
        except Exception as e:
            summary["aact_benchmark"] = {"error": str(e), "status": "AACT comparison failed"}
    else:
        summary["aact_benchmark"] = {"status": "Insufficient data for AACT comparison"}

    # ========== DATA QUALITY ==========
    data_quality = {
        "completeness": {},
        "consistency": {},
        "overall_quality_score": 0.0
    }

    # Completeness checks
    completeness_scores = []

    if demographics_data is not None and not demographics_data.empty:
        # Check key demographic fields
        required_fields = ["SubjectID", "Age", "Gender", "TreatmentArm"]
        available_fields = [f for f in required_fields if f in demographics_data.columns]
        completeness = len(available_fields) / len(required_fields)
        data_quality["completeness"]["demographics"] = completeness
        completeness_scores.append(completeness)

    if vitals_data is not None and not vitals_data.empty:
        # Check vitals completeness
        required_fields = ["SubjectID", "VisitName", "SystolicBP", "DiastolicBP"]
        available_fields = [f for f in required_fields if f in vitals_data.columns]
        completeness = len(available_fields) / len(required_fields)
        data_quality["completeness"]["vitals"] = completeness
        completeness_scores.append(completeness)

    if labs_data is not None and not labs_data.empty:
        # Check labs completeness
        required_fields = ["SubjectID", "VisitName", "TestName", "TestValue"]
        available_fields = [f for f in required_fields if f in labs_data.columns]
        completeness = len(available_fields) / len(required_fields)
        data_quality["completeness"]["labs"] = completeness
        completeness_scores.append(completeness)

    if ae_data is not None and not ae_data.empty:
        # Check AE completeness
        required_fields = ["SubjectID", "PreferredTerm", "Severity"]
        available_fields = [f for f in required_fields if f in ae_data.columns]
        completeness = len(available_fields) / len(required_fields)
        data_quality["completeness"]["ae"] = completeness
        completeness_scores.append(completeness)

    # Overall quality score
    if completeness_scores:
        data_quality["overall_quality_score"] = np.mean(completeness_scores)
    else:
        data_quality["overall_quality_score"] = 0.0

    # Quality interpretation
    quality_score = data_quality["overall_quality_score"]
    if quality_score >= 0.95:
        data_quality["quality_assessment"] = "✅ EXCELLENT - All key data fields complete"
    elif quality_score >= 0.80:
        data_quality["quality_assessment"] = "✓ GOOD - Minor data gaps"
    elif quality_score >= 0.60:
        data_quality["quality_assessment"] = "⚠ FAIR - Some data fields missing"
    else:
        data_quality["quality_assessment"] = "⚠ POOR - Significant data gaps"

    summary["data_quality"] = data_quality

    # ========== REGULATORY READINESS ==========
    regulatory_readiness = {
        "status": "",
        "requirements_met": [],
        "requirements_pending": [],
        "readiness_score": 0.0
    }

    requirements_status = []

    # Check key regulatory requirements
    if demographics_data is not None and not demographics_data.empty:
        regulatory_readiness["requirements_met"].append("Demographics baseline characteristics (Table 1)")
        requirements_status.append(True)
    else:
        regulatory_readiness["requirements_pending"].append("Demographics baseline characteristics")
        requirements_status.append(False)

    if vitals_data is not None and not vitals_data.empty:
        regulatory_readiness["requirements_met"].append("Efficacy endpoint data")
        requirements_status.append(True)
    else:
        regulatory_readiness["requirements_pending"].append("Efficacy endpoint data")
        requirements_status.append(False)

    if ae_data is not None and not ae_data.empty:
        regulatory_readiness["requirements_met"].append("Safety data (AEs)")
        requirements_status.append(True)
    else:
        regulatory_readiness["requirements_pending"].append("Safety data (AEs)")
        requirements_status.append(False)

    # AACT benchmark adds regulatory credibility
    if summary.get("aact_benchmark", {}).get("similarity_score") is not None:
        regulatory_readiness["requirements_met"].append("Real-world benchmark comparison (AACT)")
        requirements_status.append(True)
    else:
        regulatory_readiness["requirements_pending"].append("Real-world benchmark comparison")
        requirements_status.append(False)

    # Calculate readiness score
    if requirements_status:
        regulatory_readiness["readiness_score"] = sum(requirements_status) / len(requirements_status)
    else:
        regulatory_readiness["readiness_score"] = 0.0

    # Overall status
    readiness = regulatory_readiness["readiness_score"]
    if readiness >= 0.90:
        regulatory_readiness["status"] = "✅ SUBMISSION READY - All key requirements met"
    elif readiness >= 0.70:
        regulatory_readiness["status"] = "✓ NEAR READY - Minor gaps remain"
    elif readiness >= 0.50:
        regulatory_readiness["status"] = "⚠ IN PROGRESS - Significant work needed"
    else:
        regulatory_readiness["status"] = "⚠ NOT READY - Major requirements missing"

    summary["regulatory_readiness"] = regulatory_readiness

    return summary


def analyze_cross_domain_correlations(
    demographics_data: Optional[pd.DataFrame] = None,
    vitals_data: Optional[pd.DataFrame] = None,
    labs_data: Optional[pd.DataFrame] = None,
    ae_data: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Analyze correlations between different data domains

    Identifies relationships across domains (e.g., age vs BP, labs vs AEs)
    to uncover clinically meaningful patterns and potential confounders.

    Args:
        demographics_data: Demographics DataFrame (optional)
        vitals_data: Vitals DataFrame (optional)
        labs_data: Labs DataFrame (optional)
        ae_data: Adverse events DataFrame (optional)

    Returns:
        Dict containing:
        - demographics_vitals: Age/gender correlations with vitals
        - demographics_ae: Age/gender correlations with AE rates
        - labs_ae: Lab abnormalities correlated with AEs
        - vitals_labs: Vitals correlated with lab values
        - clinical_insights: Interpretation of findings
    """
    correlations = {
        "generated_at": datetime.utcnow().isoformat(),
        "domains_analyzed": []
    }

    # ========== DEMOGRAPHICS vs VITALS ==========
    if demographics_data is not None and vitals_data is not None and not demographics_data.empty and not vitals_data.empty:
        correlations["domains_analyzed"].append("Demographics-Vitals")

        try:
            # Merge on SubjectID
            # Get endpoint vitals (last visit per subject)
            visits = sorted(vitals_data["VisitName"].unique())
            if len(visits) > 0:
                endpoint_visit = visits[-1]
                endpoint_vitals = vitals_data[vitals_data["VisitName"] == endpoint_visit]

                merged = demographics_data.merge(endpoint_vitals, on="SubjectID", how="inner")

                demographics_vitals = {}

                # Age vs BP correlation
                if "Age" in merged.columns and "SystolicBP" in merged.columns:
                    age_sbp_corr, age_sbp_p = stats.pearsonr(merged["Age"].dropna(),
                                                               merged.loc[merged["Age"].notna(), "SystolicBP"].dropna())
                    demographics_vitals["age_vs_sbp"] = {
                        "correlation": float(age_sbp_corr),
                        "p_value": float(age_sbp_p),
                        "significant": age_sbp_p < 0.05,
                        "interpretation": _interpret_correlation(age_sbp_corr, age_sbp_p, "Age", "Systolic BP")
                    }

                # Gender vs BP comparison
                if "Gender" in merged.columns and "SystolicBP" in merged.columns:
                    male_sbp = merged[merged["Gender"] == "Male"]["SystolicBP"].dropna()
                    female_sbp = merged[merged["Gender"] == "Female"]["SystolicBP"].dropna()

                    if len(male_sbp) > 0 and len(female_sbp) > 0:
                        t_stat, p_val = stats.ttest_ind(male_sbp, female_sbp)
                        demographics_vitals["gender_vs_sbp"] = {
                            "male_mean": float(male_sbp.mean()),
                            "female_mean": float(female_sbp.mean()),
                            "difference": float(male_sbp.mean() - female_sbp.mean()),
                            "t_statistic": float(t_stat),
                            "p_value": float(p_val),
                            "significant": p_val < 0.05,
                            "interpretation": _interpret_gender_difference(male_sbp.mean(), female_sbp.mean(), p_val, "Systolic BP")
                        }

                correlations["demographics_vitals"] = demographics_vitals
        except Exception as e:
            correlations["demographics_vitals"] = {"error": str(e)}
    else:
        correlations["demographics_vitals"] = {"status": "Insufficient data for demographics-vitals correlation"}

    # ========== DEMOGRAPHICS vs AE RATES ==========
    if demographics_data is not None and ae_data is not None and not demographics_data.empty and not ae_data.empty:
        correlations["domains_analyzed"].append("Demographics-AE")

        try:
            # Calculate AE rate per subject
            ae_counts = ae_data.groupby("SubjectID").size().reset_index(name="ae_count")
            merged = demographics_data.merge(ae_counts, on="SubjectID", how="left")
            merged["ae_count"] = merged["ae_count"].fillna(0)

            demographics_ae = {}

            # Age vs AE rate
            if "Age" in merged.columns:
                age_ae_corr, age_ae_p = stats.pearsonr(merged["Age"].dropna(),
                                                         merged.loc[merged["Age"].notna(), "ae_count"])
                demographics_ae["age_vs_ae_rate"] = {
                    "correlation": float(age_ae_corr),
                    "p_value": float(age_ae_p),
                    "significant": age_ae_p < 0.05,
                    "interpretation": _interpret_correlation(age_ae_corr, age_ae_p, "Age", "AE rate")
                }

            # Gender vs AE rate
            if "Gender" in merged.columns:
                male_ae = merged[merged["Gender"] == "Male"]["ae_count"]
                female_ae = merged[merged["Gender"] == "Female"]["ae_count"]

                if len(male_ae) > 0 and len(female_ae) > 0:
                    u_stat, p_val = stats.mannwhitneyu(male_ae, female_ae, alternative='two-sided')
                    demographics_ae["gender_vs_ae_rate"] = {
                        "male_mean_aes": float(male_ae.mean()),
                        "female_mean_aes": float(female_ae.mean()),
                        "difference": float(male_ae.mean() - female_ae.mean()),
                        "u_statistic": float(u_stat),
                        "p_value": float(p_val),
                        "significant": p_val < 0.05,
                        "interpretation": _interpret_gender_difference(male_ae.mean(), female_ae.mean(), p_val, "AE rate")
                    }

            correlations["demographics_ae"] = demographics_ae
        except Exception as e:
            correlations["demographics_ae"] = {"error": str(e)}
    else:
        correlations["demographics_ae"] = {"status": "Insufficient data for demographics-AE correlation"}

    # ========== LABS vs AE OCCURRENCE ==========
    if labs_data is not None and ae_data is not None and not labs_data.empty and not ae_data.empty:
        correlations["domains_analyzed"].append("Labs-AE")

        try:
            # Find subjects with abnormal labs
            from labs_analytics import detect_abnormal_labs
            abnormal_result = detect_abnormal_labs(labs_data)
            abnormal_subjects = set()
            for obs in abnormal_result.get("abnormal_observations", []):
                abnormal_subjects.add(obs["SubjectID"])

            # Find subjects with AEs
            ae_subjects = set(ae_data["SubjectID"].unique())

            # Calculate overlap
            overlap = len(abnormal_subjects & ae_subjects)
            abnormal_only = len(abnormal_subjects - ae_subjects)
            ae_only = len(ae_subjects - abnormal_subjects)

            labs_ae = {
                "subjects_with_abnormal_labs": len(abnormal_subjects),
                "subjects_with_aes": len(ae_subjects),
                "subjects_with_both": overlap,
                "subjects_with_abnormal_labs_only": abnormal_only,
                "subjects_with_aes_only": ae_only,
                "overlap_rate": float(overlap / len(abnormal_subjects)) if len(abnormal_subjects) > 0 else 0.0,
                "interpretation": ""
            }

            # Interpretation
            if labs_ae["overlap_rate"] > 0.7:
                labs_ae["interpretation"] = "✓ Strong association: Most subjects with abnormal labs also had AEs"
            elif labs_ae["overlap_rate"] > 0.4:
                labs_ae["interpretation"] = "Moderate association: Many subjects with abnormal labs had AEs"
            else:
                labs_ae["interpretation"] = "Weak association: Abnormal labs and AEs largely independent"

            correlations["labs_ae"] = labs_ae
        except Exception as e:
            correlations["labs_ae"] = {"error": str(e)}
    else:
        correlations["labs_ae"] = {"status": "Insufficient data for labs-AE correlation"}

    # ========== VITALS vs LABS ==========
    if vitals_data is not None and labs_data is not None and not vitals_data.empty and not labs_data.empty:
        correlations["domains_analyzed"].append("Vitals-Labs")

        try:
            # Find common subjects and visits
            vitals_subset = vitals_data[["SubjectID", "VisitName", "SystolicBP"]].dropna()
            labs_subset = labs_data[labs_data["TestName"] == "Creatinine"][["SubjectID", "VisitName", "TestValue"]].dropna()

            if not labs_subset.empty:
                merged = vitals_subset.merge(labs_subset, on=["SubjectID", "VisitName"], how="inner")

                if len(merged) > 10:  # Need enough data points
                    sbp_creat_corr, sbp_creat_p = stats.pearsonr(merged["SystolicBP"], merged["TestValue"])

                    correlations["vitals_labs"] = {
                        "sbp_vs_creatinine": {
                            "correlation": float(sbp_creat_corr),
                            "p_value": float(sbp_creat_p),
                            "significant": sbp_creat_p < 0.05,
                            "n_observations": len(merged),
                            "interpretation": _interpret_correlation(sbp_creat_corr, sbp_creat_p, "SBP", "Creatinine")
                        }
                    }
                else:
                    correlations["vitals_labs"] = {"status": "Insufficient overlapping data points"}
            else:
                correlations["vitals_labs"] = {"status": "No Creatinine data available"}
        except Exception as e:
            correlations["vitals_labs"] = {"error": str(e)}
    else:
        correlations["vitals_labs"] = {"status": "Insufficient data for vitals-labs correlation"}

    # ========== CLINICAL INSIGHTS ==========
    insights = []

    # Check for age-related patterns
    if "demographics_vitals" in correlations and "age_vs_sbp" in correlations["demographics_vitals"]:
        age_sbp = correlations["demographics_vitals"]["age_vs_sbp"]
        if age_sbp.get("significant") and abs(age_sbp.get("correlation", 0)) > 0.3:
            insights.append(f"Age significantly correlates with blood pressure (r={age_sbp['correlation']:.2f}), suggesting age-dependent efficacy")

    # Check for gender differences
    if "demographics_vitals" in correlations and "gender_vs_sbp" in correlations["demographics_vitals"]:
        gender_sbp = correlations["demographics_vitals"]["gender_vs_sbp"]
        if gender_sbp.get("significant"):
            insights.append(f"Significant gender difference in blood pressure (Δ={gender_sbp['difference']:.1f} mmHg), consider gender-stratified analysis")

    # Check for lab-AE association
    if "labs_ae" in correlations and correlations["labs_ae"].get("overlap_rate", 0) > 0.5:
        insights.append("Strong association between lab abnormalities and AEs suggests lab monitoring is capturing safety events")

    if len(insights) == 0:
        insights.append("No significant cross-domain patterns detected")

    correlations["clinical_insights"] = insights

    return correlations


def _interpret_correlation(r: float, p: float, var1: str, var2: str) -> str:
    """Interpret correlation coefficient"""
    if p >= 0.05:
        return f"No significant correlation between {var1} and {var2}"

    abs_r = abs(r)
    strength = "strong" if abs_r > 0.7 else "moderate" if abs_r > 0.4 else "weak"
    direction = "positive" if r > 0 else "negative"

    return f"Significant {strength} {direction} correlation between {var1} and {var2} (r={r:.3f}, p={p:.4f})"


def _interpret_gender_difference(male_mean: float, female_mean: float, p: float, variable: str) -> str:
    """Interpret gender difference"""
    if p >= 0.05:
        return f"No significant gender difference in {variable}"

    diff = abs(male_mean - female_mean)
    higher = "males" if male_mean > female_mean else "females"

    return f"Significant gender difference: {higher} have {diff:.1f} units higher {variable} (p={p:.4f})"


def generate_trial_dashboard(
    demographics_data: Optional[pd.DataFrame] = None,
    vitals_data: Optional[pd.DataFrame] = None,
    labs_data: Optional[pd.DataFrame] = None,
    ae_data: Optional[pd.DataFrame] = None,
    indication: str = "hypertension",
    phase: str = "Phase 3"
) -> Dict[str, Any]:
    """
    Generate executive trial dashboard with key performance indicators

    Creates a high-level dashboard suitable for executive review, DSMB reports,
    and regulatory briefing documents. Integrates all domains with AACT context.

    Args:
        demographics_data: Demographics DataFrame (optional)
        vitals_data: Vitals DataFrame (optional)
        labs_data: Labs DataFrame (optional)
        ae_data: Adverse events DataFrame (optional)
        indication: Disease indication
        phase: Trial phase

    Returns:
        Dict containing:
        - executive_summary: High-level KPIs
        - enrollment_status: Subject enrollment and retention
        - efficacy_metrics: Key efficacy endpoints
        - safety_metrics: Key safety indicators
        - quality_metrics: Data quality and compliance
        - aact_context: Industry benchmark comparison
        - risk_flags: Critical issues requiring attention
        - recommendations: Actionable next steps
    """
    dashboard = {
        "generated_at": datetime.utcnow().isoformat(),
        "trial_name": f"{indication.capitalize()} {phase} Study",
        "indication": indication,
        "phase": phase
    }

    # ========== EXECUTIVE SUMMARY ==========
    exec_summary = {}

    # Total subjects
    n_subjects = 0
    if demographics_data is not None and not demographics_data.empty:
        n_subjects = demographics_data["SubjectID"].nunique()
    elif vitals_data is not None and not vitals_data.empty:
        n_subjects = vitals_data["SubjectID"].nunique()
    elif labs_data is not None and not labs_data.empty:
        n_subjects = labs_data["SubjectID"].nunique()

    exec_summary["total_subjects"] = n_subjects

    # Data domains
    domains = []
    if demographics_data is not None and not demographics_data.empty:
        domains.append("Demographics")
    if vitals_data is not None and not vitals_data.empty:
        domains.append("Vitals")
    if labs_data is not None and not labs_data.empty:
        domains.append("Labs")
    if ae_data is not None and not ae_data.empty:
        domains.append("AEs")

    exec_summary["data_domains"] = domains
    exec_summary["data_completeness"] = f"{len(domains)}/4 domains"

    dashboard["executive_summary"] = exec_summary

    # ========== ENROLLMENT STATUS ==========
    enrollment = {
        "total_enrolled": n_subjects,
        "target_enrollment": "Unknown",
        "percent_enrolled": "Unknown"
    }

    if demographics_data is not None and not demographics_data.empty and "TreatmentArm" in demographics_data.columns:
        arm_counts = demographics_data["TreatmentArm"].value_counts().to_dict()
        enrollment["by_treatment_arm"] = arm_counts

        # Check balance
        if len(arm_counts) == 2:
            counts = list(arm_counts.values())
            imbalance = abs(counts[0] - counts[1]) / max(counts)
            if imbalance < 0.1:
                enrollment["randomization_balance"] = "✅ Well-balanced"
            else:
                enrollment["randomization_balance"] = f"⚠ Imbalanced ({imbalance*100:.1f}% difference)"

    dashboard["enrollment_status"] = enrollment

    # ========== EFFICACY METRICS ==========
    efficacy = {}

    if vitals_data is not None and not vitals_data.empty:
        # Calculate endpoint efficacy
        visits = sorted(vitals_data["VisitName"].unique())
        if len(visits) > 0:
            endpoint_visit = visits[-1]
            efficacy["primary_endpoint_visit"] = endpoint_visit

            endpoint_data = vitals_data[vitals_data["VisitName"] == endpoint_visit]

            if "TreatmentArm" in endpoint_data.columns and "SystolicBP" in endpoint_data.columns:
                # Calculate by arm
                for arm in endpoint_data["TreatmentArm"].unique():
                    arm_data = endpoint_data[endpoint_data["TreatmentArm"] == arm]
                    efficacy[f"{arm.lower()}_mean_sbp"] = float(arm_data["SystolicBP"].mean())

                # Treatment effect
                if "active_mean_sbp" in efficacy and "placebo_mean_sbp" in efficacy:
                    treatment_effect = efficacy["active_mean_sbp"] - efficacy["placebo_mean_sbp"]
                    efficacy["treatment_effect_sbp"] = treatment_effect

                    # Interpretation
                    if treatment_effect < -10:
                        efficacy["efficacy_assessment"] = "✅ STRONG EFFECT - Clinically meaningful reduction"
                    elif treatment_effect < -5:
                        efficacy["efficacy_assessment"] = "✓ MODERATE EFFECT - Clinically relevant"
                    elif treatment_effect < 0:
                        efficacy["efficacy_assessment"] = "⚠ WEAK EFFECT - Limited clinical benefit"
                    else:
                        efficacy["efficacy_assessment"] = "⚠ NO EFFECT - Active not better than placebo"

    dashboard["efficacy_metrics"] = efficacy if efficacy else {"status": "No vitals data available"}

    # ========== SAFETY METRICS ==========
    safety = {}

    # AE metrics
    if ae_data is not None and not ae_data.empty:
        total_aes = len(ae_data)
        subjects_with_ae = ae_data["SubjectID"].nunique()
        ae_rate = (subjects_with_ae / n_subjects * 100) if n_subjects > 0 else 0

        safety["total_aes"] = total_aes
        safety["subjects_with_aes"] = subjects_with_ae
        safety["ae_rate_percent"] = ae_rate

        # SAEs
        if "Serious" in ae_data.columns:
            saes = ae_data[ae_data["Serious"] == True]
            safety["total_saes"] = len(saes)
            safety["sae_rate_percent"] = (len(saes) / total_aes * 100) if total_aes > 0 else 0

        # Top AEs
        top_aes = ae_data["PreferredTerm"].value_counts().head(5).to_dict()
        safety["top_5_aes"] = top_aes

    # Lab safety signals
    if labs_data is not None and not labs_data.empty:
        from labs_analytics import detect_safety_signals
        signals = detect_safety_signals(labs_data)

        safety["hys_law_cases"] = len(signals.get("hys_law_cases", []))
        safety["kidney_decline_cases"] = len(signals.get("kidney_decline_cases", []))

    # Overall safety assessment
    safety_flags = []
    if safety.get("sae_rate_percent", 0) > 10:
        safety_flags.append(f"⚠ High SAE rate ({safety['sae_rate_percent']:.1f}%)")
    if safety.get("hys_law_cases", 0) > 0:
        safety_flags.append(f"⚠ {safety['hys_law_cases']} Hy's Law cases")

    if len(safety_flags) == 0:
        safety["overall_safety"] = "✅ No significant safety concerns"
    else:
        safety["overall_safety"] = "; ".join(safety_flags)

    dashboard["safety_metrics"] = safety if safety else {"status": "No safety data available"}

    # ========== QUALITY METRICS ==========
    quality = {
        "data_completeness_score": 0.0,
        "sdtm_compliance": "Unknown",
        "aact_similarity": "Unknown"
    }

    # Calculate completeness
    completeness_count = len(domains)
    quality["data_completeness_score"] = completeness_count / 4.0

    if quality["data_completeness_score"] >= 0.75:
        quality["quality_assessment"] = "✅ HIGH QUALITY - All major domains captured"
    elif quality["data_completeness_score"] >= 0.50:
        quality["quality_assessment"] = "✓ GOOD QUALITY - Some domains missing"
    else:
        quality["quality_assessment"] = "⚠ LIMITED QUALITY - Major data gaps"

    dashboard["quality_metrics"] = quality

    # ========== AACT CONTEXT ==========
    if n_subjects > 0 and efficacy.get("treatment_effect_sbp") is not None:
        try:
            from aact_integration import compare_study_to_aact
            aact = compare_study_to_aact(
                n_subjects=n_subjects,
                indication=indication,
                phase=phase,
                treatment_effect=efficacy["treatment_effect_sbp"]
            )

            dashboard["aact_context"] = {
                "enrollment_percentile": aact.get("enrollment_benchmark", {}).get("percentile"),
                "treatment_effect_percentile": aact.get("treatment_effect_benchmark", {}).get("percentile"),
                "similarity_score": aact.get("similarity_score"),
                "industry_assessment": aact.get("interpretation", {}).get("overall_assessment"),
                "n_reference_trials": aact.get("aact_reference", {}).get("phase_trials_in_aact")
            }
        except:
            dashboard["aact_context"] = {"status": "AACT comparison unavailable"}
    else:
        dashboard["aact_context"] = {"status": "Insufficient data for AACT comparison"}

    # ========== RISK FLAGS ==========
    risk_flags = []

    # Enrollment risks
    if enrollment.get("randomization_balance", "").startswith("⚠"):
        risk_flags.append({
            "severity": "MEDIUM",
            "category": "Enrollment",
            "issue": "Treatment arm imbalance detected",
            "recommendation": "Review randomization procedure"
        })

    # Efficacy risks
    if efficacy.get("efficacy_assessment", "").startswith("⚠"):
        risk_flags.append({
            "severity": "HIGH",
            "category": "Efficacy",
            "issue": efficacy.get("efficacy_assessment", "Efficacy concern"),
            "recommendation": "Review dose, endpoint, or trial design"
        })

    # Safety risks
    if safety.get("hys_law_cases", 0) > 0:
        risk_flags.append({
            "severity": "CRITICAL",
            "category": "Safety",
            "issue": f"{safety['hys_law_cases']} potential DILI cases (Hy's Law)",
            "recommendation": "Immediate DSMB notification and subject review"
        })

    if safety.get("sae_rate_percent", 0) > 15:
        risk_flags.append({
            "severity": "HIGH",
            "category": "Safety",
            "issue": f"High SAE rate ({safety['sae_rate_percent']:.1f}%)",
            "recommendation": "Detailed SAE causality review"
        })

    # Data quality risks
    if quality["data_completeness_score"] < 0.5:
        risk_flags.append({
            "severity": "MEDIUM",
            "category": "Data Quality",
            "issue": "Major data domains missing",
            "recommendation": "Improve data collection or EDC system"
        })

    dashboard["risk_flags"] = risk_flags
    dashboard["risk_count"] = len(risk_flags)

    # ========== RECOMMENDATIONS ==========
    recommendations = []

    if len(risk_flags) == 0:
        recommendations.append("✅ Trial progressing well - Continue as planned")
    else:
        recommendations.append(f"⚠ {len(risk_flags)} risk flag(s) require attention")

        for flag in risk_flags:
            if flag["severity"] in ["CRITICAL", "HIGH"]:
                recommendations.append(f"• {flag['category']}: {flag['recommendation']}")

    # AACT-based recommendations
    if dashboard.get("aact_context", {}).get("similarity_score") is not None:
        score = dashboard["aact_context"]["similarity_score"]
        if score < 0.6:
            recommendations.append("• Consider adjusting trial parameters to align with industry benchmarks")

    dashboard["recommendations"] = recommendations

    return dashboard
