"""
AACT Integration Module
Integrates real-world ClinicalTrials.gov data benchmarks from AACT database

This module provides functions to compare synthetic clinical trial data
against real-world benchmarks from the Aggregate Analysis of ClinicalTrials.gov (AACT)
database processed and cached using daft.

Key Features:
- Load AACT statistics cache (557,805+ studies)
- Compare trial structure (enrollment, phase, design)
- Benchmark demographics distributions
- Benchmark adverse events patterns
- Calculate similarity scores and percentiles

AACT Database: https://aact.ctti-clinicaltrials.org/
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from collections import Counter


# AACT cache file location (relative to project root)
AACT_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "aact" / "processed" / "aact_statistics_cache.json"


def load_aact_cache() -> Dict[str, Any]:
    """
    Load AACT statistics cache from JSON file

    Returns:
        Dict containing AACT statistics for multiple indications and phases

    Raises:
        FileNotFoundError: If AACT cache file not found
        json.JSONDecodeError: If cache file is not valid JSON
    """
    if not AACT_CACHE_PATH.exists():
        raise FileNotFoundError(
            f"AACT cache not found at {AACT_CACHE_PATH}. "
            "Please run: python data/aact/scripts/02_process_aact.py"
        )

    with open(AACT_CACHE_PATH, 'r') as f:
        cache = json.load(f)

    return cache


def calculate_percentile(value: float, mean: float, std: float) -> float:
    """
    Calculate percentile using normal distribution assumption

    Args:
        value: Observed value
        mean: Population mean
        std: Population standard deviation

    Returns:
        Percentile (0-100)
    """
    if std == 0:
        return 50.0

    z_score = (value - mean) / std
    percentile = stats.norm.cdf(z_score) * 100
    return percentile


def compare_study_to_aact(
    n_subjects: int,
    indication: str,
    phase: str,
    treatment_effect: float,
    vitals_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Compare synthetic trial characteristics with AACT benchmarks

    This function provides comprehensive benchmarking of a synthetic trial
    against real-world ClinicalTrials.gov data from AACT database.

    Args:
        n_subjects: Total number of subjects enrolled
        indication: Disease indication (e.g., "hypertension", "diabetes")
        phase: Trial phase (e.g., "Phase 3")
        treatment_effect: Primary endpoint treatment effect (e.g., SBP reduction)
        vitals_data: Optional list of vitals records for additional analysis

    Returns:
        Dict containing:
        - enrollment_benchmark: How trial size compares to real trials
        - treatment_effect_benchmark: How effect size compares
        - aact_reference: AACT statistics for this indication/phase
        - similarity_score: Overall similarity (0-1, higher is better)
        - interpretation: Human-readable assessment
    """
    # Load AACT cache
    cache = load_aact_cache()

    # Normalize indication name
    indication_lower = indication.lower()
    available_indications = list(cache['indications'].keys())

    if indication_lower not in available_indications:
        return {
            "error": f"Indication '{indication}' not found in AACT cache",
            "available_indications": available_indications,
            "suggestion": "Use one of the available indications or run AACT processing script to add more"
        }

    indication_data = cache['indications'][indication_lower]

    # Check phase availability
    if phase not in indication_data.get('by_phase', {}):
        return {
            "error": f"Phase '{phase}' not found for indication '{indication}'",
            "available_phases": list(indication_data.get('by_phase', {}).keys())
        }

    phase_data = indication_data['by_phase'][phase]

    # === ENROLLMENT BENCHMARKING ===
    enrollment_stats = phase_data.get('enrollment', {})

    enrollment_benchmark = {
        "synthetic_n": n_subjects,
        "aact_mean": enrollment_stats.get('mean'),
        "aact_median": enrollment_stats.get('median'),
        "aact_std": enrollment_stats.get('std'),
        "aact_q25": enrollment_stats.get('q25'),
        "aact_q75": enrollment_stats.get('q75'),
        "n_trials_reference": phase_data.get('n_trials')
    }

    # Calculate percentile
    if enrollment_stats.get('mean') and enrollment_stats.get('std'):
        enrollment_benchmark['percentile'] = calculate_percentile(
            n_subjects,
            enrollment_stats['mean'],
            enrollment_stats['std']
        )
        enrollment_benchmark['z_score'] = (
            (n_subjects - enrollment_stats['mean']) / enrollment_stats['std']
        )

    # Interpret enrollment size
    if enrollment_benchmark.get('percentile'):
        pct = enrollment_benchmark['percentile']
        if pct < 25:
            enrollment_benchmark['interpretation'] = "Small trial (below Q1)"
        elif pct < 50:
            enrollment_benchmark['interpretation'] = "Below median size"
        elif pct < 75:
            enrollment_benchmark['interpretation'] = "Above median size"
        else:
            enrollment_benchmark['interpretation'] = "Large trial (above Q3)"

    # === TREATMENT EFFECT BENCHMARKING ===
    treatment_effects = indication_data.get('treatment_effects', {})
    phase_effects = treatment_effects.get(phase, {})

    treatment_effect_benchmark = {
        "synthetic_effect": treatment_effect,
        "aact_mean": phase_effects.get('mean'),
        "aact_median": phase_effects.get('median'),
        "aact_std": phase_effects.get('std'),
        "aact_q25": phase_effects.get('q25'),
        "aact_q75": phase_effects.get('q75'),
        "n_trials_reference": phase_effects.get('n_trials')
    }

    # Calculate percentile for treatment effect
    if phase_effects.get('mean') is not None and phase_effects.get('std'):
        treatment_effect_benchmark['percentile'] = calculate_percentile(
            treatment_effect,
            phase_effects['mean'],
            phase_effects['std']
        )
        treatment_effect_benchmark['z_score'] = (
            (treatment_effect - phase_effects['mean']) / phase_effects['std']
        )

    # Interpret treatment effect
    if treatment_effect_benchmark.get('percentile'):
        pct = treatment_effect_benchmark['percentile']
        if indication_lower == 'hypertension':
            # For hypertension, negative is better (SBP reduction)
            if pct < 25:
                treatment_effect_benchmark['interpretation'] = "Strong effect (large reduction)"
            elif pct < 50:
                treatment_effect_benchmark['interpretation'] = "Moderate-strong effect"
            elif pct < 75:
                treatment_effect_benchmark['interpretation'] = "Moderate effect"
            else:
                treatment_effect_benchmark['interpretation'] = "Weak effect or increase"
        else:
            # Generic interpretation
            if pct > 75:
                treatment_effect_benchmark['interpretation'] = "Strong effect (above Q3)"
            elif pct > 50:
                treatment_effect_benchmark['interpretation'] = "Moderate-strong effect"
            elif pct > 25:
                treatment_effect_benchmark['interpretation'] = "Moderate effect"
            else:
                treatment_effect_benchmark['interpretation'] = "Weak effect (below Q1)"

    # === OVERALL SIMILARITY SCORE ===
    # Calculate how realistic the trial is (0-1 scale, 1 = perfectly typical)
    similarity_components = []

    # Enrollment similarity (within 2 SD = high similarity)
    if enrollment_benchmark.get('z_score') is not None:
        enrollment_sim = np.exp(-0.5 * (enrollment_benchmark['z_score'] ** 2))
        similarity_components.append(enrollment_sim)

    # Treatment effect similarity
    if treatment_effect_benchmark.get('z_score') is not None:
        effect_sim = np.exp(-0.5 * (treatment_effect_benchmark['z_score'] ** 2))
        similarity_components.append(effect_sim)

    overall_similarity = np.mean(similarity_components) if similarity_components else None

    # === INTERPRETATION ===
    interpretation = {
        "overall_assessment": "",
        "enrollment_assessment": enrollment_benchmark.get('interpretation', 'Unknown'),
        "effect_assessment": treatment_effect_benchmark.get('interpretation', 'Unknown'),
        "realism_score": overall_similarity,
        "recommendation": ""
    }

    if overall_similarity is not None:
        if overall_similarity >= 0.8:
            interpretation['overall_assessment'] = "✅ HIGHLY REALISTIC - Trial characteristics match real-world patterns"
            interpretation['recommendation'] = "Trial parameters are well-calibrated for this indication and phase"
        elif overall_similarity >= 0.6:
            interpretation['overall_assessment'] = "✓ REALISTIC - Trial characteristics are within typical range"
            interpretation['recommendation'] = "Trial parameters are acceptable, minor deviations from typical"
        elif overall_similarity >= 0.4:
            interpretation['overall_assessment'] = "⚠ MODERATELY REALISTIC - Some characteristics deviate from typical"
            interpretation['recommendation'] = "Consider adjusting enrollment or treatment effect to match benchmarks"
        else:
            interpretation['overall_assessment'] = "⚠ LOW REALISM - Trial characteristics differ significantly from typical"
            interpretation['recommendation'] = "Review trial parameters against AACT benchmarks and adjust as needed"

    # === AACT REFERENCE ===
    aact_reference = {
        "indication": indication_lower,
        "phase": phase,
        "total_trials_in_aact": indication_data.get('total_trials'),
        "phase_trials_in_aact": phase_data.get('n_trials'),
        "aact_database_size": cache.get('total_studies'),
        "cache_generated_at": cache.get('generated_at')
    }

    return {
        "enrollment_benchmark": enrollment_benchmark,
        "treatment_effect_benchmark": treatment_effect_benchmark,
        "aact_reference": aact_reference,
        "similarity_score": overall_similarity,
        "interpretation": interpretation
    }


