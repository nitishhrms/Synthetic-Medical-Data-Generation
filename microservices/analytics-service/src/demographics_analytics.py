"""
Demographics Analytics Module
Provides statistical analysis and quality assessment for demographics data
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, wasserstein_distance


def calculate_baseline_characteristics(demographics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate baseline characteristics table (Table 1 in clinical trial papers)

    Provides comprehensive summary statistics for continuous and categorical variables,
    stratified by treatment arm with statistical comparisons.

    Args:
        demographics_df: DataFrame with columns:
            - SubjectID: Unique subject identifier
            - Age: Age in years
            - Gender: "Male" or "Female"
            - Race: Race category
            - Ethnicity: Ethnicity category
            - Height: Height in cm
            - Weight: Weight in kg
            - BMI: Body Mass Index
            - SmokingStatus: Smoking status
            - TreatmentArm: "Active" or "Placebo"

    Returns:
        Dict containing:
            - overall: Overall statistics across all subjects
            - by_arm: Statistics stratified by treatment arm
            - p_values: Statistical test results for arm balance
            - interpretation: Clinical interpretation of balance
    """
    # Basic validation
    if demographics_df.empty:
        raise ValueError("Demographics data is empty")

    required_cols = ["SubjectID", "Age", "Gender", "TreatmentArm"]
    missing_cols = [col for col in required_cols if col not in demographics_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Initialize results
    results = {
        "overall": {},
        "by_arm": {},
        "p_values": {},
        "interpretation": {}
    }

    # Overall statistics
    n_total = len(demographics_df)
    results["overall"]["n"] = n_total

    # Continuous variables
    continuous_vars = ["Age", "Height", "Weight", "BMI"]
    for var in continuous_vars:
        if var in demographics_df.columns:
            values = pd.to_numeric(demographics_df[var], errors='coerce').dropna()
            if len(values) > 0:
                results["overall"][f"{var.lower()}_mean"] = round(float(values.mean()), 1)
                results["overall"][f"{var.lower()}_sd"] = round(float(values.std()), 1)
                results["overall"][f"{var.lower()}_median"] = round(float(values.median()), 1)
                results["overall"][f"{var.lower()}_q1"] = round(float(values.quantile(0.25)), 1)
                results["overall"][f"{var.lower()}_q3"] = round(float(values.quantile(0.75)), 1)

    # Categorical variables
    categorical_vars = ["Gender", "Race", "Ethnicity", "SmokingStatus"]
    for var in categorical_vars:
        if var in demographics_df.columns:
            value_counts = demographics_df[var].value_counts()
            for category, count in value_counts.items():
                key = f"{var.lower()}_{str(category).lower().replace(' ', '_')}_n"
                results["overall"][key] = int(count)
                results["overall"][f"{key}_pct"] = round(100 * count / n_total, 1)

    # By treatment arm statistics
    if "TreatmentArm" in demographics_df.columns:
        for arm in demographics_df["TreatmentArm"].unique():
            arm_data = demographics_df[demographics_df["TreatmentArm"] == arm]
            n_arm = len(arm_data)

            arm_stats = {"n": n_arm}

            # Continuous variables by arm
            for var in continuous_vars:
                if var in arm_data.columns:
                    values = pd.to_numeric(arm_data[var], errors='coerce').dropna()
                    if len(values) > 0:
                        arm_stats[f"{var.lower()}_mean"] = round(float(values.mean()), 1)
                        arm_stats[f"{var.lower()}_sd"] = round(float(values.std()), 1)
                        arm_stats[f"{var.lower()}_median"] = round(float(values.median()), 1)

            # Categorical variables by arm
            for var in categorical_vars:
                if var in arm_data.columns:
                    value_counts = arm_data[var].value_counts()
                    for category, count in value_counts.items():
                        key = f"{var.lower()}_{str(category).lower().replace(' ', '_')}_n"
                        arm_stats[key] = int(count)
                        arm_stats[f"{key}_pct"] = round(100 * count / n_arm, 1)

            results["by_arm"][arm] = arm_stats

    # Statistical tests for balance
    if "TreatmentArm" in demographics_df.columns and len(demographics_df["TreatmentArm"].unique()) == 2:
        arms = demographics_df["TreatmentArm"].unique()
        arm1_data = demographics_df[demographics_df["TreatmentArm"] == arms[0]]
        arm2_data = demographics_df[demographics_df["TreatmentArm"] == arms[1]]

        # T-tests for continuous variables
        for var in continuous_vars:
            if var in demographics_df.columns:
                values1 = pd.to_numeric(arm1_data[var], errors='coerce').dropna()
                values2 = pd.to_numeric(arm2_data[var], errors='coerce').dropna()

                if len(values1) > 1 and len(values2) > 1:
                    try:
                        t_stat, p_value = ttest_ind(values1, values2, equal_var=False)
                        results["p_values"][var] = round(float(p_value), 4)
                    except:
                        results["p_values"][var] = None

        # Chi-square tests for categorical variables
        for var in categorical_vars:
            if var in demographics_df.columns:
                try:
                    contingency_table = pd.crosstab(
                        demographics_df["TreatmentArm"],
                        demographics_df[var]
                    )
                    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
                    results["p_values"][var] = round(float(p_value), 4)
                except:
                    results["p_values"][var] = None

    # Interpretation
    imbalanced_vars = []
    for var, p_val in results["p_values"].items():
        if p_val is not None and p_val < 0.05:
            imbalanced_vars.append(var)

    if len(imbalanced_vars) == 0:
        results["interpretation"]["balance_status"] = "well_balanced"
        results["interpretation"]["message"] = "Treatment arms are well balanced across all baseline characteristics"
    elif len(imbalanced_vars) <= 2:
        results["interpretation"]["balance_status"] = "mostly_balanced"
        results["interpretation"]["message"] = f"Treatment arms are mostly balanced. Minor imbalances in: {', '.join(imbalanced_vars)}"
        results["interpretation"]["imbalanced_variables"] = imbalanced_vars
    else:
        results["interpretation"]["balance_status"] = "imbalanced"
        results["interpretation"]["message"] = f"Significant imbalances detected in multiple variables: {', '.join(imbalanced_vars)}"
        results["interpretation"]["imbalanced_variables"] = imbalanced_vars

    # Format for frontend (Table 1 structure)
    characteristics = []
    
    # 1. Age
    if "Age" in demographics_df.columns:
        row = {"characteristic": "Age (years)"}
        if "by_arm" in results:
            for arm, stats in results["by_arm"].items():
                mean = stats.get("age_mean", "N/A")
                sd = stats.get("age_sd", "N/A")
                val = f"{mean} ({sd})"
                row[f"{arm.lower()}_value"] = val
                # Also add generic keys for frontend if it expects specific arm names
                if arm == "Active":
                    row["active_value"] = val
                elif arm == "Placebo":
                    row["placebo_value"] = val
        characteristics.append(row)

    # 2. Gender
    if "Gender" in demographics_df.columns:
        characteristics.append({"characteristic": "Gender, n (%)", "active_value": "", "placebo_value": ""})
        for cat in ["Male", "Female"]:
            row = {"characteristic": f"  {cat}"}
            if "by_arm" in results:
                for arm, stats in results["by_arm"].items():
                    key = f"gender_{cat.lower()}_n"
                    n = stats.get(key, 0)
                    pct = stats.get(f"{key}_pct", 0)
                    val = f"{n} ({pct}%)"
                    if arm == "Active":
                        row["active_value"] = val
                    elif arm == "Placebo":
                        row["placebo_value"] = val
            characteristics.append(row)

    # 3. Race
    if "Race" in demographics_df.columns:
        characteristics.append({"characteristic": "Race, n (%)", "active_value": "", "placebo_value": ""})
        top_races = demographics_df["Race"].value_counts().head(5).index.tolist()
        for race in top_races:
            row = {"characteristic": f"  {race}"}
            if "by_arm" in results:
                for arm, stats in results["by_arm"].items():
                    key = f"race_{str(race).lower().replace(' ', '_')}_n"
                    n = stats.get(key, 0)
                    pct = stats.get(f"{key}_pct", 0)
                    val = f"{n} ({pct}%)"
                    if arm == "Active":
                        row["active_value"] = val
                    elif arm == "Placebo":
                        row["placebo_value"] = val
            characteristics.append(row)

    # 4. BMI
    if "BMI" in demographics_df.columns:
        row = {"characteristic": "BMI (kg/m²)"}
        if "by_arm" in results:
            for arm, stats in results["by_arm"].items():
                mean = stats.get("bmi_mean", "N/A")
                sd = stats.get("bmi_sd", "N/A")
                val = f"{mean} ({sd})"
                if arm == "Active":
                    row["active_value"] = val
                elif arm == "Placebo":
                    row["placebo_value"] = val
        characteristics.append(row)

    results["characteristics"] = characteristics
    results["treatment_groups"] = results["by_arm"]  # Alias for frontend

    return results


def calculate_demographic_summary(demographics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate demographic distribution summary

    Provides high-level summary of demographic characteristics with distribution
    breakdowns for visualization.

    Args:
        demographics_df: DataFrame with demographics data

    Returns:
        Dict containing:
            - age_distribution: Age brackets with counts
            - gender_distribution: Gender breakdown
            - race_distribution: Race breakdown
            - ethnicity_distribution: Ethnicity breakdown
            - bmi_categories: BMI category breakdown
    """
    if demographics_df.empty:
        raise ValueError("Demographics data is empty")

    results = {}

    # Age distribution (bins)
    if "Age" in demographics_df.columns:
        age_values = pd.to_numeric(demographics_df["Age"], errors='coerce').dropna()
        age_bins = [0, 30, 45, 60, 75, 120]
        age_labels = ["18-30", "31-45", "46-60", "61-75", "76+"]

        age_categories = pd.cut(age_values, bins=age_bins, labels=age_labels, right=False)
        age_dist = age_categories.value_counts().sort_index()

        results["age_distribution"] = {
            "bins": age_labels,
            "counts": [int(age_dist.get(label, 0)) for label in age_labels],
            "percentages": [round(100 * age_dist.get(label, 0) / len(age_values), 1) for label in age_labels],
            "mean": round(float(age_values.mean()), 1),
            "median": round(float(age_values.median()), 1),
            "min": round(float(age_values.min()), 1),
            "max": round(float(age_values.max()), 1)
        }

    # Gender distribution
    if "Gender" in demographics_df.columns:
        gender_counts = demographics_df["Gender"].value_counts()
        total = len(demographics_df)

        results["gender_distribution"] = {
            "categories": gender_counts.index.tolist(),
            "counts": gender_counts.values.tolist(),
            "percentages": [round(100 * count / total, 1) for count in gender_counts.values]
        }

    # Race distribution
    if "Race" in demographics_df.columns:
        race_counts = demographics_df["Race"].value_counts()
        total = len(demographics_df)

        results["race_distribution"] = {
            "categories": race_counts.index.tolist(),
            "counts": race_counts.values.tolist(),
            "percentages": [round(100 * count / total, 1) for count in race_counts.values]
        }

    # Ethnicity distribution
    if "Ethnicity" in demographics_df.columns:
        ethnicity_counts = demographics_df["Ethnicity"].value_counts()
        total = len(demographics_df)

        results["ethnicity_distribution"] = {
            "categories": ethnicity_counts.index.tolist(),
            "counts": ethnicity_counts.values.tolist(),
            "percentages": [round(100 * count / total, 1) for count in ethnicity_counts.values]
        }

    # BMI categories
    if "BMI" in demographics_df.columns:
        bmi_values = pd.to_numeric(demographics_df["BMI"], errors='coerce').dropna()

        # WHO BMI categories
        def categorize_bmi(bmi):
            if bmi < 18.5:
                return "Underweight"
            elif bmi < 25:
                return "Normal"
            elif bmi < 30:
                return "Overweight"
            else:
                return "Obese"

        bmi_categories = bmi_values.apply(categorize_bmi)
        bmi_counts = bmi_categories.value_counts()

        category_order = ["Underweight", "Normal", "Overweight", "Obese"]
        results["bmi_categories"] = {
            "categories": category_order,
            "counts": [int(bmi_counts.get(cat, 0)) for cat in category_order],
            "percentages": [round(100 * bmi_counts.get(cat, 0) / len(bmi_values), 1) for cat in category_order],
            "mean": round(float(bmi_values.mean()), 1),
            "median": round(float(bmi_values.median()), 1)
        }

    # Summary statistics
    results["summary"] = {
        "total_subjects": len(demographics_df),
        "complete_records": int(demographics_df.notna().all(axis=1).sum()),
        "completeness_rate": round(100 * demographics_df.notna().all(axis=1).sum() / len(demographics_df), 1)
    }

    # Treatment Arms Summary (for frontend)
    results["treatment_arms"] = {}
    if "TreatmentArm" in demographics_df.columns:
        for arm in demographics_df["TreatmentArm"].unique():
            arm_data = demographics_df[demographics_df["TreatmentArm"] == arm]
            
            # Calculate stats for this arm
            stats = {
                "n": len(arm_data),
                "mean_age": round(float(arm_data["Age"].mean()), 1) if "Age" in arm_data else 0,
                "mean_bmi": round(float(arm_data["BMI"].mean()), 1) if "BMI" in arm_data else 0,
            }
            
            if "Gender" in arm_data:
                gender_counts = arm_data["Gender"].value_counts()
                stats["male_count"] = int(gender_counts.get("Male", 0))
                stats["female_count"] = int(gender_counts.get("Female", 0))
                stats["male_percent"] = round(100 * stats["male_count"] / len(arm_data), 1) if len(arm_data) > 0 else 0
                stats["female_percent"] = round(100 * stats["female_count"] / len(arm_data), 1) if len(arm_data) > 0 else 0
            
            results["treatment_arms"][arm] = stats

    return results


def assess_treatment_arm_balance(demographics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if randomization produced balanced treatment arms
    
    Uses statistical tests (chi-square for categorical, t-test for continuous)
    and standardized differences to assess balance.
    
    Args:
        demographics_df: DataFrame with demographics data including TreatmentArm
        
    Returns:
        Dict containing:
            - balance_tests: List of statistical test results for each variable (Frontend expects list)
            - standardized_differences: Standardized mean differences
            - overall_assessment: Summary of balance quality
    """
    if "TreatmentArm" not in demographics_df.columns:
        raise ValueError("TreatmentArm column is required")
        
    arms = demographics_df["TreatmentArm"].unique()
    if len(arms) != 2:
        raise ValueError(f"Expected 2 treatment arms, found {len(arms)}")
        
    arm1, arm2 = arms[0], arms[1]
    arm1_data = demographics_df[demographics_df["TreatmentArm"] == arm1]
    arm2_data = demographics_df[demographics_df["TreatmentArm"] == arm2]
    
    balance_tests_list = []  # Changed to list for frontend
    standardized_differences = {}
    
    # Continuous variables - T-tests and standardized differences
    continuous_vars = ["Age", "Height", "Weight", "BMI"]
    for var in continuous_vars:
        if var in demographics_df.columns:
            values1 = pd.to_numeric(arm1_data[var], errors='coerce').dropna()
            values2 = pd.to_numeric(arm2_data[var], errors='coerce').dropna()
            
            if len(values1) > 1 and len(values2) > 1:
                # T-test
                try:
                    t_stat, p_value = ttest_ind(values1, values2, equal_var=False)
                    
                    # Standardized difference (Cohen's d)
                    mean1, mean2 = values1.mean(), values2.mean()
                    std_pooled = np.sqrt((values1.var() + values2.var()) / 2)
                    std_diff = (mean1 - mean2) / std_pooled if std_pooled > 0 else 0
                    
                    test_result = {
                        "variable": var,
                        "test_name": "t-test (Welch)",
                        "statistic": round(float(t_stat), 4),
                        "p_value": round(float(p_value), 4),
                        "mean_arm1": round(float(mean1), 2),
                        "mean_arm2": round(float(mean2), 2),
                        "difference": round(float(mean1 - mean2), 2),
                        "balanced": p_value >= 0.05
                    }
                    balance_tests_list.append(test_result)
                    
                    standardized_differences[var] = {
                        "std_diff": round(float(std_diff), 3),
                        "interpretation": (
                            "negligible" if abs(std_diff) < 0.1 else
                            "small" if abs(std_diff) < 0.2 else
                            "medium" if abs(std_diff) < 0.5 else
                            "large"
                        ),
                        "acceptable": abs(std_diff) < 0.2  # Common threshold
                    }
                except Exception as e:
                    balance_tests_list.append({"variable": var, "error": str(e)})

    # Categorical variables - Chi-square tests
    categorical_vars = ["Gender", "Race", "Ethnicity", "SmokingStatus"]
    for var in categorical_vars:
        if var in demographics_df.columns:
            try:
                contingency_table = pd.crosstab(
                    demographics_df["TreatmentArm"],
                    demographics_df[var]
                )
                
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)
                
                # Get proportions for each category
                arm1_props = contingency_table.loc[arm1] / contingency_table.loc[arm1].sum()
                arm2_props = contingency_table.loc[arm2] / contingency_table.loc[arm2].sum()
                
                max_diff = max(abs(arm1_props - arm2_props))
                
                test_result = {
                    "variable": var,
                    "test_name": "chi-square",
                    "statistic": round(float(chi2), 4),
                    "p_value": round(float(p_value), 4),
                    "degrees_of_freedom": int(dof),
                    "max_proportion_difference": round(float(max_diff), 3),
                    "balanced": p_value >= 0.05
                }
                balance_tests_list.append(test_result)
            except Exception as e:
                balance_tests_list.append({"variable": var, "error": str(e)})
                
    results = {
        "balance_tests": balance_tests_list,
        "standardized_differences": standardized_differences,
        "sample_sizes": {
            arm1: len(arm1_data),
            arm2: len(arm2_data)
        }
    }

    # Overall assessment
    total_tests = len(balance_tests_list)
    balanced_tests = sum(1 for test in balance_tests_list 
                         if isinstance(test, dict) and test.get("balanced", False))
                         
    std_diffs_acceptable = sum(1 for diff in standardized_differences.values() 
                               if diff.get("acceptable", False))
    total_std_diffs = len(standardized_differences)
    
    results["overall_assessment"] = {
        "total_variables_tested": total_tests,
        "balanced_variables": balanced_tests,
        "balance_rate": round(100 * balanced_tests / total_tests, 1) if total_tests > 0 else 0,
        "acceptable_std_diffs": std_diffs_acceptable,
        "std_diff_rate": round(100 * std_diffs_acceptable / total_std_diffs, 1) if total_std_diffs > 0 else 0,
        "overall_balance": (
            "excellent" if balanced_tests / total_tests >= 0.9 else
            "good" if balanced_tests / total_tests >= 0.7 else
            "fair" if balanced_tests / total_tests >= 0.5 else
            "poor"
        ) if total_tests > 0 else "unknown",
        "recommendation": (
            "Randomization successful - arms are well balanced" if total_tests > 0 and balanced_tests / total_tests >= 0.8 else
            "Minor imbalances present - consider covariate adjustment in analysis" if total_tests > 0 and balanced_tests / total_tests >= 0.6 else
            "Significant imbalances detected - stratified randomization or adjustment recommended"
        )
    }
    
    # Add interpretation for frontend
    results["overall_balanced"] = results["overall_assessment"]["overall_balance"] in ["excellent", "good"]
    results["interpretation"] = results["overall_assessment"]["recommendation"]
    
    return results


def compare_demographics_quality(
    real_df: pd.DataFrame,
    synthetic_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Quality assessment for synthetic demographics data

    Compares distributions between real and synthetic demographics using:
    - Wasserstein distance for continuous variables
    - Chi-square tests for categorical variables
    - Correlation preservation

    Args:
        real_df: Real demographics data
        synthetic_df: Synthetic demographics data

    Returns:
        Dict containing:
            - distribution_similarity: Wasserstein distances
            - categorical_similarity: Chi-square test results
            - correlation_preservation: Correlation comparison
            - overall_quality_score: 0-1 quality score
    """
    if real_df.empty or synthetic_df.empty:
        raise ValueError("Both real and synthetic data must be non-empty")

    results = {
        "distribution_similarity": {},
        "categorical_similarity": {},
        "correlation_preservation": {}
    }

    # Continuous variables - Wasserstein distance
    continuous_vars = ["Age", "Height", "Weight", "BMI"]
    wasserstein_scores = []

    for var in continuous_vars:
        if var in real_df.columns and var in synthetic_df.columns:
            real_values = pd.to_numeric(real_df[var], errors='coerce').dropna()
            syn_values = pd.to_numeric(synthetic_df[var], errors='coerce').dropna()

            if len(real_values) > 0 and len(syn_values) > 0:
                w_dist = wasserstein_distance(real_values, syn_values)

                # Normalize by range
                value_range = real_values.max() - real_values.min()
                normalized_dist = w_dist / value_range if value_range > 0 else 0

                # Convert to similarity score (0-1, higher is better)
                similarity = max(0, 1 - normalized_dist)
                wasserstein_scores.append(similarity)

                results["distribution_similarity"][var] = {
                    "wasserstein_distance": round(float(w_dist), 3),
                    "normalized_distance": round(float(normalized_dist), 3),
                    "similarity_score": round(float(similarity), 3),
                    "real_mean": round(float(real_values.mean()), 2),
                    "synthetic_mean": round(float(syn_values.mean()), 2),
                    "real_std": round(float(real_values.std()), 2),
                    "synthetic_std": round(float(syn_values.std()), 2)
                }

    # Categorical variables - Chi-square tests
    categorical_vars = ["Gender", "Race", "Ethnicity", "SmokingStatus"]
    categorical_scores = []

    for var in categorical_vars:
        if var in real_df.columns and var in synthetic_df.columns:
            try:
                # Get category counts
                real_counts = real_df[var].value_counts()
                syn_counts = synthetic_df[var].value_counts()

                # Align categories
                all_categories = set(real_counts.index) | set(syn_counts.index)
                real_counts_aligned = [real_counts.get(cat, 0) for cat in all_categories]
                syn_counts_aligned = [syn_counts.get(cat, 0) for cat in all_categories]

                # Chi-square test
                chi2, p_value = stats.chisquare(syn_counts_aligned, f_exp=real_counts_aligned)

                # Calculate proportion differences
                real_props = real_counts / real_counts.sum()
                syn_props = syn_counts / syn_counts.sum()

                max_diff = max([abs(real_props.get(cat, 0) - syn_props.get(cat, 0))
                               for cat in all_categories])

                # Similarity score (based on p-value and max difference)
                similarity = min(p_value, 1 - max_diff)
                categorical_scores.append(similarity)

                results["categorical_similarity"][var] = {
                    "chi_square_statistic": round(float(chi2), 3),
                    "p_value": round(float(p_value), 4),
                    "max_proportion_difference": round(float(max_diff), 3),
                    "similarity_score": round(float(similarity), 3),
                    "distributions_match": p_value >= 0.05
                }
            except Exception as e:
                results["categorical_similarity"][var] = {"error": str(e)}

    # Correlation preservation (for continuous variables)
    continuous_vars_present = [var for var in continuous_vars
                               if var in real_df.columns and var in synthetic_df.columns]

    if len(continuous_vars_present) >= 2:
        try:
            real_corr = real_df[continuous_vars_present].corr()
            syn_corr = synthetic_df[continuous_vars_present].corr()

            # Frobenius norm of difference
            corr_diff = np.abs(real_corr.values - syn_corr.values)

            # Get upper triangle (exclude diagonal)
            upper_triangle_indices = np.triu_indices_from(corr_diff, k=1)
            mean_abs_diff = np.mean(corr_diff[upper_triangle_indices])

            correlation_preservation_score = max(0, 1 - mean_abs_diff)

            results["correlation_preservation"] = {
                "mean_absolute_difference": round(float(mean_abs_diff), 3),
                "preservation_score": round(float(correlation_preservation_score), 3),
                "real_correlations": real_corr.to_dict(),
                "synthetic_correlations": syn_corr.to_dict()
            }
        except Exception as e:
            results["correlation_preservation"] = {"error": str(e)}

    # Overall quality score (weighted average)
    scores = []

    if wasserstein_scores:
        scores.append(("distribution", np.mean(wasserstein_scores), 0.4))

    if categorical_scores:
        scores.append(("categorical", np.mean(categorical_scores), 0.3))

    if "preservation_score" in results["correlation_preservation"]:
        scores.append(("correlation", results["correlation_preservation"]["preservation_score"], 0.3))

    if scores:
        total_weight = sum(weight for _, _, weight in scores)
        overall_score = sum(score * weight for _, score, weight in scores) / total_weight
    else:
        overall_score = 0.0

    results["overall_quality_score"] = round(float(overall_score), 3)

    # Interpretation
    if overall_score >= 0.85:
        interpretation = "EXCELLENT - Synthetic demographics closely match real data"
    elif overall_score >= 0.70:
        interpretation = "GOOD - Synthetic demographics are usable with minor differences"
    elif overall_score >= 0.50:
        interpretation = "FAIR - Some notable differences, review generation parameters"
    else:
        interpretation = "POOR - Significant differences, consider alternative generation method"

    results["quality_interpretation"] = {
        "score": round(float(overall_score), 3),
        "rating": interpretation.split(" - ")[0],
        "message": interpretation
    }

    return results
