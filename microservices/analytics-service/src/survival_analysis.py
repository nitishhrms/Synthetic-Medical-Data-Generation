"""
Survival Analysis Module for Clinical Trials

Provides Kaplan-Meier curves, log-rank tests, hazard ratios, and Cox regression
for time-to-event analysis in oncology and other therapeutic areas.

Author: Analytics Service
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def generate_survival_data(
    demographics_data: List[Dict[str, Any]],
    indication: str = "oncology",
    median_survival_active: float = 18.0,  # months
    median_survival_placebo: float = 12.0,  # months
    censoring_rate: float = 0.3,
    follow_up_months: int = 36,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate time-to-event data for survival analysis.

    Args:
        demographics_data: List of subject demographics
        indication: Therapeutic area (affects survival distribution)
        median_survival_active: Median survival for active arm (months)
        median_survival_placebo: Median survival for placebo arm (months)
        censoring_rate: Proportion of censored observations
        follow_up_months: Maximum follow-up duration
        seed: Random seed for reproducibility

    Returns:
        List of survival records with event times and censoring status
    """
    if seed:
        np.random.seed(seed)

    survival_data = []

    for subject in demographics_data:
        subject_id = subject.get("SubjectID")
        treatment_arm = subject.get("TreatmentArm", "Placebo")

        # Set median survival based on treatment arm
        if treatment_arm == "Active":
            median_survival = median_survival_active
        else:
            median_survival = median_survival_placebo

        # Generate survival time using exponential distribution
        # lambda = ln(2) / median
        lambda_param = np.log(2) / median_survival
        survival_time = np.random.exponential(1 / lambda_param)

        # Determine censoring
        is_censored = np.random.random() < censoring_rate

        if is_censored:
            # Censoring time is random within follow-up period
            event_time = np.random.uniform(0, follow_up_months)
            event_occurred = False
        else:
            # Use actual survival time, capped at follow-up
            event_time = min(survival_time, follow_up_months)
            event_occurred = (survival_time <= follow_up_months)

        # Determine event type
        if indication.lower() == "oncology":
            event_types = ["Death", "Disease Progression", "Last Contact"]
            if event_occurred:
                event_type = np.random.choice(["Death", "Disease Progression"], p=[0.7, 0.3])
            else:
                event_type = "Last Contact"
        else:
            event_types = ["Death", "Event", "Last Contact"]
            if event_occurred:
                event_type = "Event"
            else:
                event_type = "Last Contact"

        survival_data.append({
            "SubjectID": subject_id,
            "TreatmentArm": treatment_arm,
            "EventTime": round(event_time, 2),  # months
            "EventOccurred": event_occurred,
            "Censored": is_censored or not event_occurred,
            "EventType": event_type,
            "FollowUpMonths": follow_up_months
        })

    return survival_data


