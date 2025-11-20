"""
Trials Resource - Data generation methods
"""

from typing import Optional, Literal
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Trial:
    """
    Represents a generated clinical trial

    Attributes:
        vitals: DataFrame of vitals observations
        demographics: DataFrame of demographics (if generated)
        adverse_events: List of adverse event records
        labs: DataFrame of lab results (if generated)
        protocol_deviations: List of protocol deviation records
        metadata: Generation metadata including realism scores
    """
    vitals: pd.DataFrame
    metadata: Dict[str, Any]
    demographics: Optional[pd.DataFrame] = None
    adverse_events: Optional[List[Dict]] = field(default_factory=list)
    labs: Optional[pd.DataFrame] = None
    protocol_deviations: Optional[List[Dict]] = field(default_factory=list)

    @property
    def n_subjects(self) -> int:
        """Total number of subjects"""
        return self.vitals['SubjectID'].nunique() if not self.vitals.empty else 0

    @property
    def n_records(self) -> int:
        """Total number of vitals records"""
        return len(self.vitals)

    @property
    def realism_score(self) -> float:
        """Overall realism score (0-100)"""
        return self.metadata.get('realism_score', {}).get('overall_score', 0.0)

    def to_csv(self, prefix: str = "trial"):
        """
        Export all data to CSV files

        Args:
            prefix: Filename prefix (default: "trial")
        """
        self.vitals.to_csv(f"{prefix}_vitals.csv", index=False)
        if self.demographics is not None:
            self.demographics.to_csv(f"{prefix}_demographics.csv", index=False)
        if self.labs is not None:
            self.labs.to_csv(f"{prefix}_labs.csv", index=False)
        if self.adverse_events:
            pd.DataFrame(self.adverse_events).to_csv(f"{prefix}_adverse_events.csv", index=False)
        if self.protocol_deviations:
            pd.DataFrame(self.protocol_deviations).to_csv(f"{prefix}_deviations.csv", index=False)

    def __repr__(self):
        return f"Trial(subjects={self.n_subjects}, records={self.n_records}, realism={self.realism_score:.1f}/100)"


