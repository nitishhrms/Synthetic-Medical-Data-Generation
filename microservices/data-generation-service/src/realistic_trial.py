"""
Realistic Trial Generator - Enhanced synthetic data with real-world patterns

This module generates clinical trial data with realistic imperfections:
- Variable enrollment dates (not all on Day 1)
- Site-specific baseline characteristics
- Missing data (MCAR, MAR patterns)
- Dropout/withdrawal scenarios
- Protocol deviations
- Visit window violations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from scipy import stats


class RealisticTrialGenerator:
    """
    Generates realistic clinical trial data with imperfections and patterns
    found in real studies
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.seed = seed

    def generate_enrollment_schedule(
        self,
        n_subjects: int,
        duration_months: int = 12,
        pattern: str = "linear"
    ) -> List[datetime]:
        """
        Generate realistic enrollment dates

        Args:
            n_subjects: Total number of subjects to enroll
            duration_months: Enrollment duration
            pattern: 'linear', 'exponential', or 'seasonal'

        Returns:
            List of enrollment dates
        """
        start_date = datetime(2024, 1, 1)

        if pattern == "linear":
            # Uniform enrollment over time
            days = np.linspace(0, duration_months * 30, n_subjects)

        elif pattern == "exponential":
            # Slow start, accelerating enrollment (realistic for multi-site)
            x = np.linspace(0, 1, n_subjects)
            days = (np.exp(2 * x) - 1) / (np.exp(2) - 1) * duration_months * 30

        elif pattern == "seasonal":
            # Seasonal variation (holidays, summer slowdowns)
            base_days = np.linspace(0, duration_months * 30, n_subjects)
            # Add sinusoidal variation
            seasonal_effect = 10 * np.sin(2 * np.pi * base_days / 365)
            days = base_days + seasonal_effect

        else:
            days = np.linspace(0, duration_months * 30, n_subjects)

        # Add random jitter (±3 days)
        days = days + self.rng.normal(0, 3, n_subjects)
        days = np.clip(days, 0, duration_months * 30)

        enrollment_dates = [start_date + timedelta(days=int(d)) for d in days]
        return enrollment_dates

    def assign_to_sites(
        self,
        n_subjects: int,
        n_sites: int,
        heterogeneity: float = 0.3
    ) -> np.ndarray:
        """
        Assign subjects to sites with realistic uneven distribution

        Args:
            n_subjects: Number of subjects
            n_sites: Number of sites
            heterogeneity: 0-1, how uneven the distribution (0=uniform, 1=very skewed)

        Returns:
            Array of site IDs for each subject
        """
        if heterogeneity == 0:
            # Uniform distribution
            return self.rng.integers(1, n_sites + 1, n_subjects)

        # Use Dirichlet distribution for realistic site sizes
        # Higher heterogeneity = more uneven distribution
        alpha = np.ones(n_sites) * (1 / heterogeneity)
        site_probabilities = self.rng.dirichlet(alpha)

        # Assign subjects based on probabilities
        site_ids = self.rng.choice(range(1, n_sites + 1), size=n_subjects, p=site_probabilities)

        return site_ids

    def generate_site_effects(self, n_sites: int) -> Dict[int, Dict[str, float]]:
        """
        Generate site-specific baseline effects

        Different sites have different:
        - Baseline vital signs (population differences)
        - Treatment response (site quality, adherence)
        - Dropout rates
        """
        site_effects = {}

        for site_id in range(1, n_sites + 1):
            site_effects[site_id] = {
                'baseline_sbp_shift': self.rng.normal(0, 5),  # ±5 mmHg site variation
                'baseline_dbp_shift': self.rng.normal(0, 3),  # ±3 mmHg
                'baseline_hr_shift': self.rng.normal(0, 4),   # ±4 bpm
                'treatment_response_factor': self.rng.normal(1.0, 0.2),  # 80-120% of avg response
                'dropout_rate_modifier': self.rng.uniform(0.8, 1.3),  # Site-specific dropout
                'data_quality': self.rng.uniform(0.85, 0.99),  # Missing data varies by site
            }

        return site_effects

    def generate_subject_trajectory(
        self,
        subject_id: str,
        treatment_arm: str,
        site_id: int,
        site_effect: Dict[str, float],
        enrollment_date: datetime,
        target_effect: float = -5.0,
        dropout_prob: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Generate complete trajectory for one subject across all visits

        Includes:
        - Realistic progression over time
        - Site-specific effects
        - Potential dropout
        - Missing data
        """
        visits = ["Screening", "Day 1", "Week 4", "Week 12"]
        visit_days = [0, 1, 28, 84]  # Days from enrollment

        # Subject baseline characteristics (individual variation)
        baseline_sbp = self.rng.normal(140, 12) + site_effect['baseline_sbp_shift']
        baseline_dbp = self.rng.normal(85, 8) + site_effect['baseline_dbp_shift']
        baseline_hr = self.rng.normal(75, 10) + site_effect['baseline_hr_shift']

        # Individual response to treatment (some respond more than others)
        individual_response = self.rng.normal(1.0, 0.3)

        # Check if subject drops out (and when)
        dropout = self.rng.random() < dropout_prob
        dropout_visit = self.rng.choice([1, 2, 3]) if dropout else None

        trajectory = []

        for visit_idx, (visit_name, days_from_enrollment) in enumerate(zip(visits, visit_days)):
            # Check if subject has dropped out
            if dropout and visit_idx >= dropout_visit:
                break  # No more visits after dropout

            visit_date = enrollment_date + timedelta(days=days_from_enrollment)

            # Add visit window violation (realistic - not everyone comes on exact day)
            actual_days = days_from_enrollment + self.rng.integers(-3, 4)

            # Calculate expected vitals at this timepoint
            if treatment_arm == "Active":
                # Treatment effect increases over time
                time_factor = min(actual_days / 84, 1.0)  # Max effect at Week 12
                treatment_effect = target_effect * time_factor * individual_response * site_effect['treatment_response_factor']
            else:
                treatment_effect = 0

            # Natural variation over time (regression to mean, measurement error)
            time_noise = self.rng.normal(0, 3)

            sbp = baseline_sbp + treatment_effect + time_noise
            dbp = baseline_dbp + (treatment_effect * 0.5) + time_noise * 0.7
            hr = baseline_hr + self.rng.normal(0, 5)
            temp = self.rng.normal(36.8, 0.3)

            # Clip to realistic ranges
            sbp = int(np.clip(sbp, 95, 200))
            dbp = int(np.clip(dbp, 55, 130))
            hr = int(np.clip(hr, 50, 120))
            temp = round(np.clip(temp, 35.0, 40.0), 1)

            record = {
                'SubjectID': subject_id,
                'VisitName': visit_name,
                'VisitDate': visit_date.strftime('%Y-%m-%d'),
                'DaysFromEnrollment': actual_days,
                'TreatmentArm': treatment_arm,
                'SiteID': f"Site{site_id:03d}",
                'SystolicBP': sbp,
                'DiastolicBP': dbp,
                'HeartRate': hr,
                'Temperature': temp,
                'Dropout': dropout,
                'DropoutVisit': dropout_visit if dropout else None
            }

            trajectory.append(record)

        return trajectory

    def introduce_missing_data(
        self,
        df: pd.DataFrame,
        rate: float = 0.08,
        pattern: str = "MAR"
    ) -> pd.DataFrame:
        """
        Introduce realistic missing data patterns

        Args:
            df: Complete dataset
            rate: Overall missing data rate
            pattern: 'MCAR' (completely random) or 'MAR' (missing at random, but correlated)
        """
        df = df.copy()
        n_records = len(df)
        n_to_drop = int(n_records * rate)

        if pattern == "MCAR":
            # Completely random missing
            vitals_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
            for col in vitals_cols:
                missing_indices = self.rng.choice(df.index, size=n_to_drop // 4, replace=False)
                df.loc[missing_indices, col] = np.nan

        elif pattern == "MAR":
            # Missing at random but correlated with other variables
            # E.g., later visits more likely to have missing data
            # Subjects with high BP more likely to miss visits

            visit_weights = {
                'Screening': 0.5,  # Less missing at screening
                'Day 1': 0.8,
                'Week 4': 1.0,
                'Week 12': 1.5   # More missing at later visits
            }

            for idx, row in df.iterrows():
                visit_weight = visit_weights.get(row['VisitName'], 1.0)

                # Probability of missing data increases with visit number
                if self.rng.random() < (rate * visit_weight):
                    # Randomly select which vital to make missing
                    missing_col = self.rng.choice(['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature'])
                    df.loc[idx, missing_col] = np.nan

        return df

    def generate_protocol_deviations(
        self,
        df: pd.DataFrame,
        deviation_rate: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Generate realistic protocol deviations

        Types:
        - Visit window violations (outside ±7 days)
        - Missed visits
        - Inclusion/exclusion violations
        - Consent issues
        """
        deviations = []

        n_deviations = int(len(df) * deviation_rate)

        deviation_types = [
            'Visit window violation',
            'Missed visit',
            'Inclusion criteria violation',
            'Consent form issue',
            'Medication non-compliance'
        ]

        severity_levels = ['Minor', 'Moderate', 'Major']

        for _ in range(n_deviations):
            random_record = df.sample(1, random_state=self.seed).iloc[0]

            deviation = {
                'SubjectID': random_record['SubjectID'],
                'VisitName': random_record['VisitName'],
                'SiteID': random_record['SiteID'],
                'DeviationType': self.rng.choice(deviation_types),
                'Severity': self.rng.choice(severity_levels, p=[0.6, 0.3, 0.1]),
                'Description': self._generate_deviation_description(),
                'DateIdentified': random_record['VisitDate']
            }

            deviations.append(deviation)

        return deviations

    def _generate_deviation_description(self) -> str:
        """Generate realistic deviation description"""
        descriptions = [
            "Visit conducted outside protocol-specified window",
            "Subject did not fast prior to blood draw",
            "Vital signs taken in standing position instead of seated",
            "Consent form missing investigator signature",
            "Subject took prohibited medication",
            "Laboratory sample collected outside time window"
        ]
        return self.rng.choice(descriptions)

    def generate_correlated_aes(
        self,
        vitals_df: pd.DataFrame,
        correlation_strength: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Generate adverse events correlated with vitals patterns

        E.g., high BP → headache, low HR → fatigue
        """
        aes = []

        ae_terms = {
            'high_bp': ['Headache', 'Dizziness', 'Epistaxis'],
            'low_bp': ['Fatigue', 'Lightheadedness', 'Syncope'],
            'fever': ['Pyrexia', 'Chills', 'Malaise'],
            'general': ['Nausea', 'Insomnia', 'Back pain', 'Arthralgia']
        }

        severity_levels = ['Mild', 'Moderate', 'Severe']
        causality_levels = ['Unrelated', 'Unlikely', 'Possible', 'Probable', 'Definite']

        for subject_id in vitals_df['SubjectID'].unique():
            subject_data = vitals_df[vitals_df['SubjectID'] == subject_id]

            # Check for triggers
            high_bp_count = (subject_data['SystolicBP'] > 160).sum()
            fever_count = (subject_data['Temperature'] > 38.0).sum()

            # Generate AEs based on triggers
            if high_bp_count > 0 and self.rng.random() < correlation_strength:
                ae_term = self.rng.choice(ae_terms['high_bp'])
                aes.append({
                    'SubjectID': subject_id,
                    'AE_Term': ae_term,
                    'Severity': self.rng.choice(severity_levels, p=[0.6, 0.3, 0.1]),
                    'StartDay': int(self.rng.integers(1, 85)),
                    'EndDay': int(self.rng.integers(5, 90)),
                    'Causality': self.rng.choice(causality_levels, p=[0.1, 0.2, 0.4, 0.2, 0.1]),
                    'Serious': self.rng.random() < 0.05,
                    'ActionTaken': self.rng.choice(['None', 'Dose reduced', 'Medication given', 'Hospitalized'], p=[0.7, 0.15, 0.10, 0.05])
                })

            # Random general AEs (not correlated)
            if self.rng.random() < 0.3:  # 30% of subjects have at least one general AE
                ae_term = self.rng.choice(ae_terms['general'])
                aes.append({
                    'SubjectID': subject_id,
                    'AE_Term': ae_term,
                    'Severity': self.rng.choice(severity_levels, p=[0.7, 0.25, 0.05]),
                    'StartDay': int(self.rng.integers(1, 85)),
                    'EndDay': int(self.rng.integers(5, 90)),
                    'Causality': self.rng.choice(causality_levels, p=[0.3, 0.3, 0.3, 0.08, 0.02]),
                    'Serious': False,
                    'ActionTaken': 'None'
                })

        return aes

    def calculate_realism_score(self, vitals_df: pd.DataFrame, aes: List[Dict]) -> Dict[str, Any]:
        """
        Calculate how realistic the generated data is

        Checks:
        - Appropriate missing data rate
        - Realistic correlations
        - Visit distribution
        - Dropout patterns
        """
        scores = {}

        # 1. Missing data rate (should be 5-10% for good studies)
        total_cells = len(vitals_df) * len(vitals_df.columns)
        if total_cells > 0:
            missing_rate = vitals_df.isnull().sum().sum() / total_cells
            scores['missing_data'] = max(0, min(1.0, 1.0 - abs(missing_rate - 0.08) / 0.08))
        else:
            scores['missing_data'] = 0.0

        # 2. Correlation structure (SBP-DBP should be 0.6-0.8)
        try:
            corr_df = vitals_df[['SystolicBP', 'DiastolicBP']].dropna()
            if len(corr_df) > 1:
                sbp_dbp_corr = corr_df.corr().iloc[0, 1]
                if not np.isnan(sbp_dbp_corr):
                    scores['correlation_realism'] = max(0, min(1.0, 1.0 - abs(sbp_dbp_corr - 0.7) / 0.3))
                else:
                    scores['correlation_realism'] = 0.5
            else:
                scores['correlation_realism'] = 0.5
        except:
            scores['correlation_realism'] = 0.5

        # 3. Dropout rate (realistic is 10-20%)
        total_subjects = vitals_df['SubjectID'].nunique()
        if total_subjects > 0:
            subjects_with_all_visits = (vitals_df.groupby('SubjectID').size() == 4).sum()
            dropout_rate = 1 - (subjects_with_all_visits / total_subjects)
            scores['dropout_realism'] = max(0, min(1.0, 1.0 - abs(dropout_rate - 0.15) / 0.15))
        else:
            scores['dropout_realism'] = 0.0

        # 4. AE rate (realistic is 30-50% of subjects with at least one AE)
        if total_subjects > 0:
            subjects_with_aes = len(set(ae['SubjectID'] for ae in aes))
            ae_rate = subjects_with_aes / total_subjects
            scores['ae_realism'] = max(0, min(1.0, 1.0 - abs(ae_rate - 0.40) / 0.40))
        else:
            scores['ae_realism'] = 0.0

        # Overall score (convert to 0-100 scale)
        valid_scores = [v for v in scores.values() if not np.isnan(v) and not np.isinf(v)]
        overall = np.mean(valid_scores) * 100 if valid_scores else 0.0

        # Ensure overall score is finite
        if np.isnan(overall) or np.isinf(overall):
            overall = 0.0

        # Clean up component scores - replace NaN/Inf with 0.0
        component_scores = {}
        for k, v in scores.items():
            if np.isnan(v) or np.isinf(v):
                component_scores[k] = 0.0
            else:
                component_scores[k] = float(round(v * 100, 1))

        return {
            'overall_score': float(round(overall, 1)),
            'component_scores': component_scores,
            'interpretation': 'Excellent' if overall >= 85 else 'Good' if overall >= 70 else 'Fair'
        }

    def generate_realistic_trial(
        self,
        n_per_arm: int = 50,
        target_effect: float = -5.0,
        indication: str = None,
        phase: str = None,
        n_sites: int = None,
        site_heterogeneity: float = 0.3,
        missing_data_rate: float = None,
        dropout_rate: float = None,
        protocol_deviation_rate: float = 0.05,
        enrollment_pattern: str = "exponential",
        enrollment_duration_months: int = None
    ) -> Dict[str, Any]:
        """
        Generate a complete realistic clinical trial

        This is the main entry point for realistic trial generation.

        NEW: Now supports AACT-informed defaults from 400K+ real trials!
        If indication and phase are provided, parameters like dropout_rate,
        missing_data_rate, n_sites, and enrollment_duration will be automatically
        calculated from industry benchmarks if not explicitly provided.

        Args:
            n_per_arm: Subjects per treatment arm (default: 50)
            target_effect: Target SBP reduction in mmHg (default: -5.0)
            indication: Disease indication (e.g., 'hypertension') - enables AACT defaults
            phase: Trial phase (e.g., 'Phase 3') - enables AACT defaults
            n_sites: Number of sites (auto-calculated from AACT if None and indication provided)
            site_heterogeneity: Site distribution skew, 0-1 (default: 0.3)
            missing_data_rate: Missing data rate (auto from AACT if None and indication provided)
            dropout_rate: Dropout rate (auto from AACT if None and indication provided)
            protocol_deviation_rate: Protocol deviation rate (default: 0.05)
            enrollment_pattern: 'linear', 'exponential', or 'seasonal' (default: 'exponential')
            enrollment_duration_months: Enrollment duration (auto from AACT if None and indication provided)

        Returns:
            {
                'vitals': DataFrame,
                'adverse_events': List[Dict],
                'protocol_deviations': List[Dict],
                'metadata': {
                    'sites': site metadata,
                    'enrollment': enrollment metadata,
                    'realism_score': quality metrics,
                    'aact_informed': whether AACT defaults were used
                }
            }
        """
        # Get AACT-informed defaults if indication and phase provided
        aact_informed = False
        if indication and phase:
            try:
                from aact_utils import get_aact_loader
                aact = get_aact_loader()
                defaults = aact.get_realistic_defaults(indication, phase)

                # Use AACT defaults only for parameters not explicitly provided
                if n_sites is None:
                    n_sites = defaults.get('n_sites', 5)
                    aact_informed = True
                if missing_data_rate is None:
                    missing_data_rate = defaults.get('missing_data_rate', 0.08)
                    aact_informed = True
                if dropout_rate is None:
                    dropout_rate = defaults.get('dropout_rate', 0.15)
                    aact_informed = True
                if enrollment_duration_months is None:
                    enrollment_duration_months = defaults.get('enrollment_duration_months', 12)
                    aact_informed = True
            except Exception as e:
                # Fallback to defaults if AACT loading fails
                import warnings
                warnings.warn(f"Could not load AACT defaults: {e}. Using standard defaults.", UserWarning)

        # Apply standard defaults if still None
        if n_sites is None:
            n_sites = 5
        if missing_data_rate is None:
            missing_data_rate = 0.08
        if dropout_rate is None:
            dropout_rate = 0.15
        if enrollment_duration_months is None:
            enrollment_duration_months = 12

        n_subjects = n_per_arm * 2

        # 1. Generate enrollment schedule
        enrollment_dates = self.generate_enrollment_schedule(
            n_subjects,
            enrollment_duration_months,
            enrollment_pattern
        )

        # 2. Assign to sites
        site_assignments = self.assign_to_sites(n_subjects, n_sites, site_heterogeneity)

        # 3. Generate site-specific effects
        site_effects = self.generate_site_effects(n_sites)

        # 4. Generate subject trajectories
        all_vitals = []
        for subject_idx in range(n_subjects):
            subject_id = f"S{subject_idx:04d}"
            treatment_arm = "Active" if subject_idx < n_per_arm else "Placebo"
            site_id = int(site_assignments[subject_idx])
            site_effect = site_effects[site_id]
            enrollment_date = enrollment_dates[subject_idx]

            subject_trajectory = self.generate_subject_trajectory(
                subject_id=subject_id,
                treatment_arm=treatment_arm,
                site_id=site_id,
                site_effect=site_effect,
                enrollment_date=enrollment_date,
                target_effect=target_effect,
                dropout_prob=dropout_rate
            )

            all_vitals.extend(subject_trajectory)

        vitals_df = pd.DataFrame(all_vitals)

        # 5. Introduce missing data
        vitals_df = self.introduce_missing_data(vitals_df, missing_data_rate, pattern="MAR")

        # 6. Generate protocol deviations
        deviations = self.generate_protocol_deviations(vitals_df, protocol_deviation_rate)

        # 7. Generate correlated AEs
        adverse_events = self.generate_correlated_aes(vitals_df, correlation_strength=0.3)

        # 8. Calculate realism score
        realism_score = self.calculate_realism_score(vitals_df, adverse_events)

        # 9. Generate metadata
        # Convert site_distribution to ensure JSON serializability
        site_dist = vitals_df.groupby('SiteID')['SubjectID'].nunique()
        site_distribution = {str(k): int(v) for k, v in site_dist.items()}

        metadata = {
            'total_subjects': int(n_subjects),
            'subjects_per_arm': int(n_per_arm),
            'n_sites': int(n_sites),
            'enrollment_pattern': enrollment_pattern,
            'enrollment_duration_months': int(enrollment_duration_months),
            'site_distribution': site_distribution,
            'site_statistics': {
                'total_sites': int(n_sites),
                'subjects_per_site': site_distribution,
                'enrollment_pattern': enrollment_pattern
            },
            'dropout_rate': float(round(dropout_rate, 3)),
            'missing_data_rate': float(round(missing_data_rate, 3)),
            'protocol_deviation_rate': float(round(protocol_deviation_rate, 3)),
            'realism_score': realism_score,
            'generation_timestamp': datetime.now().isoformat(),
            'total_vitals_records': int(len(vitals_df)),
            'total_adverse_events': int(len(adverse_events)),
            'total_deviations': int(len(deviations)),
            'aact_informed': aact_informed,
            'indication': indication if indication else None,
            'phase': phase if phase else None
        }

        # 10. Clean up DataFrame for JSON serialization
        # Replace NaN with None and Inf with large finite numbers
        vitals_df = vitals_df.replace([np.inf, -np.inf], np.nan)
        # For numeric columns, fill NaN with reasonable defaults or keep as None for JSON
        numeric_cols = vitals_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if vitals_df[col].isnull().any():
                # Keep NaN as None for JSON (pandas to_dict handles this)
                pass

        # Convert datetime columns to ISO format strings
        if 'EnrollmentDate' in vitals_df.columns:
            vitals_df['EnrollmentDate'] = vitals_df['EnrollmentDate'].apply(
                lambda x: x.isoformat() if pd.notnull(x) else None
            )

        return {
            'vitals': vitals_df,
            'adverse_events': adverse_events,
            'protocol_deviations': deviations,
            'metadata': metadata
        }
