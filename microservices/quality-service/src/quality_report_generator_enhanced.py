"""
Enhanced Quality Report Generator - Updated for ML Research-Grade Data
======================================================================

Integrates the 3 critical ML enhancements into quality reports:
1. Temporal correlation validation
2. Heterogeneous treatment effects
3. MAR/MNAR missingness mechanisms

Updates quality scoring to reflect research-grade standards.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime


def validate_enhanced_data_quality(synthetic_data: pd.DataFrame) -> Dict:
    """
    Validate enhanced data quality metrics
    
    Returns metrics for:
    - Temporal correlation
    - Treatment heterogeneity
    - Missingness mechanism
    """
    results = {
        'temporal_correlation': None,
        'treatment_heterogeneity': None,
        'missingness_classification': None
    }
    
    # 1. Temporal Correlation
    if 'SubjectID' in synthetic_data.columns and 'SystolicBP' in synthetic_data.columns:
        correlations = []
        for subject_id, subject_df in synthetic_data.groupby('SubjectID'):
            subject_df = subject_df.sort_values('VisitWeek') if 'VisitWeek' in subject_df.columns else subject_df
            sbp = subject_df['SystolicBP'].values
            if len(sbp) >= 2:
                with np.errstate(invalid='ignore'):
                    corr = np.corrcoef(sbp[:-1], sbp[1:])[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)
        
        if correlations:
            mean_corr = np.mean(correlations)
            results['temporal_correlation'] = {
                'mean': round(float(mean_corr), 3),
                'std': round(float(np.std(correlations)), 3),
                'status': 'excellent' if 0.6 <= mean_corr <= 0.8 else 'acceptable' if mean_corr > 0.4 else 'poor'
            }
    
    # 2. Treatment Heterogeneity
    if all(col in synthetic_data.columns for col in ['SubjectID', 'TreatmentArm', 'SystolicBP']):
        active_effects = []
        for subject_id, subject_df in synthetic_data[synthetic_data['TreatmentArm']=='Active'].groupby('SubjectID'):
            sbp_vals = subject_df.sort_values('VisitWeek')['SystolicBP'].values if 'VisitWeek' in subject_df.columns else subject_df['SystolicBP'].values
            if len(sbp_vals) >= 2:
                effect = sbp_vals[-1] - sbp_vals[0]
                active_effects.append(effect)
        
        if active_effects:
            effect_std = np.std(active_effects)
            results['treatment_heterogeneity'] = {
                'std': round(float(effect_std), 2),
                'mean': round(float(np.mean(active_effects)), 2),
                'range': [round(float(np.min(active_effects)), 1), round(float(np.max(active_effects)), 1)],
                'status': 'excellent' if effect_std >= 3.0 else 'good' if effect_std >= 2.0 else 'poor'
            }
    
    # 3. Missingness Mechanism
    if 'dropout' in synthetic_data.columns and 'has_severe_ae' in synthetic_data.columns:
        dropout_with_ae = synthetic_data[synthetic_data['has_severe_ae']==True]['dropout'].mean()
        dropout_without_ae = synthetic_data[synthetic_data['has_severe_ae']==False]['dropout'].mean()
        diff = dropout_with_ae - dropout_without_ae
        
        results['missingness_classification'] = {
            'dropout_with_ae': round(float(dropout_with_ae), 3),
            'dropout_without_ae': round(float(dropout_without_ae), 3),
            'difference': round(float(diff), 3),
            'mechanism': 'MAR' if diff > 0.10 else 'MCAR',
            'status': 'realistic' if diff > 0.10 else 'unrealistic'
        }
    
    return results


def calculate_enhanced_quality_score(
    syndata_metrics: Optional[Dict],
    enhanced_validations: Dict
) -> Dict:
    """
    Calculate overall quality score incorporating enhanced metrics
    
    Scoring breakdown:
    - SYNDATA metrics: 40%
    - Temporal correlation: 20%
    - Treatment heterogeneity: 20%
    - Missingness realism: 20%
    """
    scores = {}
    weights = {}
    
    # 1. SYNDATA Score (if available)
    if syndata_metrics and 'overall_score' in syndata_metrics:
        scores['syndata'] = syndata_metrics['overall_score'] * 100
        weights['syndata'] = 0.4
    
    # 2. Temporal Correlation Score
    if enhanced_validations.get('temporal_correlation'):
        tc = enhanced_validations['temporal_correlation']
        if tc['status'] == 'excellent':
            scores['temporal'] = 100
        elif tc['status'] == 'acceptable':
            scores['temporal'] = 75
        else:
            scores['temporal'] = 50
        weights['temporal'] = 0.2
    
    # 3. Treatment Heterogeneity Score
    if enhanced_validations.get('treatment_heterogeneity'):
        th = enhanced_validations['treatment_heterogeneity']
        if th['status'] == 'excellent':
            scores['heterogeneity'] = 100
        elif th['status'] == 'good':
            scores['heterogeneity'] = 85
        else:
            scores['heterogeneity'] = 60
        weights['heterogeneity'] = 0.2
    
    # 4. Missingness Mechanism Score
    if enhanced_validations.get('missingness_classification'):
        mc = enhanced_validations['missingness_classification']
        if mc['status'] == 'realistic':
            scores['missingness'] = 100
        else:
            scores['missingness'] = 60
        weights['missingness'] = 0.2
    
    # Calculate weighted average
    if scores and weights:
        total_weight = sum(weights.values())
        weighted_score = sum(scores[k] * weights[k] for k in scores.keys()) / total_weight
        
        # Assign grade
        if weighted_score >= 85:
            grade = 'A'
        elif weighted_score >= 75:
            grade = 'B'
        elif weighted_score >= 65:
            grade = 'C'
        else:
            grade = 'D'
        
        return {
            'overall_score': round(weighted_score, 1),
            'grade': grade,
            'component_scores': scores,
            'weights': weights
        }
    
    return {'overall_score': 0, 'grade': 'F', 'component_scores': {}, 'weights': {}}


def generate_enhanced_quality_report(
    method_name: str,
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    syndata_metrics: Optional[Dict] = None,
    privacy_metrics: Optional[Dict] = None,
    generation_time_ms: Optional[float] = None
) -> str:
    """
    Generate comprehensive quality report with enhanced validations
    
    Includes:
    - Traditional SYNDATA metrics
    - Enhanced ML validation (temporal, heterogeneity, missingness)
    - Overall quality score and grade
    - Recommendations
   
    Args:
        method_name: Generation method used
        real_data: Real baseline dataset
        synthetic_data: Generated synthetic dataset
        syndata_metrics: Optional pre-computed SYNDATA metrics
        privacy_metrics: Optional privacy assessment results
        generation_time_ms: Time taken to generate (ms)
        
    Returns:
        Markdown-formatted quality report
    """
    report = []
    
    # Header
    report.append(f"# Quality Report: {method_name.upper()}")
    report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Enhanced Validations
    enhanced_vals = validate_enhanced_data_quality(synthetic_data)
    
    # Calculate Enhanced Quality Score
    quality_score = calculate_enhanced_quality_score(syndata_metrics, enhanced_vals)
    
    # Overall Assessment
    report.append("## Overall Assessment\n")
    report.append(f"**Quality Score:** {quality_score['overall_score']}/100")
    report.append(f"**Grade:** {quality_score['grade']}")
    
    if quality_score['grade'] == 'A':
        report.append("**Status:** ✅ **Publication-Ready** - Suitable for ML research and regulatory submission\n")
    elif quality_score['grade'] == 'B':
        report.append("**Status:** ⚠️ **Good Quality** - Acceptable for most research applications\n")
    elif quality_score['grade'] == 'C':
        report.append("**Status:** ⚠️ **Moderate Quality** - Consider improvements before publication\n")
    else:
        report.append("**Status:** ❌ **Poor Quality** - Requires significant improvement\n")
    
    # Performance
    if generation_time_ms:
        report.append(f"**Generation Time:** {generation_time_ms:.2f} ms\n")
    
    # Enhanced Validation Results
    report.append("## Enhanced ML Validation\n")
    
    # Temporal Correlation
    if enhanced_vals.get('temporal_correlation'):
        tc = enhanced_vals['temporal_correlation']
        report.append("### 1. Temporal Correlation")
        report.append(f"- **Mean Correlation (ρ):** {tc['mean']}")
        report.append(f"- **Std Deviation:** {tc['std']}")
        report.append(f"- **Status:** {tc['status'].title()}")
        if tc['status'] == 'excellent':
            report.append("- ✅ Strong temporal correlation (0.6-0.8) - realistic longitudinal data")
        elif tc['status'] == 'acceptable':
            report.append("- ⚠️ Moderate correlation - acceptable for most analyses")
        else:
            report.append("- ❌ Weak correlation - data may be unrealistic")
        report.append("")
    
    # Treatment Heterogeneity
    if enhanced_vals.get('treatment_heterogeneity'):
        th = enhanced_vals['treatment_heterogeneity']
        report.append("### 2. Treatment Effect Heterogeneity")
        report.append(f"- **Effect Std:** {th['std']} mmHg")
        report.append(f"- **Mean Effect:** {th['mean']} mmHg")
        report.append(f"- **Range:** {th['range'][0]} to {th['range'][1]} mmHg")
        report.append(f"- **Status:** {th['status'].title()}")
        if th['status'] == 'excellent':
            report.append("- ✅ Realistic heterogeneity - supports responder analysis")
        elif th['status'] == 'good':
            report.append("- ⚠️ Moderate heterogeneity - acceptable variation")
        else:
            report.append("- ❌ Low heterogeneity - effects too homogeneous")
        report.append("")
    
    # Missingness Mechanism
    if enhanced_vals.get('missingness_classification'):
        mc = enhanced_vals['missingness_classification']
        report.append("### 3. Missingness Mechanism")
        report.append(f"- **Dropout with AE:** {mc['dropout_with_ae']:.1%}")
        report.append(f"- **Dropout without AE:** {mc['dropout_without_ae']:.1%}")
        report.append(f"- **Difference:** {mc['difference']:.1%}")
        report.append(f"- **Classification:** {mc['mechanism']}")
        report.append(f"- **Status:** {mc['status'].title()}")
        if mc['status'] == 'realistic':
            report.append("- ✅ MAR dropout pattern - realistic missingness")
        else:
            report.append("- ❌ MCAR dropout - unrealistic for clinical trials")
        report.append("")
    
    # SYNDATA Metrics (if available)
    if syndata_metrics:
        report.append("## SYNDATA Quality Metrics\n")
        
        if 'ci_coverage' in syndata_metrics:
            ci = syndata_metrics['ci_coverage']
            report.append(f"- **CI Coverage:** {ci.get('percentage', 0):.1f}% (Target: 88-98%)")
        
        if 'support_coverage' in syndata_metrics:
            sc = syndata_metrics['support_coverage']
            report.append(f"- **Support Coverage:** {sc.get('overall', 0):.2f}")
        
        if 'cross_classification' in syndata_metrics:
            cc = syndata_metrics['cross_classification']
            report.append(f"- **Cross-Classification:** {cc.get('utility_score', 0):.2f}")
        
        report.append("")
    
    # Privacy (if available)
    if privacy_metrics:
        report.append("## Privacy Assessment\n")
        
        if 'k_anonymity' in privacy_metrics:
            k = privacy_metrics['k_anonymity']
            report.append(f"- **K-Anonymity:** k={k.get('k', 0)}")
        
        if 'l_diversity' in privacy_metrics:
            l = privacy_metrics['l_diversity']
            report.append(f"- **L-Diversity:** l={l.get('l', 0)}")
        
        report.append("")
    
    # Recommendations
    report.append("## Recommendations\n")
    
    recs = []
    
    # Temporal correlation recommendations
    if enhanced_vals.get('temporal_correlation'):
        if enhanced_vals['temporal_correlation']['status'] == 'poor':
            recs.append("- **Temporal Correlation:** Enable temporal correlation in data generation (use_temporal_correlation=True)")
        elif enhanced_vals['temporal_correlation']['status'] == 'acceptable':
            recs.append("- **Temporal Correlation:** Consider increasing temporal_rho parameter (0.6-0.8)")
    
    # Heterogeneity recommendations
    if enhanced_vals.get('treatment_heterogeneity'):
        if enhanced_vals['treatment_heterogeneity']['status'] == 'poor':
            recs.append("- **Heterogeneity:** Increase target_effect_std parameter (recommended: 3.0-5.0)")
    
    # Missingness recommendations
    if enhanced_vals.get('missingness_classification'):
        if enhanced_vals['missingness_classification']['status'] == 'unrealistic':
            recs.append("- **Missingness:** Use 'MAR' or 'MNAR' missingness mechanism instead of 'MCAR'")
    
    # Overall quality recommendations
    if quality_score['grade'] in ['C', 'D']:
        recs.append("- **Overall:** Consider using enhanced generator with all validation options enabled")
        recs.append("- **Code Example:** `generate_vitals_enhanced(use_temporal_correlation=True, use_heterogeneous_effects=True, missingness_mechanism='MAR')`")
    
    if not recs:
        recs.append("- ✅ No major issues detected - data quality is excellent")
    
    for rec in recs:
        report.append(rec)
    
    report.append("")
    
    # Footer
    report.append("---")
    report.append("*Generated by Enhanced Quality Service v2.0*")
    
    return "\n".join(report)
