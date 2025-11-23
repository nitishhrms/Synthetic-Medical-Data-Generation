"""
Missingness Mechanisms Module
==============================

Fixes Critical Issue #3: Naive missing data (MCAR only)

Problem:
    Current implementation uses Missing Completely At Random (MCAR):
    - Dropout is random, unrelated to patient characteristics
    - Real trials have MAR (related to observed data) and MNAR (unobserved confounders)
    - This makes imputation methods artificially succeed
    - Selection bias is completely ignored

Solution:
    Implement realistic missingness mechanisms:
    - MAR: Dropout correlates with observed vitals, AEs, demographics
    - MNAR: Dropout correlates with unobserved "frailty" factor
    - Differential dropout by treatment arm

Impact:
    - Missing data patterns match real trials
    - Imputation methods face realistic challenges
    - Selection bias is properly modeled
    - Data suitable for causal inference

Author: Based on expert ML research assessment  
Date: 2025-11-22
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple, List


class MissingnessGenerator:
    """
    Generate realistic missing data patterns for clinical trials
    
    Implements three mechanisms:
    - MCAR: Random dropout (baseline, unrealistic)
    - MAR: Dropout depends on OBSERVED data (realistic)
    - MNAR: Dropout depends on UNOBSERVED factors (most realistic)
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
    
    def apply_mcar_dropout(
        self,
        n_subjects: int,
        dropout_rate: float
    ) -> np.ndarray:
        """
        Missing Completely At Random (MCAR) - UNREALISTIC
        
        Everyone has same probability of dropout regardless of characteristics.
        This is what most synthetic data generators use (WRONG!)
        
        Args:
            n_subjects: Number of subjects
            dropout_rate: Overall dropout probability
            
        Returns:
            Boolean array: True = dropped out
        """
        return np.random.random(n_subjects) < dropout_rate
    
    def apply_mar_dropout(
        self,
        df: pd.DataFrame,
        base_rate: float,
        predictors: Dict[str, float],
        arm_col: str = 'arm',
        arm_specific_rates: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Missing At Random (MAR) - REALISTIC
        
        Dropout probability depends on OBSERVED patient characteristics:
        - Higher BP → More dropout (uncontrolled hypertension)
        - Adverse events → More dropout
        - Treatment arm → Different rates (active often higher)
        
        Args:
            df: DataFrame with patient data
            base_rate: Baseline dropout rate
            predictors: Dict of {column_name: weight}
                       Example: {'sbp_week4': 0.01, 'has_ae': 0.20}
            arm_col: Column name for treatment arm
            arm_specific_rates: Dict of {arm: additional_rate}
            
        Returns:
            Boolean array: True = dropped out
            
        Example:
            >>> dropout = gen.apply_mar_dropout(
            ...     df,
            ...     base_rate=0.05,
            ...     predictors={
            ...         'sbp_week4': 0.005,  # +0.5% per mmHg above mean
            ...         'has_severe_ae': 0.25,  # +25% if severe AE
            ...         'age': 0.002  # +0.2% per year
            ...     },
            ...     arm_specific_rates={'active': 0.10}  # +10% for active
            ... )
        """
        n = len(df)
        dropout_prob = np.full(n, base_rate)
        
        # Add contributions from each predictor
        for col, weight in predictors.items():
            if col in df.columns:
                # Standardize continuous variables
                values = df[col].values
                if df[col].dtype in [np.float64, np.int64]:
                    # Center around mean
                    values_centered = values - np.mean(values)
                    dropout_prob += weight * values_centered
                else:
                    # Binary variables (AEs, etc.)
                    dropout_prob += weight * values.astype(float)
        
        # Add arm-specific rates
        if arm_specific_rates and arm_col in df.columns:
            for arm, additional_rate in arm_specific_rates.items():
                mask = df[arm_col] == arm
                dropout_prob[mask] += additional_rate
        
        # Clip to valid probability range
        dropout_prob = np.clip(dropout_prob, 0, 0.95)  # Max 95% dropout
        
        # Sample dropout
        return np.random.random(n) < dropout_prob
    
    def generate_latent_frailty(
        self,
        n_subjects: int,
        mean: float = 0.0,
        std: float = 1.0
    ) -> np.ndarray:
        """
        Generate unobserved "frailty" factor
        
        This represents unmeasured factors that predict dropout:
        - General health (not fully captured by vitals)
        - Motivation/adherence
        - Socioeconomic factors not recorded
        
        Args:
            n_subjects: Number of subjects
            mean: Mean frailty (0 = average)
            std: Std of frailty
            
        Returns:
            Array of frailty scores
        """
        return np.random.normal(mean, std, n_subjects)
    
    def apply_mnar_dropout(
        self,
        n_subjects: int,
        base_rate: float,
        latent_frailty: np.ndarray,
        frailty_weight: float = 0.15,
        observed_predictors: Optional[Dict] = None,
        df: Optional[pd.DataFrame] = None
    ) -> np.ndarray:
        """
        Missing Not At Random (MNAR) - MOST REALISTIC
        
        Dropout depends on UNOBSERVED factors (latent frailty).
        This creates selection bias that can't be corrected by observed data.
        
        Args:
            n_subjects: Number of subjects
            base_rate: Baseline dropout rate
            latent_frailty: Unobserved frailty scores
            frailty_weight: How much frailty affects dropout (0.1-0.2 typical)
            observed_predictors: Optional dict of observed predictors
            df: Optional DataFrame for observed predictors
            
        Returns:
            Boolean array: True = dropped out
            
        Example:
            >>> # Generate latent frailty
            >>> frailty = gen.generate_latent_frailty(n_subjects=100)
            >>> 
            >>> # MNAR dropout
            >>> dropout = gen.apply_mnar_dropout(
            ...     n_subjects=100,
            ...     base_rate=0.05,
            ...     latent_frailty=frailty,
            ...     frailty_weight=0.15
            ... )
            >>> 
            >>> # Frail patients more likely to drop out  
            >>> # But frailty is UNOBSERVED → selection bias!
        """
        dropout_prob = np.full(n_subjects, base_rate)
        
        # Add UNOBSERVED frailty contribution
        # Standardize frailty to mean=0, std=1
        frailty_std = (latent_frailty - np.mean(latent_frailty)) / (np.std(latent_frailty) + 1e-8)
        dropout_prob += frailty_weight * frailty_std
        
        # Optionally add observed predictors (MAR component)
        if observed_predictors and df is not None:
            for col, weight in observed_predictors.items():
                if col in df.columns:
                    values = df[col].values
                    if df[col].dtype in [np.float64, np.int64]:
                        values_centered = values - np.mean(values)
                        dropout_prob += weight * values_centered
                    else:
                        dropout_prob += weight * values.astype(float)
        
        # Clip to valid range
        dropout_prob = np.clip(dropout_prob, 0, 0.95)
        
        return np.random.random(n_subjects) < dropout_prob
    
    def apply_realistic_dropout_pattern(
        self,
        df: pd.DataFrame,
        base_dropout_rate: float,
        mechanism: str = 'MAR',
        arm_col: str = 'arm',
        arm_specific_rates: Optional[Dict[str, float]] = None,
        ae_col: Optional[str] = None,
        vital_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Apply realistic dropout pattern to clinical trial data
        
        This is the main function to use - automatically configures
        realistic predictors based on available data.
        
        Args:
            df: Trial data
            base_dropout_rate: Baseline dropout probability
            mechanism: 'MCAR', 'MAR', or 'MNAR'
            arm_col: Treatment arm column
            arm_specific_rates: Dict of {arm: rate}
            ae_col: Adverse event column (if available)
            vital_cols: List of vital sign columns
            
        Returns:
            DataFrame with added 'dropout' column
            
        Example:
            >>> df = gen.apply_realistic_dropout_pattern(
            ...     df,
            ...     base_dropout_rate=0.05,
            ...     mechanism='MAR',
            ...     arm_specific_rates={'active': 0.10},
            ...     ae_col='has_severe_ae',
            ...     vital_cols=['sbp_week4', 'dbp_week4']
            ... )
        """
        n = len(df)
        
        if mechanism == 'MCAR':
            # Simple random dropout
            df['dropout'] = self.apply_mcar_dropout(n, base_dropout_rate)
            
        elif mechanism == 'MAR':
            # Build predictors from available data
            predictors = {}
            
            # Adverse events increase dropout
            if ae_col and ae_col in df.columns:
                predictors[ae_col] = 0.20  # +20% if AE
            
            # High vitals increase dropout (uncontrolled condition)
            if vital_cols:
                for col in vital_cols:
                    if col in df.columns and 'sbp' in col.lower():
                        predictors[col] = 0.005  # +0.5% per mmHg above mean
                    elif col in df.columns and 'dbp' in col.lower():
                        predictors[col] = 0.008  # +0.8% per mmHg above mean
            
            # Age (if available)
            if 'age' in df.columns:
                predictors['age'] = 0.002  # +0.2% per year above mean
            
            df['dropout'] = self.apply_mar_dropout(
                df,
                base_rate=base_dropout_rate,
                predictors=predictors,
                arm_col=arm_col,
                arm_specific_rates=arm_specific_rates
            )
            
        elif mechanism == 'MNAR':
            # Generate latent frailty
            frailty = self.generate_latent_frailty(n)
            df['_latent_frailty'] = frailty  # Store for analysis
            
            # Build observed predictors (MAR component)
            observed_predictors = {}
            if ae_col and ae_col in df.columns:
                observed_predictors[ae_col] = 0.15
            if vital_cols:
                for col in vital_cols:
                    if col in df.columns and 'sbp' in col.lower():
                        observed_predictors[col] = 0.003
            
            df['dropout'] = self.apply_mnar_dropout(
                n_subjects=n,
                base_rate=base_dropout_rate,
                latent_frailty=frailty,
                frailty_weight=0.15,
                observed_predictors=observed_predictors,
                df=df
            )
        
        else:
            raise ValueError(f"Unknown mechanism: {mechanism}. Use 'MCAR', 'MAR', or 'MNAR'")
        
        return df
    
    def compare_missingness_mechanisms(
        self,
        df: pd.DataFrame,
        base_rate: float,
        arm_col: str = 'arm',
        ae_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Compare all three missingness mechanisms side-by-side
        
        Useful for understanding the impact of different assumptions
        
        Returns:
            DataFrame with columns: dropout_mcar, dropout_mar, dropout_mnar
        """
        df_copy = df.copy()
        
        # MCAR
        df_copy['dropout_mcar'] = self.apply_mcar_dropout(len(df), base_rate)
        
        # MAR
        predictors = {}
        if ae_col and ae_col in df.columns:
            predictors[ae_col] = 0.20
        df_copy['dropout_mar'] = self.apply_mar_dropout(
            df_copy, base_rate, predictors, arm_col
        )
        
        # MNAR
        frailty = self.generate_latent_frailty(len(df))
        df_copy['dropout_mnar'] = self.apply_mnar_dropout(
            len(df), base_rate, frailty, frailty_weight=0.15
        )
        
        return df_copy


def validate_missingness_mechanism(df: pd.DataFrame, ae_col: str = 'has_ae') -> Dict[str, float]:
    """
    Validate that missingness is realistic (not MCAR)
    
    Tests:
    - Are patients with AEs more likely to drop out?
    - Is dropout differential by arm?
    
    Returns:
        Validation metrics
    """
    results = {}
    
    # Test 1: AE correlation
    if ae_col in df.columns and 'dropout' in df.columns:
        dropout_with_ae = df[df[ae_col] == True]['dropout'].mean()
        dropout_no_ae = df[df[ae_col] == False]['dropout'].mean()
        
        results['dropout_rate_with_ae'] = dropout_with_ae
        results['dropout_rate_no_ae'] = dropout_no_ae
        results['ae_association'] = dropout_with_ae - dropout_no_ae
        results['realistic_mar'] = dropout_with_ae > dropout_no_ae
    
    # Test 2: Arm differential
    if 'arm' in df.columns and 'dropout' in df.columns:
        for arm in df['arm'].unique():
            rate = df[df['arm'] == arm]['dropout'].mean()
            results[f'dropout_rate_{arm}'] = rate
    
    return results


# Convenience function
def add_realistic_missing_data(
    df: pd.DataFrame,
    dropout_rate: float,
    mechanism: str = 'MAR',
    arm_specific_rates: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Quick function to add realistic missing data to trial
    
    Example:
        >>> df = add_realistic_missing_data(
        ...     df,
        ...     dropout_rate=0.10,
        ...     mechanism='MAR',
        ...     arm_specific_rates={'active': 0.05}  # +5% for active
        ... )
    """
    gen = MissingnessGenerator()
    return gen.apply_realistic_dropout_pattern(
        df=df,
        base_dropout_rate=dropout_rate,
        mechanism=mechanism,
        arm_specific_rates=arm_specific_rates,
        ae_col='has_ae' if 'has_ae' in df.columns else None,
        vital_cols=[col for col in df.columns if 'sbp' in col.lower() or 'dbp' in col.lower()]
    )
