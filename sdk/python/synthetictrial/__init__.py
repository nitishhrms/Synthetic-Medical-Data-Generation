"""
SyntheticTrial Python SDK

A developer-friendly Python client for generating and analyzing synthetic clinical trial data.

Usage:
    >>> from synthetictrial import SyntheticTrial
    >>> client = SyntheticTrial(api_key="your_key")
    >>> trial = client.trials.generate(indication="Hypertension", n_per_arm=50)
    >>> print(f"Generated {trial.n_subjects} subjects")
    >>> print(f"Realism score: {trial.realism_score}/100")

Features:
    - Realistic trial generation with dropout, missing data, protocol deviations
    - Statistical analysis (Week-12 efficacy, RECIST, RBQM)
    - Quality assessment (PCA, Wasserstein distance, correlation preservation)
    - SDTM export and CSR generation
    - Industry benchmarking (Phase 3 - AACT integration)

For full documentation, visit: https://github.com/your-org/synthetic-medical-data
"""

from .client import SyntheticTrial
from .resources import (
    Trial,
    StatisticalAnalysis,
    QualityAssessment,
    ProtocolBenchmark
)

__version__ = "1.0.0"
__all__ = [
    "SyntheticTrial",
    "Trial",
    "StatisticalAnalysis",
    "QualityAssessment",
    "ProtocolBenchmark",
]
