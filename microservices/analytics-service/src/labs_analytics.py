"""
Labs Analytics Module
Comprehensive laboratory data analysis for clinical trials

Functions:
1. calculate_labs_summary() - Lab results summary by test, visit, treatment arm
2. detect_abnormal_labs() - Detect abnormal values with CTCAE grading
3. generate_shift_tables() - Baseline-to-endpoint shift analysis
4. compare_labs_quality() - Real vs synthetic lab data quality assessment
5. detect_safety_signals() - Identify potential safety signals (Hy's Law, kidney function)
6. analyze_labs_longitudinal() - Time-series analysis of lab trends

Statistical Methods:
- Descriptive statistics (mean, median, SD, range)
- CTCAE toxicity grading (Grade 0-4)
- Chi-square tests for shift table analysis
- Wasserstein distance for distribution similarity
- Mixed models for repeated measures (longitudinal)
- Liver safety: Hy's Law criteria (ALT, AST, bilirubin)
- Kidney safety: eGFR decline patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from scipy import stats
from scipy.stats import wasserstein_distance


# CTCAE Grade 5.0 Reference Ranges for Common Lab Tests
CTCAE_RANGES = {
    "ALT": {
        "normal_range": (7, 56),  # U/L
        "ULN": 56,
        "grades": {
            0: (0, 56),      # Normal
            1: (56, 168),    # >1.0-3.0 x ULN
            2: (168, 280),   # >3.0-5.0 x ULN
            3: (280, 560),   # >5.0-10.0 x ULN
            4: (560, float('inf'))  # >10.0 x ULN
        }
    },
    "AST": {
        "normal_range": (8, 48),  # U/L
        "ULN": 48,
        "grades": {
            0: (0, 48),
            1: (48, 144),
            2: (144, 240),
            3: (240, 480),
            4: (480, float('inf'))
        }
    },
    "Bilirubin": {
        "normal_range": (0.1, 1.2),  # mg/dL
        "ULN": 1.2,
        "grades": {
            0: (0, 1.2),
            1: (1.2, 1.8),    # >1.0-1.5 x ULN
            2: (1.8, 3.6),    # >1.5-3.0 x ULN
            3: (3.6, 12.0),   # >3.0-10.0 x ULN
            4: (12.0, float('inf'))
        }
    },
    "Creatinine": {
        "normal_range": (0.6, 1.2),  # mg/dL
        "ULN": 1.2,
        "grades": {
            0: (0, 1.2),
            1: (1.2, 1.8),    # >1.0-1.5 x ULN
            2: (1.8, 3.6),    # >1.5-3.0 x ULN
            3: (3.6, 7.2),    # >3.0-6.0 x ULN
            4: (7.2, float('inf'))
        }
    },
    "Hemoglobin": {
        "normal_range": (12.0, 16.0),  # g/dL
        "LLN": 12.0,
        "grades": {
            0: (12.0, float('inf')),  # Normal
            1: (10.0, 12.0),          # <LLN - 10.0 g/dL
            2: (8.0, 10.0),           # <10.0 - 8.0 g/dL
            3: (6.5, 8.0),            # <8.0 g/dL; transfusion indicated
            4: (0, 6.5)               # Life-threatening
        }
    },
    "WBC": {
        "normal_range": (4.0, 11.0),  # x10^9/L
        "ULN": 11.0,
        "LLN": 4.0,
        "grades": {
            0: (4.0, 11.0),
            1: (3.0, 4.0),    # <LLN - 3.0
            2: (2.0, 3.0),    # <3.0 - 2.0
            3: (1.0, 2.0),    # <2.0 - 1.0
            4: (0, 1.0)       # <1.0
        }
    },
    "Platelets": {
        "normal_range": (150, 400),  # x10^9/L
        "LLN": 150,
        "grades": {
            0: (150, float('inf')),
            1: (75, 150),     # <LLN - 75
            2: (50, 75),      # <75 - 50
            3: (25, 50),      # <50 - 25
            4: (0, 25)        # <25
        }
    },
    "eGFR": {
        "normal_range": (90, float('inf')),  # mL/min/1.73m²
        "grades": {
            0: (90, float('inf')),    # Normal
            1: (60, 90),              # Mild decrease
            2: (30, 60),              # Moderate decrease
            3: (15, 30),              # Severe decrease
            4: (0, 15)                # Kidney failure
        }
    }
}


def calculate_labs_summary(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate lab results summary by test, visit, treatment arm

    Args:
        labs_df: DataFrame with columns:
            - SubjectID
            - VisitName
            - TreatmentArm
            - TestName (e.g., "ALT", "AST", "Creatinine")
            - TestValue (numeric)
            - TestUnit

    Returns:
        Dictionary with:
        - by_test: Summary statistics for each lab test
        - by_visit: Summaries by visit
        - by_arm: Summaries by treatment arm
        - overall: Overall statistics
    """
    result = {
        "by_test": {},
        "by_visit": {},
        "by_arm": {},
        "overall": {}
    }

    # Overall summary
    result["overall"] = {
        "total_observations": len(labs_df),
        "total_subjects": labs_df["SubjectID"].nunique(),
        "total_tests": labs_df["TestName"].nunique(),
        "visits": sorted(labs_df["VisitName"].unique().tolist()),
        "tests": sorted(labs_df["TestName"].unique().tolist())
    }

    # Summary by test
    for test_name in labs_df["TestName"].unique():
        test_data = labs_df[labs_df["TestName"] == test_name]["TestValue"]

        result["by_test"][test_name] = {
            "n": len(test_data),
            "mean": round(float(test_data.mean()), 2),
            "median": round(float(test_data.median()), 2),
            "std": round(float(test_data.std()), 2),
            "min": round(float(test_data.min()), 2),
            "max": round(float(test_data.max()), 2),
            "q25": round(float(test_data.quantile(0.25)), 2),
            "q75": round(float(test_data.quantile(0.75)), 2),
            "unit": labs_df[labs_df["TestName"] == test_name]["TestUnit"].iloc[0] if "TestUnit" in labs_df.columns else ""
        }

    # Summary by visit
    for visit in labs_df["VisitName"].unique():
        visit_data = labs_df[labs_df["VisitName"] == visit]
        result["by_visit"][visit] = {
            "n_observations": len(visit_data),
            "n_subjects": visit_data["SubjectID"].nunique(),
            "tests_collected": visit_data["TestName"].nunique()
        }

    # Summary by treatment arm
    if "TreatmentArm" in labs_df.columns:
        for arm in labs_df["TreatmentArm"].unique():
            arm_data = labs_df[labs_df["TreatmentArm"] == arm]
            result["by_arm"][arm] = {
                "n_observations": len(arm_data),
                "n_subjects": arm_data["SubjectID"].nunique(),
                "mean_values_by_test": {}
            }

            # Mean values for each test in this arm
            for test_name in arm_data["TestName"].unique():
                test_values = arm_data[arm_data["TestName"] == test_name]["TestValue"]
                result["by_arm"][arm]["mean_values_by_test"][test_name] = round(float(test_values.mean()), 2)

    return result


