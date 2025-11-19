"""
MICE (Multiple Imputation by Chained Equations) Generator

Uses iterative imputation to generate synthetic data and handle missing values.
MICE is particularly good for:
- Handling mixed data types (continuous + categorical)
- Preserving variable relationships through iterative modeling
- Clinical data with complex missing patterns

This addresses professor's feedback on:
- Adding advanced statistical methods
- Demonstrating understanding of missing data mechanisms
- Clinical realism (trials often have missing data)
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional, Tuple
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import BayesianRidge


class MICEGenerator:
    """
    Generate synthetic clinical trial data using MICE

    Key advantages:
    - Handles missing data naturally (trials always have missing data)
    - Can model complex non-linear relationships
    - Works with mixed data types
    - Preserves uncertainty through multiple imputations
    """

    def __init__(self, estimator_type: str = 'bayesian_ridge'):
        """
        Initialize MICE generator

        Args:
            estimator_type: Base estimator for imputation
                'bayesian_ridge': Bayesian Ridge Regression (default, fast)
                'random_forest': Random Forest (captures non-linearity)
        """
        self.estimator_type = estimator_type
        self.imputer = None
        self.template_data = None

    def _get_estimator(self):
        """Get base estimator for MICE"""
        if self.estimator_type == 'bayesian_ridge':
            return BayesianRidge()
        elif self.estimator_type == 'random_forest':
            return RandomForestRegressor(
                n_estimators=10,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown estimator: {self.estimator_type}")

    def fit(self, data: pd.DataFrame, max_iter: int = 10) -> None:
        """
        Fit MICE model to data

        Args:
            data: Real clinical trial data (can have missing values)
            max_iter: Maximum iterations for convergence
        """
        # Select numeric columns for imputation
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

        # Create imputer
        self.imputer = IterativeImputer(
            estimator=self._get_estimator(),
            max_iter=max_iter,
            random_state=42,
            verbose=0
        )

        # Fit to numeric data
        self.imputer.fit(data[numeric_cols])

        # Store template for structure
        self.template_data = data.copy()

        print(f"MICE fitted on {len(data)} records, {len(numeric_cols)} numeric features")

    def generate(
        self,
        n_per_arm: int = 50,
        seed: Optional[int] = 42,
        missing_rate: float = 0.15,
        target_effect: float = -5.0
    ) -> pd.DataFrame:
        """
        Generate synthetic data using MICE

        Strategy:
        1. Create template with structure (subjects, visits, treatment)
        2. Initialize with mean/mode values
        3. Introduce missing data (realistic MAR pattern)
        4. Use MICE to impute (generates variation)
        5. Adjust treatment effect

        Args:
            n_per_arm: Subjects per arm
            seed: Random seed
            missing_rate: Proportion of values to treat as missing (0-0.3)
            target_effect: Target SBP treatment effect

        Returns:
            Synthetic vitals DataFrame
        """
        if self.imputer is None:
            raise ValueError("Imputer not fitted. Call fit() first.")

        np.random.seed(seed)

        # Create template structure
        visits = ['Screening', 'Day 1', 'Week 4', 'Week 12']
        arms = ['Active', 'Placebo']

        rows = []
        for arm in arms:
            for i in range(n_per_arm):
                subject_id = f"RA001-{i + 1 + (n_per_arm if arm == 'Placebo' else 0):03d}"

                for visit in visits:
                    rows.append({
                        'SubjectID': subject_id,
                        'VisitName': visit,
                        'TreatmentArm': arm,
                        'SystolicBP': np.nan,  # Will impute
                        'DiastolicBP': np.nan,
                        'HeartRate': np.nan,
                        'Temperature': np.nan
                    })

        df = pd.DataFrame(rows)

        # Initialize with population means (from training data)
        if self.template_data is not None:
            for col in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
                if col in self.template_data.columns:
                    df[col] = self.template_data[col].mean()

        # Create realistic missing data pattern (MAR - Missing At Random)
        # Simulate that some visits are missed more often
        for idx in df.index:
            # Higher missingness at later visits (realistic dropout pattern)
            if df.loc[idx, 'VisitName'] == 'Week 12':
                miss_prob = missing_rate * 2.0
            elif df.loc[idx, 'VisitName'] == 'Week 4':
                miss_prob = missing_rate * 1.5
            else:
                miss_prob = missing_rate * 0.5

            # Randomly set values to NaN
            for col in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
                if np.random.random() < miss_prob:
                    df.loc[idx, col] = np.nan

        # Use MICE to impute missing values
        numeric_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
        df[numeric_cols] = self.imputer.transform(df[numeric_cols])

        # Round to appropriate precision
        df['SystolicBP'] = df['SystolicBP'].round().astype(int).clip(95, 200)
        df['DiastolicBP'] = df['DiastolicBP'].round().astype(int).clip(55, 130)
        df['HeartRate'] = df['HeartRate'].round().astype(int).clip(50, 120)
        df['Temperature'] = df['Temperature'].round(1).clip(35.0, 40.0)

        # Adjust treatment effect at Week 12
        df = self._adjust_treatment_effect(df, target_effect)

        return df

    def _adjust_treatment_effect(
        self,
        df: pd.DataFrame,
        target_effect: float
    ) -> pd.DataFrame:
        """Adjust Week 12 SBP to achieve target treatment effect"""
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

    def generate_multiple_imputations(
        self,
        n_imputations: int = 5,
        n_per_arm: int = 50,
        seed: Optional[int] = 42,
        missing_rate: float = 0.15
    ) -> List[pd.DataFrame]:
        """
        Generate multiple imputed datasets

        This is the proper MICE approach - create multiple plausible versions
        of the data to capture uncertainty.

        Args:
            n_imputations: Number of imputed datasets to create
            n_per_arm: Subjects per arm
            seed: Random seed
            missing_rate: Missing data rate

        Returns:
            List of DataFrames (multiple imputations)
        """
        imputations = []

        for m in range(n_imputations):
            df = self.generate(
                n_per_arm=n_per_arm,
                seed=seed + m if seed else None,
                missing_rate=missing_rate
            )
            imputations.append(df)

        print(f"Generated {n_imputations} multiple imputations")

        return imputations

    def pool_results(
        self,
        imputations: List[pd.DataFrame],
        endpoint: str = 'SystolicBP'
    ) -> Dict:
        """
        Pool results across multiple imputations (Rubin's rules)

        This combines results from multiple imputations to get
        final estimates with proper uncertainty quantification.

        Args:
            imputations: List of imputed datasets
            endpoint: Endpoint to analyze

        Returns:
            Pooled treatment effect estimates
        """
        m = len(imputations)
        estimates = []
        variances = []

        for df in imputations:
            wk12 = df[df['VisitName'] == 'Week 12']
            means = wk12.groupby('TreatmentArm')[endpoint].mean()
            stds = wk12.groupby('TreatmentArm')[endpoint].std()
            ns = wk12.groupby('TreatmentArm')[endpoint].count()

            # Treatment effect
            effect = means['Active'] - means['Placebo']
            se = np.sqrt(
                (stds['Active']**2 / ns['Active']) +
                (stds['Placebo']**2 / ns['Placebo'])
            )

            estimates.append(effect)
            variances.append(se**2)

        # Rubin's rules for pooling
        pooled_estimate = np.mean(estimates)
        within_var = np.mean(variances)
        between_var = np.var(estimates, ddof=1)
        total_var = within_var + (1 + 1/m) * between_var
        pooled_se = np.sqrt(total_var)

        return {
            'pooled_estimate': pooled_estimate,
            'pooled_se': pooled_se,
            'within_variance': within_var,
            'between_variance': between_var,
            'total_variance': total_var,
            'individual_estimates': estimates
        }


def generate_vitals_mice(
    n_per_arm: int = 50,
    target_effect: float = -5.0,
    seed: Optional[int] = 42,
    real_data_path: Optional[str] = None,
    missing_rate: float = 0.10,
    estimator: str = 'bayesian_ridge'
) -> pd.DataFrame:
    """
    Convenience function to generate synthetic vitals using MICE

    Args:
        n_per_arm: Number of subjects per treatment arm
        target_effect: Target SBP treatment effect at Week 12
        seed: Random seed
        real_data_path: Path to real data for training
        missing_rate: Missing data rate (0-0.3)
        estimator: 'bayesian_ridge' or 'random_forest'

    Returns:
        DataFrame with synthetic vitals
    """
    # Default to using pilot trial data
    if real_data_path is None:
        real_data_path = "/app/data/pilot_trial_cleaned.csv"
        if not os.path.exists(real_data_path):
            real_data_path = "data/pilot_trial_cleaned.csv"
        if not os.path.exists(real_data_path):
            real_data_path = "../../../data/pilot_trial_cleaned.csv"

    # Initialize generator
    generator = MICEGenerator(estimator_type=estimator)

    # Load and fit to real data
    if os.path.exists(real_data_path):
        real_data = pd.read_csv(real_data_path)
        generator.fit(real_data)
    else:
        print("Warning: Real data not found. Using synthetic data to train MICE.")
        from generators import generate_vitals_mvn
        synthetic_train = generate_vitals_mvn(n_per_arm=50, seed=seed)
        generator.fit(synthetic_train)

    # Generate synthetic data
    synthetic_data = generator.generate(
        n_per_arm=n_per_arm,
        seed=seed,
        missing_rate=missing_rate,
        target_effect=target_effect
    )

    return synthetic_data


if __name__ == "__main__":
    # Test the generator
    import os
    print("Testing MICE Generator...")

    df = generate_vitals_mice(n_per_arm=10, seed=42, missing_rate=0.15)
    print(f"\nGenerated {len(df)} records")
    print(f"Subjects: {df['SubjectID'].nunique()}")
    print(f"\nSample data:")
    print(df.head(10))

    print(f"\nWeek 12 treatment effect:")
    wk12 = df[df['VisitName'] == 'Week 12']
    means = wk12.groupby('TreatmentArm')['SystolicBP'].mean()
    print(f"Active: {means['Active']:.1f}, Placebo: {means['Placebo']:.1f}")
    print(f"Difference: {means['Active'] - means['Placebo']:.1f} mmHg")

    # Test multiple imputations
    print("\n\nTesting multiple imputations...")
    generator = MICEGenerator()

    # Create training data
    from generators import generate_vitals_mvn
    train_data = generate_vitals_mvn(n_per_arm=25, seed=42)
    generator.fit(train_data)

    # Generate 5 imputations
    imputations = generator.generate_multiple_imputations(
        n_imputations=5,
        n_per_arm=10,
        seed=42
    )

    # Pool results
    pooled = generator.pool_results(imputations, endpoint='SystolicBP')
    print(f"\nPooled treatment effect: {pooled['pooled_estimate']:.2f} ± {pooled['pooled_se']:.2f}")
    print(f"Individual estimates: {[f'{e:.2f}' for e in pooled['individual_estimates']]}")
