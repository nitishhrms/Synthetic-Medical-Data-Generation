"""
Enhanced Validation Module for Analytics Service
=================================================

Validates the 3 critical ML research enhancements:
1. Temporal correlation (AR1 model)
2. Heterogeneous treatment effects
3. MAR/MNAR missingness mechanisms

These validators ensure synthetic data meets research-grade quality standards.

Author: Integrated with data generation enhancements
Date: 2025-11-23
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from datetime import datetime


import json

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.generic):
            return obj.item()
        return super(NumpyEncoder, self).default(obj)

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    return json.loads(json.dumps(obj, cls=NumpyEncoder))


class TemporalCorrelationValidator:
    """Validates temporal correlation in longitudinal data"""
    
    def __init__(self, expected_rho: float = 0.7, tolerance: float = 0.2):
        """
        Initialize validator
        
        Args:
            expected_rho: Expected autocorrelation (0.6-0.8 for vitals)
            tolerance: Acceptable deviation from expected
        """
        self.expected_rho = expected_rho
        self.tolerance = tolerance
    
    def validate(self, df: pd.DataFrame) -> Dict:
        """
        Validate temporal correlation in trial data
        
        Args:
            df: DataFrame with columns [SubjectID, VisitWeek, SystolicBP, ...]
            
        Returns:
            Validation results with metrics and pass/fail status
        """
        # Calculate lag-1 autocorrelation for each subject
        correlations = []
        subject_details = []
        
        for subject_id, subject_df in df.groupby('SubjectID'):
            subject_df = subject_df.sort_values('VisitWeek')
            
            if len(subject_df) < 2:
                continue
            
            sbp_values = subject_df['SystolicBP'].values
            
            # Lag-1 autocorrelation
            if len(sbp_values) >= 2:
                with np.errstate(invalid='ignore'):  # Suppress warnings for constant values
                    corr = np.corrcoef(sbp_values[:-1], sbp_values[1:])[0, 1]
                
                if not np.isnan(corr):
                    correlations.append(corr)
                    subject_details.append({
                        'subject_id': subject_id,
                        'correlation': float(corr),
                        'n_visits': len(sbp_values)
                    })
        
        # Calculate aggregate statistics
        if correlations:
            mean_rho = np.mean(correlations)
            std_rho = np.std(correlations)
            median_rho = np.median(correlations)
            
            # Determine pass/fail
            deviation = abs(mean_rho - self.expected_rho)
            passes = deviation < self.tolerance
            
            # Grade based on how close to expected
            if deviation < 0.1:
                grade = 'A'
            elif deviation < 0.2:
                grade = 'B'
            elif deviation < 0.3:
                grade = 'C'
            else:
                grade = 'D'
            
            return {
                'status': 'pass' if passes else 'fail',
                'grade': grade,
                'metrics': {
                    'mean_correlation': round(float(mean_rho), 3),
                    'std_correlation': round(float(std_rho), 3),
                    'median_correlation': round(float(median_rho), 3),
                    'expected_correlation': self.expected_rho,
                    'tolerance': self.tolerance,
                    'deviation': round(float(deviation), 3),
                    'n_subjects_analyzed': len(correlations)
                },
                'interpretation': self._interpret_correlation(mean_rho),
                'recommendations': self._generate_recommendations(mean_rho, passes),
                'subject_details': subject_details[:10]  # Top 10 for reference
            }
        else:
            return {
                'status': 'error',
                'message': 'Insufficient data for temporal correlation analysis',
                'metrics': {}
            }
    
    def _interpret_correlation(self, rho: float) -> str:
        """Interpret correlation value"""
        if rho > 0.7:
            return "Strong temporal correlation - excellent data quality"
        elif rho > 0.5:
            return "Moderate temporal correlation - acceptable for most analyses"
        elif rho > 0.3:
            return "Weak temporal correlation - may indicate data quality issues"
        else:
            return "Very weak correlation - data may be unreliable"
    
    def _generate_recommendations(self, rho: float, passes: bool) -> List[str]:
        """Generate recommendations based on results"""
        recs = []
        
        if not passes:
            recs.append("Correlation deviates from expected - verify data generation parameters")
        
        if rho < 0.3:
            recs.append("Very low correlation suggests possible data entry errors")
            recs.append("Review subject data for unexpected jumps in values")
        
        if rho > 0.9:
            recs.append("Extremely high correlation - verify temporal model parameters")
        
        if not recs:
            recs.append("Temporal correlation is within expected range")
        
        return recs


class HeterogeneousEffectsValidator:
    """Validates treatment effect heterogeneity"""
    
    def __init__(self, min_std: float = 2.0, max_std: float = 10.0):
        """
        Initialize validator
        
        Args:
            min_std: Minimum acceptable std of treatment effects
            max_std: Maximum acceptable std (above suggests issues)
        """
        self.min_std = min_std
        self.max_std = max_std
    
    def validate(self, df: pd.DataFrame) -> Dict:
        """
        Validate treatment effect heterogeneity
        
        Args:
            df: DataFrame with trial data
            
        Returns:
            Validation results
        """
        # Calculate change from baseline for each subject
        baseline_df = df[df['VisitWeek'] == df['VisitWeek'].min()].copy()
        final_df = df[df['VisitWeek'] == df['VisitWeek'].max()].copy()
        
        # Merge to get baseline and final
        effects_df = baseline_df[['SubjectID', 'SystolicBP', 'TreatmentArm']].rename(
            columns={'SystolicBP': 'baseline_sbp'}
        ).merge(
            final_df[['SubjectID', 'SystolicBP']].rename(columns={'SystolicBP': 'final_sbp'}),
            on='SubjectID'
        )
        
        effects_df['change'] = effects_df['final_sbp'] - effects_df['baseline_sbp']
        
        # Analyze by treatment arm
        results = {}
        
        for arm in effects_df['TreatmentArm'].unique():
            arm_data = effects_df[effects_df['TreatmentArm'] == arm]['change']
            
            if len(arm_data) > 0:
                mean_effect = arm_data.mean()
                std_effect = arm_data.std()
                
                # Classify responders
                responder_categories = self._classify_responders(
                    arm_data.values, mean_effect, std_effect
                )
                
                results[arm] = {
                    'mean_effect': round(float(mean_effect), 2),
                    'std_effect': round(float(std_effect), 2),
                    'min_effect': round(float(arm_data.min()), 2),
                    'max_effect': round(float(arm_data.max()), 2),
                    'median_effect': round(float(arm_data.median()), 2),
                    'n_subjects': len(arm_data),
                    'responder_distribution': responder_categories
                }
        
        # Overall validation
        if 'Active' in results:
            active_std = results['Active']['std_effect']
            
            passes = self.min_std <= active_std <= self.max_std
            
            if active_std < self.min_std:
                grade = 'D'
                interpretation = "Insufficient heterogeneity - effects too homogeneous"
            elif active_std > self.max_std:
                grade = 'C'
                interpretation = "Excessive heterogeneity - verify data quality"
            elif active_std < 3.0:
                grade = 'B'
                interpretation = "Moderate heterogeneity - acceptable"
            else:
                grade = 'A'
                interpretation = "Good heterogeneity - realistic variation"
            
            return {
                'status': 'pass' if passes else 'fail',
                'grade': grade,
                'metrics': results,
                'interpretation': interpretation,
                'recommendations': self._generate_recommendations(results),
                'heterogeneity_score': self._calculate_heterogeneity_score(active_std)
            }
        else:
            return {
                'status': 'error',
                'message': 'No Active arm found in data'
            }
    
    def _classify_responders(self, effects: np.ndarray, mean: float, std: float) -> Dict:
        """Classify subjects into responder categories"""
        threshold_low = mean - 0.5 * std
        threshold_high = mean + 0.5 * std
        
        super_responder = np.sum(effects < threshold_low)
        moderate = np.sum((effects >= threshold_low) & (effects <= threshold_high))
        non_responder = np.sum(effects > threshold_high)
        
        total = len(effects)
        
        return {
            'super_responder': {
                'count': int(super_responder),
                'percentage': round(float(super_responder / total * 100), 1)
            },
            'moderate': {
                'count': int(moderate),
                'percentage': round(float(moderate / total * 100), 1)
            },
            'non_responder': {
                'count': int(non_responder),
                'percentage': round(float(non_responder / total * 100), 1)
            }
        }
    
    def _calculate_heterogeneity_score(self, std: float) -> int:
        """Calculate 0-100 score for heterogeneity"""
        # Optimal std is around 3.0
        if 2.5 <= std <= 4.0:
            return 100
        elif 2.0 <= std <= 5.0:
            return 85
        elif 1.5 <= std <= 6.0:
            return 70
        else:
            return 50
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations"""
        recs = []
        
        if 'Active' in results:
            active_std = results['Active']['std_effect']
            
            if active_std < self.min_std:
                recs.append("Increase treatment effect heterogeneity in data generation")
                recs.append("Consider using heterogeneous treatment effect sampler")
            elif active_std > self.max_std:
                recs.append("Reduce treatment effect variance - may indicate outliers")
            else:
                recs.append("Treatment heterogeneity is realistic")
        
        return recs


