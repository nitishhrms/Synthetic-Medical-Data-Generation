# SyntheticTrial Python SDK

A developer-friendly Python client for generating and analyzing realistic synthetic clinical trial data.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

🎲 **Realistic Data Generation**
- Variable enrollment patterns (linear, exponential, seasonal)
- Site heterogeneity and site-specific effects
- Subject dropout and missing data (MAR/MCAR)
- Protocol deviations and compliance issues
- Correlated adverse events

📊 **Statistical Analysis**
- Week-12 efficacy analysis
- Quality assessment (Wasserstein distance, PCA, correlation preservation)
- RBQM metrics and site monitoring
- CDISC SDTM export

🏆 **Industry Benchmarking** (Phase 3)
- Protocol feasibility validation
- Enrollment statistics from 400K+ trials (AACT database)

## Installation

```bash
pip install synthetictrial
```

Or install from source:

```bash
cd sdk/python
pip install -e .
```

## Quick Start

```python
from synthetictrial import SyntheticTrial

# Initialize client
client = SyntheticTrial(
    api_key="your_key",  # Optional for local dev
    base_url="http://localhost:8000"  # Optional, defaults to localhost
)

# Generate a realistic trial
trial = client.trials.generate(
    indication="Hypertension",
    n_per_arm=50,
    method="realistic",
    site_heterogeneity=0.4,
    dropout_rate=0.18,
    missing_data_rate=0.10
)

# Access results
print(f"Generated {trial.n_subjects} subjects")
print(f"Realism score: {trial.realism_score}/100")
print(trial.vitals.head())

# Export to CSV
trial.to_csv(prefix="my_trial")
```

## Usage Examples

### 1. Generate Realistic Trial with Custom Parameters

```python
# Create a trial with high site variability and dropout
trial = client.trials.generate(
    indication="Diabetes Type 2",
    n_per_arm=100,
    method="realistic",
    n_sites=8,
    site_heterogeneity=0.5,  # High variability between sites
    dropout_rate=0.22,       # 22% dropout
    missing_data_rate=0.12,  # 12% missing data
    protocol_deviation_rate=0.08,  # 8% protocol violations
    enrollment_pattern="seasonal",
    enrollment_duration_months=18,
    seed=42
)

print(f"Total records: {trial.n_records}")
print(f"Adverse events: {len(trial.adverse_events)}")
print(f"Protocol deviations: {len(trial.protocol_deviations)}")
```

### 2. Statistical Analysis

```python
# Generate trial
trial = client.trials.generate(n_per_arm=50, method="realistic")

# Analyze Week-12 efficacy
stats = client.analytics.week12_statistics(trial.vitals)

print(f"Treatment effect: {stats.treatment_effect['difference']:.2f} mmHg")
print(f"95% CI: [{stats.treatment_effect['ci_95_lower']:.2f}, {stats.treatment_effect['ci_95_upper']:.2f}]")
print(f"P-value: {stats.p_value:.4f}")
print(f"Significant: {stats.is_significant}")
```

### 3. Quality Assessment

```python
import pandas as pd

# Load real pilot data
pilot_data = pd.read_csv("data/pilot_trial_cleaned.csv")

# Generate synthetic data
trial = client.trials.generate(n_per_arm=50, method="realistic")

# Assess quality
quality = client.analytics.quality_assessment(
    original_data=pilot_data,
    synthetic_data=trial.vitals,
    k=5
)

print(f"Overall quality score: {quality.overall_quality_score:.2f}")
print(f"Correlation preservation: {quality.correlation_preservation:.2f}")
print(quality.summary)
```

### 4. Compare Generation Methods

```python
# Compare all methods
comparisons = client.trials.compare_methods(n_per_arm=30, seed=42)

for method, trial in comparisons.items():
    print(f"{method:10} - {trial.n_records:4} records")
```

### 5. Export to SDTM Format

```python
# Generate trial
trial = client.trials.generate(n_per_arm=50)

# Export to CDISC SDTM
sdtm_data = client.analytics.export_sdtm(trial.vitals)

# Save to CSV
sdtm_data.to_csv("sdtm_export.csv", index=False)
```

### 6. Generate Clinical Study Report

```python
# Generate trial and analyze
trial = client.trials.generate(n_per_arm=50, method="realistic")
stats = client.analytics.week12_statistics(trial.vitals)

# Generate CSR draft
csr_markdown = client.analytics.generate_csr(
    statistics={
        "treatment_groups": stats.treatment_groups,
        "treatment_effect": stats.treatment_effect,
        "interpretation": stats.interpretation
    },
    ae_data=trial.adverse_events,
    n_rows=trial.n_records
)

# Save to file
with open("csr_draft.md", "w") as f:
    f.write(csr_markdown)
```

