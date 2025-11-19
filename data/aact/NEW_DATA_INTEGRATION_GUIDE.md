# AACT v4.0 - New Data Integration Guide

## Overview

AACT v4.0 adds **5 new data sources** from 557K+ ClinicalTrials.gov trials to maximize synthetic data realism.

**Total Files Processed**: 17 (up from 12 in v3.0)

**New in v4.0**:
1. **Demographics** (calculated_values.txt) - Pre-computed age, gender, duration
2. **Treatment Arms** (design_groups.txt) - Real arm types and N ratios
3. **Geographic Distribution** (countries.txt) - Trial locations by country
4. **Baseline Characteristics** (baseline_counts.txt) - Disease severity, demographics
5. **Disease Taxonomy** (browse_conditions.txt) - MeSH terms for semantic matching

---

## Prerequisites

### 1. Regenerate the AACT Cache

The cache must be regenerated to include the new data:

```bash
# Run locally (where 15GB AACT data files exist)
cd data/aact/scripts
python 03_process_aact_comprehensive.py
```

**Expected output**:
- Version: `4.0_maximum_realism`
- Files processed: `17`
- New sections in cache: `demographics`, `treatment_arms`, `geographic_distribution`, `baseline_characteristics`, `disease_taxonomy`

### 2. Verify New Data Availability

```bash
# Run test script
python data/aact/scripts/04_test_new_accessors.py
```

This will show sample data from all 5 new sources.

---

## API Reference

### 1. Demographics

```python
from aact_utils import get_demographics

demo = get_demographics("hypertension", "Phase 3")

# Returns:
{
    'age': {
        'median_years': 58.0,
        'mean_years': 57.5,
        'n_studies': 428
    },
    'gender': {
        'all_percentage': 100.0,
        'male_percentage': 52.3,
        'female_percentage': 47.7,
        'n_studies': 428
    },
    'actual_duration': {
        'median_months': 18.0,
        'mean_months': 20.3,
        'n_studies': 428
    }
}
```

**Use Cases**:
- Set realistic study duration (use `actual_duration.median_months`)
- Stratify baseline vitals by age group (< vs >= median age)
- Generate gender-specific adverse events
- Calculate enrollment timelines

### 2. Treatment Arms

```python
from aact_utils import get_treatment_arms

arms = get_treatment_arms("hypertension", "Phase 3")

# Returns:
{
    'arm_type_distribution': {
        'EXPERIMENTAL': 0.48,
        'PLACEBO_COMPARATOR': 0.35,
        'ACTIVE_COMPARATOR': 0.15,
        'NO_INTERVENTION': 0.02
    },
    'common_arm_names': [
        {'name': 'Lisinopril 10 mg', 'frequency': 156},
        {'name': 'Placebo', 'frequency': 142},
        {'name': 'Amlodipine 5 mg', 'frequency': 89},
        ...
    ],
    'typical_n_arms': 2,
    'n_studies': 428
}
```

**Use Cases**:
- **Multi-arm trials**: Generate 3-arm trials (2:2:1 ratio) based on real data
- **Arm naming**: Use common arm names for realistic CSRs
- **Sample size allocation**: Allocate N based on arm type distribution
- **Comparator selection**: Choose placebo vs active comparator based on real patterns

**Example Integration**:
```python
# Generate realistic 3-arm trial
arms_data = get_treatment_arms("hypertension", "Phase 3")

# Determine number of arms
n_arms = arms_data.get('typical_n_arms', 2)

# If 3+ arms, use realistic N ratios
if n_arms >= 3:
    # Example: 2:2:1 for Experimental:Placebo:Active
    n_per_experimental = 100
    n_per_placebo = 100
    n_per_active = 50
else:
    # Standard 1:1 for 2-arm
    n_per_arm = 100
```

### 3. Geographic Distribution

```python
from aact_utils import get_geographic_distribution

geo = get_geographic_distribution("hypertension", "Phase 3", top_n=10)

# Returns:
[
    {'country': 'United States', 'percentage': 0.52},
    {'country': 'Canada', 'percentage': 0.12},
    {'country': 'United Kingdom', 'percentage': 0.08},
    {'country': 'Germany', 'percentage': 0.06},
    {'country': 'France', 'percentage': 0.05},
    {'country': 'Spain', 'percentage': 0.04},
    {'country': 'Italy', 'percentage': 0.03},
    {'country': 'China', 'percentage': 0.03},
    {'country': 'Japan', 'percentage': 0.03},
    {'country': 'Australia', 'percentage': 0.02}
]
```

**Use Cases**:
- **Site generation**: Allocate sites to countries based on real distribution
- **Site naming**: Generate realistic site names (e.g., "Massachusetts General Hospital, Boston, USA")
- **Regulatory context**: Adjust AE reporting based on region (FDA vs EMA)
- **Enrollment rates**: Regional variation in enrollment speed

