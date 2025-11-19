"""
AACT Statistics Loader - Industry benchmarks from 400K+ ClinicalTrials.gov trials

This module provides access to cached statistics extracted from the AACT database,
which contains comprehensive data from ClinicalTrials.gov.

Usage:
    from aact_utils import get_aact_loader

    aact = get_aact_loader()
    indications = aact.get_available_indications()
    stats = aact.get_enrollment_stats("hypertension", "Phase 3")
    defaults = aact.get_realistic_defaults("hypertension", "Phase 3")
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import warnings


class AACTStatisticsLoader:
    """Loader for AACT statistics cache from 400K+ clinical trials"""

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize the AACT statistics loader

        Args:
            cache_path: Path to aact_statistics_cache.json (auto-detected if None)
        """
        if cache_path is None:
            # Auto-detect cache path
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent
            cache_path = project_root / "data" / "aact" / "processed" / "aact_statistics_cache.json"

        self.cache_path = Path(cache_path)
        self.statistics = None
        self._load_cache()

    def _load_cache(self):
        """Load the statistics cache from JSON file"""
        if not self.cache_path.exists():
            warnings.warn(
                f"AACT cache not found at {self.cache_path}. "
                f"Run: python data/aact/scripts/02_process_aact.py to generate it. "
                f"Using default values as fallback.",
                UserWarning
            )
            self.statistics = self._get_fallback_statistics()
            return

        try:
            with open(self.cache_path, 'r') as f:
                self.statistics = json.load(f)
        except Exception as e:
            warnings.warn(
                f"Error loading AACT cache: {e}. Using fallback values.",
                UserWarning
            )
            self.statistics = self._get_fallback_statistics()

    def _get_fallback_statistics(self) -> Dict[str, Any]:
        """Provide minimal fallback statistics if cache is unavailable"""
        return {
            "generated_at": "fallback",
            "source": "Default values (AACT cache not available)",
            "total_studies": 0,
            "indications": {}
        }

    def get_available_indications(self) -> List[str]:
        """
        Get list of available disease indications with AACT data

        Returns:
            List of indication names (e.g., ['hypertension', 'diabetes', ...])
        """
        if not self.statistics or 'indications' not in self.statistics:
            return []

        return list(self.statistics['indications'].keys())

    def get_phase_distribution(self, indication: str) -> Dict[str, int]:
        """
        Get distribution of trials by phase for a given indication

        Args:
            indication: Disease indication (e.g., 'hypertension')

        Returns:
            Dict mapping phase names to trial counts
            Example: {'Phase 1': 156, 'Phase 2': 384, 'Phase 3': 428, 'Phase 4': 279}
        """
        if not self.statistics or 'indications' not in self.statistics:
            return {}

        indication_data = self.statistics['indications'].get(indication, {})
        by_phase = indication_data.get('by_phase', {})

        return {phase: data['n_trials'] for phase, data in by_phase.items()}

    def get_enrollment_stats(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get enrollment statistics for a specific indication and phase

        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')

        Returns:
            Dict with enrollment statistics:
            {
                'n_trials': int,
                'mean': float,
                'median': float,
                'std': float,
                'q25': float,
                'q75': float
            }
        """
        if not self.statistics or 'indications' not in self.statistics:
            return self._get_default_enrollment_stats()

        indication_data = self.statistics['indications'].get(indication.lower(), {})
        by_phase = indication_data.get('by_phase', {})
        phase_data = by_phase.get(phase, {})

        if not phase_data:
            warnings.warn(
                f"No AACT data for {indication} {phase}. Using defaults.",
                UserWarning
            )
            return self._get_default_enrollment_stats()

        enrollment = phase_data.get('enrollment', {})

        return {
            'n_trials': phase_data.get('n_trials', 0),
            'mean': enrollment.get('mean', 0),
            'median': enrollment.get('median', 0),
            'std': enrollment.get('std', 0),
            'q25': enrollment.get('q25', 0),
            'q75': enrollment.get('q75', 0)
        }

    def _get_default_enrollment_stats(self) -> Dict[str, Any]:
        """Fallback enrollment statistics when AACT data unavailable"""
        return {
            'n_trials': 0,
            'mean': 100.0,
            'median': 100.0,
            'std': 50.0,
            'q25': 60.0,
            'q75': 140.0
        }

    def get_baseline_vitals(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get real baseline vital signs from AACT data

        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')

        Returns:
            Dict with baseline vital statistics:
            {
                'systolic': {'mean': float, 'std': float, 'median': float, ...},
                'diastolic': {...},
                'heart_rate': {...},
                'temperature': {...}
            }
        """
        if not self.statistics or 'indications' not in self.statistics:
            return self._get_default_baseline_vitals()

        indication_data = self.statistics['indications'].get(indication.lower(), {})
        baseline_data = indication_data.get('baseline_vitals', {}).get(phase, {})

        if not baseline_data:
            warnings.warn(
                f"No baseline vitals data for {indication} {phase}. Using defaults.",
                UserWarning
            )
            return self._get_default_baseline_vitals()

        return baseline_data

    def _get_default_baseline_vitals(self) -> Dict[str, Any]:
        """Fallback baseline vitals when AACT data unavailable"""
        return {
            'systolic': {'mean': 140.0, 'std': 15.0, 'median': 140.0, 'q25': 130.0, 'q75': 150.0},
            'diastolic': {'mean': 85.0, 'std': 10.0, 'median': 85.0, 'q25': 78.0, 'q75': 92.0},
            'heart_rate': {'mean': 72.0, 'std': 10.0, 'median': 72.0, 'q25': 65.0, 'q75': 80.0},
            'temperature': {'mean': 36.7, 'std': 0.3, 'median': 36.7, 'q25': 36.5, 'q75': 36.9}
        }

    def get_dropout_patterns(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get real dropout/withdrawal patterns from AACT data

        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')

        Returns:
            Dict with dropout patterns:
            {
                'dropout_rate': float (0-1),
                'total_dropouts': int,
                'total_subjects': int,
                'top_reasons': [{'reason': str, 'count': int, 'percentage': float}, ...]
            }
        """
        if not self.statistics or 'indications' not in self.statistics:
            return self._get_default_dropout_pattern(phase)

        indication_data = self.statistics['indications'].get(indication.lower(), {})
        dropout_data = indication_data.get('dropout_patterns', {}).get(phase, {})

        if not dropout_data:
            warnings.warn(
                f"No dropout data for {indication} {phase}. Using defaults.",
                UserWarning
            )
            return self._get_default_dropout_pattern(phase)

        return dropout_data

    def _get_default_dropout_pattern(self, phase: str) -> Dict[str, Any]:
        """Fallback dropout patterns when AACT data unavailable"""
        # Industry-standard dropout rates by phase
        dropout_rates = {
            'Phase 1': 0.10,
            'Phase 2': 0.12,
            'Phase 3': 0.15,
            'Phase 4': 0.18
        }
        return {
            'dropout_rate': dropout_rates.get(phase, 0.15),
            'total_dropouts': 0,
            'total_subjects': 0,
            'top_reasons': [
                {'reason': 'Adverse Event', 'count': 0, 'percentage': 0.35},
                {'reason': 'Lost to Follow-up', 'count': 0, 'percentage': 0.25},
                {'reason': 'Withdrawal by Subject', 'count': 0, 'percentage': 0.20},
                {'reason': 'Protocol Violation', 'count': 0, 'percentage': 0.15},
                {'reason': 'Other', 'count': 0, 'percentage': 0.05}
            ]
        }

    def get_adverse_events(self, indication: str, phase: str = "Phase 3", top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Get real adverse event patterns from AACT data

        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')
            top_n: Number of top AEs to return (default: 20)

        Returns:
            List of AE dicts:
            [
                {
                    'term': str,
                    'frequency': float (0-1),
                    'subjects_affected': int,
                    'n_trials': int
                },
                ...
            ]
        """
        if not self.statistics or 'indications' not in self.statistics:
            return self._get_default_adverse_events()

        indication_data = self.statistics['indications'].get(indication.lower(), {})
        ae_data = indication_data.get('adverse_events', {}).get(phase, {})

        if not ae_data or 'top_events' not in ae_data:
            warnings.warn(
                f"No AE data for {indication} {phase}. Using defaults.",
                UserWarning
            )
            return self._get_default_adverse_events()

        return ae_data['top_events'][:top_n]

    def _get_default_adverse_events(self) -> List[Dict[str, Any]]:
        """Fallback AE patterns when AACT data unavailable"""
        return [
            {'term': 'Headache', 'frequency': 0.15, 'subjects_affected': 0, 'n_trials': 0},
            {'term': 'Fatigue', 'frequency': 0.12, 'subjects_affected': 0, 'n_trials': 0},
            {'term': 'Nausea', 'frequency': 0.10, 'subjects_affected': 0, 'n_trials': 0},
            {'term': 'Dizziness', 'frequency': 0.08, 'subjects_affected': 0, 'n_trials': 0},
            {'term': 'Diarrhea', 'frequency': 0.06, 'subjects_affected': 0, 'n_trials': 0}
        ]

    def get_site_distribution(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get real site count distributions from AACT data

        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')

        Returns:
            Dict with site statistics:
            {
                'mean': float,
                'median': float,
                'std': float,
                'q25': float,
                'q75': float,
                'min': int,
                'max': int,
                'n_trials': int
            }
        """
        if not self.statistics or 'indications' not in self.statistics:
            return self._get_default_site_distribution(phase)

        indication_data = self.statistics['indications'].get(indication.lower(), {})
        site_data = indication_data.get('site_distribution', {}).get(phase, {})

        if not site_data:
            warnings.warn(
                f"No site distribution data for {indication} {phase}. Using defaults.",
                UserWarning
            )
            return self._get_default_site_distribution(phase)

        return site_data

    def _get_default_site_distribution(self, phase: str) -> Dict[str, Any]:
        """Fallback site distribution when AACT data unavailable"""
        # Typical site counts by phase
        if phase == "Phase 1":
            return {'mean': 2.0, 'median': 1.0, 'std': 1.5, 'q25': 1.0, 'q75': 3.0, 'min': 1, 'max': 5, 'n_trials': 0}
        elif phase == "Phase 2":
            return {'mean': 5.0, 'median': 4.0, 'std': 3.0, 'q25': 2.0, 'q75': 7.0, 'min': 1, 'max': 15, 'n_trials': 0}
        elif phase == "Phase 3":
            return {'mean': 15.0, 'median': 10.0, 'std': 10.0, 'q25': 5.0, 'q75': 20.0, 'min': 1, 'max': 50, 'n_trials': 0}
        else:  # Phase 4
            return {'mean': 25.0, 'median': 20.0, 'std': 15.0, 'q25': 10.0, 'q75': 35.0, 'min': 1, 'max': 100, 'n_trials': 0}

    def get_realistic_defaults(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get realistic trial parameters informed by AACT statistics

        This calculates intelligent defaults for trial simulation based on
        real-world patterns from 557K+ trials in ClinicalTrials.gov.

        NOW USES REAL DATA for dropout, sites, and baseline vitals when available!

        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')

        Returns:
            Dict with recommended defaults:
            {
                'dropout_rate': float (0-1),
                'missing_data_rate': float (0-1),
                'n_sites': int,
                'enrollment_duration_months': int,
                'target_enrollment': int,
                'baseline_vitals': dict,
                'dropout_reasons': list,
                'top_adverse_events': list
            }
        """
        enrollment_stats = self.get_enrollment_stats(indication, phase)
        median_enrollment = enrollment_stats.get('median', 100)

        # Get REAL dropout rate from AACT data
        dropout_pattern = self.get_dropout_patterns(indication, phase)
        dropout_rate = dropout_pattern.get('dropout_rate', 0.15)

        # Get REAL site count from AACT data
        site_dist = self.get_site_distribution(indication, phase)
        n_sites = int(site_dist.get('median', 10))

        # Get REAL baseline vitals from AACT data
        baseline_vitals = self.get_baseline_vitals(indication, phase)

        # Get REAL adverse events from AACT data
        top_aes = self.get_adverse_events(indication, phase, top_n=10)

        # Missing data rate by phase (still estimated - not in AACT)
        if phase == "Phase 1":
            missing_data_rate = 0.05
        elif phase == "Phase 2":
            missing_data_rate = 0.06
        elif phase == "Phase 3":
            missing_data_rate = 0.08
        else:  # Phase 4
            missing_data_rate = 0.10

        # Enrollment duration estimates (still estimated - could extract from AACT later)
        if phase == "Phase 1":
            enrollment_duration = 3
        elif phase == "Phase 2":
            enrollment_duration = 8
        elif phase == "Phase 3":
            enrollment_duration = 12
        else:  # Phase 4
            enrollment_duration = 18

        return {
            'dropout_rate': dropout_rate,
            'missing_data_rate': missing_data_rate,
            'n_sites': n_sites,
            'enrollment_duration_months': enrollment_duration,
            'target_enrollment': int(median_enrollment),
            'baseline_vitals': baseline_vitals,
            'dropout_reasons': dropout_pattern.get('top_reasons', []),
            'top_adverse_events': top_aes,
            'data_source': 'AACT (real data from 557K+ trials)' if self.statistics else 'fallback'
        }

    def get_total_studies(self) -> int:
        """Get total number of studies in AACT database"""
        if not self.statistics:
            return 0
        return self.statistics.get('total_studies', 0)

    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the AACT cache source"""
        if not self.statistics:
            return {'source': 'unavailable'}

        return {
            'source': self.statistics.get('source', 'unknown'),
            'generated_at': self.statistics.get('generated_at', 'unknown'),
            'total_studies': self.statistics.get('total_studies', 0),
            'cache_path': str(self.cache_path)
        }


# Singleton instance for easy access
_aact_loader_instance = None


def get_aact_loader(cache_path: Optional[Path] = None) -> AACTStatisticsLoader:
    """
    Get the singleton AACT statistics loader instance

    Args:
        cache_path: Optional path to cache file (uses auto-detection if None)

    Returns:
        AACTStatisticsLoader instance

    Example:
        >>> from aact_utils import get_aact_loader
        >>> aact = get_aact_loader()
        >>> print(aact.get_available_indications())
        ['hypertension', 'diabetes', 'cancer', ...]
    """
    global _aact_loader_instance

    if _aact_loader_instance is None:
        _aact_loader_instance = AACTStatisticsLoader(cache_path)

    return _aact_loader_instance


# Convenience functions
def get_available_indications() -> List[str]:
    """Convenience function to get available indications"""
    return get_aact_loader().get_available_indications()


def get_enrollment_stats(indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
    """Convenience function to get enrollment statistics"""
    return get_aact_loader().get_enrollment_stats(indication, phase)


def get_realistic_defaults(indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
    """Convenience function to get realistic defaults"""
    return get_aact_loader().get_realistic_defaults(indication, phase)
