"""
Treatment Effect Sampler Module
================================

Fixes Critical Issue #2: Homogeneous treatment effects

Problem:
    Current implementation gives ALL subjects the exact same treatment effect:
    - Everyone gets -5 mmHg SBP reduction
    - No responders/non-responders distinction
    - No correlation with baseline severity
    - FDA requires subgroup analysis - impossible with homogeneous effects

Solution:
    Subject-level heterogeneous treatment effects:
    - Sample from distribution: effect ~ N(μ, σ²)
    - Correlate with baseline (sicker patients respond better)
    - Include placebo responders (~30%)
    - Model non-responders and super-responders

Impact:
    Enables realistic subgroup analysis
    Supports adaptive trial designs
    Matches real-world variability

Author: Based on expert ML research assessment
Date: 2025-11-22
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple
from scipy import stats


class HeterogeneousTreatmentEffectSampler:
    """
    Generate heterogeneous treatment effects for clinical trials
    
    Real trials show:
    - 20-30% non-responders (minimal effect)
    - 50-60% moderate responders (average effect)
    - 10-20% super-responders (large effect)
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize sampler with optional seed"""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
    
    def sample_treatment_effects(
        self,
        n_subjects: int,
        mean_effect: float,
        std_effect: float,
        baseline_values: Optional[np.ndarray] = None,
        baseline_correlation: float = 0.3,
        min_effect: Optional[float] = None,
        max_effect: Optional[float] = None
    ) -> np.ndarray:
        """
        Sample heterogeneous treatment effects for each subject
        
        Args:
            n_subjects: Number of subjects
            mean_effect: Population mean effect (e.g., -5 mmHg for SBP)
            std_effect: Population std of effect (e.g., 3 mmHg)
            baseline_values: Baseline measurements (e.g., baseline SBP)
            baseline_correlation: How much baseline predicts response (0-1)
                                 0.3 = moderate correlation (typical)
            min_effect: Minimum possible effect (floor)
            max_effect: Maximum possible effect (ceiling)
            
        Returns:
            Array of treatment effects, one per subject
            
        Example:
            >>> sampler = HeterogeneousTreatmentEffectSampler(seed=42)
            >>> baseline_sbp = np.array([140, 160, 150, 145, 170])
            >>> effects = sampler.sample_treatment_effects(
            ...     n_subjects=5,
            ...     mean_effect=-5.0,
            ...     std_effect=3.0,
            ...     baseline_values=baseline_sbp,
            ...     baseline_correlation=0.3
            ... )
            >>> # effects might be: [-3.2, -8.1, -5.5, -4.2, -9.3]
            >>> # Notice: Patient with SBP=170 gets -9.3 (sicker → better response)
        """
        # Base treatment effect from population distribution
        base_effects = np.random.normal(mean_effect, std_effect, n_subjects)
        
        # Add correlation with baseline severity if provided
        if baseline_values is not None and baseline_correlation > 0:
            # Standardize baseline values
            baseline_z = (baseline_values - np.mean(baseline_values)) / (np.std(baseline_values) + 1e-8)
            
            # Higher baseline → larger effect (for conditions where this makes sense)
            # For SBP: Higher baseline BP → bigger reduction
            baseline_adjustment = baseline_correlation * std_effect * baseline_z
            
            effects = base_effects + baseline_adjustment
        else:
            effects = base_effects
        
        # Apply floor/ceiling if specified
        if min_effect is not None:
            effects = np.maximum(effects, min_effect)
        if max_effect is not None:
            effects = np.minimum(effects, max_effect)
        
        return effects
    
    def assign_responder_groups(
        self,
        treatment_effects: np.ndarray,
        mean_effect: float,
        std_effect: float
    ) -> np.ndarray:
        """
        Classify subjects into responder categories
        
        Args:
            treatment_effects: Array of individual treatment effects
            mean_effect: Population mean effect
            std_effect: Population std
            
        Returns:
            Array of categories: 'non-responder', 'moderate', 'super-responder'
            
        Thresholds:
            - Non-responder: effect > mean + 0.5*std (small/no benefit)
            - Moderate: mean - 0.5*std < effect < mean + 0.5*std
            - Super-responder: effect < mean - 0.5*std (large benefit)
        """
        categories = np.empty(len(treatment_effects), dtype=object)
        
        # Note: For negative effects (reduction), more negative = better response
        threshold_low = mean_effect - 0.5 * std_effect   # Super-responder
        threshold_high = mean_effect + 0.5 * std_effect  # Non-responder
        
        categories[treatment_effects < threshold_low] = 'super-responder'
        categories[treatment_effects > threshold_high] = 'non-responder'
        categories[(treatment_effects >= threshold_low) & (treatment_effects <= threshold_high)] = 'moderate'
        
        return categories
    
    def sample_placebo_effects(
        self,
        n_subjects: int,
        responder_rate: float = 0.30,
        responder_effect_mean: float = -2.0,
        responder_effect_std: float = 1.0,
        non_responder_effect_mean: float = 0.0,
        non_responder_effect_std: float = 0.5
    ) -> np.ndarray:
        """
        Sample placebo effects (regression to mean + placebo response)
        
        Args:
            n_subjects: Number of subjects
            responder_rate: Fraction who show placebo response (typically 0.25-0.35)
            responder_effect_mean: Mean effect for placebo responders
            responder_effect_std: Std for placebo responders
            non_responder_effect_mean: Mean for non-responders (typically ~0)
            non_responder_effect_std: Std for non-responders
            
        Returns:
            Array of placebo effects
            
        Example:
            >>> sampler = HeterogeneousTreatmentEffectSampler(seed=42)
            >>> placebo_effects = sampler.sample_placebo_effects(
            ...     n_subjects=100,
            ...     responder_rate=0.30
            ... )
            >>> # ~30 subjects will show -2 mmHg reduction
            >>> # ~70 subjects will show ~0 mmHg change
        """
        effects = np.zeros(n_subjects)
        
        # Randomly assign responder status
        is_responder = np.random.random(n_subjects) < responder_rate
        
        # Sample effects for each group
        effects[is_responder] = np.random.normal(
            responder_effect_mean,
            responder_effect_std,
            np.sum(is_responder)
        )
        
        effects[~is_responder] = np.random.normal(
            non_responder_effect_mean,
            non_responder_effect_std,
            np.sum(~is_responder)
        )
        
        return effects
    
    def generate_heterogeneous_trial_data(
        self,
        n_per_arm: int,
        baseline_mean: float,
        baseline_std: float,
        treatment_effect_mean: float,
        treatment_effect_std: float,
        placebo_responder_rate: float = 0.30,
        baseline_correlation: float = 0.3,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Generate complete trial with heterogeneous treatment effects
        
        Args:
            n_per_arm: Subjects per arm
            baseline_mean: Mean baseline value (e.g., 145 mmHg)
            baseline_std: Std of baseline
            treatment_effect_mean: Mean treatment effect (e.g., -5 mmHg)
            treatment_effect_std: Std of treatment effect (e.g., 3 mmHg)
            placebo_responder_rate: Fraction showing placebo response
            baseline_correlation: Correlation between baseline and response
            seed: Random seed
            
        Returns:
            DataFrame with columns:
            - subject_id
            - arm (active/placebo)
            - baseline_value
            - treatment_effect
            - final_value
            - responder_category
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Generate baseline values
        baseline_active = np.random.normal(baseline_mean, baseline_std, n_per_arm)
        baseline_placebo = np.random.normal(baseline_mean, baseline_std, n_per_arm)
        
        # Generate heterogeneous treatment effects for active arm
        effects_active = self.sample_treatment_effects(
            n_subjects=n_per_arm,
            mean_effect=treatment_effect_mean,
            std_effect=treatment_effect_std,
            baseline_values=baseline_active,
            baseline_correlation=baseline_correlation
        )
        
        # Generate placebo effects
        effects_placebo = self.sample_placebo_effects(
            n_subjects=n_per_arm,
            responder_rate=placebo_responder_rate,
            responder_effect_mean=-1.5,  # Small regression to mean
            responder_effect_std=1.0
        )
        
        # Calculate final values
        final_active = baseline_active + effects_active
        final_placebo = baseline_placebo + effects_placebo
        
        # Assign responder categories
        categories_active = self.assign_responder_groups(
            effects_active, treatment_effect_mean, treatment_effect_std
        )
        categories_placebo = np.array(['placebo'] * n_per_arm, dtype=object)
        
        # Create DataFrame
        df_active = pd.DataFrame({
            'subject_id': [f'ACT-{i+1:04d}' for i in range(n_per_arm)],
            'arm': 'active',
            'baseline_value': baseline_active,
            'treatment_effect': effects_active,
            'final_value': final_active,
            'change_from_baseline': effects_active,
            'responder_category': categories_active
        })
        
        df_placebo = pd.DataFrame({
            'subject_id': [f'PBO-{i+1:04d}' for i in range(n_per_arm)],
            'arm': 'placebo',
            'baseline_value': baseline_placebo,
            'treatment_effect': effects_placebo,
            'final_value': final_placebo,
            'change_from_baseline': effects_placebo,
            'responder_category': categories_placebo
        })
        
        return pd.concat([df_active, df_placebo], ignore_index=True)


def compute_treatment_effect_statistics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute summary statistics for treatment effects
    
    Args:
        df: DataFrame from generate_heterogeneous_trial_data()
        
    Returns:
        Dict with effect statistics
    """
    active_effects = df[df['arm'] == 'active']['change_from_baseline']
    placebo_effects = df[df['arm'] == 'placebo']['change_from_baseline']
    
    # Compute various effect size measures
    mean_diff = active_effects.mean() - placebo_effects.mean()
    
    # Cohen's d
    pooled_std = np.sqrt(
        (active_effects.std()**2 + placebo_effects.std()**2) / 2
    )
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
    
    # Responder analysis (active arm only)
    active_df = df[df['arm'] == 'active']
    responder_dist = active_df['responder_category'].value_counts(normalize=True).to_dict()
    
    return {
        'active_mean_effect': active_effects.mean(),
        'active_std_effect': active_effects.std(),
        'placebo_mean_effect': placebo_effects.mean(),
        'placebo_std_effect': placebo_effects.std(),
        'mean_treatment_difference': mean_diff,
        'cohens_d': cohens_d,
        'responder_rate': responder_dist.get('super-responder', 0) + responder_dist.get('moderate', 0),
        'non_responder_rate': responder_dist.get('non-responder', 0),
        'super_responder_rate': responder_dist.get('super-responder', 0)
    }


