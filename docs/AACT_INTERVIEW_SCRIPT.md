# AACT Dataset Integration — Feature Deep Dive & Interview Script

> **What is AACT?** The Aggregate Analysis of ClinicalTrials.gov (AACT) is a publicly available relational database containing all information from ClinicalTrials.gov — the world's largest registry of clinical trials.

---

## 1. What This Feature Does

The AACT integration is a **data pipeline + API layer** that processes raw ClinicalTrials.gov data (557,805 studies, ~10GB) into compact, queryable statistics that drive realistic synthetic data generation.

### The Pipeline at a Glance

```
46 raw AACT files (10GB+)        Processing Scripts         Statistics Cache
─────────────────────────   ─────────────────────────   ─────────────────
studies.txt                 02_process_aact.py          aact_statistics
conditions.txt        ───→  (base: enrollment stats)    _cache.json
baseline_measurements.txt        ↓                      (484KB)
drop_withdrawals.txt        03_process_aact             ─────────────────
reported_events.txt    ───→ _comprehensive.py      ───→ 8 indications
facilities.txt              (1,772 lines)               × 4 phases
outcome_measurements.txt    + 04_patch_cache.py         × 12 data domains
eligibilities.txt           (6 enhancements)
interventions.txt                                             ↓
                                                    ┌─────────┴──────────┐
                                                    ▼                    ▼
                                             Data Gen Service    Analytics Service
                                              (port 8002)         (port 8003)
                                             aact_utils.py       aact_integration.py
                                             8 /generate/*-aact  3 /aact/benchmark-*
                                             endpoints            endpoints
```

### What It Extracts (12 Data Domains)

| Data Domain | Source File | Example (Hypertension Phase 3) |
|---|---|---|
| **Enrollment stats** | `studies.txt` | Median: 225 subjects, Mean: 470 |
| **Phase distribution** | `studies.txt` | 1,025 Phase 3 trials |
| **Baseline vitals** | `baseline_measurements.txt` | SBP: 152.3±14.2 mmHg (not hardcoded 140) |
| **Dropout rates** | `drop_withdrawals.txt` | 13.4% (not estimated 15%) |
| **Dropout reasons** | `drop_withdrawals.txt` | AE: 42%, Lost to follow-up: 23% |
| **Arm-specific dropout** | `drop_withdrawals.txt` | Active: 45%, Placebo: 8.3% |
| **Trial-level variance** | `drop_withdrawals.txt` | σ=17.5% (range: 0–30%+) |
| **Adverse events** | `reported_events.txt` (4.7GB) | Top 20 AEs with real frequencies |
| **Site distribution** | `facilities.txt` | Median: 12 sites (not enrollment/15) |
| **Treatment effects** | `outcome_measurements.txt` | Median: -1.5 mmHg SBP reduction |
| **Age criteria** | `eligibilities.txt` | Mean min: 18.5, Mean max: 65.2 years |
| **Common drugs** | `interventions.txt` | Amlodipine (450), Lisinopril (380), ... |

---

## 2. How the Data Is Consumed

### Data Generation Service (Port 8002)

The `AACTStatisticsLoader` class (`aact_utils.py`, 1,009 lines) provides:

| Method | What It Returns |
|---|---|
| `get_enrollment_stats()` | Mean, median, std, Q25, Q75 enrollment |
| `get_baseline_vitals()` | Systolic, diastolic, HR, temp distributions |
| `get_dropout_patterns()` | Rate, total dropouts, top reasons |
| `get_adverse_events()` | Top N AEs with frequencies from real trials |
| `get_site_distribution()` | Site count statistics |
| `get_treatment_effects()` | Effect size distributions |
| `get_realistic_defaults()` | All-in-one: returns comprehensive params |
| `sample_dropout_rate()` | Variance-aware sampling (different each call) |
| `get_arm_specific_dropout_rates()` | Per-arm dropout (active vs placebo) |

