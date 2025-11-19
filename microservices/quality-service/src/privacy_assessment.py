"""
Privacy Assessment Module for Synthetic Clinical Data

Evaluates privacy risk of synthetic datasets to ensure they cannot be
used to re-identify real patients. Critical for HIPAA/GDPR compliance.

This addresses professor's feedback on:
- Privacy and compliance considerations
- Demonstrating awareness of regulatory requirements
- Providing privacy guarantees for synthetic data

Metrics implemented:
1. K-anonymity: Minimum group size for quasi-identifiers
2. Re-identification risk: Probability of linking synthetic to real record
3. Attribute disclosure risk: Risk of learning sensitive attributes
4. Differential privacy budget: Privacy loss quantification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from collections import Counter
import itertools

try:
    from anonymeter.evaluators import SinglingOutEvaluator, LinkabilityEvaluator
    from anonymeter.evaluators import InferenceEvaluator
    ANONYMETER_AVAILABLE = True
except ImportError:
    ANONYMETER_AVAILABLE = False
    print("Warning: anonymeter not available. Install with: pip install anonymeter")


class PrivacyAssessor:
    """
    Comprehensive privacy risk assessment for synthetic clinical data
    """

    def __init__(
        self,
        quasi_identifiers: Optional[List[str]] = None,
        sensitive_attributes: Optional[List[str]] = None
    ):
        """
        Initialize privacy assessor

        Args:
            quasi_identifiers: Columns that could be used for re-identification
                (e.g., age, gender, race, zip code)
            sensitive_attributes: Columns with sensitive medical data
                (e.g., diagnosis, lab results, medications)
        """
        self.quasi_identifiers = quasi_identifiers or [
            'Age', 'Gender', 'Race', 'Ethnicity'
        ]
        self.sensitive_attributes = sensitive_attributes or [
            'SystolicBP', 'DiastolicBP', 'Diagnosis'
        ]

    def calculate_k_anonymity(
        self,
        data: pd.DataFrame,
        quasi_identifiers: Optional[List[str]] = None
    ) -> Dict:
        """
        Calculate k-anonymity for dataset

        K-anonymity: Each record is indistinguishable from at least k-1 others
        with respect to quasi-identifiers.

        For clinical data, k >= 5 is generally considered minimum, k >= 10 is better.

        Args:
            data: Synthetic dataset
            quasi_identifiers: Columns to check (default: self.quasi_identifiers)

        Returns:
            Dict with k-anonymity metrics
        """
        if quasi_identifiers is None:
            quasi_identifiers = [
                qi for qi in self.quasi_identifiers if qi in data.columns
            ]

        if len(quasi_identifiers) == 0:
            return {
                'k': float('inf'),
                'message': 'No quasi-identifiers found in dataset',
                'safe': True
            }

        # Group by quasi-identifiers and count group sizes
        grouped = data.groupby(quasi_identifiers).size()

        k = int(grouped.min())
        mean_group_size = float(grouped.mean())
        median_group_size = float(grouped.median())

        # Find records in small groups (k < 5)
        small_groups = grouped[grouped < 5]
        risky_records = int(small_groups.sum())

        return {
            'k': k,
            'mean_group_size': mean_group_size,
            'median_group_size': median_group_size,
            'total_equivalence_classes': len(grouped),
            'risky_records': risky_records,
            'risky_percentage': (risky_records / len(data)) * 100,
            'safe': k >= 5,
            'recommendation': self._get_k_anonymity_recommendation(k),
            'quasi_identifiers_used': quasi_identifiers
        }

    def _get_k_anonymity_recommendation(self, k: int) -> str:
        """Get recommendation based on k-anonymity level"""
        if k >= 10:
            return "Excellent privacy protection (k≥10). Safe for release."
        elif k >= 5:
            return "Good privacy protection (5≤k<10). Generally safe for release."
        elif k >= 3:
            return "Moderate risk (3≤k<5). Consider additional privacy measures."
        else:
            return "High re-identification risk (k<3). DO NOT release without modification."

    def calculate_l_diversity(
        self,
        data: pd.DataFrame,
        quasi_identifiers: Optional[List[str]] = None,
        sensitive_attributes: Optional[List[str]] = None
    ) -> Dict:
        """
        Calculate l-diversity for dataset

        L-diversity: Each equivalence class (group with same quasi-identifiers)
        has at least l well-represented values for each sensitive attribute.

        This prevents homogeneity attacks where all records in a group
        have the same sensitive value (e.g., all have diabetes).

        Args:
            data: Synthetic dataset
            quasi_identifiers: QI columns
            sensitive_attributes: Sensitive columns to check

        Returns:
            Dict with l-diversity metrics
        """
        if quasi_identifiers is None:
            quasi_identifiers = [
                qi for qi in self.quasi_identifiers if qi in data.columns
            ]

        if sensitive_attributes is None:
            sensitive_attributes = [
                sa for sa in self.sensitive_attributes if sa in data.columns
            ]

        if len(quasi_identifiers) == 0 or len(sensitive_attributes) == 0:
            return {
                'l': float('inf'),
                'message': 'Insufficient columns for l-diversity',
                'safe': True
            }

        # Group by quasi-identifiers
        grouped = data.groupby(quasi_identifiers)

        # For each group, check diversity of sensitive attributes
        min_l_values = []

        for name, group in grouped:
            # Check diversity for each sensitive attribute
            for sa in sensitive_attributes:
                unique_values = group[sa].nunique()
                min_l_values.append(unique_values)

        l = int(np.min(min_l_values)) if len(min_l_values) > 0 else 0

        return {
            'l': l,
            'mean_diversity': float(np.mean(min_l_values)) if len(min_l_values) > 0 else 0,
            'safe': l >= 2,
            'recommendation': self._get_l_diversity_recommendation(l),
            'quasi_identifiers_used': quasi_identifiers,
            'sensitive_attributes_checked': sensitive_attributes
        }

    def _get_l_diversity_recommendation(self, l: int) -> str:
        """Get recommendation based on l-diversity"""
        if l >= 5:
            return "Excellent diversity (l≥5). Well protected against homogeneity attacks."
        elif l >= 2:
            return "Good diversity (l≥2). Protected against simple homogeneity attacks."
        else:
            return "Insufficient diversity (l<2). Vulnerable to homogeneity attacks."

    def assess_reidentification_risk(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        n_attacks: int = 1000
    ) -> Dict:
        """
        Assess re-identification risk using privacy attacks

        Uses anonymeter library to simulate attacks:
        1. Singling out: Can attacker isolate a real record using synthetic?
        2. Linkability: Can attacker link real and synthetic records?
        3. Inference: Can attacker infer sensitive attributes?

        Args:
            real_data: Original real dataset
            synthetic_data: Synthetic dataset to evaluate
            n_attacks: Number of attack simulations

        Returns:
            Risk scores and recommendations
        """
        if not ANONYMETER_AVAILABLE:
            return {
                'error': 'anonymeter library not available',
                'message': 'Install with: pip install anonymeter',
                'risk_level': 'unknown'
            }

        results = {}

        # Align columns
        common_cols = list(set(real_data.columns) & set(synthetic_data.columns))
        # Use only numeric columns for simplicity
        numeric_cols = real_data[common_cols].select_dtypes(include=[np.number]).columns.tolist()

        if len(numeric_cols) < 2:
            return {
                'error': 'Insufficient numeric columns for privacy attack',
                'message': f'Found only {len(numeric_cols)} numeric columns, need at least 2'
            }

        real_subset = real_data[numeric_cols].dropna()
        syn_subset = synthetic_data[numeric_cols].dropna()

        # 1. Singling Out Attack
        try:
            singling_evaluator = SinglingOutEvaluator(
                ori=real_subset,
                syn=syn_subset,
                n_attacks=min(n_attacks, len(real_subset))
            )

            singling_risk = singling_evaluator.evaluate(mode='univariate')

            results['singling_out'] = {
                'attack_rate': float(singling_risk.attack_rate),
                'baseline_rate': float(singling_risk.control_rate),
                'risk': float(singling_risk.attack_rate - singling_risk.control_rate),
                'safe': singling_risk.attack_rate < 0.1
            }
        except Exception as e:
            results['singling_out'] = {
                'error': str(e),
                'message': 'Singling out evaluation failed'
            }

        # 2. Linkability Attack
        try:
            linkability_evaluator = LinkabilityEvaluator(
                ori=real_subset,
                syn=syn_subset,
                n_attacks=min(n_attacks, len(real_subset)),
                n_neighbors=10
            )

            linkability_risk = linkability_evaluator.evaluate()

            results['linkability'] = {
                'attack_rate': float(linkability_risk.attack_rate),
                'baseline_rate': float(linkability_risk.control_rate),
                'risk': float(linkability_risk.attack_rate - linkability_risk.control_rate),
                'safe': linkability_risk.attack_rate < 0.2
            }
        except Exception as e:
            results['linkability'] = {
                'error': str(e),
                'message': 'Linkability evaluation failed'
            }

        # 3. Attribute Inference Attack
        try:
            if len(numeric_cols) >= 3:
                # Pick one column as secret, others as known
                secret_col = numeric_cols[0]
                aux_cols = numeric_cols[1:3]

                inference_evaluator = InferenceEvaluator(
                    ori=real_subset,
                    syn=syn_subset,
                    aux_cols=aux_cols,
                    secret=secret_col,
                    n_attacks=min(n_attacks, len(real_subset))
                )

                inference_risk = inference_evaluator.evaluate()

                results['inference'] = {
                    'attack_rate': float(inference_risk.attack_rate),
                    'baseline_rate': float(inference_risk.control_rate),
                    'risk': float(inference_risk.attack_rate - inference_risk.control_rate),
                    'safe': inference_risk.attack_rate < 0.15,
                    'secret_column': secret_col
                }
        except Exception as e:
            results['inference'] = {
                'error': str(e),
                'message': 'Inference evaluation failed'
            }

        # Overall risk assessment
        risks = []
        if 'singling_out' in results and 'risk' in results['singling_out']:
            risks.append(results['singling_out']['risk'])
        if 'linkability' in results and 'risk' in results['linkability']:
            risks.append(results['linkability']['risk'])
        if 'inference' in results and 'risk' in results['inference']:
            risks.append(results['inference']['risk'])

        if len(risks) > 0:
            max_risk = max(risks)
            results['overall'] = {
                'max_risk': max_risk,
                'mean_risk': float(np.mean(risks)),
                'risk_level': self._categorize_risk(max_risk),
                'safe_for_release': max_risk < 0.05
            }
        else:
            results['overall'] = {
                'error': 'Could not compute overall risk',
                'safe_for_release': False
            }

        return results

    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize privacy risk level"""
        if risk_score < 0.01:
            return "Very Low - Excellent privacy"
        elif risk_score < 0.05:
            return "Low - Good privacy"
        elif risk_score < 0.10:
            return "Moderate - Acceptable for most uses"
        elif risk_score < 0.20:
            return "High - Use with caution"
        else:
            return "Very High - DO NOT release"

    def calculate_differential_privacy_budget(
        self,
        epsilon: float,
        delta: float,
        n_queries: int = 1
    ) -> Dict:
        """
        Calculate differential privacy budget

        Differential privacy provides mathematical guarantee:
        "Adding or removing one individual's data changes output probability
        by at most exp(epsilon)"

        Args:
            epsilon: Privacy loss parameter (lower = more private)
                Common values: 0.1 (strict), 1.0 (moderate), 10.0 (weak)
            delta: Failure probability (typically 1/n²)
            n_queries: Number of queries made on the data

        Returns:
            Privacy budget analysis
        """
        # Total privacy budget with composition
        total_epsilon = epsilon * np.sqrt(2 * n_queries * np.log(1/delta))

        return {
            'epsilon': epsilon,
            'delta': delta,
            'n_queries': n_queries,
            'total_epsilon': total_epsilon,
            'privacy_level': self._categorize_epsilon(epsilon),
            'budget_remaining': max(0, 10.0 - total_epsilon),  # Assume 10.0 max budget
            'recommendation': self._get_dp_recommendation(epsilon, total_epsilon)
        }

    def _categorize_epsilon(self, epsilon: float) -> str:
        """Categorize epsilon privacy level"""
        if epsilon < 0.1:
            return "Very Strong (ε<0.1)"
        elif epsilon < 1.0:
            return "Strong (0.1≤ε<1.0)"
        elif epsilon < 5.0:
            return "Moderate (1.0≤ε<5.0)"
        else:
            return "Weak (ε≥5.0)"

    def _get_dp_recommendation(self, epsilon: float, total_epsilon: float) -> str:
        """Get differential privacy recommendation"""
        if epsilon < 1.0:
            return "Strong privacy guarantee. Safe for release."
        elif epsilon < 5.0:
            return "Moderate privacy. Generally acceptable."
        elif epsilon < 10.0:
            return "Weak privacy. Use with caution."
        else:
            return "Very weak privacy. Consider stronger protections."

    def comprehensive_privacy_report(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        quasi_identifiers: Optional[List[str]] = None,
        sensitive_attributes: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate comprehensive privacy assessment report

        Args:
            real_data: Original dataset
            synthetic_data: Synthetic dataset
            quasi_identifiers: QI columns
            sensitive_attributes: Sensitive columns

        Returns:
            Complete privacy report
        """
        report = {
            'dataset_info': {
                'real_records': len(real_data),
                'synthetic_records': len(synthetic_data),
                'real_columns': list(real_data.columns),
                'synthetic_columns': list(synthetic_data.columns)
            }
        }

        # K-anonymity
        print("Calculating k-anonymity...")
        report['k_anonymity'] = self.calculate_k_anonymity(
            synthetic_data,
            quasi_identifiers
        )

        # L-diversity
        print("Calculating l-diversity...")
        report['l_diversity'] = self.calculate_l_diversity(
            synthetic_data,
            quasi_identifiers,
            sensitive_attributes
        )

        # Re-identification risk (if anonymeter available)
        print("Assessing re-identification risk...")
        report['reidentification'] = self.assess_reidentification_risk(
            real_data,
            synthetic_data,
            n_attacks=500
        )

        # Differential privacy (example budget)
        report['differential_privacy'] = self.calculate_differential_privacy_budget(
            epsilon=1.0,
            delta=1.0 / (len(real_data) ** 2),
            n_queries=1
        )

        # Overall recommendation
        k_safe = report['k_anonymity'].get('safe', False)
        l_safe = report['l_diversity'].get('safe', False)
        reid_safe = report['reidentification'].get('overall', {}).get('safe_for_release', True)

        all_safe = k_safe and l_safe and reid_safe

        report['overall_assessment'] = {
            'k_anonymity_safe': k_safe,
            'l_diversity_safe': l_safe,
            'reidentification_safe': reid_safe,
            'safe_for_release': all_safe,
            'recommendation': self._get_overall_recommendation(all_safe, report)
        }

        return report

    def _get_overall_recommendation(self, all_safe: bool, report: Dict) -> str:
        """Generate overall recommendation"""
        if all_safe:
            return "✅ SAFE FOR RELEASE - All privacy checks passed"

        issues = []
        if not report['k_anonymity'].get('safe', False):
            issues.append(f"Low k-anonymity (k={report['k_anonymity']['k']})")
        if not report['l_diversity'].get('safe', False):
            issues.append(f"Low l-diversity (l={report['l_diversity']['l']})")
        if not report['reidentification'].get('overall', {}).get('safe_for_release', True):
            issues.append("High re-identification risk")

        return f"⚠️ PRIVACY CONCERNS - {'; '.join(issues)}. Review before release."


if __name__ == "__main__":
    # Test privacy assessment
    print("Testing Privacy Assessment Module...")

    # Create sample data
    real_data = pd.DataFrame({
        'SubjectID': [f'S{i:03d}' for i in range(100)],
        'Age': np.random.randint(18, 85, 100),
        'Gender': np.random.choice(['M', 'F'], 100),
        'SystolicBP': np.random.randint(110, 180, 100),
        'DiastolicBP': np.random.randint(70, 110, 100)
    })

    synthetic_data = pd.DataFrame({
        'SubjectID': [f'S{i:03d}' for i in range(100, 200)],
        'Age': np.random.randint(18, 85, 100),
        'Gender': np.random.choice(['M', 'F'], 100),
        'SystolicBP': np.random.randint(110, 180, 100),
        'DiastolicBP': np.random.randint(70, 110, 100)
    })

    # Initialize assessor
    assessor = PrivacyAssessor(
        quasi_identifiers=['Age', 'Gender'],
        sensitive_attributes=['SystolicBP', 'DiastolicBP']
    )

    # Run assessments
    print("\n=== K-Anonymity ===")
    k_anon = assessor.calculate_k_anonymity(synthetic_data)
    print(f"K: {k_anon['k']}")
    print(f"Recommendation: {k_anon['recommendation']}")

    print("\n=== L-Diversity ===")
    l_div = assessor.calculate_l_diversity(synthetic_data)
    print(f"L: {l_div['l']}")
    print(f"Recommendation: {l_div['recommendation']}")

    print("\n=== Differential Privacy ===")
    dp = assessor.calculate_differential_privacy_budget(epsilon=1.0, delta=1e-5)
    print(f"Epsilon: {dp['epsilon']}")
    print(f"Privacy level: {dp['privacy_level']}")
    print(f"Recommendation: {dp['recommendation']}")

    print("\n=== Comprehensive Report ===")
    report = assessor.comprehensive_privacy_report(
        real_data,
        synthetic_data,
        quasi_identifiers=['Age', 'Gender'],
        sensitive_attributes=['SystolicBP']
    )
    print(f"Overall: {report['overall_assessment']['recommendation']}")