**Example Integration**:
```python
# Generate 50 sites across realistic countries
geo_dist = get_geographic_distribution("hypertension", "Phase 3")

n_sites = 50
site_countries = []

for country_data in geo_dist:
    n_sites_in_country = int(n_sites * country_data['percentage'])
    site_countries.extend([country_data['country']] * n_sites_in_country)

# Generate site names
site_names = [
    f"Site {i+1} - {random.choice(HOSPITALS[country])}, {country}"
    for i, country in enumerate(site_countries)
]
```

### 4. Baseline Characteristics

```python
from aact_utils import get_baseline_characteristics

baseline = get_baseline_characteristics("hypertension", "Phase 3", top_n=5)

# Returns:
{
    'Age': {
        '<65': 0.62,
        '>=65': 0.38
    },
    'Disease Severity': {
        'Mild': 0.28,
        'Moderate': 0.54,
        'Severe': 0.18
    },
    'Gender': {
        'Male': 0.53,
        'Female': 0.47
    },
    'Race': {
        'White': 0.71,
        'Black or African American': 0.15,
        'Asian': 0.09,
        'Other': 0.05
    },
    'Smoking Status': {
        'Never': 0.45,
        'Former': 0.35,
        'Current': 0.20
    }
}
```

**Use Cases**:
- **Stratified baseline vitals**: Higher SBP for "Severe" vs "Mild" disease
- **Demographic realism**: Generate subjects matching real age/gender/race distribution
- **Subgroup analysis**: Populate SDTM DM domain with realistic demographics
- **Enrollment criteria**: Set inclusion/exclusion based on real distributions

**Example Integration**:
```python
# Generate baseline vitals stratified by disease severity
baseline_chars = get_baseline_characteristics("hypertension", "Phase 3")

severity_dist = baseline_chars.get('Disease Severity', {})

for subject in subjects:
    # Assign severity based on real distribution
    severity = np.random.choice(
        list(severity_dist.keys()),
        p=list(severity_dist.values())
    )

    # Adjust baseline SBP based on severity
    if severity == 'Severe':
        baseline_sbp = np.random.normal(160, 12)
    elif severity == 'Moderate':
        baseline_sbp = np.random.normal(145, 10)
    else:  # Mild
        baseline_sbp = np.random.normal(135, 8)
```

### 5. Disease Taxonomy

```python
from aact_utils import get_disease_taxonomy

taxonomy = get_disease_taxonomy("hypertension", max_terms=10)

# Returns:
{
    'mesh_terms': [
        'hypertension',
        'essential hypertension',
        'blood pressure',
        'systolic pressure',
        'diastolic pressure',
        'antihypertensive agents',
        'cardiovascular diseases',
        'renal hypertension',
        'pulmonary hypertension',
        'white coat hypertension'
    ],
    'term_count': 47,
    'n_studies': 1853
}
```

**Use Cases**:
- **Semantic matching**: Map user indication to closest AACT indication
- **Related conditions**: Generate comorbidities based on MeSH hierarchy
- **Protocol text**: Use MeSH terms in protocol summaries for realism
- **Search enhancement**: Find similar indications for fallback data

**Example Integration**:
```python
# Semantic matching for user-provided indication
user_indication = "high blood pressure"

# Get MeSH terms for all indications
indication_scores = {}
for indication in aact.get_available_indications():
    taxonomy = get_disease_taxonomy(indication)
    mesh_terms = taxonomy['mesh_terms']

    # Simple keyword matching (could use embeddings for better results)
    score = sum(
        1 for term in mesh_terms
        if any(word in term for word in user_indication.lower().split())
    )
    indication_scores[indication] = score

# Get best match
best_match = max(indication_scores, key=indication_scores.get)
print(f"Matched '{user_indication}' to '{best_match}'")
```

---

## Integration Examples

### Example 1: Enhanced Realistic Trial Generator

```python
from aact_utils import (
    get_realistic_defaults,
    get_demographics,
    get_treatment_arms,
    get_geographic_distribution
)

def generate_enhanced_trial(indication: str, phase: str = "Phase 3"):
    """Generate trial with all v4.0 enhancements"""

    # Get base defaults
    defaults = get_realistic_defaults(indication, phase)

    # NEW: Get demographics
    demo = get_demographics(indication, phase)
    study_duration = demo['actual_duration']['median_months']

    # NEW: Get treatment arms for multi-arm trials
    arms_data = get_treatment_arms(indication, phase)
    n_arms = arms_data.get('typical_n_arms', 2)

    # NEW: Get geographic distribution
    geo_dist = get_geographic_distribution(indication, phase)

    # Generate trial config
    config = {
        'indication': indication,
        'phase': phase,
        'duration_months': study_duration,
        'n_arms': n_arms,
        'arm_types': arms_data['arm_type_distribution'],
        'countries': [c['country'] for c in geo_dist[:10]],
        'baseline_vitals': defaults['baseline_vitals'],
        'dropout_rate': defaults['dropout_rate'],
        'n_sites': defaults['n_sites']
    }

    return config
```

### Example 2: Multi-Arm Trial with Realistic N Ratios