**8 AACT-variant endpoints** — each generation method (MVN, Bootstrap, Rules, Bayesian, MICE, LLM, Demographics, Labs, AEs) has an `-aact` variant that automatically uses real benchmarks:
- `POST /generate/mvn-aact` — MVN with AACT baseline vitals
- `POST /generate/bootstrap-aact` — Bootstrap with real enrollment stats
- `POST /generate/demographics-aact` — Demographics from real age/gender distributions
- `POST /generate/ae-aact` — AEs from real adverse event patterns
- etc.

**Realistic Trial Generator** (`realistic_trial.py`) automatically fetches AACT defaults when `indication` and `phase` are provided:
```python
# If indication="hypertension" and phase="Phase 3":
# - dropout_rate = 0.134  (from AACT, not hardcoded 0.15)
# - n_sites = 12          (from AACT, not calculated)
# - missing_data_rate = 0.08
# - enrollment_duration = 12 months
```

### Analytics Service (Port 8003)

The `aact_integration.py` module (626 lines) provides **benchmarking** — comparing synthetic data against real-world standards:

| Endpoint | What It Does |
|---|---|
| `POST /aact/compare-study` | Compares enrollment, response rates, vitals against AACT. Returns percentile rankings. |
| `POST /aact/benchmark-demographics` | Benchmarks age, gender, race distributions against real trials |
| `POST /aact/benchmark-ae` | Compares AE frequencies via Jaccard similarity against real patterns |

---

## 3. How I Developed This Feature

### Development Steps

1. **Downloaded the AACT database** — 46 pipe-delimited text files from ClinicalTrials.gov (~10GB compressed). These are real, public clinical trial data.

2. **Inspected the schema** — `01_inspect_aact.py` explores file structures, column names, and data types before processing.

3. **Built the base processor** — `02_process_aact.py` uses **Daft** (distributed dataframe library) to load and join `studies.txt` + `conditions.txt`, extracting enrollment statistics by indication and phase.

4. **Built the comprehensive processor** — `03_process_aact_comprehensive.py` (1,772 lines) processes 7 additional files:
   - Parses `baseline_measurements.txt` (457MB) for vital sign distributions
   - Calculates dropout rates from `drop_withdrawals.txt` (46MB)
   - Extracts adverse event patterns from `reported_events.txt` (4.7GB — the largest file)
   - Counts sites from `facilities.txt` (366MB)
   - Extracts treatment effects from `outcome_measurements.txt` (2.9GB)
   - Uses `is_plausible_vital()` to filter out non-physiological values from baseline measurements

5. **Patched with 6 enhancements** — `04_patch_aact_cache.py` added:
   - Arm-specific dropout rates (active vs placebo)
   - Trial-level variance (σ, not just mean)
   - Fixed null treatment effects (vectorized processing)
   - Study duration extraction (start→completion date)
   - Age distribution parsing (handles "18 Years", "6 Months", "2 Days")
   - Common drug names

6. **Built the API layer** — `AACTStatisticsLoader` class with 20+ methods, all with graceful fallbacks when AACT data is unavailable.

7. **Integrated into generators** — Modified `realistic_trial.py` and created 8 AACT-variant generation endpoints.

8. **Built the benchmarking module** — `aact_integration.py` in analytics-service for comparing synthetic vs real-world distributions.

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **Cache as JSON, not DB** | 484KB file can be committed to git and loaded instantly. No database dependency. |
| **Graceful fallbacks everywhere** | Every `get_*` method returns sensible defaults if cache is missing. Services never crash. |
| **Daft for processing** | Handles 4.7GB `reported_events.txt` efficiently with lazy evaluation and distributed processing. |
| **Singleton loader** | `get_aact_loader()` returns a singleton — cache loaded once, shared across all requests. |
| **Physiological validation** | `is_plausible_vital()` filters out lab values that keyword-matched as vitals (e.g., "systolic" in a non-BP context). |

---

## 4. Interview Script

### The Pitch