def benchmark_demographics(
    demographics_df: pd.DataFrame,
    indication: str,
    phase: str
) -> Dict[str, Any]:
    """
    Benchmark demographics against AACT real-world trials

    Note: Current AACT cache has limited demographic distributions.
    This function provides what's available and suggests future enhancements.

    Args:
        demographics_df: DataFrame with columns:
            - SubjectID
            - Age
            - Gender (Male/Female)
            - Race
            - TreatmentArm
        indication: Disease indication
        phase: Trial phase

    Returns:
        Dict containing:
        - demographics_summary: Summary of synthetic demographics
        - aact_benchmarks: Available AACT demographic benchmarks
        - comparison: Statistical comparison where possible
        - limitations: What demographic data is not available in cache
    """
    # Load AACT cache
    cache = load_aact_cache()

    # Normalize indication
    indication_lower = indication.lower()

    if indication_lower not in cache['indications']:
        return {
            "error": f"Indication '{indication}' not found in AACT cache",
            "available_indications": list(cache['indications'].keys())
        }

    indication_data = cache['indications'][indication_lower]

    # === SYNTHETIC DEMOGRAPHICS SUMMARY ===
    demographics_summary = {
        "n_subjects": len(demographics_df),
        "age": {
            "mean": float(demographics_df['Age'].mean()),
            "median": float(demographics_df['Age'].median()),
            "std": float(demographics_df['Age'].std()),
            "min": float(demographics_df['Age'].min()),
            "max": float(demographics_df['Age'].max())
        },
        "gender": {
            "male_pct": float((demographics_df['Gender'] == 'Male').sum() / len(demographics_df) * 100),
            "female_pct": float((demographics_df['Gender'] == 'Female').sum() / len(demographics_df) * 100)
        },
        "race_distribution": demographics_df['Race'].value_counts().to_dict(),
        "treatment_arms": demographics_df['TreatmentArm'].value_counts().to_dict()
    }

    # === AACT BENCHMARKS ===
    # Note: Current AACT cache has limited demographic details
    # Primarily has study duration data
    demographics_data = indication_data.get('demographics', {})
    phase_demo = demographics_data.get(phase, {})

    aact_benchmarks = {
        "available_data": list(phase_demo.keys()),
        "actual_duration": phase_demo.get('actual_duration', {}),
        "note": "AACT cache currently provides study duration. Age/gender/race distributions "
                "require additional AACT table processing (baseline_measurements, baseline_counts)"
    }

    # === COMPARISON ===
    # Limited comparison possible with current cache
    comparison = {
        "status": "Limited demographic benchmarks available",
        "age_benchmark": "Not available in current AACT cache",
        "gender_benchmark": "Not available in current AACT cache",
        "race_benchmark": "Not available in current AACT cache"
    }

    # === LIMITATIONS & RECOMMENDATIONS ===
    limitations = {
        "current_limitations": [
            "AACT cache does not include detailed baseline demographics distributions",
            "Age, gender, race distributions require processing AACT baseline_measurements table",
            "Eligibility criteria (age ranges) are available in cache but not yet parsed"
        ],
        "future_enhancements": [
            "Process AACT baseline_measurements table for age/gender/race distributions",
            "Parse eligibility criteria for typical age ranges",
            "Add geographic distribution demographics",
            "Include comorbidity patterns from baseline data"
        ],
        "workaround": "Use enrollment and treatment effect benchmarks as primary validation"
    }

    # === QUALITATIVE ASSESSMENT ===
    # Provide typical ranges based on clinical trial knowledge
    qualitative_assessment = {}

    if indication_lower == 'hypertension':
        qualitative_assessment = {
            "typical_age_range": "45-65 years (hypertension trials)",
            "typical_gender_split": "55-60% male, 40-45% female",
            "assessment": _assess_hypertension_demographics(demographics_summary)
        }
    elif indication_lower == 'diabetes':
        qualitative_assessment = {
            "typical_age_range": "50-65 years (type 2 diabetes trials)",
            "typical_gender_split": "50-55% male, 45-50% female",
            "assessment": _assess_diabetes_demographics(demographics_summary)
        }

    return {
        "demographics_summary": demographics_summary,
        "aact_benchmarks": aact_benchmarks,
        "comparison": comparison,
        "qualitative_assessment": qualitative_assessment,
        "limitations": limitations
    }


