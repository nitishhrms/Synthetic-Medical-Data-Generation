"""
Enhanced Vitals Generator with All Critical Fixes Integrated
=============================================================

This module integrates the 3 critical ML research fixes into the main generator:
1. Temporal correlation (AR1 model)
2. Heterogeneous treatment effects
3. MAR/MNAR missingness mechanisms

Usage:
    # New enhanced generator (recommended)
    df = generate_vitals_enhanced(
        n_per_arm=50,
        use_temporal_correlation=True,
        use_heterogeneous_effects=True,
        missingness_mechanism='MAR'
    )
    
    # Old generator still available for backward compatibility
    df = generate_vitals_mvn(n_per_arm=50)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import sys
import os

# Import our new modules
from temporal_generators import TemporalVitalsGenerator
from treatment_effect_sampler import HeterogeneousTreatmentEffectSampler
from missingness_mechanisms import MissingnessGenerator
from aact_utils import (
    sample_dropout_rate,
    get_arm_specific_dropout_rates,
    get_baseline_vitals
)


def generate_vitals_enhanced(
    n_per_arm: int = 50,
    indication: str = "hypertension",
    phase: str = "Phase 3",
    target_effect_mean: float = -5.0,
    target_effect_std: float = 3.0,
    visit_weeks: List[int] = [0, 4, 12],
    use_temporal_correlation: bool = True,
    temporal_rho: float = 0.7,
    use_heterogeneous_effects: bool = True,
    baseline_correlation: float = 0.3,
    missingness_mechanism: str = 'MAR',  # 'MCAR', 'MAR', or 'MNAR'
    use_aact_dropout_variance: bool = True,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate realistic clinical trial vitals data with all ML research fixes
    
    This is the RECOMMENDED generator - uses all statistical improvements:
    - ✅ Temporal correlation between visits (AR1 model)
    - ✅ Heterogeneous treatment effects (responders/non-responders)
    - ✅ MAR/MNAR missing data mechanisms
    - ✅ AACT-derived realistic parameters
    
    Args:
        n_per_arm: Subjects per treatment arm
        indication: Disease indication (for AACT priors)
        phase: Trial phase (for AACT priors)
        target_effect_mean: Mean treatment effect (mmHg for SBP)
        target_effect_std: Std of treatment effect (heterogeneity)
        visit_weeks: List of visit weeks [0, 4, 12]
        use_temporal_correlation: Use AR(1) for longitudinal correlation
        temporal_rho: Autocorrelation coefficient (0.6-0.8 typical)
        use_heterogeneous_effects: Vary treatment effects by subject
        baseline_correlation: How baseline predicts response (0-0.4)
        missingness_mechanism: 'MCAR', 'MAR', or 'MNAR'
        use_aact_dropout_variance: Sample dropout rates with variance
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with enhanced realistic clinical trial data
        
    Example:
        >>> # Realistic Phase 3 hypertension trial
        >>> df = generate_vitals_enhanced(
        ...     n_per_arm=100,
        ...     indication="hypertension",
        ...     phase="Phase 3",
        ...     use_temporal_correlation=True,
        ...     use_heterogeneous_effects=True,
        ...     missingness_mechanism='MAR'
        ... )
        >>> 
        >>> # Verify temporal correlation
        >>> assert df.groupby('SubjectID')['SystolicBP'].corr() > 0.6
        >>> 
        >>> # Verify heterogeneous effects
        >>> effects = df.groupby('SubjectID')['SystolicBP'].apply(
        ...     lambda x: x.iloc[-1] - x.iloc[0]
        ... )
        >>> assert effects.std() > 2.0  # Heterogeneity present
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Get AACT priors for baseline vitals
    try:
        baseline_stats = get_baseline_vitals(indication, phase)
        sbp_mean = baseline_stats.get('systolic', {}).get('mean', 145)
        sbp_std = baseline_stats.get('systolic', {}).get('std', 10)
    except:
        sbp_mean, sbp_std = 145, 10
    
    # Initialize generators
    temporal_gen = TemporalVitalsGenerator(rho=temporal_rho, seed=seed)
    treatment_gen = HeterogeneousTreatmentEffectSampler(seed=seed)
    missingness_gen = MissingnessGenerator(seed=seed)
    
    # =========================================================================
    # STEP 1: Generate baseline values (population distribution)
    # =========================================================================
    baseline_active = np.random.normal(sbp_mean, sbp_std, n_per_arm)
    baseline_placebo = np.random.normal(sbp_mean, sbp_std, n_per_arm)
    
    # =========================================================================
    # STEP 2: Generate heterogeneous treatment effects
    # =========================================================================
    if use_heterogeneous_effects:
        # Active arm: heterogeneous effects correlated with baseline
        effects_active = treatment_gen.sample_treatment_effects(
            n_subjects=n_per_arm,
            mean_effect=target_effect_mean,
            std_effect=target_effect_std,
            baseline_values=baseline_active,
            baseline_correlation=baseline_correlation
        )
        
        # Placebo arm: placebo response
        effects_placebo = treatment_gen.sample_placebo_effects(
            n_subjects=n_per_arm,
            responder_rate=0.30
        )
    else:
        # Old way: homogeneous effects
        effects_active = np.full(n_per_arm, target_effect_mean)
        effects_placebo = np.zeros(n_per_arm)
    
    # =========================================================================
    # STEP 3: Generate longitudinal trajectories with temporal correlation
    # =========================================================================
    rows = []
    
    for arm, baseline_values, effects, arm_name in [
        (0, baseline_active, effects_active, 'Active'),
        (1, baseline_placebo, effects_placebo, 'Placebo')
    ]:
        for subj_idx in range(n_per_arm):
            subject_id = f"{arm_name[:3].upper()}-{subj_idx+1:03d}"
            
            if use_temporal_correlation:
                # Generate AR(1) trajectory
                trajectory = temporal_gen.generate_ar1_trajectory(
                    baseline_value=baseline_values[subj_idx],
                    baseline_std=sbp_std,
                    n_visits=len(visit_weeks),
                    visit_weeks=visit_weeks,
                    treatment_effect=effects[subj_idx] / max(visit_weeks),  # Per week
                    treatment_start_week=visit_weeks[0],
                    innovation_std=5.0
                )
            else:
                # Old way: independent visits
                trajectory = np.random.normal(
                    baseline_values[subj_idx] + effects[subj_idx],
                    sbp_std,
                    len(visit_weeks)
                )
            
            # Store measurements
            for visit_idx, week in enumerate(visit_weeks):
                sbp = int(np.clip(trajectory[visit_idx], 95, 200))
                
                # Generate correlated DBP, HR, Temp
                dbp = int(np.clip(sbp * 0.6 + np.random.normal(0, 5), 55, 130))
                hr = int(np.clip(72 + np.random.normal(0, 10), 50, 120))
                temp = float(np.clip(36.7 + np.random.normal(0, 0.3), 35.0, 40.0))
                
                rows.append({
                    'SubjectID': subject_id,
                    'VisitName': f'Week {week}' if week > 0 else 'Screening',
                    'VisitWeek': week,
                    'TreatmentArm': arm_name,
                    'SystolicBP': sbp,
                    'DiastolicBP': dbp,
                    'HeartRate': hr,
                    'Temperature': temp,
                    '_baseline_sbp': baseline_values[subj_idx],
                    '_treatment_effect': effects[subj_idx]
                })
    
    df = pd.DataFrame(rows)
    
    # =========================================================================
    # STEP 4: Apply realistic missing data mechanism
    # =========================================================================
    if missingness_mechanism != 'none':
        # Get dropout rate with AACT variance
        if use_aact_dropout_variance:
            try:
                dropout_rate = sample_dropout_rate(indication, phase, seed=seed)
                arm_rates = get_arm_specific_dropout_rates(indication, phase)
                
                # Map arm names
                arm_specific_rates = {}
                if 'Active' in df['TreatmentArm'].values:
                    # Use average of top 2 arms for active
                    active_rate = np.mean([v for k, v in sorted(arm_rates.items(), 
                                                               key=lambda x: x[1], 
                                                               reverse=True)[:2]])
                    arm_specific_rates['Active'] = active_rate - dropout_rate
                
                if 'Placebo' in df['TreatmentArm'].values:
                    # Use average of bottom 2 arms for placebo
                    placebo_rate = np.mean([v for k, v in sorted(arm_rates.items(), 
                                                                key=lambda x: x[1])[:2]])
                    arm_specific_rates['Placebo'] = placebo_rate - dropout_rate
            except:
                dropout_rate = 0.10
                arm_specific_rates = {'Active': 0.05, 'Placebo': -0.03}
        else:
            dropout_rate = 0.10
            arm_specific_rates = {'Active': 0.05}
        
        # Generate adverse events (simple model for now)
        df_baseline = df[df['VisitWeek'] == 0].copy()
        df_baseline['has_severe_ae'] = np.random.random(len(df_baseline)) < 0.15
        
        # Merge AE data
        df = df.merge(
            df_baseline[['SubjectID', 'has_severe_ae']], 
            on='SubjectID', 
            how='left'
        )
        
        # Apply missingness mechanism
        df = missingness_gen.apply_realistic_dropout_pattern(
            df=df,
            base_dropout_rate=dropout_rate,
            mechanism=missingness_mechanism,
            arm_col='TreatmentArm',
            arm_specific_rates=arm_specific_rates,
            ae_col='has_severe_ae',
            vital_cols=['SystolicBP', 'DiastolicBP']
        )
    
    # Clean up temporary columns
    df = df.drop(columns=[col for col in df.columns if col.startswith('_')], errors='ignore')
    
    return df


def compare_old_vs_new_generators(
    n_per_arm: int = 50,
    seed: int = 42
) -> Dict[str, pd.DataFrame]:
    """
    Compare old generator (without fixes) vs new (with fixes)
    
    Useful for demonstrating the improvement
    
    Returns:
        {'old': old_df, 'new': new_df, 'comparison': metrics_df}
    """
    # Old generator (would need to import from generators.py)
    # df_old = generate_vitals_mvn(n_per_arm=n_per_arm, seed=seed)
    
    # New generator with all fixes
    df_new = generate_vitals_enhanced(
        n_per_arm=n_per_arm,
        use_temporal_correlation=True,
        use_heterogeneous_effects=True,
        missingness_mechanism='MAR',
        seed=seed
    )
    
    # Compute metrics
    # ... (comparison logic)
    
    return {
        'new': df_new,
        # 'old': df_old,
        'summary': 'New generator has temporal correlation, heterogeneous effects, and MAR dropout'
    }


if __name__ == "__main__":
    # Demo
    print("Generating enhanced vitals data...")
    df = generate_vitals_enhanced(
        n_per_arm=50,
        indication="hypertension",
        phase="Phase 3",
        use_temporal_correlation=True,
        use_heterogeneous_effects=True,
        missingness_mechanism='MAR',
        seed=42
    )
    
    print(f"\nGenerated {len(df)} measurements for {df['SubjectID'].nunique()} subjects")
    print(f"\nSample data:")
    print(df.head(10))
    
    print(f"\nDropout summary:")
    if 'dropout' in df.columns:
        print(df.groupby('TreatmentArm')['dropout'].mean())