> "A fundamental challenge in synthetic clinical trial data is making it realistic. Most generators use hardcoded values — 140/85 mmHg for blood pressure, 15% dropout. Real trials vary enormously. I built a data pipeline that processes 557,000+ real clinical trials from ClinicalTrials.gov's AACT database to extract actual statistical distributions — baseline vitals, dropout rates, adverse event patterns, site counts, treatment effects, and drug names across 8 disease indications and 4 trial phases.
>
> The raw data is ~10GB across 46 files. My processing pipeline compresses this into a 484KB JSON cache that gets committed to git, so the microservices load it instantly without a database. The data generation service uses these real-world distributions to generate synthetic data that's statistically indistinguishable from actual trials."

### "How do you process 10GB of clinical data?"

> "The processing pipeline uses Daft — a distributed dataframe library similar to Spark but Python-native. The largest file, `reported_events.txt`, is 4.7GB. Daft uses lazy evaluation, so it only loads columns I need and processes in batches. The `03_process_aact_comprehensive.py` script processes 7 critical files and outputs a 484KB statistics cache — that's a 20,000x compression ratio. The cache is structured by indication → phase → data domain, so lookups are O(1) dictionary access at runtime."

### "What's the difference between your synthetic data with and without AACT?"

> "Night and day. Without AACT, every synthetic hypertension trial starts with SBP=140, has exactly 15% dropout, and reports generic AEs like headache and fatigue. With AACT, the baseline SBP is 152.3±14.2 mmHg — because that's what real hypertension patients actually present with. Dropout varies trial-to-trial (σ=17.5%), active arms drop out at 45% vs 8% for placebo — because side effects drive differential dropout. And the adverse events are Dizziness (18%), Peripheral edema (14%) — actual hypertension drug side effects, not generic terms."

### "How do you handle data quality issues in the raw AACT data?"

> "The AACT data has real-world messiness. Baseline measurements sometimes capture lab values, not vitals — 'systolic' appears in non-BP contexts. I built `is_plausible_vital()` with wide physiological ranges (SBP: 70-250 mmHg) to filter out non-vital-sign values while capturing legitimate extreme cases. For age criteria, I parse free-text like '18 Years', '6 Months', '2 Days' with unit-aware conversion. For treatment effects, the outcome_measurements table has 2.9GB of data — I fixed a null-value bug by switching from row-by-row iteration to vectorized pandas processing."

### "What if the AACT cache isn't available?"

> "Every access method has a graceful fallback. If the cache file doesn't load, the `AACTStatisticsLoader` returns hardcoded but reasonable defaults — SBP=140, dropout=15%, generic AEs. The `realistic_trial.py` generator wraps the AACT import in a try/except and metadata includes `aact_informed: true/false` so downstream consumers know whether parameters came from real data or defaults."

### "How would you improve it?"

> "Three things: (1) **Stratified distributions** — age-stratified and gender-stratified vitals, because a 25-year-old and a 65-year-old have different blood pressure. The data is available in `baseline_measurements.txt` but I haven't cross-referenced it yet. (2) **Temporal patterns** — visit-to-visit variability and time-based dropout curves, not just aggregate rates. (3) **Live updates** — right now the cache is static. I'd add a scheduled job that re-processes from ClinicalTrials.gov's API when new studies are registered."

---

## 5. Summary

| Aspect | Detail |
|---|---|
| **What it is** | Data pipeline + API for real-world clinical trial statistics |
| **Data source** | AACT / ClinicalTrials.gov — 557,805 studies, 46 files, ~10GB |
| **Processing** | Daft-based pipeline, 1,772+ lines, 7 critical files processed |
| **Output** | `aact_statistics_cache.json` — 484KB, 8 indications, 12 data domains |
| **Consumers** | Data Gen Service (8 endpoints), Analytics (3 benchmarking endpoints), `realistic_trial.py` |
| **Key insight** | Real hypertension trials show SBP=152±14 (not 140), dropout=13.4% (not 15%), top AE is Dizziness (not Headache) |
| **Error handling** | Graceful fallbacks at every level — services never crash if cache is missing |
| **Compression** | 10GB raw → 484KB cached (20,000x reduction) |
