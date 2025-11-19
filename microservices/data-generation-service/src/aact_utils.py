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

    def get_realistic_defaults(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get realistic trial parameters informed by AACT statistics

        This calculates intelligent defaults for trial simulation based on
        real-world patterns from 400K+ trials in ClinicalTrials.gov.

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
                'target_enrollment': int
            }
        """
        enrollment_stats = self.get_enrollment_stats(indication, phase)
        median_enrollment = enrollment_stats.get('median', 100)

        # Calculate number of sites based on enrollment
        # Rule of thumb: 1 site per 15-20 subjects for Phase 3
        if phase == "Phase 1":
            sites_per_subject_ratio = 8  # Smaller, single-center often
        elif phase == "Phase 2":
            sites_per_subject_ratio = 12
        elif phase == "Phase 3":
            sites_per_subject_ratio = 15  # Multi-center
        else:  # Phase 4
            sites_per_subject_ratio = 20  # Large post-marketing studies

        n_sites = max(1, min(30, int(median_enrollment / sites_per_subject_ratio)))

        # Industry-standard dropout and missing data rates
        if phase == "Phase 1":
            dropout_rate = 0.10  # 10% - healthier subjects, shorter duration
            missing_data_rate = 0.05  # 5% - more controlled
        elif phase == "Phase 2":
            dropout_rate = 0.12  # 12%
            missing_data_rate = 0.06  # 6%
        elif phase == "Phase 3":
            dropout_rate = 0.15  # 15% - longer trials, more real-world
            missing_data_rate = 0.08  # 8%
        else:  # Phase 4
            dropout_rate = 0.18  # 18% - real-world, less monitoring
            missing_data_rate = 0.10  # 10%

        # Enrollment duration estimates
        if phase == "Phase 1":
            enrollment_duration = 3  # 3 months - small, fast
        elif phase == "Phase 2":
            enrollment_duration = 8  # 8 months
        elif phase == "Phase 3":
            enrollment_duration = 12  # 12 months - typical
        else:  # Phase 4
            enrollment_duration = 18  # 18 months - large, slow

        return {
            'dropout_rate': dropout_rate,
            'missing_data_rate': missing_data_rate,
            'n_sites': n_sites,
            'enrollment_duration_months': enrollment_duration,
            'target_enrollment': int(median_enrollment)
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