### 7. Protocol Feasibility Check (Phase 3 - Coming Soon)

```python
# Check if your protocol is realistic
feasibility = client.benchmarks.check_feasibility(
    indication="Hypertension",
    target_enrollment=50,
    n_sites=5,
    phase="Phase 3"
)

print(f"Z-score: {feasibility['feasibility_analysis']['z_score']:.2f}")
print(feasibility['feasibility_analysis']['recommendation'])
```

## API Reference

### SyntheticTrial Client

```python
client = SyntheticTrial(
    api_key: Optional[str] = None,       # API key for authentication
    base_url: Optional[str] = None,      # API base URL
    timeout: int = 120,                  # Request timeout in seconds
    max_retries: int = 3                 # Max retry attempts
)
```

### Trials Resource

#### `client.trials.generate()`

Generate a synthetic clinical trial.

**Parameters:**
- `indication` (str): Disease indication (e.g., "Hypertension")
- `n_per_arm` (int): Subjects per treatment arm (default: 50)
- `method` (str): Generation method - "realistic", "mvn", "rules", "bootstrap" (default: "realistic")
- `target_effect` (float): Target treatment effect in mmHg (default: -5.0)
- `n_sites` (int): Number of study sites (default: 5)
- `site_heterogeneity` (float): 0-1, site enrollment variability (default: 0.3)
- `missing_data_rate` (float): 0-0.3, fraction of missing data (default: 0.08)
- `dropout_rate` (float): 0-0.5, subject dropout rate (default: 0.15)
- `protocol_deviation_rate` (float): 0-0.3, protocol violation rate (default: 0.05)
- `enrollment_pattern` (str): "linear", "exponential", or "seasonal" (default: "exponential")
- `enrollment_duration_months` (int): 1-24 months (default: 12)
- `seed` (int): Random seed (default: 42)

**Returns:** `Trial` object

#### `client.trials.compare_methods()`

Compare all generation methods.

**Returns:** Dict[str, Trial]

### Analytics Resource

#### `client.analytics.week12_statistics(trial_data)`

Analyze Week-12 efficacy endpoint.

**Returns:** `StatisticalAnalysis` object

#### `client.analytics.quality_assessment(original_data, synthetic_data, k=5)`

Comprehensive quality assessment.

**Returns:** `QualityAssessment` object

#### `client.analytics.export_sdtm(vitals_data)`

Export to CDISC SDTM format.

**Returns:** pandas DataFrame

### Trial Object

```python
trial = client.trials.generate(...)

# Properties
trial.n_subjects        # Total number of subjects
trial.n_records         # Total vitals records
trial.realism_score     # Overall realism score (0-100)

# Data
trial.vitals            # pandas DataFrame
trial.demographics      # pandas DataFrame (if generated)
trial.adverse_events    # List[Dict]
trial.labs              # pandas DataFrame (if generated)
trial.protocol_deviations  # List[Dict]
trial.metadata          # Dict with generation details

# Methods
trial.to_csv(prefix="trial")  # Export all data to CSV
```

## Environment Variables

```bash
# Optional configuration
export SYNTHETICTRIAL_API_KEY="your_api_key"
export SYNTHETICTRIAL_BASE_URL="http://localhost:8000"
```

## Development

```bash
# Clone repository
git clone https://github.com/your-org/synthetic-medical-data.git
cd synthetic-medical-data/sdk/python

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black synthetictrial/

# Type checking
mypy synthetictrial/
```

## Roadmap

- [x] **Phase 1.1**: Realistic trial generator with imperfections
- [x] **Phase 1.2**: Python SDK (current)
- [ ] **Phase 2**: AI-powered query detection and predictive RBQM
- [ ] **Phase 3**: AACT industry benchmarking (400K+ trials)
- [ ] **Phase 4**: Trial simulation and Monte Carlo optimization

## License

MIT License - see LICENSE file for details

## Support

- Documentation: [https://docs.example.com](https://docs.example.com)
- Issues: [GitHub Issues](https://github.com/your-org/synthetic-medical-data/issues)
- Email: support@example.com

## Citation

If you use this SDK in your research, please cite:

```bibtex
@software{synthetictrial2025,
  title = {SyntheticTrial: Realistic Synthetic Clinical Trial Data Generator},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/your-org/synthetic-medical-data}
}
```