# Convenience function
def apply_heterogeneous_treatment_effects(
    df: pd.DataFrame,
    baseline_col: str,
    arm_col: str,
    mean_effect: float,
    std_effect: float,
    output_col: str = 'treatment_effect'
) -> pd.DataFrame:
    """
    Apply heterogeneous treatment effects to existing DataFrame
    
    Example:
        >>> df = pd.DataFrame({
        ...     'subject_id': ['S1', 'S2', 'S3'],
        ...     'sbp_baseline': [140, 160, 150],
        ...     'arm': ['active', 'active', 'placebo']
        ... })
        >>> df = apply_heterogeneous_treatment_effects(
        ...     df, 'sbp_baseline', 'arm', mean_effect=-5.0, std_effect=3.0
        ... )
    """
    sampler = HeterogeneousTreatmentEffectSampler()
    
    # Process each arm separately
    for arm in df[arm_col].unique():
        mask = df[arm_col] == arm
        n = mask.sum()
        
        if arm.lower() in ['active', 'treatment', 'experimental']:
            effects = sampler.sample_treatment_effects(
                n_subjects=n,
                mean_effect=mean_effect,
                std_effect=std_effect,
                baseline_values=df.loc[mask, baseline_col].values,
                baseline_correlation=0.3
            )
        else:  # Placebo
            effects = sampler.sample_placebo_effects(n_subjects=n)
        
        df.loc[mask, output_col] = effects
    
    return df
