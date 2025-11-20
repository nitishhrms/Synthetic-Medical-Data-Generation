# Quick Start Guide - AACT-Powered Synthetic Trials

**Last Updated**: November 19, 2025

---

## 🚀 60-Second Start

### 1. Start the Backend

```bash
cd microservices/data-generation-service/src
uvicorn main:app --reload --port 8002
```

### 2. Generate Your First Realistic Trial

```python
from synthetictrial import SyntheticTrial

# Initialize
client = SyntheticTrial(base_url="http://localhost:8002")

# Generate trial (uses AACT data from 400K+ real trials)
trial = client.trials.generate(
    indication="Hypertension",
    phase="Phase 3",
    n_per_arm=50,
    method="realistic"
)

# View results
print(f"✅ Generated {trial.n_subjects} subjects")
print(f"📊 Realism score: {trial.realism_score}/100")
print(trial.vitals.head())

# Export to CSV
trial.to_csv(prefix="my_trial")
```

**Done!** You now have realistic clinical trial data with dropout, missing values, site effects, and adverse events.

---

## 📋 Common Tasks

### See Available Indications (from 400K+ trials)

```python
indications = client.trials.get_available_indications()

for ind in indications:
    print(f"{ind['name']}: {ind['total_trials']} trials")
```

Output:
```
hypertension: 1247 trials
diabetes: 2156 trials
cancer: 18432 trials
cardiovascular: 3421 trials
...
```

### Get Industry Statistics

```python
stats = client.trials.get_indication_stats("Hypertension", phase="Phase 3")

print(stats['enrollment_statistics'])
# {
#   "median": 150,     # Typical Phase 3 hypertension trial
#   "mean": 285.4,
#   "std": 342.1,
#   "q25": 80,
#   "q75": 320
# }
```

### Check Protocol Feasibility

```python
feasibility = client.benchmarks.check_feasibility(
    indication="Hypertension",
    target_enrollment=500,
    n_sites=25,
    phase="Phase 3"
)

print(feasibility['feasibility_analysis']['interpretation'])
# "✅ Within normal range (above average)"
# "Your trial is larger than 73.6% of similar trials"
```

### Analyze Week-12 Efficacy

```python
# Generate trial
trial = client.trials.generate(indication="Hypertension", n_per_arm=50, method="realistic")

# Analyze primary endpoint
stats = client.analytics.week12_statistics(trial.vitals)

print(f"Treatment effect: {stats['treatment_effect']['difference']:.2f} mmHg")
print(f"P-value: {stats['treatment_effect']['p_value']:.4f}")
print(f"Significant: {stats['interpretation']['significant']}")
```

### Compare Generation Methods

```python
comparison = client.trials.compare_methods(indication="Hypertension", n_per_arm=50)

print("Method comparison:")
for method, results in comparison.items():
    if isinstance(results, dict) and 'realism_score' in results:
        print(f"  {method}: {results['realism_score']}/100 ({results['generation_time_ms']}ms)")
```

Output:
```
Method comparison:
  mvn: 65/100 (28ms)
  bootstrap: 72/100 (30ms)
  rules: 68/100 (50ms)
  realistic: 87/100 (245ms)
```

---

## 🎯 SDK Resources

### `client.trials` - Data Generation
```python
# Generate trials
trial = client.trials.generate(indication, phase, n_per_arm, method)

# Get real pilot data
pilot_data = client.trials.get_pilot_data()

# Compare methods
comparison = client.trials.compare_methods(indication, n_per_arm)

# AACT integration
indications = client.trials.get_available_indications()
stats = client.trials.get_indication_stats(indication, phase)
```

### `client.analytics` - Analysis
```python
# Primary efficacy endpoint
stats = client.analytics.week12_statistics(vitals_df)

# Quality assessment
quality = client.analytics.comprehensive_quality(original_df, synthetic_df)

# PCA visualization
pca_data = client.analytics.pca_comparison(original_df, synthetic_df)

# Oncology endpoints
recist = client.analytics.recist_orr(vitals_df, p_active=0.35, p_placebo=0.20)
```

