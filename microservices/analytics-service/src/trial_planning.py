"""
Trial Planning Simulator - Virtual Control Arms and What-If Scenarios

Addresses professor's feedback on advanced use-cases:
- Generate virtual control arms to augment small real control groups
- Run what-if scenarios (enrollment size, patient mix variations)
- Estimate trial feasibility and power
- Simulate trial outcomes

Inspired by Medidata's Synthetic Control Arms product, adapted for
smaller-scale clinical trials.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from datetime import datetime, timedelta


@dataclass
class TrialParameters:
    """Trial design parameters"""
    n_per_arm: int = 50
    target_effect: float = -5.0  # Target SBP reduction in mmHg
    alpha: float = 0.05  # Significance level
    power: float = 0.80  # Statistical power
    dropout_rate: float = 0.10  # Expected dropout rate
    enrollment_duration_days: int = 180  # Enrollment period
    treatment_duration_weeks: int = 12  # Treatment duration


class VirtualControlArmGenerator:
    """
    Generate synthetic control arm to augment or replace real control data

    Use Cases:
    - Reduce placebo patients needed in trial
    - Augment small historical control groups
    - Simulate control arm for trial planning
    - Ethical alternative when placebo is problematic
    """

    def __init__(self, real_control_data: Optional[pd.DataFrame] = None):
        """
        Initialize generator with optional real control data

        Args:
            real_control_data: Historical or concurrent real control data
                               If provided, virtual arm will match its characteristics
        """
        self.real_control_data = real_control_data
        self.fitted = False

        # Default control arm characteristics (hypertension trial)
        self.baseline_vitals = {
            'SystolicBP': {'mean': 142, 'std': 10},
            'DiastolicBP': {'mean': 88, 'std': 8},
            'HeartRate': {'mean': 72, 'std': 10},
            'Temperature': {'mean': 36.6, 'std': 0.3}
        }

        # Expected changes over time (placebo effect, regression to mean)
        self.placebo_effect = {
            'SystolicBP': -2.0,  # Small placebo reduction
            'DiastolicBP': -1.0,
            'HeartRate': 0,
            'Temperature': 0
        }

    def fit(self, real_control_data: pd.DataFrame) -> None:
        """
        Learn parameters from real control data

        Args:
            real_control_data: Real control arm data to match
        """
        self.real_control_data = real_control_data

        # Learn baseline characteristics from Screening visit
        screening = real_control_data[real_control_data['VisitName'] == 'Screening']

        for vital in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
            if vital in screening.columns:
                self.baseline_vitals[vital] = {
                    'mean': screening[vital].mean(),
                    'std': screening[vital].std()
                }

        # Learn placebo effect from real data progression
        if 'Week 12' in real_control_data['VisitName'].values:
            screening_means = screening[['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']].mean()
            week12 = real_control_data[real_control_data['VisitName'] == 'Week 12']
            week12_means = week12[['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']].mean()

            for vital in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
                if vital in week12_means.index:
                    self.placebo_effect[vital] = week12_means[vital] - screening_means[vital]

        self.fitted = True

    def generate_virtual_control_arm(
        self,
        n_subjects: int = 50,
        visits: List[str] = None,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Generate synthetic control arm data

        Args:
            n_subjects: Number of virtual control subjects
            visits: Visit schedule (default: Screening, Day 1, Week 4, Week 12)
            seed: Random seed for reproducibility

        Returns:
            DataFrame with virtual control arm data
        """
        if seed is not None:
            np.random.seed(seed)

        if visits is None:
            visits = ['Screening', 'Day 1', 'Week 4', 'Week 12']

        records = []

        for subj_idx in range(n_subjects):
            subject_id = f"VCA-{subj_idx+1:03d}"  # Virtual Control Arm

            # Generate baseline vitals for this subject
            baseline_sbp = np.random.normal(
                self.baseline_vitals['SystolicBP']['mean'],
                self.baseline_vitals['SystolicBP']['std']
            )
            baseline_dbp = np.random.normal(
                self.baseline_vitals['DiastolicBP']['mean'],
                self.baseline_vitals['DiastolicBP']['std']
            )
            baseline_hr = np.random.normal(
                self.baseline_vitals['HeartRate']['mean'],
                self.baseline_vitals['HeartRate']['std']
            )
            baseline_temp = np.random.normal(
                self.baseline_vitals['Temperature']['mean'],
                self.baseline_vitals['Temperature']['std']
            )

            # Generate trajectory over time (placebo effect + noise)
            for visit in visits:
                # Time factor (0 at screening, 1 at week 12)
                if visit == 'Screening':
                    time_factor = 0
                elif visit == 'Day 1':
                    time_factor = 0.1
                elif visit == 'Week 4':
                    time_factor = 0.33
                elif visit == 'Week 12':
                    time_factor = 1.0
                else:
                    time_factor = 0

                # Apply placebo effect over time + random noise
                sbp = baseline_sbp + self.placebo_effect['SystolicBP'] * time_factor + np.random.normal(0, 3)
                dbp = baseline_dbp + self.placebo_effect['DiastolicBP'] * time_factor + np.random.normal(0, 2)
                hr = baseline_hr + self.placebo_effect['HeartRate'] * time_factor + np.random.normal(0, 4)
                temp = baseline_temp + self.placebo_effect['Temperature'] * time_factor + np.random.normal(0, 0.2)

                records.append({
                    'SubjectID': subject_id,
                    'VisitName': visit,
                    'TreatmentArm': 'Virtual_Placebo',
                    'SystolicBP': int(np.clip(sbp, 95, 200)),
                    'DiastolicBP': int(np.clip(dbp, 55, 130)),
                    'HeartRate': int(np.clip(hr, 50, 120)),
                    'Temperature': round(np.clip(temp, 35.0, 40.0), 1)
                })

        return pd.DataFrame(records)

    def augment_small_control_arm(
        self,
        real_control: pd.DataFrame,
        target_n: int = 50,
        seed: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Augment a small real control arm with virtual subjects

        Use Case: You have only 20 real control subjects but need 50 for power.
        This generates 30 virtual controls matching the real data characteristics.

        Args:
            real_control: Small real control arm data
            target_n: Target total sample size
            seed: Random seed

        Returns:
            Tuple of (augmented_data, statistics)
        """
        # Learn from real control data
        self.fit(real_control)

        # Count real subjects
        n_real = real_control['SubjectID'].nunique()

        if n_real >= target_n:
            return real_control, {
                'n_real': n_real,
                'n_virtual': 0,
                'augmentation_needed': False,
                'message': f'Real control arm (n={n_real}) already meets target (n={target_n})'
            }

        # Generate virtual subjects to reach target
        n_virtual = target_n - n_real
        virtual_control = self.generate_virtual_control_arm(
            n_subjects=n_virtual,
            seed=seed
        )

        # Combine real and virtual
        augmented = pd.concat([real_control, virtual_control], ignore_index=True)

        stats_dict = {
            'n_real': n_real,
            'n_virtual': n_virtual,
            'n_total': target_n,
            'augmentation_ratio': n_virtual / target_n,
            'augmentation_needed': True,
            'message': f'Augmented {n_real} real controls with {n_virtual} virtual controls'
        }

        return augmented, stats_dict


class WhatIfScenarioSimulator:
    """
    Simulate trial outcomes under different scenarios

    What-If Questions:
    - What if we enroll only 30 patients per arm instead of 50?
    - What if we have more severe patients (higher baseline BP)?
    - What if dropout rate is 20% instead of 10%?
    - What if treatment effect is smaller than expected?
    """

    def __init__(self, baseline_data: pd.DataFrame):
        """
        Initialize with baseline trial data

        Args:
            baseline_data: Real or synthetic baseline data
        """
        self.baseline_data = baseline_data

    def simulate_enrollment_scenarios(
        self,
        enrollment_sizes: List[int] = None,
        n_simulations: int = 1000,
        target_effect: float = -5.0,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate trial outcomes for different enrollment sizes

        Args:
            enrollment_sizes: List of n_per_arm values to test (e.g., [25, 50, 75, 100])
            n_simulations: Monte Carlo simulations per scenario
            target_effect: Expected treatment effect (SBP reduction)
            seed: Random seed

        Returns:
            Dictionary with power analysis for each scenario
        """
        if enrollment_sizes is None:
            enrollment_sizes = [25, 50, 75, 100, 150]

        if seed is not None:
            np.random.seed(seed)

        results = {}

        # Estimate parameters from baseline data
        baseline_sbp = self.baseline_data[
            self.baseline_data['VisitName'] == 'Screening'
        ]['SystolicBP']
        baseline_mean = baseline_sbp.mean()
        baseline_std = baseline_sbp.std()

        for n_per_arm in enrollment_sizes:
            significant_count = 0

            for _ in range(n_simulations):
                # Simulate control arm (placebo effect)
                control_week12 = np.random.normal(baseline_mean - 2.0, baseline_std, n_per_arm)

                # Simulate active arm (placebo + treatment effect)
                active_week12 = np.random.normal(baseline_mean - 2.0 + target_effect, baseline_std, n_per_arm)

                # Run t-test
                t_stat, p_value = stats.ttest_ind(active_week12, control_week12)

                if p_value < 0.05:
                    significant_count += 1

            power = significant_count / n_simulations

            results[f'n={n_per_arm}'] = {
                'n_per_arm': n_per_arm,
                'total_n': n_per_arm * 2,
                'power': power,
                'required_for_80pct_power': power >= 0.80,
                'required_for_90pct_power': power >= 0.90
            }

        return {
            'scenarios': results,
            'recommendation': self._recommend_sample_size(results),
            'parameters': {
                'target_effect': target_effect,
                'baseline_mean': baseline_mean,
                'baseline_std': baseline_std,
                'n_simulations': n_simulations
            }
        }

    def simulate_patient_mix_scenarios(
        self,
        severity_shifts: List[float] = None,
        n_per_arm: int = 50,
        n_simulations: int = 1000,
        target_effect: float = -5.0,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate outcomes with different patient populations

        Args:
            severity_shifts: List of baseline SBP shifts (e.g., [-10, 0, +10] mmHg)
            n_per_arm: Sample size per arm
            n_simulations: Monte Carlo simulations
            target_effect: Expected treatment effect
            seed: Random seed

        Returns:
            Dictionary with outcomes for each patient mix scenario
        """
        if severity_shifts is None:
            severity_shifts = [-10, -5, 0, 5, 10]  # Milder to more severe

        if seed is not None:
            np.random.seed(seed)

        baseline_sbp = self.baseline_data[
            self.baseline_data['VisitName'] == 'Screening'
        ]['SystolicBP']
        baseline_mean = baseline_sbp.mean()
        baseline_std = baseline_sbp.std()

        results = {}

        for shift in severity_shifts:
            adjusted_baseline = baseline_mean + shift
            significant_count = 0
            effect_estimates = []

            for _ in range(n_simulations):
                # Simulate with adjusted baseline
                control_week12 = np.random.normal(adjusted_baseline - 2.0, baseline_std, n_per_arm)
                active_week12 = np.random.normal(adjusted_baseline - 2.0 + target_effect, baseline_std, n_per_arm)

                # Run t-test
                t_stat, p_value = stats.ttest_ind(active_week12, control_week12)
                effect_estimate = control_week12.mean() - active_week12.mean()

                if p_value < 0.05:
                    significant_count += 1

                effect_estimates.append(effect_estimate)

            power = significant_count / n_simulations

            severity_label = "milder" if shift < 0 else "more severe" if shift > 0 else "baseline"

            results[f'shift_{shift:+d}mmHg'] = {
                'baseline_sbp_shift': shift,
                'adjusted_baseline_sbp': adjusted_baseline,
                'severity': severity_label,
                'power': power,
                'mean_effect_estimate': np.mean(effect_estimates),
                'effect_estimate_std': np.std(effect_estimates)
            }

        return {
            'scenarios': results,
            'interpretation': self._interpret_patient_mix(results),
            'parameters': {
                'n_per_arm': n_per_arm,
                'target_effect': target_effect,
                'baseline_mean': baseline_mean,
                'n_simulations': n_simulations
            }
        }

    def _recommend_sample_size(self, results: Dict) -> str:
        """Generate sample size recommendation"""
        for scenario_name, metrics in results.items():
            if metrics['power'] >= 0.80:
                return f"Minimum {metrics['n_per_arm']} per arm for 80% power (total N={metrics['total_n']})"
        return "Sample sizes tested insufficient for 80% power. Consider larger trial."

    def _interpret_patient_mix(self, results: Dict) -> str:
        """Interpret patient mix scenario results"""
        interpretations = []
        for scenario_name, metrics in results.items():
            if metrics['power'] >= 0.80:
                interpretations.append(
                    f"{metrics['severity'].capitalize()} patients "
                    f"(baseline SBP {metrics['adjusted_baseline_sbp']:.0f}): "
                    f"{metrics['power']:.1%} power"
                )
        return "\n".join(interpretations) if interpretations else "No scenarios achieved 80% power"


class TrialFeasibilityEstimator:
    """
    Estimate trial feasibility and provide planning recommendations

    Considers:
    - Sample size requirements
    - Expected enrollment rate
    - Dropout compensation
    - Budget constraints
    - Timeline feasibility
    """

    def __init__(self, trial_params: TrialParameters):
        """
        Initialize with trial parameters

        Args:
            trial_params: Trial design parameters
        """
        self.params = trial_params

    def estimate_sample_size_required(
        self,
        baseline_std: float,
        target_effect: float,
        alpha: float = 0.05,
        power: float = 0.80
    ) -> Dict:
        """
        Calculate required sample size for desired power

        Args:
            baseline_std: Standard deviation of primary endpoint
            target_effect: Minimum clinically important difference
            alpha: Significance level (default 0.05)
            power: Desired statistical power (default 0.80)

        Returns:
            Dictionary with sample size requirements
        """
        # Cohen's d effect size
        effect_size = abs(target_effect) / baseline_std

        # Z-scores for alpha and power
        z_alpha = stats.norm.ppf(1 - alpha / 2)  # Two-tailed
        z_beta = stats.norm.ppf(power)

        # Sample size per arm (assuming equal allocation)
        n_per_arm = ((z_alpha + z_beta) ** 2 * 2 * baseline_std ** 2) / (target_effect ** 2)
        n_per_arm = int(np.ceil(n_per_arm))

        # Adjust for dropout
        n_per_arm_adjusted = int(np.ceil(n_per_arm / (1 - self.params.dropout_rate)))

        return {
            'n_per_arm': n_per_arm,
            'n_per_arm_with_dropout': n_per_arm_adjusted,
            'total_n': n_per_arm * 2,
            'total_n_with_dropout': n_per_arm_adjusted * 2,
            'effect_size_cohens_d': effect_size,
            'dropout_rate': self.params.dropout_rate,
            'power': power,
            'alpha': alpha
        }

    def estimate_enrollment_timeline(
        self,
        target_n: int,
        sites: int = 5,
        enrollment_rate_per_site_per_month: float = 3.0
    ) -> Dict:
        """
        Estimate enrollment timeline

        Args:
            target_n: Total subjects needed
            sites: Number of sites
            enrollment_rate_per_site_per_month: Expected enrollment rate

        Returns:
            Dictionary with timeline estimates
        """
        total_enrollment_rate_per_month = sites * enrollment_rate_per_site_per_month
        enrollment_duration_months = target_n / total_enrollment_rate_per_month

        # Add treatment duration
        treatment_duration_months = self.params.treatment_duration_weeks / 4.33
        total_duration_months = enrollment_duration_months + treatment_duration_months

        return {
            'enrollment_duration_months': enrollment_duration_months,
            'treatment_duration_months': treatment_duration_months,
            'total_duration_months': total_duration_months,
            'total_duration_years': total_duration_months / 12,
            'sites': sites,
            'enrollment_rate_per_site_per_month': enrollment_rate_per_site_per_month,
            'total_enrollment_rate': total_enrollment_rate_per_month
        }

    def comprehensive_feasibility_assessment(
        self,
        baseline_data: pd.DataFrame
    ) -> Dict:
        """
        Comprehensive feasibility assessment

        Args:
            baseline_data: Baseline data for parameter estimation

        Returns:
            Comprehensive feasibility report
        """
        # Estimate parameters from baseline data
        baseline_sbp = baseline_data[baseline_data['VisitName'] == 'Screening']['SystolicBP']
        baseline_std = baseline_sbp.std()

        # Calculate sample size
        sample_size_req = self.estimate_sample_size_required(
            baseline_std=baseline_std,
            target_effect=self.params.target_effect,
            alpha=self.params.alpha,
            power=self.params.power
        )

        # Estimate timeline
        timeline = self.estimate_enrollment_timeline(
            target_n=sample_size_req['total_n_with_dropout']
        )

        # Feasibility assessment
        feasible = timeline['total_duration_months'] <= 24  # 2-year threshold
        risk_level = "low" if feasible else "high"

        return {
            'sample_size': sample_size_req,
            'timeline': timeline,
            'feasibility': {
                'feasible': feasible,
                'risk_level': risk_level,
                'recommendation': self._generate_recommendation(sample_size_req, timeline)
            },
            'parameters': {
                'target_effect': self.params.target_effect,
                'baseline_std': baseline_std,
                'power': self.params.power,
                'alpha': self.params.alpha,
                'dropout_rate': self.params.dropout_rate
            }
        }

    def _generate_recommendation(self, sample_size: Dict, timeline: Dict) -> str:
        """Generate feasibility recommendation"""
        if timeline['total_duration_months'] <= 18:
            return "✅ Highly feasible trial design. Recommended to proceed."
        elif timeline['total_duration_months'] <= 24:
            return "✓ Feasible trial design. Consider additional sites to accelerate enrollment."
        elif timeline['total_duration_months'] <= 36:
            return "⚠️ Challenging timeline. Consider increasing sites or reducing sample size if clinically acceptable."
        else:
            return "❌ High-risk timeline. Strongly recommend redesigning trial or using adaptive design."


# ============================================================================
# Convenience Functions
# ============================================================================

def generate_virtual_control_arm(
    n_subjects: int = 50,
    real_control_data: Optional[pd.DataFrame] = None,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Convenience function to generate virtual control arm

    Args:
        n_subjects: Number of virtual subjects
        real_control_data: Optional real data to match characteristics
        seed: Random seed

    Returns:
        DataFrame with virtual control arm data
    """
    generator = VirtualControlArmGenerator(real_control_data)
    if real_control_data is not None:
        generator.fit(real_control_data)

    return generator.generate_virtual_control_arm(n_subjects=n_subjects, seed=seed)


def run_what_if_enrollment_analysis(
    baseline_data: pd.DataFrame,
    enrollment_sizes: List[int] = None,
    target_effect: float = -5.0,
    seed: Optional[int] = None
) -> Dict:
    """
    Convenience function for enrollment what-if analysis

    Args:
        baseline_data: Baseline trial data
        enrollment_sizes: List of sample sizes to test
        target_effect: Expected treatment effect
        seed: Random seed

    Returns:
        What-if analysis results
    """
    simulator = WhatIfScenarioSimulator(baseline_data)
    return simulator.simulate_enrollment_scenarios(
        enrollment_sizes=enrollment_sizes,
        target_effect=target_effect,
        seed=seed
    )


def estimate_trial_feasibility(
    baseline_data: pd.DataFrame,
    target_effect: float = -5.0,
    power: float = 0.80,
    dropout_rate: float = 0.10
) -> Dict:
    """
    Convenience function for trial feasibility estimation

    Args:
        baseline_data: Baseline trial data
        target_effect: Expected treatment effect
        power: Desired statistical power
        dropout_rate: Expected dropout rate

    Returns:
        Feasibility assessment
    """
    params = TrialParameters(
        target_effect=target_effect,
        power=power,
        dropout_rate=dropout_rate
    )

    estimator = TrialFeasibilityEstimator(params)
    return estimator.comprehensive_feasibility_assessment(baseline_data)
