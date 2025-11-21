"""
Automated Quality Report Generator for Synthetic Clinical Trial Data

Generates comprehensive, human-readable quality reports for each
synthetic dataset.

This addresses professor's feedback on:
- Automated small report for each synthetic dataset
- Means/variances comparison to expected values
- CI coverage statistics (CART study: 88-98%)
- Overall reliability assessment

Output format: Markdown with tables, metrics, and recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime


class QualityReportGenerator:
    """
    Generate automated quality assessment reports

    Creates comprehensive, readable reports combining:
    - SYNDATA metrics
    - Privacy assessment
    - Method comparison results
    - Recommendations
    """

    def __init__(self):
        """Initialize report generator"""
        pass

    def generate_report(
        self,
        method_name: str,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        syndata_metrics: Optional[Dict] = None,
        privacy_metrics: Optional[Dict] = None,
        generation_time_ms: Optional[float] = None
    ) -> str:
        """
        Generate comprehensive quality report in Markdown format

        Args:
            method_name: Generation method used
            real_data: Real baseline data
            synthetic_data: Generated synthetic data
            syndata_metrics: SYNDATA quality metrics (optional)
            privacy_metrics: Privacy assessment metrics (optional)
            generation_time_ms: Generation time (optional)

        Returns:
            Markdown-formatted quality report
        """
        report_lines = []

        # Header
        report_lines.append(f"# Synthetic Data Quality Report")
        report_lines.append(f"")
        report_lines.append(f"**Generation Method**: {method_name.upper()}")
        report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Real Records**: {len(real_data)}")
        report_lines.append(f"**Synthetic Records**: {len(synthetic_data)}")
        if generation_time_ms:
            report_lines.append(f"**Generation Time**: {generation_time_ms:.1f} ms ({len(synthetic_data) / (generation_time_ms / 1000):.0f} records/sec)")
        report_lines.append(f"")
        report_lines.append("---")
        report_lines.append("")

        # Summary Statistics
        report_lines.extend(self._generate_summary_stats_section(real_data, synthetic_data))

        # CI Coverage (CART Study Metric)
        if syndata_metrics and 'ci_coverage' in syndata_metrics:
            report_lines.extend(self._generate_ci_coverage_section(syndata_metrics['ci_coverage']))

        # SYNDATA Metrics
        if syndata_metrics:
            report_lines.extend(self._generate_syndata_section(syndata_metrics))

        # Privacy Assessment
        if privacy_metrics:
            report_lines.extend(self._generate_privacy_section(privacy_metrics))

        # Overall Assessment
        report_lines.extend(self._generate_overall_assessment(
            method_name, syndata_metrics, privacy_metrics
        ))

        # Recommendations
        report_lines.extend(self._generate_recommendations(
            method_name, syndata_metrics, privacy_metrics
        ))

        return "\n".join(report_lines)

    def _generate_summary_stats_section(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> list:
        """Generate summary statistics comparison"""
        lines = []
        lines.append("## 📊 Summary Statistics")
        lines.append("")
        lines.append("### Mean and Variance Comparison")
        lines.append("")

        # Get numeric columns
        numeric_cols = real_data.select_dtypes(include=[np.number]).columns.tolist()

        # Create table
        lines.append("| Variable | Real Mean | Synthetic Mean | Diff (%) | Real Std | Synthetic Std | Diff (%) |")
        lines.append("|----------|-----------|----------------|----------|----------|---------------|----------|")

        for col in numeric_cols:
            if col not in synthetic_data.columns:
                continue

            real_mean = real_data[col].mean()
            synth_mean = synthetic_data[col].mean()
            mean_diff = abs(real_mean - synth_mean) / real_mean * 100 if real_mean != 0 else 0

            real_std = real_data[col].std()
            synth_std = synthetic_data[col].std()
            std_diff = abs(real_std - synth_std) / real_std * 100 if real_std != 0 else 0

            lines.append(
                f"| {col} | {real_mean:.2f} | {synth_mean:.2f} | {mean_diff:.1f}% | "
                f"{real_std:.2f} | {synth_std:.2f} | {std_diff:.1f}% |"
            )

        lines.append("")
        return lines

    def _generate_ci_coverage_section(self, ci_coverage: Dict) -> list:
        """Generate CI coverage section (CART study metric)"""
        lines = []
        lines.append("## 🎯 Confidence Interval Coverage (CART Study Metric)")
        lines.append("")
        lines.append("**Target**: 88-98% of synthetic values should fall within real data 95% CI")
        lines.append("")
        lines.append(f"**Overall Coverage**: {ci_coverage['average_coverage_95']:.1f}%")
        lines.append(f"**CART Compliant Variables**: {ci_coverage['cart_compliant_variables']} / {len(ci_coverage['by_column'])}")
        lines.append(f"**Compliance Rate**: {ci_coverage['cart_compliance_pct']:.0f}%")
        lines.append("")
        lines.append(f"**Interpretation**: {ci_coverage['interpretation']}")
        lines.append("")

        # Table of CI coverage by variable
        lines.append("### Coverage by Variable")
        lines.append("")
        lines.append("| Variable | Real Mean ± SD | 95% CI | Coverage | CART Standard |")
        lines.append("|----------|----------------|--------|----------|---------------|")

        for col, metrics in ci_coverage['by_column'].items():
            ci_str = f"[{metrics['ci_95'][0]:.1f}, {metrics['ci_95'][1]:.1f}]"
            cart_status = "✅" if metrics['meets_cart_standard'] else "❌"

            lines.append(
                f"| {col} | {metrics['real_mean']:.2f} ± {metrics['real_std']:.2f} | "
                f"{ci_str} | {metrics['coverage_95_pct']:.1f}% | {cart_status} {metrics['quality']} |"
            )

        lines.append("")
        lines.append("**Legend**:")
        lines.append("- ✅ Meets CART standard (88-98%)")
        lines.append("- ❌ Outside CART range")
        lines.append("")

        return lines

    def _generate_syndata_section(self, syndata_metrics: Dict) -> list:
        """Generate SYNDATA metrics section"""
        lines = []
        lines.append("## 📈 SYNDATA Quality Metrics")
        lines.append("")
        lines.append(f"**Overall SYNDATA Score**: {syndata_metrics['overall_syndata_score']:.3f}")
        lines.append(f"**Interpretation**: {syndata_metrics['interpretation']}")
        lines.append("")

        # Support Coverage
        if 'support_coverage' in syndata_metrics:
            sc = syndata_metrics['support_coverage']
            lines.append("### Support Coverage")
            lines.append(f"- **Score**: {sc['overall_score']:.3f}")
            lines.append(f"- **Interpretation**: {sc['interpretation']}")
            lines.append("")

        # Cross-Classification
        if 'cross_classification' in syndata_metrics:
            cc = syndata_metrics['cross_classification']
            lines.append("### Cross-Classification (Joint Distributions)")
            lines.append(f"- **Score**: {cc['overall_score']:.3f}")
            lines.append(f"- **Interpretation**: {cc['interpretation']}")
            lines.append("")

        # Membership Disclosure
        if 'membership_disclosure' in syndata_metrics:
            md = syndata_metrics['membership_disclosure']
            if 'classifier_test_accuracy' in md:
                lines.append("### Membership Disclosure Risk")
                lines.append(f"- **Classifier Accuracy**: {md['classifier_test_accuracy']:.3f} (baseline: 0.5)")
                lines.append(f"- **Privacy Score**: {md['privacy_score']:.3f}")
                lines.append(f"- **Risk Level**: {md['risk_level']}")
                lines.append("")

        # Attribute Disclosure
        if 'attribute_disclosure' in syndata_metrics:
            ad = syndata_metrics['attribute_disclosure']
            if 'r2_score' in ad:
                lines.append("### Attribute Disclosure Risk")
                lines.append(f"- **Prediction R²**: {ad['r2_score']:.3f}")
                lines.append(f"- **Privacy Score**: {ad['privacy_score']:.3f}")
                lines.append(f"- **Risk**: {ad['disclosure_risk']}")
                lines.append("")

        return lines

    def _generate_privacy_section(self, privacy_metrics: Dict) -> list:
        """Generate privacy assessment section"""
        lines = []
        lines.append("## 🔒 Privacy Assessment")
        lines.append("")

        if 'k_anonymity' in privacy_metrics:
            k_anon = privacy_metrics['k_anonymity']
            lines.append(f"### K-Anonymity")
            lines.append(f"- **k value**: {k_anon['k']}")
            lines.append(f"- **Safe**: {k_anon['safe']}")
            lines.append(f"- **Recommendation**: {k_anon['recommendation']}")
            lines.append("")

        if 'overall_assessment' in privacy_metrics:
            overall = privacy_metrics['overall_assessment']
            lines.append(f"### Overall Privacy")
            lines.append(f"- **Safe for Release**: {overall['safe_for_release']}")
            lines.append(f"- **Recommendation**: {overall['recommendation']}")
            lines.append("")

        return lines

    def _generate_overall_assessment(
        self,
        method_name: str,
        syndata_metrics: Optional[Dict],
        privacy_metrics: Optional[Dict]
    ) -> list:
        """Generate overall quality assessment"""
        lines = []
        lines.append("## ✅ Overall Assessment")
        lines.append("")

        quality_score = syndata_metrics.get('overall_syndata_score', 0) if syndata_metrics else 0
        privacy_safe = privacy_metrics.get('overall_assessment', {}).get('safe_for_release', True) if privacy_metrics else True

        if quality_score >= 0.85 and privacy_safe:
            grade = "A"
            status = "✅ EXCELLENT"
            recommendation = "Synthetic data is high quality and safe for release. Suitable for research and analysis."
        elif quality_score >= 0.70 and privacy_safe:
            grade = "B"
            status = "✓ GOOD"
            recommendation = "Synthetic data quality is good. Suitable for most use cases."
        elif quality_score >= 0.60:
            grade = "C"
            status = "⚠️ ACCEPTABLE"
            recommendation = "Synthetic data quality is acceptable but could be improved. Review specific metrics."
        else:
            grade = "D"
            status = "❌ NEEDS IMPROVEMENT"
            recommendation = "Synthetic data quality needs improvement. Consider different generation method or parameters."

        lines.append(f"**Grade**: {grade}")
        lines.append(f"**Status**: {status}")
        lines.append(f"**Recommendation**: {recommendation}")
        lines.append("")

        return lines

    def _generate_recommendations(
        self,
        method_name: str,
        syndata_metrics: Optional[Dict],
        privacy_metrics: Optional[Dict]
    ) -> list:
        """Generate actionable recommendations"""
        lines = []
        lines.append("## 💡 Recommendations")
        lines.append("")

        recommendations = []

        # Check CI coverage
        if syndata_metrics and 'ci_coverage' in syndata_metrics:
            ci = syndata_metrics['ci_coverage']
            if ci['cart_compliance_pct'] < 50:
                recommendations.append(
                    "⚠️ **CI Coverage**: Less than 50% of variables meet CART standard. "
                    "Consider adjusting generation parameters or using Bootstrap method."
                )

        # Check privacy
        if privacy_metrics and 'k_anonymity' in privacy_metrics:
            k_anon = privacy_metrics['k_anonymity']
            if k_anon['k'] < 5:
                recommendations.append(
                    f"⚠️ **Privacy**: K-anonymity is {k_anon['k']} (target: ≥5). "
                    "Consider adding more noise or using differential privacy."
                )

        # Check membership disclosure
        if syndata_metrics and 'membership_disclosure' in syndata_metrics:
            md = syndata_metrics['membership_disclosure']
            if md.get('classifier_test_accuracy', 0) > 0.70:
                recommendations.append(
                    f"⚠️ **Membership Disclosure**: Classifier accuracy is {md['classifier_test_accuracy']:.2f}. "
                    "Real and synthetic records can be distinguished. Consider using MICE or adding more variation."
                )

        # Method-specific recommendations
        method_recommendations = {
            'mvn': "Consider Bootstrap for better distribution matching or Bayesian for causal relationships.",
            'bootstrap': "Already using best method for realism. Consider increasing jitter_frac if privacy is concern.",
            'rules': "Consider MVN or Bootstrap for more realistic distributions.",
            'bayesian': "Good for capturing dependencies. Ensure network structure is correct.",
            'mice': "Good for handling missing data. Adjust missing_rate if needed.",
            'llm': "Good for creative scenarios but slower. Consider MVN for large datasets."
        }

        if method_name.lower() in method_recommendations:
            recommendations.append(f"💡 **Method**: {method_recommendations[method_name.lower()]}")

        if not recommendations:
            recommendations.append("✅ **All metrics look good!** No specific recommendations.")

        for rec in recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        return lines

    def generate_compact_summary(
        self,
        method_name: str,
        syndata_metrics: Dict
    ) -> str:
        """
        Generate compact one-line summary

        Useful for quick comparison across methods
        """
        score = syndata_metrics.get('overall_syndata_score', 0)
        ci_coverage = syndata_metrics.get('ci_coverage', {})
        avg_coverage = ci_coverage.get('average_coverage_95', 0)
        cart_compliant = ci_coverage.get('cart_compliant_variables', 0)

        return (
            f"{method_name.upper()}: Score={score:.3f}, "
            f"CI Coverage={avg_coverage:.0f}%, "
            f"CART Compliant={cart_compliant}"
        )


def generate_quality_report(
    method_name: str,
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    **kwargs
) -> str:
    """
    Convenience function to generate quality report

    Args:
        method_name: Generation method
        real_data: Real baseline data
        synthetic_data: Synthetic data
        **kwargs: Additional metrics (syndata_metrics, privacy_metrics, etc.)

    Returns:
        Markdown-formatted quality report
    """
    generator = QualityReportGenerator()
    return generator.generate_report(
        method_name, real_data, synthetic_data, **kwargs
    )


if __name__ == "__main__":
    # Test report generation
    print("Testing Quality Report Generator...")

    # Create sample data
    np.random.seed(42)
    n = 200

    real_data = pd.DataFrame({
        'SystolicBP': np.random.normal(140, 10, n),
        'DiastolicBP': np.random.normal(85, 8, n),
        'HeartRate': np.random.randint(60, 100, n)
    })

    synthetic_data = pd.DataFrame({
        'SystolicBP': np.random.normal(140, 11, n),
        'DiastolicBP': np.random.normal(85, 8.5, n),
        'HeartRate': np.random.randint(60, 100, n)
    })

    # Generate report
    report = generate_quality_report(
        "mvn",
        real_data,
        synthetic_data,
        generation_time_ms=28.5
    )

    print(report)