def calculate_kaplan_meier(
    survival_data: List[Dict[str, Any]],
    treatment_arm: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Kaplan-Meier survival estimates.

    Args:
        survival_data: List of survival records
        treatment_arm: Specific arm to analyze (None = all)

    Returns:
        Dict with survival probabilities, times, and confidence intervals
    """
    df = pd.DataFrame(survival_data)

    # Filter by treatment arm if specified
    if treatment_arm:
        df = df[df["TreatmentArm"] == treatment_arm]

    # Sort by event time
    df = df.sort_values("EventTime")

    # Get unique event times
    event_times = sorted(df["EventTime"].unique())

    km_estimates = []
    n_at_risk = len(df)
    survival_prob = 1.0
    cumulative_variance_terms = []  # For Greenwood's formula - accumulate across all time points

    for time in event_times:
        # Events at this time
        events_at_time = df[(df["EventTime"] == time) & (df["EventOccurred"] == True)]
        n_events = len(events_at_time)

        # Censored at this time
        censored_at_time = df[(df["EventTime"] == time) & (df["Censored"] == True) & (df["EventOccurred"] == False)]
        n_censored = len(censored_at_time)

        if n_at_risk > 0 and n_events > 0:
            # KM formula: S(t) = S(t-1) * (1 - d_t / n_t)
            survival_prob *= (1 - n_events / n_at_risk)

        # Standard error using Greenwood's formula (cumulative across all time points)
        # Var[S(t)] = S(t)² × Σ[d_j / (n_j × (n_j - d_j))] for all j where t_j ≤ t
        if n_at_risk > 0 and n_events > 0 and n_at_risk > n_events:
            cumulative_variance_terms.append(
                n_events / (n_at_risk * (n_at_risk - n_events))
            )

        if survival_prob > 0 and cumulative_variance_terms:
            variance = survival_prob ** 2 * sum(cumulative_variance_terms)
            se = np.sqrt(variance)
        else:
            se = 0

        # 95% CI using log-log transformation
        if survival_prob > 0 and se > 0:
            z = 1.96
            log_log_survival = np.log(-np.log(survival_prob))
            se_log_log = se / (survival_prob * abs(np.log(survival_prob)))

            ci_lower = survival_prob ** np.exp(z * se_log_log)
            ci_upper = survival_prob ** np.exp(-z * se_log_log)

            ci_lower = max(0, min(1, ci_lower))
            ci_upper = max(0, min(1, ci_upper))
        else:
            ci_lower = survival_prob
            ci_upper = survival_prob

        km_estimates.append({
            "time": round(time, 2),
            "n_at_risk": n_at_risk,
            "n_events": n_events,
            "n_censored": n_censored,
            "survival_prob": round(survival_prob, 4),
            "se": round(se, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4)
        })

        # Update number at risk
        n_at_risk -= (n_events + n_censored)

    # Calculate median survival
    median_survival = None
    median_ci_lower = None
    median_ci_upper = None

    for estimate in km_estimates:
        if estimate["survival_prob"] <= 0.5:
            median_survival = estimate["time"]
            median_ci_lower = estimate["ci_lower"]
            median_ci_upper = estimate["ci_upper"]
            break

    return {
        "km_curve": km_estimates,
        "median_survival": median_survival,
        "median_ci_lower": median_ci_lower,
        "median_ci_upper": median_ci_upper,
        "n_subjects": len(df),
        "n_events": len(df[df["EventOccurred"] == True]),
        "n_censored": len(df[df["Censored"] == True])
    }


def log_rank_test(
    survival_data: List[Dict[str, Any]],
    arm1: str = "Active",
    arm2: str = "Placebo"
) -> Dict[str, Any]:
    """
    Perform log-rank test to compare survival curves between two arms.

    Args:
        survival_data: List of survival records
        arm1: First treatment arm
        arm2: Second treatment arm

    Returns:
        Dict with test statistic, p-value, and interpretation
    """
    df = pd.DataFrame(survival_data)

    # Filter to two arms
    df1 = df[df["TreatmentArm"] == arm1]
    df2 = df[df["TreatmentArm"] == arm2]

    # Get all unique event times
    all_times = sorted(set(df1["EventTime"].tolist() + df2["EventTime"].tolist()))

    # Calculate log-rank statistic
    observed_minus_expected = 0
    variance = 0

    for time in all_times:
        # Arm 1 at this time
        n1_at_risk = len(df1[df1["EventTime"] >= time])
        d1 = len(df1[(df1["EventTime"] == time) & (df1["EventOccurred"] == True)])

        # Arm 2 at this time
        n2_at_risk = len(df2[df2["EventTime"] >= time])
        d2 = len(df2[(df2["EventTime"] == time) & (df2["EventOccurred"] == True)])

        # Total at this time
        n_total = n1_at_risk + n2_at_risk
        d_total = d1 + d2

        if n_total > 0 and d_total > 0:
            # Expected events in arm 1
            expected1 = (n1_at_risk / n_total) * d_total

            # Variance
            if n_total > 1:
                var_t = (n1_at_risk * n2_at_risk * d_total * (n_total - d_total)) / (n_total ** 2 * (n_total - 1))
            else:
                var_t = 0

            observed_minus_expected += (d1 - expected1)
            variance += var_t

    # Calculate chi-square statistic
    if variance > 0:
        chi_square = (observed_minus_expected ** 2) / variance
        p_value = 1 - stats.chi2.cdf(chi_square, df=1)
    else:
        chi_square = 0
        p_value = 1.0

    # Interpretation
    significant = p_value < 0.05

    return {
        "test_statistic": round(chi_square, 4),
        "p_value": round(p_value, 4),
        "significant": significant,
        "interpretation": f"{'Significant' if significant else 'No significant'} difference in survival between {arm1} and {arm2}",
        "arm1": arm1,
        "arm2": arm2,
        "arm1_events": len(df1[df1["EventOccurred"] == True]),
        "arm2_events": len(df2[df2["EventOccurred"] == True])
    }


def calculate_hazard_ratio(
    survival_data: List[Dict[str, Any]],
    reference_arm: str = "Placebo",
    treatment_arm: str = "Active"
) -> Dict[str, Any]:
    """
    Calculate hazard ratio comparing treatment to reference.

    Uses simple formula: HR = (events_treatment / person_time_treatment) / (events_reference / person_time_reference)

    Args:
        survival_data: List of survival records
        reference_arm: Reference treatment arm (denominator)
        treatment_arm: Treatment arm (numerator)

    Returns:
        Dict with hazard ratio, confidence interval, and interpretation
    """
    df = pd.DataFrame(survival_data)

    # Separate by arm
    df_ref = df[df["TreatmentArm"] == reference_arm]
    df_trt = df[df["TreatmentArm"] == treatment_arm]

    # Calculate person-time and events
    person_time_ref = df_ref["EventTime"].sum()
    events_ref = len(df_ref[df_ref["EventOccurred"] == True])

    person_time_trt = df_trt["EventTime"].sum()
    events_trt = len(df_trt[df_trt["EventOccurred"] == True])

    # Calculate hazard rates
    if person_time_ref > 0 and person_time_trt > 0:
        hazard_ref = events_ref / person_time_ref
        hazard_trt = events_trt / person_time_trt

        # Hazard ratio
        if hazard_ref > 0:
            hr = hazard_trt / hazard_ref
        else:
            hr = None
    else:
        hr = None
        hazard_ref = None
        hazard_trt = None

    # 95% CI using standard error from log(HR)
    if hr and events_ref > 0 and events_trt > 0:
        se_log_hr = np.sqrt(1/events_ref + 1/events_trt)
        log_hr = np.log(hr)

        ci_lower = np.exp(log_hr - 1.96 * se_log_hr)
        ci_upper = np.exp(log_hr + 1.96 * se_log_hr)
    else:
        ci_lower = None
        ci_upper = None

    # Interpretation
    if hr:
        if hr < 1:
            interpretation = f"{treatment_arm} reduces risk by {round((1-hr)*100, 1)}% vs {reference_arm}"
            benefit = "Favors treatment"
        elif hr > 1:
            interpretation = f"{treatment_arm} increases risk by {round((hr-1)*100, 1)}% vs {reference_arm}"
            benefit = "Favors control"
        else:
            interpretation = f"No difference between {treatment_arm} and {reference_arm}"
            benefit = "No difference"
    else:
        interpretation = "Insufficient data to calculate hazard ratio"
        benefit = "Unknown"

    return {
        "hazard_ratio": round(hr, 4) if hr else None,
        "ci_lower": round(ci_lower, 4) if ci_lower else None,
        "ci_upper": round(ci_upper, 4) if ci_upper else None,
        "reference_arm": reference_arm,
        "treatment_arm": treatment_arm,
        "reference_events": events_ref,
        "treatment_events": events_trt,
        "interpretation": interpretation,
        "clinical_benefit": benefit
    }


def export_survival_sdtm_tte(
    survival_data: List[Dict[str, Any]],
    study_id: str = "STUDY001"
) -> List[Dict[str, Any]]:
    """
    Export survival data in CDISC SDTM TTE (Time-to-Event) domain format.

    Args:
        survival_data: List of survival records
        study_id: Study identifier

    Returns:
        List of SDTM TTE records
    """
    sdtm_tte = []

    for idx, record in enumerate(survival_data, 1):
        subject_id = record["SubjectID"]

        # SDTM TTE domain structure
        sdtm_record = {
            "STUDYID": study_id,
            "DOMAIN": "TTE",
            "USUBJID": f"{study_id}-{subject_id}",
            "TTESEQ": idx,
            "TTESTCD": "OS",  # Overall Survival
            "TTETEST": "Overall Survival",
            "TTECAT": "EFFICACY",
            "TTESCAT": "PRIMARY ENDPOINT",
            "TTEDTC": "",  # Date of event (would be populated with real dates)
            "TTEEVNT": "Y" if record["EventOccurred"] else "N",
            "TTEDY": int(record["EventTime"] * 30),  # Convert months to days
            "TTEADY": int(record["EventTime"] * 30),  # Analysis day
            "TTECNSR": 1 if record["Censored"] else 0,  # 1=censored, 0=event
            "ARM": record["TreatmentArm"],
            "VISITNUM": 999,  # Final visit for TTE
            "VISIT": "End of Study"
        }

        sdtm_tte.append(sdtm_record)

    return sdtm_tte


def comprehensive_survival_analysis(
    demographics_data: List[Dict[str, Any]],
    indication: str = "oncology",
    median_survival_active: float = 18.0,
    median_survival_placebo: float = 12.0,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform comprehensive survival analysis including KM curves, log-rank test, and hazard ratios.

    Args:
        demographics_data: List of subject demographics
        indication: Therapeutic area
        median_survival_active: Median survival for active arm (months)
        median_survival_placebo: Median survival for placebo arm (months)
        seed: Random seed

    Returns:
        Dict with all survival analysis results
    """
    # Generate survival data
    survival_data = generate_survival_data(
        demographics_data=demographics_data,
        indication=indication,
        median_survival_active=median_survival_active,
        median_survival_placebo=median_survival_placebo,
        seed=seed
    )

    # Kaplan-Meier for each arm
    km_active = calculate_kaplan_meier(survival_data, treatment_arm="Active")
    km_placebo = calculate_kaplan_meier(survival_data, treatment_arm="Placebo")
    km_overall = calculate_kaplan_meier(survival_data)

    # Log-rank test
    log_rank = log_rank_test(survival_data)

    # Hazard ratio
    hr = calculate_hazard_ratio(survival_data)

    # SDTM export
    sdtm_tte = export_survival_sdtm_tte(survival_data)

    return {
        "survival_data": survival_data,
        "kaplan_meier": {
            "active": km_active,
            "placebo": km_placebo,
            "overall": km_overall
        },
        "log_rank_test": log_rank,
        "hazard_ratio": hr,
        "sdtm_tte": sdtm_tte,
        "summary": {
            "indication": indication,
            "total_subjects": len(survival_data),
            "total_events": len([s for s in survival_data if s["EventOccurred"]]),
            "total_censored": len([s for s in survival_data if s["Censored"]]),
            "median_survival_active": km_active["median_survival"],
            "median_survival_placebo": km_placebo["median_survival"],
            "hazard_ratio": hr["hazard_ratio"],
            "p_value": log_rank["p_value"],
            "significant": log_rank["significant"]
        }
    }
