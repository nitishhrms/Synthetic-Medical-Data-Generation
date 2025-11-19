"""
AACT Utilities - Load cached AACT statistics for data generation

This module replaces pilot_trial_cleaned.csv with industry-wide statistics
from 400,000+ ClinicalTrials.gov trials processed via Daft.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np


class AACTStatisticsLoader:
    """Load and query AACT statistics cache"""
    
    def __init__(self, cache_path: Optional[str] = None):
        if cache_path is None:
            # Auto-detect cache path
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            cache_path = project_root / "data" / "aact" / "processed" / "aact_statistics_cache.json"
        
        self.cache_path = Path(cache_path)
        self._load_cache()
    
    def _load_cache(self):
        """Load AACT statistics from cache file"""
        if not self.cache_path.exists():
            raise FileNotFoundError(
                f"AACT cache not found at {self.cache_path}. "
                f"Run: python data/aact/scripts/02_process_aact.py"
            )
        
        with open(self.cache_path, 'r') as f:
            self.stats = json.load(f)
    
    def get_enrollment_stats(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get enrollment statistics for a specific indication and phase
        
        Args:
            indication: Disease indication (e.g., "hypertension", "diabetes")
            phase: Trial phase (e.g., "Phase 3")
            
        Returns:
            Dictionary with mean, median, std, q25, q75 enrollment
        """
        indication_lower = indication.lower()
        
        if indication_lower not in self.stats.get("indications", {}):
            # Fallback to overall statistics
            return self.stats.get("overall_enrollment", {
                "mean": 100,
                "median": 80,
                "std": 50,
                "min": 10,
                "max": 500
            })
        
        indication_data = self.stats["indications"][indication_lower]
        phase_data = indication_data.get("by_phase", {}).get(phase, {})
        
        if "enrollment" in phase_data:
            return phase_data["enrollment"]
        
        # Fallback to overall for this indication
        return self.stats.get("overall_enrollment", {})
    
    def get_realistic_defaults(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get realistic default parameters for trial generation based on AACT data
        
        Returns:
            Dictionary with dropout_rate, missing_rate, n_sites estimates
        """
        enrollment_stats = self.get_enrollment_stats(indication, phase)
        
        # Industry-typical defaults based on AACT analysis
        # These can be enhanced with more detailed AACT processing
        return {
            "dropout_rate": 0.15,  # Typical 15% dropout across trials
            "missing_data_rate": 0.08,  # Typical 8% missing data
            "n_sites": max(3, int(enrollment_stats.get("median", 100) / 15)),  # ~15 subjects/site
            "enrollment_duration_months": 12,
            "target_enrollment": int(enrollment_stats.get("median", 100))
        }
    
    def get_available_indications(self) -> list:
        """Get list of indications with AACT data"""
        return list(self.stats.get("indications", {}).keys())
    
    def get_phase_distribution(self, indication: str) -> Dict[str, int]:
        """Get trial count by phase for an indication"""
        indication_lower = indication.lower()
        
        if indication_lower not in self.stats.get("indications", {}):
            return {}
        
        indication_data = self.stats["indications"][indication_lower]
        by_phase = indication_data.get("by_phase", {})
        
        return {
            phase: data.get("n_trials", 0) 
            for phase, data in by_phase.items()
        }


# Singleton instance
_aact_loader = None

def get_aact_loader() -> AACTStatisticsLoader:
    """Get singleton AACT statistics loader"""
    global _aact_loader
    if _aact_loader is None:
        _aact_loader = AACTStatisticsLoader()
    return _aact_loader