class MissingnessValidator:
    """Validates missingness mechanism (MCAR vs MAR vs MNAR)"""
    
    def validate(self, df: pd.DataFrame) -> Dict:
        """
        Classify and validate missingness mechanism
        
        Args:
            df: DataFrame with dropout and predictor columns
            
        Returns:
            Classification and validation results
        """
        if 'dropout' not in df.columns:
            # Try to infer dropout from visit patterns
            if 'SubjectID' in df.columns and 'VisitWeek' in df.columns:
                # Calculate if subjects have missing visits
                max_visits = df.groupby('SubjectID')['VisitWeek'].count().max()
                subject_visits = df.groupby('SubjectID')['VisitWeek'].count()
                df = df.copy()
                df['dropout'] = df['SubjectID'].map(lambda sid: bool(subject_visits.get(sid, 0) < max_visits))
            else:
                result = {
                    'status': 'error',
                    'message': 'No dropout column found and cannot infer from visit patterns'
                }
                return convert_numpy_types(result)
        
        # Test for MAR associations
        mar_tests = {}
        has_any_test = False
        
        # Test 1: Association with adverse events (if available)
        if 'has_severe_ae' in df.columns:
            try:
                dropout_with_ae = df[df['has_severe_ae'] == True]['dropout'].mean()
                dropout_without_ae = df[df['has_severe_ae'] == False]['dropout'].mean()
                
                diff = dropout_with_ae - dropout_without_ae
                
                # Chi-square test
                contingency = pd.crosstab(df['has_severe_ae'], df['dropout'])
                chi2, p_value, _, _ = stats.chi2_contingency(contingency)
                
                mar_tests['adverse_events'] = {
                    'dropout_with_ae': round(float(dropout_with_ae), 3),
                    'dropout_without_ae': round(float(dropout_without_ae), 3),
                    'difference': round(float(diff), 3),
                    'chi2_statistic': round(float(chi2), 3),
                    'p_value': round(float(p_value), 4),
                    'significant': bool(p_value < 0.05)
                }
                has_any_test = True
            except Exception as e:
                mar_tests['adverse_events'] = {'error': str(e)}
        
        # Test 2: Association with treatment arm (if available)
        if 'TreatmentArm' in df.columns:
            try:
                arm_dropout = df.groupby('TreatmentArm')['dropout'].mean()
                
                mar_tests['treatment_arm'] = {
                    arm: round(float(rate), 3) 
                    for arm, rate in arm_dropout.items()
                }
                has_any_test = True
            except Exception as e:
                mar_tests['treatment_arm'] = {'error': str(e)}
        
        # Test 3: Association with vitals (check first visit)
        if 'VisitWeek' in df.columns and 'SystolicBP' in df.columns:
            try:
                baseline_df = df[df['VisitWeek'] == df['VisitWeek'].min()].copy()
                if len(baseline_df) > 0:
                    # Split by median SBP
                    median_sbp = baseline_df['SystolicBP'].median()
                    baseline_df['high_sbp'] = baseline_df['SystolicBP'] > median_sbp
                    
                    dropout_high_sbp = baseline_df[baseline_df['high_sbp'] == True]['dropout'].mean()
                    dropout_low_sbp = baseline_df[baseline_df['high_sbp'] == False]['dropout'].mean()
                    
                    mar_tests['baseline_vitals'] = {
                        'dropout_high_sbp': round(float(dropout_high_sbp), 3),
                        'dropout_low_sbp': round(float(dropout_low_sbp), 3),
                        'difference': round(float(dropout_high_sbp - dropout_low_sbp), 3)
                    }
                    has_any_test = True
            except Exception as e:
                mar_tests['baseline_vitals'] = {'error': str(e)}
        
        # If no tests could be performed
        if not has_any_test:
            result = {
                'status': 'insufficient_data',
                'classification': 'UNKNOWN',
                'mar_tests': mar_tests,
                'interpretation': 'Insufficient data to classify missingness mechanism',
                'recommendations': ['Add predictor columns (has_severe_ae, TreatmentArm) to enable MAR testing']
            }
            return convert_numpy_types(result)
        
        # Classify mechanism
        classification = self._classify_mechanism(mar_tests)
        
        result = {
            'status': 'success',
            'classification': classification,
            'mar_tests': mar_tests,
            'interpretation': self._interpret_mechanism(classification),
            'recommendations': self._generate_mar_recommendations(classification)
        }
        
        # Convert all numpy types before returning
        return convert_numpy_types(result)
    
    def _classify_mechanism(self, tests: Dict) -> str:
        """Classify missingness mechanism based on tests"""
        significant_associations = 0
        
        if 'adverse_events' in tests and 'error' not in tests['adverse_events']:
            if tests['adverse_events'].get('significant', False) and \
               tests['adverse_events'].get('difference', 0) > 0.10:
                significant_associations += 1
        
        if 'baseline_vitals' in tests and 'error' not in tests['baseline_vitals']:
            if abs(tests['baseline_vitals'].get('difference', 0)) > 0.10:
                significant_associations += 1
        
        if significant_associations >= 2:
            return 'MAR'
        elif significant_associations == 1:
            return 'MAR (weak)'
        else:
            return 'MCAR'
    
    def _interpret_mechanism(self, classification: str) -> str:
        """Interpret mechanism classification"""
        interpretations = {
            'MCAR': "Missing Completely At Random - dropout independent of observed/unobserved data",
            'MAR (weak)': "Likely MAR with weak associations - some dropout related to observed data",
            'MAR': "Missing At Random - dropout depends on observed data (realistic)",
            'MNAR': "Missing Not At Random - dropout depends on unobserved factors",
            'UNKNOWN': "Cannot classify - insufficient predictor data"
        }
        return interpretations.get(classification, "Unknown mechanism")
    
    def _generate_mar_recommendations(self, classification: str) -> List[str]:
        """Generate recommendations based on mechanism"""
        if classification == 'MCAR':
            return [
                "Data shows MCAR pattern - unrealistic for clinical trials",
                "Consider using MAR or MNAR missingness in data generation",
                "Real trials typically show MAR dropout (correlated with AEs, vitals)"
            ]
        elif classification in ['MAR', 'MAR (weak)']:
           return [
                "Realistic MAR pattern detected",
                "Dropout appropriately correlated with observed data",
                "Suitable for most imputation and analysis methods"
            ]
        elif classification == 'UNKNOWN':
            return [
                "Add predictor columns to enable missingness classification",
                "Recommended columns: has_severe_ae, baseline vitals"
            ]
        else:
            return ["Mechanism classification uncertain - review data"]


