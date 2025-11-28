"""
AACT Statistics Loader - Industry benchmarks from 557K+ ClinicalTrials.gov trials

This module provides access to cached statistics extracted from the AACT database,
which contains comprehensive data from ClinicalTrials.gov.

Features:
    - Real baseline vital signs (SBP/DBP/HR/Temp) from 557K trials
    - Real dropout rates and withdrawal patterns
    - Adverse event frequencies by indication and phase
    - Site distribution statistics
    - Demographics (age, gender) aggregations
    - Treatment arm configurations
    - Geographic distribution of trial sites
    - Baseline characteristic distributions
    - Disease taxonomy (MeSH terms)
    - **NEW: Realistic variance sampling** for dropout rates and treatment effects

Data Source:
    - AACT database (Aggregated Analysis of ClinicalTrials.gov)
    - Processed by data/aact/scripts/03_process_aact_comprehensive.py
    - Cache location: data/aact/processed/aact_statistics_cache.json

Usage:
    >>> from aact_utils import get_aact_loader
    >>> aact = get_aact_loader()
    >>> 
    >>> # Get realistic trial parameters
    >>> defaults = aact.get_realistic_defaults("hypertension", "Phase 3")
    >>> 
    >>> # Sample dropout rate with realistic variance
    >>> dropout_rate = aact.sample_dropout_rate("hypertension", "Phase 3")
    >>> # Returns different values: 0.03, 0.15, 0.22, etc. (not always 0.0524!)
    >>> 
    >>> # Get arm-specific dropout rates
    >>> arm_rates = aact.get_arm_specific_dropout_rates("hypertension", "Phase 3")
    >>> # Returns: {'FG000': 0.45, 'FG001': 0.23, ...}
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import warnings
import numpy as np  # NEW: For variance sampling


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
            cache_path = project_root / "data" / "AACT" / "processed" / "aact_statistics_cache.json"

        self.cache_path = Path(cache_path)
        self.statistics = None
        self._load_cache()

    def _load_cache(self):
        """Load the statistics cache from JSON file"""
        if not self.cache_path.exists():
            warnings.warn(
                f"AACT cache not found at {self.cache_path}. "
                f"Run: python data/AACT/scripts/03_process_aact_comprehensive.py to generate it. "
                f"Using default values as fallback.",
                UserWarning
            )
            self.statistics = self._get_fallback_statistics()
            return

        try:
            with open(self.cache_path, 'r') as f:
                # Load JSON with NaN handling (converts nan to None)
                content = f.read()
                # Replace JSON nan with null for proper parsing
                content = content.replace(': nan,', ': null,').replace(': nan}', ': null}')
                self.statistics = json.loads(content)
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

    # ... (rest of the existing methods remain unchanged) ...

    # NEW METHODS FOR PHASE 1 ENHANCEMENTS
    # ================================================================================
    
    def sample_dropout_rate(
        self, 
        indication: str, 
        phase: str = "Phase 3",
        seed: Optional[int] = None
    ) -> float:
        """
        Sample a realistic dropout rate with trial-level variance
        
        This returns different values each time, simulating the natural variation
        across real trials. For example, for hypertension Phase 3:
        - Mean: 5.24%
        - Std Dev: 17.46%
        - Range: 0% to 104% (some trials have no dropout, others catastrophic)
        
        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')
            seed: Optional random seed for reproducibility
            
        Returns:
            Sampled dropout rate (0-1), varies each call unless seed is set
            
        Example:
            >>> aact = get_aact_loader()
            >>> # Generate 5 trials with different dropout rates
            >>> for i in range(5):
            ...     rate = aact.sample_dropout_rate("hypertension", "Phase 3")
            ...     print(f"Trial {i+1}: {rate:.1%} dropout")
            Trial 1: 2.3% dropout
            Trial 2: 18.7% dropout
            Trial 3: 5.1% dropout
            Trial 4: 0.0% dropout
            Trial 5: 22.4% dropout
        """
        if seed is not None:
            np.random.seed(seed)
        
        dropout_data = self.get_dropout_patterns(indication, phase)
        
        # Check if we have variance data from Phase 1 enhancements
        if 'trial_variance' in dropout_data and dropout_data['trial_variance']:
            variance = dropout_data['trial_variance']
            mean_rate = dropout_data['dropout_rate']
            std_dev = variance.get('std_dev', 0)
            
            # Sample from normal distribution
            sampled_rate = np.random.normal(mean_rate, std_dev)
            
            # Clip to observed range from real trials
            min_rate = variance.get('min_rate', 0)
            max_rate = variance.get('max_rate', 1.0)
            
            return float(np.clip(sampled_rate, min_rate, max_rate))
        else:
            # Fallback: return mean dropout rate (no variance)
            warnings.warn(
                f"No trial variance data for {indication} {phase}. "
                f"Returning mean dropout rate. Re-run AACT processing to get variance.",
                UserWarning
            )
            return dropout_data.get('dropout_rate', 0.15)

    def get_arm_specific_dropout_rates(
        self, 
        indication: str, 
        phase: str = "Phase 3"
    ) -> Dict[str, float]:
        """
        Get dropout rates specific to each treatment arm
        
        Real trials show differential dropout between arms:
        - Active arms often have 5-10% higher dropout due to side effects
        - Placebo arms have lower dropout
        - Different dose levels have different rates
        
        Args:
            indication: Disease indication (e.g., 'hypertension')
            phase: Trial phase (e.g., 'Phase 3')
            
        Returns:
            Dict mapping arm codes to dropout rates:
            {
                'FG000': 0.4496,  # 44.96% dropout (likely active high dose)
                'FG001': 0.2332,  # 23.32% dropout (likely active low dose)
                'FG002': 0.0825,  # 8.25% dropout (likely placebo)
                ...
            }
            
        Example:
            >>> aact = get_aact_loader()
            >>> arm_rates = aact.get_arm_specific_dropout_rates("hypertension", "Phase 3")
            >>> for arm, rate in sorted(arm_rates.items(), key=lambda x: x[1], reverse=True):
            ...     print(f"{arm}: {rate:.1%} dropout")
            FG000: 45.0% dropout
            FG001: 23.3% dropout
            FG002: 8.3% dropout
        """
        dropout_data = self.get_dropout_patterns(indication, phase)
        
        # Check if we have arm-specific rates from Phase 1 enhancements
        if 'arm_specific_rates' in dropout_data:
            return dropout_data['arm_specific_rates']
        else:
            # Fallback: return overall dropout rate for all arms
            warnings.warn(
                f"No arm-specific dropout rates for {indication} {phase}. "
                f"Using overall dropout rate for all arms. Re-run AACT processing to get arm-specific data.",
                UserWarning
            )
            overall_rate = dropout_data.get('dropout_rate', 0.15)
            # Return a default 2-arm structure
            return {
                'active': overall_rate,
                'placebo': overall_rate * 0.7  # Assume placebo has 30% less dropout
            }

    def get_dropout_variance_stats(
        self, 
        indication: str, 
        phase: str = "Phase 3"
    ) -> Dict[str, float]:
        """
        Get trial-level variance statistics for dropout rates
        
        Returns:
            Dict with variance statistics:
            {
                'mean_rate': float,     # Mean dropout rate across all trials
                'std_dev': float,       # Standard deviation of dropout rates
                'min_rate': float,      # Minimum observed dropout rate
                'max_rate': float,      # Maximum observed dropout rate
                'median_rate': float,   # Median dropout rate
                'n_trials': int        # Number of trials analyzed
            }
        """
        dropout_data = self.get_dropout_patterns(indication, phase)
        
        if 'trial_variance' in dropout_data and dropout_data['trial_variance']:
            variance = dropout_data['trial_variance']
            return {
                'mean_rate': dropout_data.get('dropout_rate', 0),
                'std_dev': variance.get('std_dev', 0),
                'min_rate': variance.get('min_rate', 0),
                'max_rate': variance.get('max_rate', 0),
                'median_rate': variance.get('median_rate', 0),
                'n_trials': variance.get('n_trials', 0)
            }
        else:
            # Return defaults if variance data not available
            return {
                'mean_rate': dropout_data.get('dropout_rate', 0.15),
                'std_dev': 0.0,
                'min_rate': 0.0,
                'max_rate': 0.0,
                'median_rate': dropout_data.get('dropout_rate', 0.15),
                'n_trials': 0
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


# Convenience functions (existing + new)
def get_available_indications() -> List[str]:
    """Convenience function to get available indications"""
    return get_aact_loader().get_available_indications()


def sample_dropout_rate(indication: str, phase: str = "Phase 3", seed: Optional[int] = None) -> float:
    """
    Convenience function to sample realistic dropout rate with variance
    
    Example:
        >>> from aact_utils import sample_dropout_rate
        >>> rate = sample_dropout_rate("hypertension", "Phase 3")
        >>> print(f"Sampled dropout rate: {rate:.1%}")
    """
    return get_aact_loader().sample_dropout_rate(indication, phase, seed)


def get_arm_specific_dropout_rates(indication: str, phase: str = "Phase 3") -> Dict[str, float]:
    """
    Convenience function to get arm-specific dropout rates
    
    Example:
        >>> from aact_utils import get_arm_specific_dropout_rates
        >>> arm_rates = get_arm_specific_dropout_rates("hypertension", "Phase 3")
        >>> print(f"Active arm dropout: {arm_rates.get('FG000', 0):.1%}")
    """
    return get_aact_loader().get_arm_specific_dropout_rates(indication, phase)


def get_dropout_variance_stats(indication: str, phase: str = "Phase 3") -> Dict[str, float]:
    """Convenience function to get dropout variance statistics"""
    return get_aact_loader().get_dropout_variance_stats(indication, phase)