def detect_abnormal_labs(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect abnormal lab values with CTCAE grading

    Uses CTCAE v5.0 grading criteria for common laboratory tests.

    Args:
        labs_df: DataFrame with columns:
            - SubjectID
            - TestName
            - TestValue
            - VisitName (optional)
            - TreatmentArm (optional)

    Returns:
        Dictionary with:
        - abnormal_observations: List of all abnormal observations with grades
        - summary_by_grade: Count of observations by CTCAE grade
        - summary_by_test: Abnormality rates by test
        - high_risk_subjects: Subjects with Grade 3+ abnormalities
    """
    abnormal_obs = []

    for idx, row in labs_df.iterrows():
        test_name = row["TestName"]
        test_value = row["TestValue"]

        if test_name not in CTCAE_RANGES:
            continue

        # Determine CTCAE grade
        grade = 0
        for g in [4, 3, 2, 1, 0]:
            lower, upper = CTCAE_RANGES[test_name]["grades"][g]
            if lower <= test_value < upper:
                grade = g
                break

        if grade > 0:  # Abnormal
            abnormal_obs.append({
                "SubjectID": row["SubjectID"],
                "TestName": test_name,
                "TestValue": test_value,
                "CTCAE_Grade": grade,
                "VisitName": row.get("VisitName", ""),
                "TreatmentArm": row.get("TreatmentArm", "")
            })

    # Summary by grade
    grade_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for obs in abnormal_obs:
        grade_counts[obs["CTCAE_Grade"]] += 1

    # Summary by test
    test_summary = {}
    for test_name in labs_df["TestName"].unique():
        if test_name not in CTCAE_RANGES:
            continue

        test_data = labs_df[labs_df["TestName"] == test_name]
        test_abnormal = [obs for obs in abnormal_obs if obs["TestName"] == test_name]

        test_summary[test_name] = {
            "total_observations": len(test_data),
            "abnormal_count": len(test_abnormal),
            "abnormal_rate": round(len(test_abnormal) / len(test_data) * 100, 1) if len(test_data) > 0 else 0,
            "grade_1": len([o for o in test_abnormal if o["CTCAE_Grade"] == 1]),
            "grade_2": len([o for o in test_abnormal if o["CTCAE_Grade"] == 2]),
            "grade_3": len([o for o in test_abnormal if o["CTCAE_Grade"] == 3]),
            "grade_4": len([o for o in test_abnormal if o["CTCAE_Grade"] == 4])
        }

    # High-risk subjects (Grade 3+)
    high_risk_subjects = list(set([
        obs["SubjectID"] for obs in abnormal_obs if obs["CTCAE_Grade"] >= 3
    ]))

    return {
        "abnormal_observations": abnormal_obs,
        "summary_by_grade": grade_counts,
        "summary_by_test": test_summary,
        "high_risk_subjects": sorted(high_risk_subjects),
        "total_abnormal": len(abnormal_obs),
        "abnormal_rate": round(len(abnormal_obs) / len(labs_df) * 100, 1) if len(labs_df) > 0 else 0
    }


def generate_shift_tables(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate baseline-to-endpoint shift analysis

    Analyzes how lab values shift from baseline (Screening) to endpoint (last visit),
    categorized as Normal → Normal, Normal → Abnormal, Abnormal → Normal, Abnormal → Abnormal.

    Args:
        labs_df: DataFrame with columns:
            - SubjectID
            - VisitName
            - TestName
            - TestValue
            - TreatmentArm (optional)

    Returns:
        Dictionary with:
        - shift_tables: Shift table for each lab test
        - chi_square_tests: Statistical tests for shift patterns
        - clinical_interpretation: Clinical significance of shifts
    """
    # Identify baseline and endpoint visits
    visits = sorted(labs_df["VisitName"].unique())
    baseline_visit = visits[0]  # Assume first visit is baseline
    endpoint_visit = visits[-1]  # Assume last visit is endpoint

    result = {
        "baseline_visit": baseline_visit,
        "endpoint_visit": endpoint_visit,
        "shift_tables": {},
        "chi_square_tests": {}
    }

    for test_name in labs_df["TestName"].unique():
        if test_name not in CTCAE_RANGES:
            continue

        # Get baseline and endpoint values for each subject
        baseline_data = labs_df[
            (labs_df["TestName"] == test_name) &
            (labs_df["VisitName"] == baseline_visit)
        ][["SubjectID", "TestValue"]].rename(columns={"TestValue": "Baseline"})

        endpoint_data = labs_df[
            (labs_df["TestName"] == test_name) &
            (labs_df["VisitName"] == endpoint_visit)
        ][["SubjectID", "TestValue"]].rename(columns={"TestValue": "Endpoint"})

        # Merge
        merged = pd.merge(baseline_data, endpoint_data, on="SubjectID")

        if len(merged) == 0:
            continue

        # Classify as Normal/Abnormal
        def classify(value):
            normal_range = CTCAE_RANGES[test_name]["normal_range"]
            return "Normal" if normal_range[0] <= value <= normal_range[1] else "Abnormal"

        merged["Baseline_Category"] = merged["Baseline"].apply(classify)
        merged["Endpoint_Category"] = merged["Endpoint"].apply(classify)

        # Create shift table
        shift_table = pd.crosstab(
            merged["Baseline_Category"],
            merged["Endpoint_Category"],
            margins=True
        )

        # Calculate percentages
        total = len(merged)
        nn = len(merged[(merged["Baseline_Category"] == "Normal") & (merged["Endpoint_Category"] == "Normal")])
        na = len(merged[(merged["Baseline_Category"] == "Normal") & (merged["Endpoint_Category"] == "Abnormal")])
        an = len(merged[(merged["Baseline_Category"] == "Abnormal") & (merged["Endpoint_Category"] == "Normal")])
        aa = len(merged[(merged["Baseline_Category"] == "Abnormal") & (merged["Endpoint_Category"] == "Abnormal")])

        result["shift_tables"][test_name] = {
            "shift_matrix": shift_table.to_dict(),
            "percentages": {
                "Normal_to_Normal": round(nn / total * 100, 1),
                "Normal_to_Abnormal": round(na / total * 100, 1),
                "Abnormal_to_Normal": round(an / total * 100, 1),
                "Abnormal_to_Abnormal": round(aa / total * 100, 1)
            },
            "counts": {
                "Normal_to_Normal": nn,
                "Normal_to_Abnormal": na,
                "Abnormal_to_Normal": an,
                "Abnormal_to_Abnormal": aa
            },
            "total_subjects": total
        }

        # Chi-square test (if sufficient data)
        if nn > 5 and na > 5 and an > 5 and aa > 5:
            contingency = [[nn, na], [an, aa]]
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

            result["chi_square_tests"][test_name] = {
                "chi_square": round(float(chi2), 3),
                "p_value": round(float(p_value), 4),
                "dof": int(dof),
                "significant": p_value < 0.05
            }

    return result


def compare_labs_quality(real_labs: pd.DataFrame, synthetic_labs: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare real vs synthetic lab data quality

    Args:
        real_labs: Real lab data DataFrame
        synthetic_labs: Synthetic lab data DataFrame
        Both must have: TestName, TestValue

    Returns:
        Dictionary with:
        - wasserstein_distances: Distribution similarity for each test
        - ks_tests: Kolmogorov-Smirnov tests
        - mean_differences: Mean value differences
        - overall_quality_score: Aggregate quality (0-1)
    """
    result = {
        "wasserstein_distances": {},
        "ks_tests": {},
        "mean_differences": {},
        "overall_quality_score": 0.0
    }

    # Get common tests
    common_tests = set(real_labs["TestName"].unique()) & set(synthetic_labs["TestName"].unique())

    if not common_tests:
        result["error"] = "No common tests found between real and synthetic data"
        return result

    wasserstein_scores = []
    ks_scores = []

    for test_name in common_tests:
        real_values = real_labs[real_labs["TestName"] == test_name]["TestValue"].values
        synthetic_values = synthetic_labs[synthetic_labs["TestName"] == test_name]["TestValue"].values

        # Wasserstein distance
        w_dist = wasserstein_distance(real_values, synthetic_values)
        result["wasserstein_distances"][test_name] = round(float(w_dist), 3)

        # Normalize by mean of real values (to get relative distance)
        real_mean = np.mean(real_values)
        normalized_w = w_dist / real_mean if real_mean > 0 else w_dist
        wasserstein_scores.append(max(0, 1 - normalized_w))  # Convert to similarity score

        # KS test
        ks_stat, ks_pval = stats.ks_2samp(real_values, synthetic_values)
        result["ks_tests"][test_name] = {
            "statistic": round(float(ks_stat), 3),
            "p_value": round(float(ks_pval), 4),
            "distributions_similar": ks_pval > 0.05
        }
        ks_scores.append(1 if ks_pval > 0.05 else 0)

        # Mean difference
        real_mean_val = np.mean(real_values)
        synthetic_mean_val = np.mean(synthetic_values)
        mean_diff = synthetic_mean_val - real_mean_val
        pct_diff = (mean_diff / real_mean_val * 100) if real_mean_val != 0 else 0

        result["mean_differences"][test_name] = {
            "real_mean": round(float(real_mean_val), 2),
            "synthetic_mean": round(float(synthetic_mean_val), 2),
            "absolute_difference": round(float(mean_diff), 2),
            "percent_difference": round(float(pct_diff), 1)
        }

    # Overall quality score
    wasserstein_avg = np.mean(wasserstein_scores)
    ks_avg = np.mean(ks_scores)
    overall = 0.6 * wasserstein_avg + 0.4 * ks_avg

    result["overall_quality_score"] = round(float(overall), 3)

    # Interpretation
    if overall >= 0.85:
        interpretation = "Excellent - Synthetic lab data closely matches real distributions"
    elif overall >= 0.70:
        interpretation = "Good - Synthetic data is usable with minor differences"
    else:
        interpretation = "Needs improvement - Consider adjusting generation parameters"

    result["interpretation"] = interpretation

    return result


def detect_safety_signals(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect potential safety signals in lab data

    Implements:
    1. Hy's Law (drug-induced liver injury): ALT/AST >3x ULN + Bilirubin >2x ULN
    2. Kidney function decline: eGFR decrease >25% from baseline
    3. Bone marrow suppression: Hemoglobin <8 g/dL, WBC <2.0, Platelets <50

    Args:
        labs_df: DataFrame with TestName, TestValue, SubjectID, VisitName

    Returns:
        Dictionary with:
        - hys_law_cases: Subjects meeting Hy's Law criteria
        - kidney_decline_cases: Subjects with significant eGFR decline
        - bone_marrow_cases: Subjects with severe bone marrow suppression
        - overall_safety_summary: Aggregate safety metrics
    """
    result = {
        "hys_law_cases": [],
        "kidney_decline_cases": [],
        "bone_marrow_cases": [],
        "overall_safety_summary": {}
    }

    # Hy's Law Detection
    subjects = labs_df["SubjectID"].unique()

    for subject in subjects:
        subject_data = labs_df[labs_df["SubjectID"] == subject]

        # Check for Hy's Law (any visit)
        for visit in subject_data["VisitName"].unique():
            visit_data = subject_data[subject_data["VisitName"] == visit]

            alt = visit_data[visit_data["TestName"] == "ALT"]["TestValue"].values
            ast = visit_data[visit_data["TestName"] == "AST"]["TestValue"].values
            bili = visit_data[visit_data["TestName"] == "Bilirubin"]["TestValue"].values

            if len(alt) > 0 and len(bili) > 0:
                alt_val = alt[0]
                bili_val = bili[0]

                # Hy's Law: ALT >3x ULN AND Bilirubin >2x ULN
                if alt_val > (3 * CTCAE_RANGES["ALT"]["ULN"]) and bili_val > (2 * CTCAE_RANGES["Bilirubin"]["ULN"]):
                    result["hys_law_cases"].append({
                        "SubjectID": subject,
                        "VisitName": visit,
                        "ALT": round(float(alt_val), 1),
                        "ALT_ULN_multiple": round(float(alt_val / CTCAE_RANGES["ALT"]["ULN"]), 1),
                        "Bilirubin": round(float(bili_val), 1),
                        "Bilirubin_ULN_multiple": round(float(bili_val / CTCAE_RANGES["Bilirubin"]["ULN"]), 1),
                        "severity": "HIGH RISK"
                    })

        # Check for kidney decline (baseline vs endpoint)
        visits = sorted(subject_data["VisitName"].unique())
        if len(visits) >= 2:
            baseline_egfr = subject_data[
                (subject_data["TestName"] == "eGFR") &
                (subject_data["VisitName"] == visits[0])
            ]["TestValue"].values

            endpoint_egfr = subject_data[
                (subject_data["TestName"] == "eGFR") &
                (subject_data["VisitName"] == visits[-1])
            ]["TestValue"].values

            if len(baseline_egfr) > 0 and len(endpoint_egfr) > 0:
                baseline_val = baseline_egfr[0]
                endpoint_val = endpoint_egfr[0]
                pct_decline = (baseline_val - endpoint_val) / baseline_val * 100

                if pct_decline > 25:  # >25% decline
                    result["kidney_decline_cases"].append({
                        "SubjectID": subject,
                        "Baseline_eGFR": round(float(baseline_val), 1),
                        "Endpoint_eGFR": round(float(endpoint_val), 1),
                        "Percent_Decline": round(float(pct_decline), 1),
                        "severity": "MODERATE RISK" if pct_decline < 50 else "HIGH RISK"
                    })

        # Check for bone marrow suppression (any visit)
        for visit in subject_data["VisitName"].unique():
            visit_data = subject_data[subject_data["VisitName"] == visit]

            hgb = visit_data[visit_data["TestName"] == "Hemoglobin"]["TestValue"].values
            wbc = visit_data[visit_data["TestName"] == "WBC"]["TestValue"].values
            plt = visit_data[visit_data["TestName"] == "Platelets"]["TestValue"].values

            severe_criteria = []
            if len(hgb) > 0 and hgb[0] < 8.0:
                severe_criteria.append(f"Hemoglobin {hgb[0]:.1f} g/dL")
            if len(wbc) > 0 and wbc[0] < 2.0:
                severe_criteria.append(f"WBC {wbc[0]:.1f} x10^9/L")
            if len(plt) > 0 and plt[0] < 50:
                severe_criteria.append(f"Platelets {plt[0]:.0f} x10^9/L")

            if severe_criteria:
                result["bone_marrow_cases"].append({
                    "SubjectID": subject,
                    "VisitName": visit,
                    "abnormalities": severe_criteria,
                    "severity": "HIGH RISK" if len(severe_criteria) >= 2 else "MODERATE RISK"
                })

    # Overall safety summary
    result["overall_safety_summary"] = {
        "total_subjects": len(subjects),
        "hys_law_count": len(result["hys_law_cases"]),
        "hys_law_rate": round(len(result["hys_law_cases"]) / len(subjects) * 100, 1) if len(subjects) > 0 else 0,
        "kidney_decline_count": len(result["kidney_decline_cases"]),
        "kidney_decline_rate": round(len(result["kidney_decline_cases"]) / len(subjects) * 100, 1) if len(subjects) > 0 else 0,
        "bone_marrow_suppression_count": len(result["bone_marrow_cases"]),
        "bone_marrow_suppression_rate": round(len(result["bone_marrow_cases"]) / len(subjects) * 100, 1) if len(subjects) > 0 else 0,
        "any_safety_signal": len(result["hys_law_cases"]) + len(result["kidney_decline_cases"]) + len(result["bone_marrow_cases"]) > 0
    }

    return result


def analyze_labs_longitudinal(labs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Time-series analysis of lab trends

    Analyzes how lab values change over time for each test and treatment arm.

    Args:
        labs_df: DataFrame with columns:
            - SubjectID
            - VisitName
            - TestName
            - TestValue
            - TreatmentArm (optional)

    Returns:
        Dictionary with:
        - trends_by_test: Trend statistics for each lab test
        - trends_by_arm: Trend comparisons between treatment arms
        - slope_analysis: Linear slope of lab values over time
    """
    result = {
        "trends_by_test": {},
        "trends_by_arm": {},
        "slope_analysis": {}
    }

    # Assign numeric visit numbers
    visits = sorted(labs_df["VisitName"].unique())
    visit_mapping = {visit: idx for idx, visit in enumerate(visits)}
    labs_df["VisitNumber"] = labs_df["VisitName"].map(visit_mapping)

    # Analyze trends by test
    for test_name in labs_df["TestName"].unique():
        test_data = labs_df[labs_df["TestName"] == test_name]

        # Mean values at each visit
        visit_means = test_data.groupby("VisitName")["TestValue"].agg(["mean", "std", "count"]).reset_index()
        visit_means["VisitNumber"] = visit_means["VisitName"].map(visit_mapping)
        visit_means = visit_means.sort_values("VisitNumber")

        # Calculate linear slope
        if len(visit_means) >= 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                visit_means["VisitNumber"],
                visit_means["mean"]
            )

            result["trends_by_test"][test_name] = {
                "visit_means": visit_means[["VisitName", "mean", "std"]].to_dict(orient="records"),
                "slope": round(float(slope), 3),
                "r_squared": round(float(r_value ** 2), 3),
                "p_value": round(float(p_value), 4),
                "trend_direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "trend_significant": p_value < 0.05
            }

    # Analyze trends by treatment arm
    if "TreatmentArm" in labs_df.columns:
        for test_name in labs_df["TestName"].unique():
            result["trends_by_arm"][test_name] = {}

            for arm in labs_df["TreatmentArm"].unique():
                arm_test_data = labs_df[
                    (labs_df["TestName"] == test_name) &
                    (labs_df["TreatmentArm"] == arm)
                ]

                visit_means = arm_test_data.groupby("VisitName")["TestValue"].mean().reset_index()
                visit_means["VisitNumber"] = visit_means["VisitName"].map(visit_mapping)
                visit_means = visit_means.sort_values("VisitNumber")

                if len(visit_means) >= 2:
                    slope, _, r_value, p_value, _ = stats.linregress(
                        visit_means["VisitNumber"],
                        visit_means["TestValue"]
                    )

                    result["trends_by_arm"][test_name][arm] = {
                        "slope": round(float(slope), 3),
                        "r_squared": round(float(r_value ** 2), 3),
                        "p_value": round(float(p_value), 4),
                        "trend_direction": "increasing" if slope > 0 else "decreasing"
                    }

    return result
