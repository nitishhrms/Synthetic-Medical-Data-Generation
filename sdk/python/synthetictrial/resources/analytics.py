"""
Analytics Resource - Statistical analysis and quality assessment
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from dataclasses import dataclass


@dataclass
class StatisticalAnalysis:
    """Results from Week-12 efficacy analysis"""
    treatment_groups: Dict[str, Any]
    treatment_effect: Dict[str, Any]
    interpretation: Dict[str, Any]

    @property
    def p_value(self) -> float:
        """P-value for treatment effect"""
        return self.treatment_effect.get("p_value", 1.0)

    @property
    def is_significant(self) -> bool:
        """Whether the effect is statistically significant"""
        return self.interpretation.get("significant", False)

    def __repr__(self):
        effect = self.treatment_effect.get("difference", 0)
        return f"StatisticalAnalysis(effect={effect:.2f} mmHg, p={self.p_value:.4f}, significant={self.is_significant})"


@dataclass
class QualityAssessment:
    """Quality metrics for synthetic data"""
    wasserstein_distances: Dict[str, float]
    correlation_preservation: float
    overall_quality_score: float
    summary: str

    def __repr__(self):
        return f"QualityAssessment(score={self.overall_quality_score:.2f}, summary='{self.summary[:50]}...')"


class AnalyticsResource:
    """
    Resource for statistical analysis and quality assessment

    Access via: client.analytics
    """

    def __init__(self, client):
        self._client = client

    def week12_statistics(self, trial_data: pd.DataFrame) -> StatisticalAnalysis:
        """
        Analyze Week-12 efficacy endpoint

        Args:
            trial_data: DataFrame with vitals data

        Returns:
            StatisticalAnalysis object

        Example:
            >>> trial = client.trials.generate(n_per_arm=50)
            >>> stats = client.analytics.week12_statistics(trial.vitals)
            >>> print(f"Treatment effect: {stats.treatment_effect['difference']:.2f} mmHg")
            >>> print(f"P-value: {stats.p_value:.4f}")
        """
        response = self._client.request(
            "POST",
            "/stats/week12",
            data={"vitals_data": trial_data.to_dict(orient="records")}
        )

        return StatisticalAnalysis(
            treatment_groups=response["treatment_groups"],
            treatment_effect=response["treatment_effect"],
            interpretation=response["interpretation"]
        )

    def quality_assessment(
        self,
        original_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        k: int = 5
    ) -> QualityAssessment:
        """
        Comprehensive quality assessment comparing synthetic to real data

        Args:
            original_data: Real/pilot data DataFrame
            synthetic_data: Synthetic data DataFrame
            k: Number of nearest neighbors for KNN analysis

        Returns:
            QualityAssessment object

        Example:
            >>> pilot = pd.read_csv("pilot_data.csv")
            >>> trial = client.trials.generate(n_per_arm=50)
            >>> quality = client.analytics.quality_assessment(pilot, trial.vitals)
            >>> print(f"Quality score: {quality.overall_quality_score:.2f}")
            >>> print(quality.summary)
        """
        response = self._client.request(
            "POST",
            "/quality/comprehensive",
            data={
                "original_data": original_data.to_dict(orient="records"),
                "synthetic_data": synthetic_data.to_dict(orient="records"),
                "k": k
            }
        )

        return QualityAssessment(
            wasserstein_distances=response["wasserstein_distances"],
            correlation_preservation=response["correlation_preservation"],
            overall_quality_score=response["overall_quality_score"],
            summary=response["summary"]
        )

    def pca_comparison(
        self,
        original_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        PCA-based visual quality comparison

        Args:
            original_data: Real data DataFrame
            synthetic_data: Synthetic data DataFrame

        Returns:
            Dictionary with PCA coordinates and quality score

        Example:
            >>> pilot = pd.read_csv("pilot_data.csv")
            >>> trial = client.trials.generate(n_per_arm=50)
            >>> pca_results = client.analytics.pca_comparison(pilot, trial.vitals)
            >>> print(f"Quality score: {pca_results['quality_score']:.2f}")
        """
        response = self._client.request(
            "POST",
            "/quality/pca-comparison",
            data={
                "original_data": original_data.to_dict(orient="records"),
                "synthetic_data": synthetic_data.to_dict(orient="records")
            }
        )

        return response

    def generate_csr(
        self,
        statistics: Dict[str, Any],
        ae_data: Optional[List[Dict]] = None,
        n_rows: int = 400
    ) -> str:
        """
        Generate Clinical Study Report draft

        Args:
            statistics: Week-12 statistics dictionary
            ae_data: Adverse events data
            n_rows: Total number of records

        Returns:
            CSR markdown text

        Example:
            >>> trial = client.trials.generate(n_per_arm=50)
            >>> stats = client.analytics.week12_statistics(trial.vitals)
            >>> csr = client.analytics.generate_csr(
            ...     statistics=stats.__dict__,
            ...     ae_data=trial.adverse_events
            ... )
            >>> with open("csr_draft.md", "w") as f:
            ...     f.write(csr)
        """
        response = self._client.request(
            "POST",
            "/csr/draft",
            data={
                "statistics": statistics,
                "ae_data": ae_data or [],
                "n_rows": n_rows
            }
        )

        return response.get("csr_markdown", "")

    def export_sdtm(self, vitals_data: pd.DataFrame) -> pd.DataFrame:
        """
        Export data to CDISC SDTM format

        Args:
            vitals_data: Vitals DataFrame

        Returns:
            SDTM-formatted DataFrame

        Example:
            >>> trial = client.trials.generate(n_per_arm=50)
            >>> sdtm_data = client.analytics.export_sdtm(trial.vitals)
            >>> sdtm_data.to_csv("sdtm_export.csv", index=False)
        """
        response = self._client.request(
            "POST",
            "/sdtm/export",
            data={"vitals_data": vitals_data.to_dict(orient="records")}
        )

        return pd.DataFrame(response["sdtm_data"])
