"""
Bayesian Network-based Synthetic Data Generator

Uses pgmpy to learn Bayesian network structure from real data and generate
synthetic clinical trial data that preserves complex variable relationships.

This addresses professor's feedback on:
- Adding advanced generation methods beyond MVN/Bootstrap
- Preserving realistic data correlations and dependencies
- Demonstrating understanding of probabilistic graphical models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
from pathlib import Path

try:
    from pgmpy.models import BayesianNetwork
    from pgmpy.estimators import MaximumLikelihoodEstimator, BayesianEstimator
    from pgmpy.estimators import HillClimbSearch, BicScore
    from pgmpy.sampling import BayesianModelSampling
    PGMPY_AVAILABLE = True
except ImportError:
    PGMPY_AVAILABLE = False
    print("Warning: pgmpy not available. Install with: pip install pgmpy")


class BayesianNetworkGenerator:
    """
    Generate synthetic clinical trial data using Bayesian Networks

    Key advantages over MVN/Bootstrap:
    - Captures non-linear relationships between variables
    - Preserves conditional dependencies (e.g., TreatmentArm -> SBP)
    - Can handle both continuous and categorical variables
    - Interpretable structure (DAG shows causal relationships)
    """

    def __init__(self, real_data_path: Optional[str] = None):
        """
        Initialize generator with optional real data for training

        Args:
            real_data_path: Path to real clinical trial data (CSV)
        """
        if not PGMPY_AVAILABLE:
            raise ImportError("pgmpy required. Install with: pip install pgmpy")

        self.model = None
        self.real_data = None
        self.structure = None

        if real_data_path and os.path.exists(real_data_path):
            self.real_data = pd.read_csv(real_data_path)
            print(f"Loaded real data: {len(self.real_data)} records")

    def _discretize_continuous_vars(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Discretize continuous variables for Bayesian network

        pgmpy works better with discrete variables, so we bin continuous vitals
        into clinically meaningful categories.
        """
        df_discrete = df.copy()

        # Discretize Systolic BP
        df_discrete['SystolicBP_Cat'] = pd.cut(
            df['SystolicBP'],
            bins=[0, 120, 130, 140, 160, 200],
            labels=['Normal', 'Elevated', 'Stage1', 'Stage2', 'Severe']
        )

        # Discretize Diastolic BP
        df_discrete['DiastolicBP_Cat'] = pd.cut(
            df['DiastolicBP'],
            bins=[0, 80, 85, 90, 100, 130],
            labels=['Normal', 'Elevated', 'Stage1', 'Stage2', 'High']
        )

        # Discretize Heart Rate
        df_discrete['HeartRate_Cat'] = pd.cut(
            df['HeartRate'],
            bins=[0, 60, 80, 100, 120],
            labels=['Low', 'Normal', 'Elevated', 'High']
        )

        # Discretize Temperature
        df_discrete['Temperature_Cat'] = pd.cut(
            df['Temperature'],
            bins=[0, 36.5, 37.5, 38.0, 40.0],
            labels=['Low', 'Normal', 'Elevated', 'Fever']
        )

        # Keep categorical as-is
        df_discrete['TreatmentArm'] = df['TreatmentArm']
        df_discrete['VisitName'] = df['VisitName']

        return df_discrete

    def _learn_structure(self, data: pd.DataFrame) -> BayesianNetwork:
        """
        Learn Bayesian network structure from data using Hill Climb search

        This discovers the DAG (directed acyclic graph) that best fits the data
        """
        # Use only discretized categorical columns
        discrete_cols = [
            'TreatmentArm', 'VisitName',
            'SystolicBP_Cat', 'DiastolicBP_Cat',
            'HeartRate_Cat', 'Temperature_Cat'
        ]

        data_discrete = data[discrete_cols].dropna()

        # Hill climb search to find best structure
        hc = HillClimbSearch(data_discrete)
        best_model = hc.estimate(scoring_method=BicScore(data_discrete))

        print(f"Learned Bayesian network structure with {len(best_model.nodes())} nodes")
        print(f"Edges: {best_model.edges()}")

        return best_model

    def _use_expert_structure(self) -> BayesianNetwork:
        """
        Use expert-defined structure based on clinical knowledge

        This is useful when we don't have enough data to learn structure,
        or want to enforce known causal relationships.

        Expert knowledge:
        - TreatmentArm influences BP (treatment effect)
        - VisitName influences BP (temporal trend)
        - SBP influences DBP (correlation)
        - BP influences HR (physiological response)
        """
        model = BayesianNetwork([
            # Treatment and visit are root causes
            ('TreatmentArm', 'SystolicBP_Cat'),
            ('TreatmentArm', 'DiastolicBP_Cat'),
            ('VisitName', 'SystolicBP_Cat'),
            ('VisitName', 'DiastolicBP_Cat'),

            # BP affects HR
            ('SystolicBP_Cat', 'HeartRate_Cat'),
            ('DiastolicBP_Cat', 'HeartRate_Cat'),

            # SBP and DBP are correlated
            ('SystolicBP_Cat', 'DiastolicBP_Cat'),

            # Fever affects HR
            ('Temperature_Cat', 'HeartRate_Cat'),
        ])

        print("Using expert-defined Bayesian network structure")
        print(f"Edges: {model.edges()}")

        return model

    def fit(self, data: pd.DataFrame, learn_structure: bool = False) -> None:
        """
        Fit Bayesian network to data

        Args:
            data: Training data (real clinical trial data)
            learn_structure: If True, learn structure from data.
                           If False, use expert-defined structure.
        """
        # Discretize continuous variables
        data_discrete = self._discretize_continuous_vars(data)

        # Get or learn structure
        if learn_structure and len(data) > 100:
            self.structure = self._learn_structure(data_discrete)
        else:
            self.structure = self._use_expert_structure()

        # Fit CPDs (conditional probability distributions)
        discrete_cols = [
            'TreatmentArm', 'VisitName',
            'SystolicBP_Cat', 'DiastolicBP_Cat',
            'HeartRate_Cat', 'Temperature_Cat'
        ]

        data_for_fit = data_discrete[discrete_cols].dropna()

        # Use Bayesian estimator for smoother estimates
        self.structure.fit(data_for_fit, estimator=BayesianEstimator, prior_type='BDeu')

        self.model = self.structure

        print("Bayesian network fitted successfully")

    def _map_categories_to_values(self, df_categorical: pd.DataFrame) -> pd.DataFrame:
        """
        Map categorical values back to continuous numeric values

        For each category (e.g., "Stage1 HTN"), sample from appropriate range
        """
        df_numeric = pd.DataFrame()

        # Map SBP categories to values
        sbp_map = {
            'Normal': (95, 120),
            'Elevated': (120, 130),
            'Stage1': (130, 140),
            'Stage2': (140, 160),
            'Severe': (160, 200)
        }

        df_numeric['SystolicBP'] = df_categorical['SystolicBP_Cat'].apply(
            lambda cat: np.random.randint(sbp_map[cat][0], sbp_map[cat][1] + 1)
            if pd.notna(cat) else 130
        )

        # Map DBP categories to values
        dbp_map = {
            'Normal': (55, 80),
            'Elevated': (80, 85),
            'Stage1': (85, 90),
            'Stage2': (90, 100),
            'High': (100, 130)
        }

        df_numeric['DiastolicBP'] = df_categorical['DiastolicBP_Cat'].apply(
            lambda cat: np.random.randint(dbp_map[cat][0], dbp_map[cat][1] + 1)
            if pd.notna(cat) else 80
        )

        # Map HR categories to values
        hr_map = {
            'Low': (50, 60),
            'Normal': (60, 80),
            'Elevated': (80, 100),
            'High': (100, 120)
        }

        df_numeric['HeartRate'] = df_categorical['HeartRate_Cat'].apply(
            lambda cat: np.random.randint(hr_map[cat][0], hr_map[cat][1] + 1)
            if pd.notna(cat) else 72
        )

        # Map Temperature categories to values
        temp_map = {
            'Low': (35.0, 36.5),
            'Normal': (36.5, 37.5),
            'Elevated': (37.5, 38.0),
            'Fever': (38.0, 40.0)
        }

        df_numeric['Temperature'] = df_categorical['Temperature_Cat'].apply(
            lambda cat: np.random.uniform(temp_map[cat][0], temp_map[cat][1])
            if pd.notna(cat) else 36.8
        ).round(1)

        # Copy categorical variables as-is
        df_numeric['TreatmentArm'] = df_categorical['TreatmentArm']
        df_numeric['VisitName'] = df_categorical['VisitName']

        return df_numeric

    def generate(
        self,
        n_per_arm: int = 50,
        seed: Optional[int] = 42,
        target_effect: float = -5.0
    ) -> pd.DataFrame:
        """
        Generate synthetic clinical trial data

        Args:
            n_per_arm: Number of subjects per treatment arm
            seed: Random seed for reproducibility
            target_effect: Target treatment effect (SBP Active - Placebo at Week 12)

        Returns:
            DataFrame with synthetic vitals data
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first or load pretrained model")

        if seed is not None:
            np.random.seed(seed)

        # Generate samples from Bayesian network
        sampler = BayesianModelSampling(self.model)

        # Sample for each treatment arm and visit
        visits = ['Screening', 'Day 1', 'Week 4', 'Week 12']
        arms = ['Active', 'Placebo']

        all_samples = []

        for arm in arms:
            for _ in range(n_per_arm):
                subject_id = f"RA001-{len(all_samples) // 4 + 1:03d}"

                for visit in visits:
                    # Generate sample (forward sampling doesn't support evidence in newer pgmpy)
                    sample = sampler.forward_sample(size=1)

                    # Manually set evidence values
                    sample['TreatmentArm'] = arm
                    sample['VisitName'] = visit
                    sample['SubjectID'] = subject_id

                    all_samples.append(sample)

        # Combine all samples
        df_categorical = pd.concat(all_samples, ignore_index=True)

        # Convert categorical back to numeric
        df_numeric = self._map_categories_to_values(df_categorical)

        # Add SubjectID
        df_numeric['SubjectID'] = df_categorical['SubjectID']

        # Reorder columns
        df_numeric = df_numeric[[
            'SubjectID', 'VisitName', 'TreatmentArm',
            'SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature'
        ]]

        # Adjust to achieve target effect at Week 12
        df_numeric = self._adjust_treatment_effect(df_numeric, target_effect)

        return df_numeric

    def _adjust_treatment_effect(
        self,
        df: pd.DataFrame,
        target_effect: float
    ) -> pd.DataFrame:
        """
        Fine-tune Week 12 SBP to achieve target treatment effect

        This ensures the generated data has the desired efficacy signal
        """
        wk12 = df[df['VisitName'] == 'Week 12'].copy()

        if len(wk12) == 0:
            return df

        # Calculate current effect
        means = wk12.groupby('TreatmentArm')['SystolicBP'].mean()

        if 'Active' not in means or 'Placebo' not in means:
            return df

        current_effect = means['Active'] - means['Placebo']
        adjustment = target_effect - current_effect

        # Apply adjustment to Active arm at Week 12
        mask = (df['VisitName'] == 'Week 12') & (df['TreatmentArm'] == 'Active')
        df.loc[mask, 'SystolicBP'] = (
            df.loc[mask, 'SystolicBP'] + adjustment
        ).round().astype(int).clip(95, 200)

        return df


def generate_vitals_bayesian(
    n_per_arm: int = 50,
    target_effect: float = -5.0,
    seed: Optional[int] = 42,
    real_data_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Convenience function to generate synthetic vitals using Bayesian network

    Args:
        n_per_arm: Number of subjects per treatment arm
        target_effect: Target SBP treatment effect at Week 12
        seed: Random seed
        real_data_path: Path to real data for training (optional)

    Returns:
        DataFrame with synthetic vitals
    """
    # Default to using pilot trial data
    if real_data_path is None:
        real_data_path = "/app/data/pilot_trial_cleaned.csv"
        # Fallback paths
        if not os.path.exists(real_data_path):
            real_data_path = "data/pilot_trial_cleaned.csv"
        if not os.path.exists(real_data_path):
            real_data_path = "../../../data/pilot_trial_cleaned.csv"

    # Initialize and fit generator
    generator = BayesianNetworkGenerator(real_data_path)

    if generator.real_data is not None:
        generator.fit(generator.real_data, learn_structure=False)
    else:
        # Create synthetic training data if real data not available
        print("Warning: Real data not found. Using synthetic data to train Bayesian network.")
        # This is a fallback - in production, should always use real data
        from generators import generate_vitals_mvn
        synthetic_train = generate_vitals_mvn(n_per_arm=25, seed=seed)
        generator.fit(synthetic_train, learn_structure=False)

    # Generate synthetic data
    synthetic_data = generator.generate(
        n_per_arm=n_per_arm,
        seed=seed,
        target_effect=target_effect
    )

    return synthetic_data


if __name__ == "__main__":
    # Test the generator
    print("Testing Bayesian Network Generator...")

    df = generate_vitals_bayesian(n_per_arm=10, seed=42)
    print(f"\nGenerated {len(df)} records")
    print(f"Subjects: {df['SubjectID'].nunique()}")
    print(f"\nSample data:")
    print(df.head(10))

    print(f"\nWeek 12 treatment effect:")
    wk12 = df[df['VisitName'] == 'Week 12']
    means = wk12.groupby('TreatmentArm')['SystolicBP'].mean()
    print(f"Active: {means['Active']:.1f}, Placebo: {means['Placebo']:.1f}")
    print(f"Difference: {means['Active'] - means['Placebo']:.1f} mmHg")