def _assess_hypertension_demographics(demo_summary: Dict[str, Any]) -> str:
    """Assess if demographics are typical for hypertension trials"""
    age_mean = demo_summary['age']['mean']
    male_pct = demo_summary['gender']['male_pct']

    issues = []

    if age_mean < 40:
        issues.append("Mean age < 40 is young for hypertension trials (typical 45-65)")
    elif age_mean > 70:
        issues.append("Mean age > 70 is old for hypertension trials (typical 45-65)")

    if male_pct < 45:
        issues.append("Male % < 45% is low for hypertension trials (typical 55-60%)")
    elif male_pct > 70:
        issues.append("Male % > 70% is high for hypertension trials (typical 55-60%)")

    if not issues:
        return "✅ Demographics are typical for hypertension trials"
    else:
        return "⚠ " + "; ".join(issues)


def _assess_diabetes_demographics(demo_summary: Dict[str, Any]) -> str:
    """Assess if demographics are typical for diabetes trials"""
    age_mean = demo_summary['age']['mean']
    male_pct = demo_summary['gender']['male_pct']

    issues = []

    if age_mean < 45:
        issues.append("Mean age < 45 is young for Type 2 diabetes trials (typical 50-65)")
    elif age_mean > 75:
        issues.append("Mean age > 75 is old for diabetes trials (typical 50-65)")

    if male_pct < 40:
        issues.append("Male % < 40% is low for diabetes trials (typical 50-55%)")
    elif male_pct > 65:
        issues.append("Male % > 65% is high for diabetes trials (typical 50-55%)")

    if not issues:
        return "✅ Demographics are typical for Type 2 diabetes trials"
    else:
        return "⚠ " + "; ".join(issues)


