"""
SYNDATA-Style Quality Metrics for Synthetic Clinical Trial Data

Implements metrics from NIH's SYNDATA project for comprehensive
synthetic data quality assessment.

This directly addresses professor's feedback on:
- Support coverage
- Cross-classification for utility
- Membership/attribute disclosure
- Confidence interval coverage (CART study metric: 88-98%)

Reference: SYNDATA project (NIH), CART study on synthetic patient data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from collections import defaultdict
import math


def safe_float(value, default=0.0):
    """Convert value to float, handling NaN/Inf cases"""
    try:
        if value is None:
            return default
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return default
        return val
    except (ValueError, TypeError):
        return default


def safe_value(value):
    """Convert numpy types to Python native types for JSON serialization"""
    if value is None:
        return None

    # Handle numpy bool
    if isinstance(value, (np.bool_, np.bool8)):
        return bool(value)

    # Handle numpy integers
    if isinstance(value, (np.integer, np.int_, np.int8, np.int16, np.int32, np.int64)):
        return int(value)

    # Handle numpy floats
    if isinstance(value, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        val = float(value)
        # Check for NaN/Inf
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return val

    # Already a Python type
    return value


def sanitize_for_json(obj):
    """Recursively sanitize object for JSON serialization, handling NaN/Inf"""
    if obj is None:
        return None

    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]

    # Handle numpy bools
    if isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)

    # Handle numpy integers
    if isinstance(obj, (np.integer, np.int_, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)

    # Handle floats (both numpy and Python)
    if isinstance(obj, (float, np.floating, np.float_, np.float16, np.float32, np.float64)):
        try:
            val = float(obj)
            if math.isnan(val) or math.isinf(val):
                return 0.0
            return val
        except (ValueError, TypeError):
            return 0.0

    # Handle integers
    if isinstance(obj, (int, np.integer)):
        return int(obj)

    # Return as-is for strings, bools, etc.
    return obj


class SYNDATAMetrics:
    """
    SYNDATA-style quality metrics for synthetic data validation

    Key metrics:
    1. Support Coverage: Does synthetic data cover same value ranges as real?
    2. Cross-Classification: Do joint distributions match?
    3. Confidence Interval Coverage: % of synthetic values within real CI
    4. Membership Disclosure: Can we tell if a record is real or synthetic?
    5. Attribute Disclosure: Can we infer attributes from synthetic data?
    """

    def __init__(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame):
        """
        Initialize SYNDATA metrics calculator

        Args:
            real_data: Real clinical trial data (baseline)
            synthetic_data: Synthetic data to evaluate
        """
        self.real_data = real_data
        self.synthetic_data = synthetic_data

    def compute_all_metrics(self) -> Dict:
        """
        Compute all SYNDATA-style metrics

        Returns comprehensive quality report
        """
        results = {
            "support_coverage": self.compute_support_coverage(),
            "cross_classification": self.compute_cross_classification(),
            "ci_coverage": self.compute_ci_coverage(),
            "membership_disclosure": self.assess_membership_disclosure(),
            "attribute_disclosure": self.assess_attribute_disclosure(),
            "overall_syndata_score": 0.0
        }

        # Compute overall SYNDATA score
        results["overall_syndata_score"] = self._compute_overall_score(results)

        # Generate interpretation
        results["interpretation"] = self._generate_interpretation(results)

        # Sanitize all values for JSON serialization
        return sanitize_for_json(results)

    def compute_support_coverage(self) -> Dict:
        """
        Support Coverage: Does synthetic data cover the same value ranges as real?

        For each numeric column, check:
        - Min/max coverage
        - Percentile coverage (10th, 25th, 50th, 75th, 90th)
        - % of synthetic values that fall outside real data range

        Returns:
            Support coverage metrics per column
        """
        numeric_cols = self.real_data.select_dtypes(include=[np.number]).columns.tolist()

        coverage_results = {}

        for col in numeric_cols:
            if col not in self.synthetic_data.columns:
                continue

            real_vals = self.real_data[col].dropna()
            synth_vals = self.synthetic_data[col].dropna()

            # Min/max coverage
            real_min, real_max = real_vals.min(), real_vals.max()
            synth_min, synth_max = synth_vals.min(), synth_vals.max()

            # Check if synthetic stays within real bounds
            within_bounds = synth_vals.between(real_min, real_max)
            coverage_pct = (within_bounds.sum() / len(synth_vals)) * 100 if len(synth_vals) > 0 else 0

            # Percentile coverage
            real_percentiles = {
                'p10': np.percentile(real_vals, 10),
                'p25': np.percentile(real_vals, 25),
                'p50': np.percentile(real_vals, 50),
                'p75': np.percentile(real_vals, 75),
                'p90': np.percentile(real_vals, 90)
            }

            synth_percentiles = {
                'p10': np.percentile(synth_vals, 10),
                'p25': np.percentile(synth_vals, 25),
                'p50': np.percentile(synth_vals, 50),
                'p75': np.percentile(synth_vals, 75),
                'p90': np.percentile(synth_vals, 90)
            }

            # Percentile overlap score
            percentile_diffs = [
                abs(real_percentiles[p] - synth_percentiles[p]) / real_percentiles[p] * 100
                for p in real_percentiles.keys()
            ]
            avg_percentile_diff = np.mean(percentile_diffs)

            coverage_results[col] = {
                "real_range": [float(real_min), float(real_max)],
                "synthetic_range": [float(synth_min), float(synth_max)],
                "within_bounds_pct": round(coverage_pct, 2),
                "real_percentiles": {k: round(v, 2) for k, v in real_percentiles.items()},
                "synthetic_percentiles": {k: round(v, 2) for k, v in synth_percentiles.items()},
                "avg_percentile_diff_pct": round(avg_percentile_diff, 2),
                "coverage_score": round(max(0, 1 - avg_percentile_diff / 100), 3)
            }

        # Overall support coverage score
        scores = [c["coverage_score"] for c in coverage_results.values()]
        overall_score = safe_float(np.mean(scores) if scores else 0.0, 0.0)

        return {
            "by_column": coverage_results,
            "overall_score": round(overall_score, 3),
            "by_variable": {col: c["coverage_score"] for col, c in coverage_results.items()},  # Frontend expects by_variable
            "interpretation": self._interpret_support_coverage(overall_score)
        }

    def _interpret_support_coverage(self, score: float) -> str:
        """Interpret support coverage score"""
        if score > 0.95:
            return "Excellent - Synthetic data fully covers real data support"
        elif score > 0.85:
            return "Good - Synthetic data covers most of real data range"
        elif score > 0.70:
            return "Acceptable - Some support coverage gaps"
        else:
            return "Poor - Synthetic data doesn't cover real data range well"

    def compute_cross_classification(self) -> Dict:
        """
        Cross-Classification for Utility: Do joint distributions match?

        Tests if combinations of variables occur with similar frequencies
        in real vs synthetic data.

        Example: In real data, 30% are "Male + Age 50-60 + Active treatment"
                 Does synthetic have ~30% too?

        Returns:
            Cross-classification metrics
        """
        # For clinical trial data, test common cross-classifications
        results = {}

        # 1. TreatmentArm × VisitName
        if 'TreatmentArm' in self.real_data.columns and 'VisitName' in self.real_data.columns:
            results['treatment_x_visit'] = self._cross_classify_two_vars(
                'TreatmentArm', 'VisitName'
            )

        # 2. TreatmentArm × Blood Pressure Category
        if 'TreatmentArm' in self.real_data.columns and 'SystolicBP' in self.real_data.columns:
            # Create BP categories
            real_bp_cat = pd.cut(
                self.real_data['SystolicBP'],
                bins=[0, 120, 130, 140, 200],
                labels=['Normal', 'Elevated', 'Stage1', 'Stage2']
            )
            synth_bp_cat = pd.cut(
                self.synthetic_data['SystolicBP'],
                bins=[0, 120, 130, 140, 200],
                labels=['Normal', 'Elevated', 'Stage1', 'Stage2']
            )

            real_with_bp = self.real_data.copy()
            real_with_bp['BP_Category'] = real_bp_cat
            synth_with_bp = self.synthetic_data.copy()
            synth_with_bp['BP_Category'] = synth_bp_cat

            results['treatment_x_bp_category'] = self._cross_classify_two_vars_df(
                real_with_bp, synth_with_bp, 'TreatmentArm', 'BP_Category'
            )
        
        # 3. Fallback: SystolicBP × DiastolicBP (Binned) - ALWAYS RUN if vitals exist
        # This ensures we have a utility score even if categorical columns are missing
        if 'SystolicBP' in self.real_data.columns and 'DiastolicBP' in self.real_data.columns:
            # Bin both variables
            real_sbp_cat = pd.cut(self.real_data['SystolicBP'], bins=3, labels=['Low', 'Medium', 'High'])
            synth_sbp_cat = pd.cut(self.synthetic_data['SystolicBP'], bins=3, labels=['Low', 'Medium', 'High'])
            
            real_dbp_cat = pd.cut(self.real_data['DiastolicBP'], bins=3, labels=['Low', 'Medium', 'High'])
            synth_dbp_cat = pd.cut(self.synthetic_data['DiastolicBP'], bins=3, labels=['Low', 'Medium', 'High'])
            
            real_binned = pd.DataFrame({'SBP_Group': real_sbp_cat, 'DBP_Group': real_dbp_cat})
            synth_binned = pd.DataFrame({'SBP_Group': synth_sbp_cat, 'DBP_Group': synth_dbp_cat})
            
            results['sbp_x_dbp_binned'] = self._cross_classify_two_vars_df(
                real_binned, synth_binned, 'SBP_Group', 'DBP_Group'
            )

        # Overall cross-classification score
        scores = [r['utility_score'] for r in results.values() if 'utility_score' in r]
        overall_score = safe_float(np.mean(scores) if scores else 0.0, 0.0)

        return {
            "cross_classifications": results,
            "overall_score": round(overall_score, 3),
            "interpretation": self._interpret_cross_classification(overall_score)
        }

    def _cross_classify_two_vars(self, var1: str, var2: str) -> Dict:
        """Cross-classify two categorical variables"""
        return self._cross_classify_two_vars_df(
            self.real_data, self.synthetic_data, var1, var2
        )

    def _cross_classify_two_vars_df(
        self,
        real_df: pd.DataFrame,
        synth_df: pd.DataFrame,
        var1: str,
        var2: str
    ) -> Dict:
        """Helper for cross-classification"""
        # Get frequency tables
        real_counts = pd.crosstab(real_df[var1], real_df[var2], normalize=True)
        synth_counts = pd.crosstab(synth_df[var1], synth_df[var2], normalize=True)

        # Align indices
        all_combinations = set(real_counts.stack().index) | set(synth_counts.stack().index)

        # Compute total variation distance
        differences = []
        for idx in all_combinations:
            real_prop = real_counts.stack().get(idx, 0)
            synth_prop = synth_counts.stack().get(idx, 0)
            differences.append(abs(real_prop - synth_prop))

        total_variation_distance = sum(differences) / 2
        utility_score = 1 - total_variation_distance

        return {
            "variables": f"{var1} × {var2}",
            "total_variation_distance": round(total_variation_distance, 3),
            "utility_score": round(utility_score, 3),
            "real_distribution": real_counts.to_dict(),
            "synthetic_distribution": synth_counts.to_dict()
        }

    def _interpret_cross_classification(self, score: float) -> str:
        """Interpret cross-classification score"""
        if score > 0.95:
            return "Excellent - Joint distributions nearly identical"
        elif score > 0.85:
            return "Good - Joint distributions well matched"
        elif score > 0.70:
            return "Acceptable - Some joint distribution differences"
        else:
            return "Poor - Joint distributions differ significantly"

    def compute_ci_coverage(self) -> Dict:
        """
        Confidence Interval Coverage (CART Study Metric)

        **This is the key metric the professor mentioned!**

        For each numeric variable:
        1. Compute 95% CI from real data: [mean - 1.96*se, mean + 1.96*se]
        2. Check what % of synthetic values fall within this CI
        3. Target: 88-98% (like CART study)

        This validates that synthetic data is statistically consistent with real.

        Returns:
            CI coverage metrics per column
        """
        numeric_cols = self.real_data.select_dtypes(include=[np.number]).columns.tolist()

        ci_results = {}

        for col in numeric_cols:
            if col not in self.synthetic_data.columns:
                continue

            real_vals = self.real_data[col].dropna()
            synth_vals = self.synthetic_data[col].dropna()

            # Compute 95% prediction interval from real data
            # Use STANDARD DEVIATION (SD) not Standard Error (SE)
            # SE is for confidence interval of the MEAN
            # SD is for prediction interval where INDIVIDUAL VALUES fall
            real_mean = real_vals.mean()
            real_std = real_vals.std()  # Use SD for individual predictions
            ci_lower = real_mean - 1.96 * real_std
            ci_upper = real_mean + 1.96 * real_std

            # Check how many synthetic values fall within CI
            within_ci = synth_vals.between(ci_lower, ci_upper)
            coverage_pct = (within_ci.sum() / len(synth_vals)) * 100 if len(synth_vals) > 0 else 0

            # Also compute 90% and 99% CIs for completeness
            ci_90_lower = real_mean - 1.645 * real_std
            ci_90_upper = real_mean + 1.645 * real_std
            ci_99_lower = real_mean - 2.576 * real_std
            ci_99_upper = real_mean + 2.576 * real_std

            coverage_90 = (synth_vals.between(ci_90_lower, ci_90_upper).sum() / len(synth_vals)) * 100
            coverage_99 = (synth_vals.between(ci_99_lower, ci_99_upper).sum() / len(synth_vals)) * 100

            # Interpretation
            if 88 <= coverage_pct <= 98:
                quality = "Excellent (CART study range)"
            elif 80 <= coverage_pct < 88:
                quality = "Good (slightly below CART)"
            elif coverage_pct < 80:
                quality = "Poor (too few within CI)"
            else:  # > 98
                quality = "Good (slightly above CART, may be too conservative)"

            ci_results[col] = {
                "real_mean": round(real_mean, 2),
                "real_std": round(real_std, 2),  # Changed from real_se to real_std
                "ci_95": [round(ci_lower, 2), round(ci_upper, 2)],
                "ci_90": [round(ci_90_lower, 2), round(ci_90_upper, 2)],
                "ci_99": [round(ci_99_lower, 2), round(ci_99_upper, 2)],
                "coverage_95_pct": round(coverage_pct, 2),
                "coverage_90_pct": round(coverage_90, 2),
                "coverage_99_pct": round(coverage_99, 2),
                "quality": quality,
                "meets_cart_standard": bool(88 <= coverage_pct <= 98)
            }

        # Overall CI coverage score
        coverage_values = [c["coverage_95_pct"] for c in ci_results.values()]
        avg_coverage = safe_float(np.mean(coverage_values) if coverage_values else 0.0, 0.0)

        # How many variables meet CART standard?
        cart_compliant = sum(1 for c in ci_results.values() if c["meets_cart_standard"])
        cart_compliance_pct = safe_float((cart_compliant / len(ci_results)) * 100 if ci_results else 0.0, 0.0)

        return {
            "by_column": ci_results,
            "average_coverage_95": round(avg_coverage, 2),
            "cart_compliant_variables": cart_compliant,
            "cart_compliance_pct": round(cart_compliance_pct, 2),
            "overall_coverage": round(safe_float(avg_coverage / 100, 0.0), 3),  # Frontend expects overall_coverage
            "overall_score": round(safe_float(avg_coverage / 100, 0.0), 3),  # Keep for backwards compat
            "by_variable": {col: c["coverage_95_pct"] / 100 for col, c in ci_results.items()},  # Frontend expects by_variable
            "meets_cart_standard": cart_compliant > 0,
            "interpretation": self._interpret_ci_coverage(avg_coverage, cart_compliance_pct)
        }

    def _interpret_ci_coverage(self, avg_coverage: float, cart_compliance_pct: float) -> str:
        """Interpret CI coverage results"""
        if cart_compliance_pct >= 75:
            return f"Excellent - {cart_compliance_pct:.0f}% of variables meet CART study standard (88-98%)"
        elif cart_compliance_pct >= 50:
            return f"Good - {cart_compliance_pct:.0f}% of variables meet CART standard"
        elif avg_coverage >= 85:
            return f"Acceptable - Average coverage {avg_coverage:.0f}%, but only {cart_compliance_pct:.0f}% meet CART standard"
        else:
            return f"Poor - Average coverage {avg_coverage:.0f}%, {cart_compliance_pct:.0f}% meet CART standard"

    def assess_membership_disclosure(self) -> Dict:
        """
        Membership Disclosure Risk: Can we tell if a record is real or synthetic?

        Train a classifier to distinguish real from synthetic.
        If accuracy >> 50%, there's disclosure risk.

        Returns:
            Membership disclosure metrics
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler

        # Get numeric columns
        numeric_cols = list(
            set(self.real_data.select_dtypes(include=[np.number]).columns) &
            set(self.synthetic_data.select_dtypes(include=[np.number]).columns)
        )

        if len(numeric_cols) < 2:
            return {
                "error": "Insufficient numeric columns for membership disclosure test"
            }

        # Create labeled dataset: 1 = real, 0 = synthetic
        real_subset = self.real_data[numeric_cols].dropna()
        synth_subset = self.synthetic_data[numeric_cols].dropna()

        # Balance if needed
        n = min(len(real_subset), len(synth_subset), 500)  # Cap at 500 for speed
        real_sample = real_subset.sample(n=n, random_state=42)
        synth_sample = synth_subset.sample(n=n, random_state=42)

        X_real = real_sample.values
        X_synth = synth_sample.values

        X = np.vstack([X_real, X_synth])
        y = np.hstack([np.ones(len(X_real)), np.zeros(len(X_synth))])

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )

        # Scale
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # Train classifier
        clf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
        clf.fit(X_train, y_train)

        # Evaluate
        train_acc = clf.score(X_train, y_train)
        test_acc = clf.score(X_test, y_test)

        # Interpretation
        # If accuracy ≈ 50%, real and synthetic are indistinguishable (good privacy)
        # If accuracy >> 50%, they can be distinguished (disclosure risk)
        disclosure_risk = max(0, test_acc - 0.5) * 2  # Scale to 0-1

        if test_acc < 0.55:
            risk_level = "Very Low - Real and synthetic indistinguishable"
        elif test_acc < 0.60:
            risk_level = "Low - Slight differences detectable"
        elif test_acc < 0.70:
            risk_level = "Moderate - Some membership disclosure risk"
        elif test_acc < 0.80:
            risk_level = "High - Significant disclosure risk"
        else:
            risk_level = "Very High - Easy to distinguish real from synthetic"

        return {
            "classifier_test_accuracy": round(test_acc, 3),
            "classifier_train_accuracy": round(train_acc, 3),
            "baseline_accuracy": 0.5,
            "disclosure_risk_score": round(disclosure_risk, 3),
            "risk_level": risk_level,
            "privacy_score": round(1 - disclosure_risk, 3),
            "interpretation": "Lower accuracy is better for privacy"
        }

    def assess_attribute_disclosure(self) -> Dict:
        """
        Attribute Disclosure Risk: Can we infer sensitive attributes?

        Test if knowing some attributes allows inferring others
        in synthetic data.

        Returns:
            Attribute disclosure metrics
        """
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import r2_score

        numeric_cols = list(
            set(self.real_data.select_dtypes(include=[np.number]).columns) &
            set(self.synthetic_data.select_dtypes(include=[np.number]).columns)
        )

        if len(numeric_cols) < 3:
            return {
                "error": "Insufficient columns for attribute disclosure test"
            }

        # Test: Can we predict SystolicBP from other vitals?
        if 'SystolicBP' in numeric_cols:
            target = 'SystolicBP'
            features = [c for c in numeric_cols if c != 'SystolicBP'][:3]
        else:
            target = numeric_cols[0]
            features = numeric_cols[1:4]

        # Test on real data
        real_clean = self.real_data[features + [target]].dropna()
        X_real = real_clean[features].values
        y_real = real_clean[target].values

        # Test on synthetic data
        synth_clean = self.synthetic_data[features + [target]].dropna()
        X_synth = synth_clean[features].values
        y_synth = synth_clean[target].values

        if len(X_real) < 50 or len(X_synth) < 50:
            return {"error": "Insufficient data for attribute disclosure test"}

        # Train on real, test on synthetic
        clf = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
        clf.fit(X_real, y_real)

        y_pred = clf.predict(X_synth)
        r2 = r2_score(y_synth, y_pred)

        # High R² means attributes are highly predictable (disclosure risk)
        if r2 > 0.8:
            risk = "High - Attributes highly predictable"
        elif r2 > 0.6:
            risk = "Moderate - Attributes somewhat predictable"
        else:
            risk = "Low - Attributes not easily inferred"

        return {
            "target_attribute": target,
            "predictor_attributes": features,
            "r2_score": round(r2, 3),
            "disclosure_risk": risk,
            "privacy_score": round(max(0, 1 - r2), 3)
        }

    def _compute_overall_score(self, results: Dict) -> float:
        """Compute overall SYNDATA quality score (0-1)"""
        scores = []

        if "support_coverage" in results:
            scores.append(safe_float(results["support_coverage"].get("overall_score", 0), 0.0))

        if "cross_classification" in results:
            scores.append(safe_float(results["cross_classification"].get("overall_score", 0), 0.0))

        if "ci_coverage" in results:
            scores.append(safe_float(results["ci_coverage"].get("overall_score", 0), 0.0))

        if "membership_disclosure" in results:
            scores.append(safe_float(results["membership_disclosure"].get("privacy_score", 0), 0.0))

        if "attribute_disclosure" in results:
            scores.append(safe_float(results["attribute_disclosure"].get("privacy_score", 0), 0.0))

        mean_score = safe_float(np.mean(scores) if scores else 0.0, 0.0)
        return round(mean_score, 3)

    def _generate_interpretation(self, results: Dict) -> str:
        """Generate overall interpretation"""
        score = results["overall_syndata_score"]

        ci_coverage = results.get("ci_coverage", {})
        cart_compliant = ci_coverage.get("cart_compliant_variables", 0)

        if score >= 0.90 and cart_compliant >= 3:
            return (
                f"✅ EXCELLENT - SYNDATA score: {score:.2f}. "
                f"{cart_compliant} variables meet CART study standard (88-98% CI coverage). "
                "Synthetic data is high quality and suitable for research use."
            )
        elif score >= 0.75:
            return (
                f"✓ GOOD - SYNDATA score: {score:.2f}. "
                "Synthetic data quality is acceptable for most use cases."
            )
        else:
            return (
                f"⚠️ NEEDS IMPROVEMENT - SYNDATA score: {score:.2f}. "
                "Consider adjusting generation parameters or using different method."
            )