class TrialsResource:
    """
    Resource for generating synthetic clinical trial data

    Access via: client.trials
    """

    def __init__(self, client):
        self._client = client

    def generate(
        self,
        indication: str = "Hypertension",
        phase: str = "Phase 3",  # NEW PARAMETER
        n_per_arm: int = 50,
        method: Literal["realistic", "mvn", "rules", "bootstrap"] = "realistic",
        target_effect: float = -5.0,
        # Realistic trial parameters (now optional, auto from AACT)
        n_sites: int = None,  # Changed to Optional
        site_heterogeneity: float = 0.3,
        missing_data_rate: float = None,  # Changed to Optional
        dropout_rate: float = None,  # Changed to Optional
        protocol_deviation_rate: float = 0.05,
        enrollment_pattern: Literal["linear", "exponential", "seasonal"] = "exponential",
        enrollment_duration_months: int = None,  # Changed to Optional
        # Comprehensive study parameters
        include_demographics: bool = False,
        include_labs: bool = False,
        include_ae: bool = True,
        seed: int = 42
    ) -> Trial:
        """
        Generate a synthetic clinical trial
        
        NEW: Now uses AACT statistics from 400K+ real trials!

        Args:
            indication: Disease indication (e.g., "Hypertension", "Diabetes")
            phase: Trial phase (e.g., "Phase 3") - NEW
            n_per_arm: Number of subjects per treatment arm
            method: Generation method
                - "realistic": Full realistic trial with AACT-informed defaults (recommended)
                - "mvn": Multivariate normal distribution
                - "rules": Rules-based generation
                - "bootstrap": Bootstrap from pilot data
            target_effect: Target treatment effect in mmHg
            n_sites: Number of study sites (auto from AACT if None)
            site_heterogeneity: Site enrollment variability 0-1
            missing_data_rate: Fraction of missing data (auto from AACT if None)
            dropout_rate: Subject dropout rate (auto from AACT if None)
            protocol_deviation_rate: Protocol violation rate
            enrollment_pattern: Enrollment pattern
            enrollment_duration_months: Enrollment duration (auto from AACT if None)
            include_demographics: Generate demographics data
            include_labs: Generate lab results
            include_ae: Generate adverse events
            seed: Random seed for reproducibility

        Returns:
            Trial object with generated data

        Example:
            >>> # Realistic trial with AACT industry defaults
            >>> trial = client.trials.generate(
            ...     indication="Hypertension",
            ...     phase="Phase 3",
            ...     n_per_arm=50,
            ...     method="realistic"
            ... )
            >>> print(f"Realism score: {trial.realism_score}/100")
            >>> print(f"Used {trial.metadata['n_sites']} sites (from AACT)")
        """
        if method == "realistic":
            return self._generate_realistic(
                indication=indication,
                phase=phase,  # Pass through
                n_per_arm=n_per_arm,
                target_effect=target_effect,
                n_sites=n_sites,
                site_heterogeneity=site_heterogeneity,
                missing_data_rate=missing_data_rate,
                dropout_rate=dropout_rate,
                protocol_deviation_rate=protocol_deviation_rate,
                enrollment_pattern=enrollment_pattern,
                enrollment_duration_months=enrollment_duration_months,
                seed=seed
            )
        elif method == "mvn":
            return self._generate_mvn(n_per_arm, target_effect, seed)
        elif method == "rules":
            return self._generate_rules(n_per_arm, target_effect, seed)
        elif method == "bootstrap":
            return self._generate_bootstrap(n_per_arm, target_effect, seed)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _generate_realistic(
        self,
        indication: str,
        phase: str,  # NEW
        n_per_arm: int,
        target_effect: float,
        n_sites: int,
        site_heterogeneity: float,
        missing_data_rate: float,
        dropout_rate: float,
        protocol_deviation_rate: float,
        enrollment_pattern: str,
        enrollment_duration_months: int,
        seed: int
    ) -> Trial:
        """Generate realistic trial with AACT-informed imperfections"""
        response = self._client.request(
            "POST",
            "/generate/realistic-trial",
            data={
                "n_per_arm": n_per_arm,
                "target_effect": target_effect,
                "indication": indication,  # NEW
                "phase": phase,  # NEW
                "n_sites": n_sites,
                "site_heterogeneity": site_heterogeneity,
                "missing_data_rate": missing_data_rate,
                "dropout_rate": dropout_rate,
                "protocol_deviation_rate": protocol_deviation_rate,
                "enrollment_pattern": enrollment_pattern,
                "enrollment_duration_months": enrollment_duration_months,
                "seed": seed
            }
        )

        return Trial(
            vitals=pd.DataFrame(response["vitals"]),
            adverse_events=response.get("adverse_events", []),
            protocol_deviations=response.get("protocol_deviations", []),
            metadata=response["metadata"]
        )

    def _generate_mvn(self, n_per_arm: int, target_effect: float, seed: int) -> Trial:
        """Generate using multivariate normal distribution"""
        response = self._client.request(
            "POST",
            "/generate/mvn",
            data={
                "n_per_arm": n_per_arm,
                "target_effect": target_effect,
                "seed": seed
            }
        )

        # MVN returns just the data array
        return Trial(
            vitals=pd.DataFrame(response),
            metadata={"method": "mvn", "n_per_arm": n_per_arm}
        )

    def _generate_rules(self, n_per_arm: int, target_effect: float, seed: int) -> Trial:
        """Generate using rules-based method"""
        response = self._client.request(
            "POST",
            "/generate/rules",
            data={
                "n_per_arm": n_per_arm,
                "target_effect": target_effect,
                "seed": seed
            }
        )

        return Trial(
            vitals=pd.DataFrame(response),
            metadata={"method": "rules", "n_per_arm": n_per_arm}
        )

    def _generate_bootstrap(self, n_per_arm: int, target_effect: float, seed: int) -> Trial:
        """Generate using bootstrap sampling"""
        # First get pilot data
        pilot_response = self._client.request("GET", "/data/pilot")

        # Then generate via bootstrap
        response = self._client.request(
            "POST",
            "/generate/bootstrap",
            data={
                "training_data": pilot_response,
                "n_per_arm": n_per_arm,
                "target_effect": target_effect,
                "seed": seed
            }
        )

        return Trial(
            vitals=pd.DataFrame(response),
            metadata={"method": "bootstrap", "n_per_arm": n_per_arm}
        )

    def compare_methods(
        self,
        n_per_arm: int = 50,
        target_effect: float = -5.0,
        seed: int = 42
    ) -> Dict[str, Trial]:
        """
        Compare all generation methods

        Args:
            n_per_arm: Subjects per arm
            target_effect: Target treatment effect
            seed: Random seed

        Returns:
            Dictionary with Trial objects for each method

        Example:
            >>> comparisons = client.trials.compare_methods(n_per_arm=30)
            >>> for method, trial in comparisons.items():
            ...     print(f"{method}: {trial.n_records} records")
        """
        response = self._client.request(
            "GET",
            "/compare",
            params={
                "n_per_arm": n_per_arm,
                "target_effect": target_effect,
                "seed": seed
            }
        )

        return {
            "mvn": Trial(
                vitals=pd.DataFrame(response["mvn"]["data"]),
                metadata=response["mvn"]["stats"]
            ),
            "bootstrap": Trial(
                vitals=pd.DataFrame(response["bootstrap"]["data"]),
                metadata=response["bootstrap"]["stats"]
            ),
            "rules": Trial(
                vitals=pd.DataFrame(response["rules"]["data"]),
                metadata=response["rules"]["stats"]
            )
        }

    def get_available_indications(self) -> List[Dict[str, Any]]:
        """
        Get list of disease indications with AACT data
        
        Returns:
            List of dictionaries with indication details from 400K+ trials
            
        Example:
            >>> indications = client.trials.get_available_indications()
            >>> for ind in indications:
            ...     print(f"{ind['name']}: {ind['total_trials']} trials")
            hypertension: 1247 trials
            diabetes: 2103 trials
            ...
        """
        response = self._client.request("GET", "/aact/indications")
        return response.get("indications", [])

    def get_indication_stats(self, indication: str, phase: str = "Phase 3") -> Dict[str, Any]:
        """
        Get industry statistics for an indication from AACT
        
        Args:
            indication: Disease indication
            phase: Trial phase
            
        Returns:
            Dictionary with enrollment stats and recommended defaults
            
        Example:
            >>> stats = client.trials.get_indication_stats("hypertension")
            >>> print(f"Median enrollment: {stats['enrollment_statistics']['median']}")
            >>> print(f"Recommended sites: {stats['recommended_defaults']['n_sites']}")
        """
        response = self._client.request(
            "GET",
            f"/aact/stats/{indication}",
            params={"phase": phase}
        )
        return response