def benchmark_adverse_events(
    ae_df: pd.DataFrame,
    indication: str,
    phase: str
) -> Dict[str, Any]:
    """
    Benchmark adverse events patterns against AACT real-world trials

    Compares synthetic AE frequencies, top events, and distributions
    against real-world ClinicalTrials.gov data.

    Args:
        ae_df: DataFrame with columns:
            - SubjectID
            - PreferredTerm
            - SystemOrganClass
            - Severity (Mild/Moderate/Severe)
            - Serious (boolean)
            - TreatmentArm
        indication: Disease indication
        phase: Trial phase

    Returns:
        Dict containing:
        - ae_summary: Summary of synthetic AEs
        - aact_benchmarks: AACT top events for this indication/phase
        - comparison: Statistical comparison of event frequencies
        - similarity_score: Jaccard similarity of top events
        - interpretation: Assessment of AE realism
    """
    # Load AACT cache
    cache = load_aact_cache()

    # Normalize indication
    indication_lower = indication.lower()

    if indication_lower not in cache['indications']:
        return {
            "error": f"Indication '{indication}' not found in AACT cache",
            "available_indications": list(cache['indications'].keys())
        }

    indication_data = cache['indications'][indication_lower]

    # Get AACT AE data for this phase
    ae_data = indication_data.get('adverse_events', {})
    phase_ae = ae_data.get(phase, {})

    if not phase_ae:
        return {
            "error": f"No AE data for {phase} in AACT cache for {indication}",
            "available_phases": list(ae_data.keys())
        }

    # === SYNTHETIC AE SUMMARY ===
    total_aes = len(ae_df)
    n_subjects = ae_df['SubjectID'].nunique()

    ae_summary = {
        "total_aes": total_aes,
        "n_subjects": n_subjects,
        "aes_per_subject": total_aes / n_subjects if n_subjects > 0 else 0,
        "unique_terms": ae_df['PreferredTerm'].nunique(),
        "top_10_events": ae_df['PreferredTerm'].value_counts().head(10).to_dict(),
        "severity_distribution": ae_df['Severity'].value_counts().to_dict() if 'Severity' in ae_df.columns else {},
        "serious_ae_count": int(ae_df['Serious'].sum()) if 'Serious' in ae_df.columns else 0,
        "serious_ae_rate": float(ae_df['Serious'].mean() * 100) if 'Serious' in ae_df.columns else 0
    }

    # === AACT BENCHMARKS ===
    top_events_aact = phase_ae.get('top_events', [])

    aact_benchmarks = {
        "n_trials_reference": top_events_aact[0].get('n_trials') if top_events_aact else 0,
        "top_events": [
            {
                "term": event['term'],
                "frequency": event.get('frequency', 0),
                "subjects_affected": event.get('subjects_affected', 0),
                "n_trials": event.get('n_trials', 0)
            }
            for event in top_events_aact[:15]  # Top 15 from AACT
        ]
    }

    # === COMPARISON ===
    # Calculate Jaccard similarity for top events
    synthetic_top_terms = set(ae_summary['top_10_events'].keys())
    aact_top_terms = set([event['term'] for event in top_events_aact[:15]])

    if synthetic_top_terms and aact_top_terms:
        intersection = len(synthetic_top_terms & aact_top_terms)
        union = len(synthetic_top_terms | aact_top_terms)
        jaccard_similarity = intersection / union if union > 0 else 0
    else:
        jaccard_similarity = 0

    # Find matching events
    matching_events = []
    for term in synthetic_top_terms:
        # Find in AACT top events
        aact_event = next((e for e in top_events_aact if e['term'].lower() == term.lower()), None)
        if aact_event:
            synthetic_freq = ae_summary['top_10_events'][term] / n_subjects if n_subjects > 0 else 0
            aact_freq = aact_event.get('frequency', 0)

            matching_events.append({
                "term": term,
                "synthetic_frequency": synthetic_freq,
                "aact_frequency": aact_freq,
                "frequency_diff": abs(synthetic_freq - aact_freq),
                "frequency_ratio": synthetic_freq / aact_freq if aact_freq > 0 else None
            })

    comparison = {
        "jaccard_similarity": jaccard_similarity,
        "matching_events_count": len(matching_events),
        "matching_events": sorted(matching_events, key=lambda x: x['frequency_diff']),
        "synthetic_only_events": list(synthetic_top_terms - aact_top_terms),
        "aact_only_events": list(aact_top_terms - synthetic_top_terms)
    }

    # === SIMILARITY SCORE ===
    # Weighted score: 70% Jaccard + 30% frequency matching
    jaccard_component = jaccard_similarity

    # Frequency matching component
    if matching_events:
        freq_diffs = [e['frequency_diff'] for e in matching_events]
        avg_freq_diff = np.mean(freq_diffs)
        # Convert to 0-1 scale (assume <0.1 diff = good)
        freq_matching = max(0, 1 - (avg_freq_diff / 0.1))
    else:
        freq_matching = 0

    overall_similarity = 0.7 * jaccard_component + 0.3 * freq_matching

    # === INTERPRETATION ===
    if overall_similarity >= 0.7:
        assessment = "✅ HIGHLY REALISTIC - AE patterns closely match real-world trials"
        recommendation = "AE generation parameters are well-calibrated"
    elif overall_similarity >= 0.5:
        assessment = "✓ REALISTIC - AE patterns are within expected range"
        recommendation = "AE patterns are acceptable with minor differences"
    elif overall_similarity >= 0.3:
        assessment = "⚠ MODERATELY REALISTIC - Some AE patterns differ from typical"
        recommendation = "Review top AE terms and frequencies against AACT benchmarks"
    else:
        assessment = "⚠ LOW REALISM - AE patterns differ significantly from typical"
        recommendation = "Consider using AACT top events to guide AE generation"

    interpretation = {
        "overall_assessment": assessment,
        "similarity_score": overall_similarity,
        "jaccard_similarity": jaccard_similarity,
        "recommendation": recommendation,
        "key_findings": []
    }

    # Add specific findings
    if len(matching_events) > 0:
        interpretation['key_findings'].append(
            f"{len(matching_events)} of top 10 synthetic events match AACT top events"
        )

    if comparison['synthetic_only_events']:
        interpretation['key_findings'].append(
            f"Synthetic data has {len(comparison['synthetic_only_events'])} events not in AACT top 15: "
            f"{', '.join(list(comparison['synthetic_only_events'])[:3])}"
        )

    if comparison['aact_only_events']:
        interpretation['key_findings'].append(
            f"AACT has {len(comparison['aact_only_events'])} common events not in synthetic top 10: "
            f"{', '.join(list(comparison['aact_only_events'])[:3])}"
        )

    return {
        "ae_summary": ae_summary,
        "aact_benchmarks": aact_benchmarks,
        "comparison": comparison,
        "similarity_score": overall_similarity,
        "interpretation": interpretation
    }
