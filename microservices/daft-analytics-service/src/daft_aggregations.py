"""
Daft Aggregations Module - Statistical aggregations and groupby operations
Provides comprehensive aggregation capabilities for medical data analysis
"""
import daft
from daft import col
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test


class DaftAggregator:
    """
    Aggregation engine for medical data using Daft
    Supports groupby, statistical aggregations, and clinical trial analytics
    """

    def __init__(self, df: daft.DataFrame):
        """
        Initialize aggregator with a Daft DataFrame

        Args:
            df: Daft DataFrame to aggregate
        """
        self.df = df

    def groupby_treatment_arm(self) -> Dict[str, Any]:
        """
        Group data by treatment arm and compute comprehensive statistics

        Returns:
            Dictionary with statistics by treatment arm
        """
        # Convert to pandas for complex aggregations
        pdf = self.df.to_pandas()

        results = {}
        for arm in pdf['TreatmentArm'].unique():
            arm_data = pdf[pdf['TreatmentArm'] == arm]
            results[arm] = {
                'n': len(arm_data),
                'vitals': {
                    'SystolicBP': {
                        'mean': float(arm_data['SystolicBP'].mean()),
                        'std': float(arm_data['SystolicBP'].std()),
                        'min': float(arm_data['SystolicBP'].min()),
                        'max': float(arm_data['SystolicBP'].max()),
                        'median': float(arm_data['SystolicBP'].median()),
                        'q25': float(arm_data['SystolicBP'].quantile(0.25)),
                        'q75': float(arm_data['SystolicBP'].quantile(0.75))
                    },
                    'DiastolicBP': {
                        'mean': float(arm_data['DiastolicBP'].mean()),
                        'std': float(arm_data['DiastolicBP'].std()),
                        'min': float(arm_data['DiastolicBP'].min()),
                        'max': float(arm_data['DiastolicBP'].max()),
                        'median': float(arm_data['DiastolicBP'].median()),
                        'q25': float(arm_data['DiastolicBP'].quantile(0.25)),
                        'q75': float(arm_data['DiastolicBP'].quantile(0.75))
                    },
                    'HeartRate': {
                        'mean': float(arm_data['HeartRate'].mean()),
                        'std': float(arm_data['HeartRate'].std()),
                        'min': float(arm_data['HeartRate'].min()),
                        'max': float(arm_data['HeartRate'].max()),
                        'median': float(arm_data['HeartRate'].median()),
                        'q25': float(arm_data['HeartRate'].quantile(0.25)),
                        'q75': float(arm_data['HeartRate'].quantile(0.75))
                    },
                    'Temperature': {
                        'mean': float(arm_data['Temperature'].mean()),
                        'std': float(arm_data['Temperature'].std()),
                        'min': float(arm_data['Temperature'].min()),
                        'max': float(arm_data['Temperature'].max()),
                        'median': float(arm_data['Temperature'].median()),
                        'q25': float(arm_data['Temperature'].quantile(0.25)),
                        'q75': float(arm_data['Temperature'].quantile(0.75))
                    }
                }
            }

        return results

    def groupby_visit(self) -> Dict[str, Any]:
        """
        Group data by visit and compute statistics

        Returns:
            Dictionary with statistics by visit
        """
        pdf = self.df.to_pandas()

        results = {}
        for visit in pdf['VisitName'].unique():
            visit_data = pdf[pdf['VisitName'] == visit]
            results[visit] = {
                'n': len(visit_data),
                'mean_systolic': float(visit_data['SystolicBP'].mean()),
                'mean_diastolic': float(visit_data['DiastolicBP'].mean()),
                'mean_heartrate': float(visit_data['HeartRate'].mean()),
                'mean_temperature': float(visit_data['Temperature'].mean())
            }

        return results

    def groupby_subject(self) -> Dict[str, Any]:
        """
        Group data by subject and compute subject-level statistics

        Returns:
            Dictionary with statistics by subject
        """
        pdf = self.df.to_pandas()

        results = {}
        for subject in pdf['SubjectID'].unique():
            subject_data = pdf[pdf['SubjectID'] == subject]
            results[subject] = {
                'treatment_arm': subject_data['TreatmentArm'].iloc[0] if len(subject_data) > 0 else None,
                'visit_count': len(subject_data),
                'baseline_systolic': float(subject_data[subject_data['VisitName'] == 'Screening']['SystolicBP'].iloc[0]) if 'Screening' in subject_data['VisitName'].values else None,
                'mean_systolic': float(subject_data['SystolicBP'].mean()),
                'systolic_change': None  # Will be computed if baseline exists
            }

            # Compute change from baseline if baseline exists
            if results[subject]['baseline_systolic'] is not None:
                week12_data = subject_data[subject_data['VisitName'] == 'Week 12']
                if len(week12_data) > 0:
                    week12_systolic = float(week12_data['SystolicBP'].iloc[0])
                    results[subject]['systolic_change'] = week12_systolic - results[subject]['baseline_systolic']

        return results

    def compute_treatment_effect(self, endpoint: str = 'SystolicBP', visit: str = 'Week 12') -> Dict[str, Any]:
        """
        Compute treatment effect with statistical testing

        Args:
            endpoint: Vital sign to analyze (default: SystolicBP)
            visit: Visit to analyze (default: Week 12)

        Returns:
            Dictionary with treatment effect statistics
        """
        pdf = self.df.to_pandas()

        # Filter by visit
        visit_data = pdf[pdf['VisitName'] == visit]

        # Split by treatment arm
        active = visit_data[visit_data['TreatmentArm'] == 'Active'][endpoint]
        placebo = visit_data[visit_data['TreatmentArm'] == 'Placebo'][endpoint]

        # Check for sufficient data
        if len(active) < 2 or len(placebo) < 2:
            raise ValueError(f"Insufficient data for analysis. Need at least 2 subjects per arm. Found Active: {len(active)}, Placebo: {len(placebo)}")

        # Compute statistics with NaN handling
        active_mean = float(active.mean()) if not np.isnan(active.mean()) else 0.0
        placebo_mean = float(placebo.mean()) if not np.isnan(placebo.mean()) else 0.0
        mean_diff = active_mean - placebo_mean

        active_std = float(active.std()) if not np.isnan(active.std()) else 0.0
        placebo_std = float(placebo.std()) if not np.isnan(placebo.std()) else 0.0

        se_active = active_std / np.sqrt(len(active))
        se_placebo = placebo_std / np.sqrt(len(placebo))
        se_diff = float(np.sqrt(se_active**2 + se_placebo**2))

        # T-test
        try:
            t_stat, p_value = stats.ttest_ind(active, placebo)
            t_stat = float(t_stat) if not np.isnan(t_stat) and not np.isinf(t_stat) else 0.0
            p_value = float(p_value) if not np.isnan(p_value) and not np.isinf(p_value) else 1.0
        except Exception:
            t_stat, p_value = 0.0, 1.0

        # Confidence interval
        ci_95_lower = mean_diff - 1.96 * se_diff
        ci_95_upper = mean_diff + 1.96 * se_diff

        return {
            'endpoint': endpoint,
            'visit': visit,
            'active': {
                'n': int(len(active)),
                'mean': active_mean,
                'std': active_std,
                'se': float(se_active)
            },
            'placebo': {
                'n': int(len(placebo)),
                'mean': placebo_mean,
                'std': placebo_std,
                'se': float(se_placebo)
            },
            'treatment_effect': {
                'difference': float(mean_diff),
                'se_difference': float(se_diff),
                't_statistic': t_stat,
                'p_value': p_value,
                'ci_95_lower': float(ci_95_lower),
                'ci_95_upper': float(ci_95_upper),
                'significant': bool(p_value < 0.05)
            }
        }

    def compute_change_from_baseline(self) -> pd.DataFrame:
        """
        Compute change from baseline for each subject

        Returns:
            Pandas DataFrame with change from baseline
        """
        pdf = self.df.to_pandas()

        # Get baseline values (Screening visit)
        baseline = pdf[pdf['VisitName'] == 'Screening'][['SubjectID', 'SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']]
        baseline = baseline.rename(columns={
            'SystolicBP': 'BaselineSystolicBP',
            'DiastolicBP': 'BaselineDiastolicBP',
            'HeartRate': 'BaselineHeartRate',
            'Temperature': 'BaselineTemperature'
        })

        # Merge with full data
        merged = pdf.merge(baseline, on='SubjectID', how='left')

        # Compute changes
        merged['ChangeSystolicBP'] = merged['SystolicBP'] - merged['BaselineSystolicBP']
        merged['ChangeDiastolicBP'] = merged['DiastolicBP'] - merged['BaselineDiastolicBP']
        merged['ChangeHeartRate'] = merged['HeartRate'] - merged['BaselineHeartRate']
        merged['ChangeTemperature'] = merged['Temperature'] - merged['BaselineTemperature']

        return merged

    def compute_longitudinal_summary(self) -> Dict[str, Any]:
        """
        Compute longitudinal summary statistics across all visits

        Returns:
            Dictionary with longitudinal statistics
        """
        pdf = self.df.to_pandas()

        # Get visit order
        visit_order = ['Screening', 'Day 1', 'Week 4', 'Week 12']
        visits = [v for v in visit_order if v in pdf['VisitName'].unique()]

        results = {
            'visits': visits,
            'by_arm': {}
        }

        for arm in pdf['TreatmentArm'].unique():
            arm_data = pdf[pdf['TreatmentArm'] == arm]
            results['by_arm'][arm] = {
                'trajectories': {
                    'SystolicBP': [],
                    'DiastolicBP': [],
                    'HeartRate': [],
                    'Temperature': []
                }
            }

            for visit in visits:
                visit_data = arm_data[arm_data['VisitName'] == visit]
                results['by_arm'][arm]['trajectories']['SystolicBP'].append({
                    'visit': visit,
                    'mean': float(visit_data['SystolicBP'].mean()),
                    'se': float(visit_data['SystolicBP'].std() / np.sqrt(len(visit_data)))
                })
                results['by_arm'][arm]['trajectories']['DiastolicBP'].append({
                    'visit': visit,
                    'mean': float(visit_data['DiastolicBP'].mean()),
                    'se': float(visit_data['DiastolicBP'].std() / np.sqrt(len(visit_data)))
                })
                results['by_arm'][arm]['trajectories']['HeartRate'].append({
                    'visit': visit,
                    'mean': float(visit_data['HeartRate'].mean()),
                    'se': float(visit_data['HeartRate'].std() / np.sqrt(len(visit_data)))
                })
                results['by_arm'][arm]['trajectories']['Temperature'].append({
                    'visit': visit,
                    'mean': float(visit_data['Temperature'].mean()),
                    'se': float(visit_data['Temperature'].std() / np.sqrt(len(visit_data)))
                })

        return results

    def compute_correlation_matrix(self) -> Dict[str, Any]:
        """
        Compute correlation matrix for vital signs

        Returns:
            Dictionary with correlation matrix
        """
        pdf = self.df.to_pandas()

        # Select numeric columns
        numeric_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
        corr_matrix = pdf[numeric_cols].corr()

        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'variables': numeric_cols
        }

    def compute_percentile_rank(self, column: str = 'SystolicBP') -> pd.DataFrame:
        """
        Compute percentile rank for a given column

        Args:
            column: Column name to compute percentile for

        Returns:
            Pandas DataFrame with percentile ranks
        """
        pdf = self.df.to_pandas()
        pdf[f'{column}_Percentile'] = pdf[column].rank(pct=True) * 100
        return pdf

    def compute_outliers(self, column: str = 'SystolicBP', method: str = 'iqr') -> Dict[str, Any]:
        """
        Detect outliers using IQR or Z-score method

        Args:
            column: Column to check for outliers
            method: 'iqr' or 'zscore'

        Returns:
            Dictionary with outlier information
        """
        pdf = self.df.to_pandas()

        if method == 'iqr':
            Q1 = pdf[column].quantile(0.25)
            Q3 = pdf[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = pdf[(pdf[column] < lower_bound) | (pdf[column] > upper_bound)]

            return {
                'method': 'iqr',
                'column': column,
                'bounds': {
                    'lower': float(lower_bound),
                    'upper': float(upper_bound),
                    'q1': float(Q1),
                    'q3': float(Q3),
                    'iqr': float(IQR)
                },
                'outlier_count': len(outliers),
                'outlier_percentage': float(len(outliers) / len(pdf) * 100),
                'outliers': outliers.to_dict('records')
            }

        elif method == 'zscore':
            mean = pdf[column].mean()
            std = pdf[column].std()
            z_scores = np.abs((pdf[column] - mean) / std)
            outliers = pdf[z_scores > 3]

            return {
                'method': 'zscore',
                'column': column,
                'threshold': 3,
                'statistics': {
                    'mean': float(mean),
                    'std': float(std)
                },
                'outlier_count': len(outliers),
                'outlier_percentage': float(len(outliers) / len(pdf) * 100),
                'outliers': outliers.to_dict('records')
            }

    def compute_responder_analysis(self, threshold: float = -10.0, endpoint: str = 'SystolicBP') -> Dict[str, Any]:
        """
        Compute responder analysis (subjects achieving a threshold change)

        Args:
            threshold: Threshold for response (e.g., -10 mmHg reduction)
            endpoint: Vital sign to analyze

        Returns:
            Dictionary with responder analysis
        """
        # Compute change from baseline
        change_df = self.compute_change_from_baseline()

        results = {}
        for arm in change_df['TreatmentArm'].unique():
            arm_data = change_df[change_df['TreatmentArm'] == arm]
            week12_data = arm_data[arm_data['VisitName'] == 'Week 12']

            change_col = f'Change{endpoint}'
            if change_col in week12_data.columns:
                responders = week12_data[week12_data[change_col] <= threshold]
                response_rate = len(responders) / len(week12_data) if len(week12_data) > 0 else 0

                results[arm] = {
                    'n': len(week12_data),
                    'responders': len(responders),
                    'response_rate': float(response_rate),
                    'response_percentage': float(response_rate * 100)
                }

        # Compute difference in response rates
        if 'Active' in results and 'Placebo' in results:
            results['difference'] = {
                'absolute_difference': float(results['Active']['response_rate'] - results['Placebo']['response_rate']),
                'relative_risk': float(results['Active']['response_rate'] / results['Placebo']['response_rate']) if results['Placebo']['response_rate'] > 0 else None
            }

        return results

    def compute_time_to_effect(self, threshold: float = -5.0, endpoint: str = 'SystolicBP') -> Dict[str, Any]:
        """
        Analyze when treatment effect becomes significant over time

        Args:
            threshold: Threshold for meaningful change
            endpoint: Vital sign to analyze

        Returns:
            Dictionary with time-to-effect analysis
        """
        pdf = self.df.to_pandas()
        visit_order = ['Screening', 'Day 1', 'Week 4', 'Week 12']

        results = {
            'visits': [],
            'treatment_effect_by_visit': []
        }

        for visit in visit_order:
            if visit == 'Screening':
                continue  # Skip baseline

            visit_data = pdf[pdf['VisitName'] == visit]
            if len(visit_data) == 0:
                continue

            active = visit_data[visit_data['TreatmentArm'] == 'Active'][endpoint]
            placebo = visit_data[visit_data['TreatmentArm'] == 'Placebo'][endpoint]

            if len(active) > 0 and len(placebo) > 0:
                mean_diff = float(active.mean() - placebo.mean())
                t_stat, p_value = stats.ttest_ind(active, placebo)

                results['visits'].append(visit)
                results['treatment_effect_by_visit'].append({
                    'visit': visit,
                    'difference': mean_diff,
                    'p_value': float(p_value),
                    'significant': p_value < 0.05,
                    'meets_threshold': mean_diff <= threshold
                })

        return results

    def compute_kaplan_meier(self, time_col: str = 'Time', event_col: str = 'Event', group_col: str = 'TreatmentArm') -> Dict[str, Any]:
        """
        Compute Kaplan-Meier survival estimates

        Args:
            time_col: Column containing time to event
            event_col: Column containing event status (1=event, 0=censored)
            group_col: Column to group by (e.g., TreatmentArm)

        Returns:
            Dictionary with Kaplan-Meier estimates by group
        """
        pdf = self.df.to_pandas()
        kmf = KaplanMeierFitter()
        
        results = {}
        
        # Get unique groups
        groups = pdf[group_col].unique()
        
        for group in groups:
            mask = (pdf[group_col] == group)
            group_data = pdf[mask]
            
            if len(group_data) > 0:
                kmf.fit(group_data[time_col], group_data[event_col], label=str(group))
                
                # Get survival table
                # survival_function_ returns a dataframe with time as index
                timeline = kmf.timeline.tolist()
                survival_probs = kmf.survival_function_[str(group)].tolist()
                
                # Confidence intervals
                ci = kmf.confidence_interval_
                ci_lower = ci[f'{group}_lower_0.95'].tolist()
                ci_upper = ci[f'{group}_upper_0.95'].tolist()
                
                data_points = []
                for t, s, l, u in zip(timeline, survival_probs, ci_lower, ci_upper):
                    data_points.append({
                        'time': float(t),
                        'survival_prob': float(s),
                        'ci_lower': float(l),
                        'ci_upper': float(u)
                    })
                
                results[str(group)] = {
                    'median_survival_time': float(kmf.median_survival_time_) if not np.isinf(kmf.median_survival_time_) else None,
                    'curve': data_points
                }
                
        return results

    def compute_log_rank_test(self, time_col: str = 'Time', event_col: str = 'Event', group_col: str = 'TreatmentArm', group1: str = 'Active', group2: str = 'Placebo') -> Dict[str, Any]:
        """
        Compute Log-Rank test between two groups

        Args:
            time_col: Column containing time to event
            event_col: Column containing event status
            group_col: Column to group by
            group1: Name of first group
            group2: Name of second group

        Returns:
            Dictionary with Log-Rank test results
        """
        pdf = self.df.to_pandas()
        
        mask1 = (pdf[group_col] == group1)
        mask2 = (pdf[group_col] == group2)
        
        data1 = pdf[mask1]
        data2 = pdf[mask2]
        
        if len(data1) == 0 or len(data2) == 0:
            return {
                'test_statistic': None,
                'p_value': None,
                'significant': False,
                'message': 'Insufficient data for one or both groups'
            }
            
        results = logrank_test(
            data1[time_col], data2[time_col],
            event_observed_A=data1[event_col], event_observed_B=data2[event_col]
        )
        
        return {
            'test_statistic': float(results.test_statistic),
            'p_value': float(results.p_value),
            'significant': bool(results.p_value < 0.05),
            'group1': group1,
            'group2': group2
        }