def compute_syndata_metrics(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame
) -> Dict:
    """
    Convenience function to compute all SYNDATA metrics

    Args:
        real_data: Real clinical trial data
        synthetic_data: Synthetic data to evaluate

    Returns:
        Comprehensive SYNDATA quality report
    """
    metrics = SYNDATAMetrics(real_data, synthetic_data)
    return metrics.compute_all_metrics()


if __name__ == "__main__":
    # Test SYNDATA metrics
    print("Testing SYNDATA Metrics...")

    # Create sample data
    np.random.seed(42)
    n = 200

    real_data = pd.DataFrame({
        'SubjectID': [f'S{i:03d}' for i in range(n)],
        'TreatmentArm': np.random.choice(['Active', 'Placebo'], n),
        'VisitName': np.random.choice(['Screening', 'Week 12'], n),
        'SystolicBP': np.random.normal(140, 10, n),
        'DiastolicBP': np.random.normal(85, 8, n),
        'HeartRate': np.random.randint(60, 100, n)
    })

    # Generate synthetic with similar but not identical distribution
    synthetic_data = pd.DataFrame({
        'SubjectID': [f'S{i:03d}' for i in range(n, 2*n)],
        'TreatmentArm': np.random.choice(['Active', 'Placebo'], n),
        'VisitName': np.random.choice(['Screening', 'Week 12'], n),
        'SystolicBP': np.random.normal(140, 11, n),  # Slightly different std
        'DiastolicBP': np.random.normal(85, 8.5, n),
        'HeartRate': np.random.randint(60, 100, n)
    })

    # Compute metrics
    results = compute_syndata_metrics(real_data, synthetic_data)

    print("\n=== SYNDATA Metrics Results ===")
    print(f"Overall Score: {results['overall_syndata_score']:.3f}")
    print(f"\nInterpretation: {results['interpretation']}")

    print("\n=== CI Coverage (CART Study Metric) ===")
    ci = results['ci_coverage']
    print(f"Average Coverage: {ci['average_coverage_95']:.1f}%")
    print(f"CART Compliant Variables: {ci['cart_compliant_variables']}")
    print(f"Interpretation: {ci['interpretation']}")

    for col, metrics in ci['by_column'].items():
        print(f"\n{col}:")
        print(f"  Real Mean: {metrics['real_mean']:.1f}")
        print(f"  95% CI: {metrics['ci_95']}")
        print(f"  Coverage: {metrics['coverage_95_pct']:.1f}%")
        print(f"  Quality: {metrics['quality']}")