```python
def allocate_subjects_to_arms(n_total: int, indication: str, phase: str):
    """Allocate subjects to arms based on real AACT patterns"""

    arms_data = get_treatment_arms(indication, phase)
    arm_dist = arms_data['arm_type_distribution']

    # Determine number of arms
    n_arms = arms_data.get('typical_n_arms', 2)

    if n_arms == 2:
        # Standard 1:1
        return {
            'Experimental': n_total // 2,
            'Placebo': n_total // 2
        }
    elif n_arms == 3:
        # Realistic 2:2:1 (based on arm type distribution)
        n_experimental = int(n_total * 0.4)
        n_placebo = int(n_total * 0.4)
        n_active = n_total - n_experimental - n_placebo
        return {
            'Experimental': n_experimental,
            'Placebo': n_placebo,
            'Active Comparator': n_active
        }
    else:
        # Distribute evenly
        n_per_arm = n_total // n_arms
        return {f'Arm {i+1}': n_per_arm for i in range(n_arms)}
```

### Example 3: Geographic Site Generator

```python
def generate_realistic_sites(n_sites: int, indication: str, phase: str):
    """Generate sites with realistic geographic distribution"""

    geo_dist = get_geographic_distribution(indication, phase)

    sites = []
    for i, country_data in enumerate(geo_dist):
        n_sites_in_country = max(1, int(n_sites * country_data['percentage']))

        for j in range(n_sites_in_country):
            site_id = f"Site{len(sites)+1:03d}"
            sites.append({
                'site_id': site_id,
                'country': country_data['country'],
                'name': f"{site_id} - {country_data['country']}"
            })

            if len(sites) >= n_sites:
                break

        if len(sites) >= n_sites:
            break

    return sites
```

---

## Next Steps

### 1. Update Generators

Modify existing generators to use the new data:

**Files to update**:
- `microservices/data-generation-service/src/generators.py` (MVN, Bootstrap, Rules)
- `microservices/data-generation-service/src/realistic_trial.py`

**Changes**:
- Use `get_demographics()` for study duration
- Use `get_treatment_arms()` for multi-arm trials
- Use `get_geographic_distribution()` for site generation
- Use `get_baseline_characteristics()` for stratified baseline vitals

### 2. Add Multi-Arm Trial Support

Currently all generators use 2-arm (Active vs Placebo). Add 3-arm support:

```python
# In generators.py
def generate_mvn_enhanced(n_per_arm=50, indication="hypertension", phase="Phase 3"):
    """MVN generator with multi-arm support"""

    arms_data = get_treatment_arms(indication, phase)
    n_arms = arms_data.get('typical_n_arms', 2)

    if n_arms >= 3:
        # Generate 3-arm trial with 2:2:1 ratio
        df_experimental_1 = generate_arm(n_per_arm, "Experimental Dose 1")
        df_experimental_2 = generate_arm(n_per_arm, "Experimental Dose 2")
        df_placebo = generate_arm(n_per_arm // 2, "Placebo")
        return pd.concat([df_experimental_1, df_experimental_2, df_placebo])
    else:
        # Standard 2-arm
        return generate_standard_2_arm(n_per_arm)
```

### 3. Test Thoroughly

After integration:

1. **Run test suite**: `pytest tests/`
2. **Check cache loading**: `python data/aact/scripts/04_test_new_accessors.py`
3. **Generate synthetic data**: Verify new fields are populated
4. **Quality checks**: Ensure distributions match AACT patterns

---

## Data Quality Notes

### ✅ High Confidence Data

- **Demographics** (age, gender): Direct calculation from calculated_values
- **Treatment arms** (arm types): Direct extraction from design_groups
- **Geographic distribution**: Direct count from countries table

### ⚠️ Medium Confidence Data

- **Baseline characteristics**: May have missing values, limited to reported categories
- **Actual duration**: Only available for completed trials (subset)

### 💡 Fallback Strategy

All methods have fallback defaults if AACT data unavailable:

```python
# Graceful degradation
demo = get_demographics("unknown_indication", "Phase 3")
# Returns default values with warning, never crashes
```

---

## Troubleshooting

### Problem: "No demographics data for X Phase 3. Using defaults."

**Solution**: The indication/phase combination may not have calculated_values data. Check:

```python
aact = get_aact_loader()
indications = aact.get_available_indications()
phase_dist = aact.get_phase_distribution(indication)
print(f"Available phases for {indication}: {phase_dist.keys()}")
```

### Problem: Cache file not found

**Solution**: Regenerate cache:

```bash
cd data/aact/scripts
python 03_process_aact_comprehensive.py
```

### Problem: Import errors for new methods

**Solution**: Ensure using latest version:

```python
from aact_utils import get_aact_loader
aact = get_aact_loader()
info = aact.get_source_info()
print(f"Version: {info.get('version', 'unknown')}")  # Should be 4.0_maximum_realism
```

---

## Version History

- **v3.0_ultra_comprehensive**: 12 AACT files
- **v4.0_maximum_realism**: 17 AACT files (added demographics, treatment arms, geographic, baseline chars, taxonomy)

---

## Contact

For questions about the new data sources, see:

- **Implementation**: `microservices/data-generation-service/src/aact_utils.py`
- **Processor**: `data/aact/scripts/03_process_aact_comprehensive.py`
- **Test script**: `data/aact/scripts/04_test_new_accessors.py`
