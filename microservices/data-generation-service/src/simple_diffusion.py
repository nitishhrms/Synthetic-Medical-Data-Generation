"""
Lightweight Diffusion-Style Generator for Synthetic Clinical Trial Data

This module implements a simplified diffusion-inspired approach for generating
synthetic vitals data without requiring deep learning frameworks. It uses
statistical methods with iterative refinement similar to diffusion processes.

Key Idea:
- Start with random noise
- Iteratively refine through multiple steps
- Learn from real data distribution
- Add realistic correlations and constraints

This is a lightweight alternative to full DDPM that works well for tabular data.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple
from pathlib import Path


class SimpleDiffusionGenerator:
    """
    Lightweight diffusion-style generator using statistical methods

    Instead of neural networks, this uses:
    - Multivariate statistics from real data
    - Iterative refinement with noise annealing
    - Correlation-preserving transformations
    - Constraint enforcement at each step
    """

    def __init__(self, training_data: pd.DataFrame):
        """
        Initialize generator with training data

        Args:
            training_data: DataFrame with real vitals records
        """
        self.training_data = training_data

        # Define column types
        self.numerical_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
        self.categorical_cols = ['VisitName', 'TreatmentArm']

        # Learn statistical properties from training data
        self._learn_statistics()

    def _learn_statistics(self):
        """Learn statistical properties from training data"""
        # Numerical data statistics
        self.means = {}
        self.stds = {}
        self.correlations = {}

        for col in self.numerical_cols:
            self.means[col] = self.training_data[col].mean()
            self.stds[col] = self.training_data[col].std()

        # Compute correlation matrix
        numerical_data = self.training_data[self.numerical_cols].values
        self.correlation_matrix = np.corrcoef(numerical_data.T)

        # Compute Cholesky decomposition for multivariate sampling
        try:
            self.cholesky = np.linalg.cholesky(self.correlation_matrix)
        except np.linalg.LinAlgError:
            # If matrix is not positive definite, use eigenvalue regularization
            eigenvalues, eigenvectors = np.linalg.eigh(self.correlation_matrix)
            eigenvalues = np.maximum(eigenvalues, 1e-6)  # Ensure positive
            self.correlation_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
            self.cholesky = np.linalg.cholesky(self.correlation_matrix)

        # Learn conditional distributions (visit-specific and treatment-specific)
        self.conditional_stats = {}

        for visit in self.training_data['VisitName'].unique():
            for arm in self.training_data['TreatmentArm'].unique():
                key = (visit, arm)
                subset = self.training_data[
                    (self.training_data['VisitName'] == visit) &
                    (self.training_data['TreatmentArm'] == arm)
                ]

                if len(subset) > 0:
                    self.conditional_stats[key] = {
                        'means': {col: subset[col].mean() for col in self.numerical_cols},
                        'stds': {col: subset[col].std() for col in self.numerical_cols},
                        'count': len(subset)
                    }

        # Learn categorical distributions
        self.visit_probs = (self.training_data['VisitName'].value_counts(normalize=True)
                           .to_dict())
        self.treatment_probs = (self.training_data['TreatmentArm'].value_counts(normalize=True)
                               .to_dict())

    def _generate_noise(self, n_samples: int, seed: Optional[int] = None) -> np.ndarray:
        """
        Generate initial noise following data distribution

        Args:
            n_samples: Number of samples
            seed: Random seed

        Returns:
            Initial noise array [n_samples, n_features]
        """
        if seed is not None:
            np.random.seed(seed)

        # Generate correlated Gaussian noise
        uncorrelated_noise = np.random.randn(n_samples, len(self.numerical_cols))
        correlated_noise = uncorrelated_noise @ self.cholesky.T

        # Scale by standard deviations and shift by means
        noise = np.zeros((n_samples, len(self.numerical_cols)))
        for i, col in enumerate(self.numerical_cols):
            noise[:, i] = correlated_noise[:, i] * self.stds[col] + self.means[col]

        return noise

    def _refine_step(self, data: np.ndarray, step: int, total_steps: int,
                     visit_names: List[str], treatment_arms: List[str]) -> np.ndarray:
        """
        Single refinement step (similar to reverse diffusion)

        Args:
            data: Current data [n_samples, n_features]
            step: Current step number
            total_steps: Total number of steps
            visit_names: Visit names for each sample
            treatment_arms: Treatment arms for each sample

        Returns:
            Refined data
        """
        # Compute noise level (annealing schedule)
        noise_level = (total_steps - step) / total_steps

        refined = data.copy()

        # Apply conditional refinement based on visit and treatment
        for i in range(len(data)):
            visit = visit_names[i]
            arm = treatment_arms[i]
            key = (visit, arm)

            if key in self.conditional_stats:
                stats = self.conditional_stats[key]

                # Move towards conditional mean with decreasing noise
                for j, col in enumerate(self.numerical_cols):
                    target_mean = stats['means'][col]
                    target_std = stats['stds'][col]

                    # Blend between current value and target
                    blend_factor = 1.0 - noise_level
                    noise_factor = noise_level * 0.5  # Reduce noise over time

                    refined[i, j] = (
                        blend_factor * target_mean +
                        (1 - blend_factor) * refined[i, j] +
                        noise_factor * np.random.randn() * target_std
                    )

        return refined

    def _enforce_constraints(self, data: np.ndarray) -> np.ndarray:
        """
        Enforce physiological constraints

        Args:
            data: Data array [n_samples, n_features]

        Returns:
            Constrained data
        """
        constrained = data.copy()

        # Clip to valid ranges
        constraints = {
            0: (95, 200),    # SystolicBP
            1: (55, 130),    # DiastolicBP
            2: (50, 120),    # HeartRate
            3: (35.0, 40.0)  # Temperature
        }

        for idx, (min_val, max_val) in constraints.items():
            constrained[:, idx] = np.clip(constrained[:, idx], min_val, max_val)

        # Ensure SBP > DBP
        for i in range(len(constrained)):
            if constrained[i, 0] <= constrained[i, 1]:  # SBP <= DBP
                # Adjust to maintain valid relationship
                mean_bp = (constrained[i, 0] + constrained[i, 1]) / 2
                constrained[i, 0] = mean_bp + 10  # SBP higher
                constrained[i, 1] = mean_bp - 10  # DBP lower

                # Re-clip
                constrained[i, 0] = np.clip(constrained[i, 0], 95, 200)
                constrained[i, 1] = np.clip(constrained[i, 1], 55, 130)

        return constrained

    def generate(self, n_samples: int, n_steps: int = 50,
                 seed: Optional[int] = None) -> pd.DataFrame:
        """
        Generate synthetic vitals data using diffusion-inspired refinement

        Args:
            n_samples: Number of samples to generate
            n_steps: Number of refinement steps
            seed: Random seed for reproducibility

        Returns:
            DataFrame with synthetic vitals records
        """
        if seed is not None:
            np.random.seed(seed)

        # Sample categorical variables
        visit_names = np.random.choice(
            list(self.visit_probs.keys()),
            size=n_samples,
            p=list(self.visit_probs.values())
        )

        treatment_arms = np.random.choice(
            list(self.treatment_probs.keys()),
            size=n_samples,
            p=list(self.treatment_probs.values())
        )

        # Generate initial noise
        data = self._generate_noise(n_samples, seed)

        # Iterative refinement (diffusion reverse process)
        for step in range(n_steps):
            data = self._refine_step(data, step, n_steps, visit_names, treatment_arms)

            # Enforce constraints at each step
            data = self._enforce_constraints(data)

        # Create DataFrame
        result = pd.DataFrame(data, columns=self.numerical_cols)
        result['VisitName'] = visit_names
        result['TreatmentArm'] = treatment_arms
        result['SubjectID'] = [f"DIFF{i:04d}" for i in range(n_samples)]

        # Round numerical values
        result['SystolicBP'] = result['SystolicBP'].round().astype(int)
        result['DiastolicBP'] = result['DiastolicBP'].round().astype(int)
        result['HeartRate'] = result['HeartRate'].round().astype(int)
        result['Temperature'] = result['Temperature'].round(1)

        return result


def load_and_train_simple_diffusion(data_path: str) -> SimpleDiffusionGenerator:
    """
    Load training data and create diffusion generator

    Args:
        data_path: Path to pilot data CSV

    Returns:
        Trained SimpleDiffusionGenerator
    """
    df = pd.read_csv(data_path)
    return SimpleDiffusionGenerator(df)


def generate_with_simple_diffusion(
    data_path: str,
    n_per_arm: int = 50,
    n_steps: int = 50,
    target_effect: float = -5.0,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic data using simple diffusion approach

    Args:
        data_path: Path to pilot data CSV
        n_per_arm: Number of subjects per treatment arm
        n_steps: Number of diffusion refinement steps
        target_effect: Target treatment effect (for SBP reduction)
        seed: Random seed

    Returns:
        DataFrame with synthetic vitals data
    """
    # Load generator
    generator = load_and_train_simple_diffusion(data_path)

    # Generate samples (4 visits per subject)
    n_samples = n_per_arm * 2 * 4  # 2 arms, 4 visits
    df = generator.generate(n_samples, n_steps=n_steps, seed=seed)

    # Organize by subject
    # Assign subjects to visits
    visits = ['Screening', 'Day 1', 'Week 4', 'Week 12']

    result_records = []
    for arm_idx, arm in enumerate(['Active', 'Placebo']):
        for subj_idx in range(n_per_arm):
            subject_id = f"DIFF{arm_idx*n_per_arm + subj_idx + 1:04d}"

            for visit in visits:
                # Sample from generated data
                mask = (df['TreatmentArm'] == arm) & (df['VisitName'] == visit)
                available = df[mask]

                if len(available) > 0:
                    record = available.sample(1, random_state=seed).iloc[0].to_dict()
                else:
                    # Fallback: sample any record and override
                    record = df.sample(1, random_state=seed).iloc[0].to_dict()
                    record['TreatmentArm'] = arm
                    record['VisitName'] = visit

                record['SubjectID'] = subject_id

                # Apply treatment effect for Active arm at Week 12
                if arm == 'Active' and visit == 'Week 12':
                    record['SystolicBP'] = max(95, min(200,
                        int(record['SystolicBP'] + target_effect)))

                result_records.append(record)

    return pd.DataFrame(result_records)


if __name__ == "__main__":
    # Test the generator
    import sys

    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = "../../data/pilot_trial_cleaned.csv"

    print("Loading data and training generator...")
    generator = load_and_train_simple_diffusion(data_path)

    print("Generating synthetic data...")
    synthetic_data = generator.generate(400, n_steps=50, seed=42)

    print(f"\nGenerated {len(synthetic_data)} records")
    print("\nSample records:")
    print(synthetic_data.head(10))

    print("\nStatistics:")
    print(synthetic_data[['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']].describe())