def validate_comprehensive(df: pd.DataFrame) -> Dict:
    """
    Run all enhanced validations
    
    Args:
        df: Trial DataFrame
        
    Returns:
        Comprehensive validation results
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'n_subjects': df['SubjectID'].nunique() if 'SubjectID' in df.columns else 0,
        'n_measurements': len(df),
        'validations': {}
    }
    
    # Validation 1: Temporal Correlation
    temporal_validator = TemporalCorrelationValidator()
    results['validations']['temporal_correlation'] = temporal_validator.validate(df)
    
    # Validation 2: Heterogeneous Effects
    heterogeneity_validator = HeterogeneousEffectsValidator()
    results['validations']['heterogeneous_effects'] = heterogeneity_validator.validate(df)
    
    # Validation 3: Missingness Mechanism
    missingness_validator = MissingnessValidator()
    results['validations']['missingness'] = missingness_validator.validate(df)
    
    # Calculate overall score
    scores = []
    if results['validations']['temporal_correlation']['status'] == 'pass':
        scores.append(100 if results['validations']['temporal_correlation']['grade'] == 'A' else 85)
    
    if results['validations']['heterogeneous_effects']['status'] == 'pass':
        scores.append(results['validations']['heterogeneous_effects']['heterogeneity_score'])
    
    if results['validations']['missingness'].get('classification') in ['MAR', 'MAR (weak)']:
        scores.append(90)
    elif results['validations']['missingness'].get('classification') == 'MCAR':
        scores.append(60)
    
    overall_score = np.mean(scores) if scores else 0
    
    results['overall'] = {
        'score': round(float(overall_score), 1),
        'grade': 'A' if overall_score >= 85 else 'B' if overall_score >= 75 else 'C' if overall_score >= 65 else 'D',
        'summary': f"Data quality: {overall_score:.0f}/100"
    }
    
    # Convert all numpy types to native Python types for JSON serialization
    return convert_numpy_types(results)