### `client.benchmarks` - Industry Validation
```python
# Check feasibility
feasibility = client.benchmarks.check_feasibility(indication, target_enrollment, n_sites, phase)

# Get percentile ranking
percentile = client.benchmarks.get_industry_percentile(indication, enrollment, phase)

# Get benchmarks
benchmarks = client.benchmarks.get_enrollment_benchmarks(indication, phase)
```

---

## 🔧 API Endpoints (Direct Usage)

### Generate Realistic Trial
```bash
curl -X POST http://localhost:8002/generate/realistic-trial \
  -H "Content-Type: application/json" \
  -d '{
    "indication": "Hypertension",
    "phase": "Phase 3",
    "n_per_arm": 50,
    "site_heterogeneity": 0.4,
    "enrollment_pattern": "exponential",
    "seed": 42
  }'
```

### Get Available Indications
```bash
curl http://localhost:8002/aact/indications
```

### Get Indication Statistics
```bash
curl "http://localhost:8002/aact/stats/Hypertension?phase=Phase%203"
```

---

## 📊 Understanding Realism Scores

| Score | Interpretation | Action |
|-------|----------------|--------|
| **85-100** | ✅ Excellent - Production ready | Use as-is |
| **70-84** | ⚠️ Good - Minor adjustments | Fine-tune parameters |
| **50-69** | ⚠️ Moderate - Needs improvement | Review configuration |
| **0-49** | ❌ Poor - Major issues | Check input data |

**What affects realism score?**
- Dropout rate matching industry average (~15%)
- Missing data rate (~8%)
- Site variability (heterogeneity 0.3-0.5)
- Adverse event correlation with vitals
- Protocol deviation count (5-10%)

---

## 🎨 Complete Example: End-to-End Workflow

```python
from synthetictrial import SyntheticTrial
import pandas as pd

# Initialize
client = SyntheticTrial(base_url="http://localhost:8002")

# 1. Explore available indications
print("Available indications from 400K+ trials:")
indications = client.trials.get_available_indications()
for ind in indications[:5]:
    print(f"  • {ind['name']}: {ind['total_trials']} trials")

# 2. Get industry benchmarks
print("\nIndustry statistics for Hypertension Phase 3:")
stats = client.trials.get_indication_stats("Hypertension", phase="Phase 3")
print(f"  Median enrollment: {stats['enrollment_statistics']['median']}")
print(f"  Typical dropout: {stats['recommended_defaults']['dropout_rate']*100}%")
print(f"  Typical sites: {stats['recommended_defaults']['n_sites']}")

# 3. Check your protocol feasibility
print("\nChecking protocol feasibility...")
feasibility = client.benchmarks.check_feasibility(
    indication="Hypertension",
    target_enrollment=150,
    n_sites=10,
    phase="Phase 3"
)
print(f"  Z-score: {feasibility['feasibility_analysis']['z_score']}")
print(f"  Assessment: {feasibility['feasibility_analysis']['interpretation']}")

# 4. Generate realistic trial
print("\nGenerating realistic trial...")
trial = client.trials.generate(
    indication="Hypertension",
    phase="Phase 3",
    n_per_arm=75,  # 150 total
    method="realistic",
    seed=42
)

# 5. Review trial metadata
print(f"\n✅ Trial generated successfully!")
print(f"  Subjects: {trial.n_subjects}")
print(f"  Sites: {trial.metadata.get('n_sites', 'N/A')}")
print(f"  Dropout: {trial.metadata.get('actual_dropout', 0)*100:.1f}%")
print(f"  Missing data: {trial.metadata.get('actual_missing', 0)*100:.1f}%")
print(f"  Adverse events: {len(trial.adverse_events)}")
print(f"  Protocol deviations: {len(trial.protocol_deviations)}")
print(f"  Realism score: {trial.realism_score:.1f}/100")

# 6. Analyze efficacy
print("\nAnalyzing Week-12 efficacy endpoint...")
efficacy = client.analytics.week12_statistics(trial.vitals)
print(f"  Treatment effect: {efficacy['treatment_effect']['difference']:.2f} mmHg")
print(f"  95% CI: [{efficacy['treatment_effect']['ci_95_lower']:.2f}, {efficacy['treatment_effect']['ci_95_upper']:.2f}]")
print(f"  P-value: {efficacy['treatment_effect']['p_value']:.4f}")
print(f"  Significant: {'Yes ✓' if efficacy['interpretation']['significant'] else 'No ✗'}")

# 7. Assess quality
print("\nAssessing data quality...")
pilot_data = client.trials.get_pilot_data()
quality = client.analytics.comprehensive_quality(pilot_data, trial.vitals)
print(f"  Overall quality score: {quality['overall_quality_score']:.2f}")
print(f"  Summary: {quality['summary']}")

# 8. Export data
print("\nExporting data...")
trial.to_csv(prefix="hypertension_phase3_trial")
print("  ✅ Files created:")
print("     • hypertension_phase3_trial_vitals.csv")
print("     • hypertension_phase3_trial_adverse_events.csv")
print("     • hypertension_phase3_trial_deviations.csv")

print("\n🎉 Complete! Your realistic clinical trial data is ready.")
```

**Expected Output:**
```
Available indications from 400K+ trials:
  • hypertension: 1247 trials
  • diabetes: 2156 trials
  • cancer: 18432 trials
  • cardiovascular: 3421 trials
  • asthma: 892 trials

Industry statistics for Hypertension Phase 3:
  Median enrollment: 150
  Typical dropout: 15.0%
  Typical sites: 10

Checking protocol feasibility...
  Z-score: 0.0
  Assessment: ✅ Exactly at industry median (perfect alignment)

Generating realistic trial...

✅ Trial generated successfully!
  Subjects: 150
  Sites: 10
  Dropout: 13.3%
  Missing data: 8.7%
  Adverse events: 28
  Protocol deviations: 7
  Realism score: 86.4/100

Analyzing Week-12 efficacy endpoint...
  Treatment effect: -5.23 mmHg
  95% CI: [-9.12, -1.34]
  P-value: 0.0094
  Significant: Yes ✓

Assessing data quality...
  Overall quality score: 0.87
  Summary: ✅ EXCELLENT - Quality score: 0.87 (Production ready)

Exporting data...
  ✅ Files created:
     • hypertension_phase3_trial_vitals.csv
     • hypertension_phase3_trial_adverse_events.csv
     • hypertension_phase3_trial_deviations.csv

🎉 Complete! Your realistic clinical trial data is ready.
```

---

## 🐛 Troubleshooting

### Backend not running
```bash
# Check if service is running
curl http://localhost:8002/health

# If not, start it
cd microservices/data-generation-service/src
uvicorn main:app --reload --port 8002
```

### AACT cache not found
```bash
# Process AACT data (one-time setup)
python data/aact/scripts/02_process_aact.py

# This creates: data/aact/processed/aact_statistics_cache.json
```

### SDK import errors
```bash
# Install SDK dependencies
cd sdk/python
pip install -r requirements.txt

# Install SDK in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/sdk/python"
```

### Low realism scores
```python
# Increase realism by tuning parameters
trial = client.trials.generate(
    indication="Hypertension",
    n_per_arm=50,
    method="realistic",
    site_heterogeneity=0.4,      # 0.3-0.5 is realistic
    dropout_rate=0.15,            # Match industry average
    missing_data_rate=0.08,       # ~8% is typical
    protocol_deviation_rate=0.05  # 5% is standard
)
```

---

## 📚 Further Reading

- **Complete Technical Overview**: `FUNCTIONAL_OVERVIEW.md`
- **Transformation Story**: `PROJECT_TRANSFORMATION_SUMMARY.md`
- **SDK Documentation**: `sdk/python/README.md`
- **Backend Reference**: `CLAUDE.md`
- **Scaling Guide**: `SCALING_TO_MILLIONS_GUIDE.md`

---

## 💡 Tips & Best Practices

1. **Always specify indication and phase** for AACT-informed defaults
2. **Use realistic method** for production-quality data (87/100 realism score)
3. **Set a seed** for reproducible results
4. **Check feasibility first** before running large trials
5. **Export to CSV** for use in other tools (R, SAS, SPSS)
6. **Review adverse events and deviations** for realism
7. **Validate quality score** ≥85 for production use

---

**Need Help?**
- API Docs: http://localhost:8002/docs
- SDK Examples: `sdk/python/examples/`
- Full Documentation: See markdown files in project root

---

*Start generating realistic clinical trial data in 60 seconds!*
