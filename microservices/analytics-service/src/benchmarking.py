"""
Benchmarking & Extensions Module
Performance comparison and parameter optimization for synthetic data generation

This module provides utilities for:
- Comparing generation methods (MVN, Bootstrap, Rules, LLM)
- Aggregating quality scores across all domains
- Generating recommendations for parameter optimization

Key Features:
- Multi-method performance benchmarking
- Cross-domain quality aggregation
- Automated parameter recommendations
- Industry benchmark integration (AACT)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime


def compare_generation_methods(
    methods_data: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare performance of different synthetic data generation methods

    Benchmarks MVN, Bootstrap, Rules, and LLM methods across multiple dimensions:
    - Generation speed (records/second)
    - Data quality scores
    - AACT similarity
    - Resource utilization
    - Use case suitability

    Args:
        methods_data: Dict with method names as keys, containing:
            - generation_time_ms: Time taken to generate data
            - records_generated: Number of records produced
            - quality_score: Overall quality score (0-1)
            - aact_similarity: AACT benchmark similarity (0-1, optional)
            - memory_mb: Memory usage in MB (optional)
            - method_params: Parameters used (optional)

    Returns:
        Dict containing:
        - method_comparison: Performance metrics by method
        - ranking: Methods ranked by overall score
        - recommendations: Which method to use for different scenarios
        - tradeoffs: Speed vs quality analysis
    """
    comparison = {
        "generated_at": datetime.utcnow().isoformat(),
        "methods_compared": list(methods_data.keys()),
        "comparison_metrics": {}
    }

    # ========== CALCULATE METRICS PER METHOD ==========
    method_metrics = {}

    for method_name, data in methods_data.items():
        # Extract data
        gen_time_ms = data.get("generation_time_ms", 0)
        records = data.get("records_generated", 0)
        quality = data.get("quality_score", 0)
        aact_sim = data.get("aact_similarity")
        memory_mb = data.get("memory_mb")

        # Calculate performance metrics
        records_per_sec = (records / (gen_time_ms / 1000.0)) if gen_time_ms > 0 else 0
        time_per_1000_records = (gen_time_ms / records * 1000) if records > 0 else 0

        method_metrics[method_name] = {
            "generation_time_ms": gen_time_ms,
            "records_generated": records,
            "records_per_second": records_per_sec,
            "time_per_1000_records_ms": time_per_1000_records,
            "quality_score": quality,
            "aact_similarity": aact_sim,
            "memory_mb": memory_mb,
            "overall_score": None  # Calculated below
        }

    comparison["method_comparison"] = method_metrics

    # ========== CALCULATE OVERALL SCORES ==========
    # Normalize metrics for comparison
    speeds = [m["records_per_second"] for m in method_metrics.values()]
    qualities = [m["quality_score"] for m in method_metrics.values()]

    max_speed = max(speeds) if speeds else 1
    max_quality = max(qualities) if qualities else 1

    for method_name, metrics in method_metrics.items():
        # Weighted score: 40% quality, 40% speed, 20% AACT similarity
        quality_norm = metrics["quality_score"] / max_quality if max_quality > 0 else 0
        speed_norm = metrics["records_per_second"] / max_speed if max_speed > 0 else 0
        aact_norm = metrics["aact_similarity"] if metrics["aact_similarity"] is not None else 0.5

        overall_score = (0.4 * quality_norm) + (0.4 * speed_norm) + (0.2 * aact_norm)
        method_metrics[method_name]["overall_score"] = overall_score

    # ========== RANKING ==========
    ranking = sorted(
        method_metrics.items(),
        key=lambda x: x[1]["overall_score"],
        reverse=True
    )

    comparison["ranking"] = [
        {
            "rank": idx + 1,
            "method": method_name,
            "overall_score": metrics["overall_score"],
            "strengths": _identify_strengths(method_name, metrics, method_metrics)
        }
        for idx, (method_name, metrics) in enumerate(ranking)
    ]

    # ========== RECOMMENDATIONS ==========
    recommendations = _generate_method_recommendations(method_metrics)
    comparison["recommendations"] = recommendations

    # ========== TRADEOFFS ANALYSIS ==========
    tradeoffs = {
        "speed_vs_quality": [],
        "summary": ""
    }

    for method_name, metrics in method_metrics.items():
        tradeoffs["speed_vs_quality"].append({
            "method": method_name,
            "speed_percentile": _calculate_percentile(metrics["records_per_second"], speeds),
            "quality_percentile": _calculate_percentile(metrics["quality_score"], qualities),
            "speed_quality_ratio": metrics["records_per_second"] / (metrics["quality_score"] * 1000) if metrics["quality_score"] > 0 else 0
        })

    # Identify best tradeoff
    best_balanced = max(
        tradeoffs["speed_vs_quality"],
        key=lambda x: min(x["speed_percentile"], x["quality_percentile"])
    )
    tradeoffs["summary"] = f"{best_balanced['method']} offers the best speed-quality balance"

    comparison["tradeoffs"] = tradeoffs

    return comparison


def _identify_strengths(method_name: str, metrics: Dict[str, Any], all_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
    """Identify strengths of a generation method"""
    strengths = []

    # Speed comparison
    speeds = [m["records_per_second"] for m in all_metrics.values()]
    if metrics["records_per_second"] >= max(speeds):
        strengths.append("Fastest generation speed")
    elif metrics["records_per_second"] >= np.percentile(speeds, 75):
        strengths.append("High generation speed")

    # Quality comparison
    qualities = [m["quality_score"] for m in all_metrics.values()]
    if metrics["quality_score"] >= max(qualities):
        strengths.append("Highest quality score")
    elif metrics["quality_score"] >= np.percentile(qualities, 75):
        strengths.append("High quality score")

    # AACT similarity
    if metrics["aact_similarity"] is not None and metrics["aact_similarity"] >= 0.8:
        strengths.append("Highly realistic (AACT)")

    # Method-specific strengths
    if "mvn" in method_name.lower():
        strengths.append("Statistically principled")
    elif "bootstrap" in method_name.lower():
        strengths.append("Preserves real data characteristics")
    elif "rules" in method_name.lower():
        strengths.append("Deterministic and reproducible")
    elif "llm" in method_name.lower():
        strengths.append("Context-aware generation")

    return strengths if strengths else ["Standard performance"]


def _generate_method_recommendations(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """Generate use-case specific recommendations"""
    recommendations = {}

    # Find fastest method
    fastest = max(metrics.items(), key=lambda x: x[1]["records_per_second"])
    recommendations["for_speed"] = f"{fastest[0]} ({fastest[1]['records_per_second']:.0f} records/sec)"

    # Find highest quality
    highest_quality = max(metrics.items(), key=lambda x: x[1]["quality_score"])
    recommendations["for_quality"] = f"{highest_quality[0]} (quality: {highest_quality[1]['quality_score']:.3f})"

    # Find best AACT similarity
    with_aact = [(name, m) for name, m in metrics.items() if m["aact_similarity"] is not None]
    if with_aact:
        best_aact = max(with_aact, key=lambda x: x[1]["aact_similarity"])
        recommendations["for_realism"] = f"{best_aact[0]} (AACT similarity: {best_aact[1]['aact_similarity']:.3f})"

    # Balanced recommendation
    best_overall = max(metrics.items(), key=lambda x: x[1]["overall_score"])
    recommendations["balanced"] = f"{best_overall[0]} (overall score: {best_overall[1]['overall_score']:.3f})"

    # Use case recommendations
    recommendations["for_prototyping"] = "Use fastest method for rapid iteration"
    recommendations["for_production"] = "Use highest quality method for final datasets"
    recommendations["for_regulatory"] = "Use method with best AACT similarity for credibility"

    return recommendations


def _calculate_percentile(value: float, all_values: List[float]) -> float:
    """Calculate percentile of value in list"""
    if not all_values:
        return 50.0
    return (sum(1 for v in all_values if v <= value) / len(all_values)) * 100


def aggregate_quality_scores(
    demographics_quality: Optional[float] = None,
    vitals_quality: Optional[float] = None,
    labs_quality: Optional[float] = None,
    ae_quality: Optional[float] = None,
    aact_similarity: Optional[float] = None
) -> Dict[str, Any]:
    """
    Aggregate quality scores across all data domains

    Combines quality metrics from demographics, vitals, labs, and AEs
    into a unified quality assessment with domain-specific and overall scores.

    Args:
        demographics_quality: Demographics quality score (0-1)
        vitals_quality: Vitals quality score (0-1)
        labs_quality: Labs quality score (0-1)
        ae_quality: AE quality score (0-1)
        aact_similarity: AACT benchmark similarity (0-1)

    Returns:
        Dict containing:
        - domain_scores: Quality score per domain
        - overall_quality: Weighted aggregate score (0-1)
        - completeness: Which domains have quality scores
        - interpretation: Quality grade and recommendations
        - benchmarks: Comparison with quality thresholds
    """
    aggregation = {
        "generated_at": datetime.utcnow().isoformat(),
        "domain_scores": {},
        "overall_quality": None,
        "completeness": 0.0
    }

    # ========== COLLECT DOMAIN SCORES ==========
    domains = {
        "demographics": demographics_quality,
        "vitals": vitals_quality,
        "labs": labs_quality,
        "adverse_events": ae_quality,
        "aact_benchmark": aact_similarity
    }

    available_scores = {}
    for domain, score in domains.items():
        if score is not None:
            aggregation["domain_scores"][domain] = {
                "score": score,
                "grade": _score_to_grade(score),
                "status": _score_to_status(score)
            }
            available_scores[domain] = score

    # Calculate completeness
    aggregation["completeness"] = len(available_scores) / len(domains)

    # ========== CALCULATE OVERALL QUALITY ==========
    if available_scores:
        # Weighted average (prioritize core domains)
        weights = {
            "demographics": 0.20,
            "vitals": 0.25,
            "labs": 0.25,
            "adverse_events": 0.20,
            "aact_benchmark": 0.10
        }

        weighted_sum = sum(
            available_scores[domain] * weights[domain]
            for domain in available_scores
            if domain in weights
        )

        total_weight = sum(weights[domain] for domain in available_scores if domain in weights)

        aggregation["overall_quality"] = weighted_sum / total_weight if total_weight > 0 else 0.0
    else:
        aggregation["overall_quality"] = 0.0

    # ========== INTERPRETATION ==========
    overall_score = aggregation["overall_quality"]

    interpretation = {
        "grade": _score_to_grade(overall_score),
        "status": _score_to_status(overall_score),
        "recommendation": "",
        "strengths": [],
        "weaknesses": []
    }

    # Identify strengths and weaknesses
    for domain, score in available_scores.items():
        if score >= 0.85:
            interpretation["strengths"].append(f"{domain.replace('_', ' ').title()}: Excellent quality")
        elif score < 0.70:
            interpretation["weaknesses"].append(f"{domain.replace('_', ' ').title()}: Needs improvement")

    # Overall recommendation
    if overall_score >= 0.90:
        interpretation["recommendation"] = "✅ PRODUCTION READY - Excellent quality across all domains"
    elif overall_score >= 0.80:
        interpretation["recommendation"] = "✓ HIGH QUALITY - Ready for most use cases, minor improvements possible"
    elif overall_score >= 0.70:
        interpretation["recommendation"] = "⚠ ACCEPTABLE - Usable but review weak domains"
    else:
        interpretation["recommendation"] = "⚠ NEEDS IMPROVEMENT - Review generation parameters"

    aggregation["interpretation"] = interpretation

    # ========== BENCHMARKS ==========
    benchmarks = {
        "excellent_threshold": 0.85,
        "good_threshold": 0.70,
        "acceptable_threshold": 0.60,
        "your_score": overall_score,
        "comparison": ""
    }

    if overall_score >= benchmarks["excellent_threshold"]:
        benchmarks["comparison"] = f"Above excellent threshold (+{(overall_score - benchmarks['excellent_threshold']):.3f})"
    elif overall_score >= benchmarks["good_threshold"]:
        benchmarks["comparison"] = f"Above good threshold (+{(overall_score - benchmarks['good_threshold']):.3f})"
    elif overall_score >= benchmarks["acceptable_threshold"]:
        benchmarks["comparison"] = f"Above acceptable threshold (+{(overall_score - benchmarks['acceptable_threshold']):.3f})"
    else:
        benchmarks["comparison"] = f"Below acceptable threshold (-{(benchmarks['acceptable_threshold'] - overall_score):.3f})"

    aggregation["benchmarks"] = benchmarks

    return aggregation


def _score_to_grade(score: float) -> str:
    """Convert quality score to letter grade"""
    if score >= 0.90:
        return "A+"
    elif score >= 0.85:
        return "A"
    elif score >= 0.80:
        return "B+"
    elif score >= 0.75:
        return "B"
    elif score >= 0.70:
        return "C+"
    elif score >= 0.65:
        return "C"
    elif score >= 0.60:
        return "D"
    else:
        return "F"


def _score_to_status(score: float) -> str:
    """Convert quality score to status"""
    if score >= 0.85:
        return "Excellent"
    elif score >= 0.70:
        return "Good"
    elif score >= 0.60:
        return "Fair"
    else:
        return "Poor"


def generate_recommendations(
    current_quality: float,
    aact_similarity: Optional[float] = None,
    generation_method: Optional[str] = None,
    n_subjects: Optional[int] = None,
    indication: Optional[str] = None,
    phase: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate recommendations for improving synthetic data generation

    Analyzes current performance and suggests parameter adjustments
    to improve data quality, AACT similarity, and generation efficiency.

    Args:
        current_quality: Current overall quality score (0-1)
        aact_similarity: AACT benchmark similarity score (0-1, optional)
        generation_method: Method used (MVN/Bootstrap/Rules/LLM, optional)
        n_subjects: Number of subjects in current trial
        indication: Disease indication
        phase: Trial phase

    Returns:
        Dict containing:
        - current_status: Assessment of current parameters
        - improvement_opportunities: Specific areas to improve
        - parameter_recommendations: Suggested parameter changes
        - method_recommendations: Alternative methods to consider
        - expected_improvements: Estimated impact of recommendations
    """
    recommendations = {
        "generated_at": datetime.utcnow().isoformat(),
        "current_status": {},
        "improvement_opportunities": [],
        "parameter_recommendations": [],
        "method_recommendations": [],
        "expected_improvements": {}
    }

    # ========== CURRENT STATUS ASSESSMENT ==========
    recommendations["current_status"] = {
        "quality_score": current_quality,
        "quality_grade": _score_to_grade(current_quality),
        "aact_similarity": aact_similarity,
        "generation_method": generation_method,
        "n_subjects": n_subjects
    }

    # ========== IDENTIFY IMPROVEMENT OPPORTUNITIES ==========
    opportunities = []

    # Quality-based opportunities
    if current_quality < 0.70:
        opportunities.append({
            "area": "Data Quality",
            "priority": "HIGH",
            "issue": f"Current quality score ({current_quality:.3f}) is below acceptable threshold (0.70)",
            "impact": "May not be suitable for regulatory submissions"
        })
    elif current_quality < 0.85:
        opportunities.append({
            "area": "Data Quality",
            "priority": "MEDIUM",
            "issue": f"Current quality score ({current_quality:.3f}) is good but below excellent (0.85)",
            "impact": "Could be improved for production use"
        })

    # AACT similarity opportunities
    if aact_similarity is not None:
        if aact_similarity < 0.60:
            opportunities.append({
                "area": "AACT Realism",
                "priority": "HIGH",
                "issue": f"AACT similarity ({aact_similarity:.3f}) is below 0.60",
                "impact": "Synthetic data may not match real-world trial patterns"
            })
        elif aact_similarity < 0.80:
            opportunities.append({
                "area": "AACT Realism",
                "priority": "MEDIUM",
                "issue": f"AACT similarity ({aact_similarity:.3f}) could be improved",
                "impact": "Better alignment with industry benchmarks possible"
            })

    # Sample size opportunities
    if n_subjects is not None and indication and phase:
        # Check against AACT benchmarks (simplified - would use actual AACT data in production)
        if indication.lower() == "hypertension" and phase == "Phase 3":
            if n_subjects < 80:
                opportunities.append({
                    "area": "Sample Size",
                    "priority": "MEDIUM",
                    "issue": f"Sample size ({n_subjects}) is below Q1 for {indication} {phase} trials",
                    "impact": "Trial may appear unusually small compared to real-world trials"
                })

    recommendations["improvement_opportunities"] = opportunities

    # ========== PARAMETER RECOMMENDATIONS ==========
    param_recommendations = []

    # Quality improvement recommendations
    if current_quality < 0.85:
        if generation_method and "mvn" in generation_method.lower():
            param_recommendations.append({
                "parameter": "correlation_preservation",
                "current": "Unknown",
                "recommended": "Increase correlation preservation to match real data",
                "expected_improvement": "+0.05 to +0.10 quality score"
            })
        elif generation_method and "bootstrap" in generation_method.lower():
            param_recommendations.append({
                "parameter": "jitter_fraction",
                "current": "Unknown",
                "recommended": "Reduce jitter_fraction to 0.03-0.05 for higher fidelity",
                "expected_improvement": "+0.05 to +0.08 quality score"
            })

    # AACT similarity recommendations
    if aact_similarity is not None and aact_similarity < 0.80:
        param_recommendations.append({
            "parameter": "target_effect",
            "current": "Unknown",
            "recommended": "Adjust treatment effect to match AACT median for this indication/phase",
            "expected_improvement": "+0.10 to +0.15 AACT similarity"
        })

        param_recommendations.append({
            "parameter": "n_subjects",
            "current": n_subjects,
            "recommended": "Consider aligning enrollment with AACT median or Q1-Q3 range",
            "expected_improvement": "+0.05 to +0.10 AACT similarity"
        })

    recommendations["parameter_recommendations"] = param_recommendations

    # ========== METHOD RECOMMENDATIONS ==========
    method_recommendations = []

    if generation_method:
        if current_quality < 0.70:
            # Recommend switching methods
            if "rules" in generation_method.lower():
                method_recommendations.append({
                    "current_method": generation_method,
                    "recommended_method": "Bootstrap",
                    "reason": "Bootstrap preserves real data characteristics better than rules-based",
                    "trade_off": "Slightly slower but significantly higher quality"
                })
            elif "mvn" in generation_method.lower():
                method_recommendations.append({
                    "current_method": generation_method,
                    "recommended_method": "Bootstrap",
                    "reason": "Bootstrap may better capture non-normal distributions",
                    "trade_off": "Similar speed, potentially higher quality"
                })
        else:
            # Current method is good, suggest alternatives for specific use cases
            method_recommendations.append({
                "current_method": generation_method,
                "recommended_method": "Current method is performing well",
                "reason": f"Quality score ({current_quality:.3f}) is acceptable",
                "trade_off": "Consider LLM method only if context-aware generation is needed"
            })

    recommendations["method_recommendations"] = method_recommendations

    # ========== EXPECTED IMPROVEMENTS ==========
    # Estimate impact of implementing all recommendations
    quality_improvement = 0.0
    aact_improvement = 0.0

    if len(param_recommendations) > 0:
        quality_improvement += 0.08  # Average improvement from parameter tuning

    if len(method_recommendations) > 0 and current_quality < 0.70:
        quality_improvement += 0.12  # Switching methods can have significant impact

    if aact_similarity is not None:
        aact_improvement = 0.15  # Average improvement from AACT-aligned parameters

    recommendations["expected_improvements"] = {
        "quality_score": {
            "current": current_quality,
            "estimated": min(1.0, current_quality + quality_improvement),
            "improvement": quality_improvement
        },
        "aact_similarity": {
            "current": aact_similarity if aact_similarity is not None else "N/A",
            "estimated": min(1.0, aact_similarity + aact_improvement) if aact_similarity is not None else "N/A",
            "improvement": aact_improvement if aact_similarity is not None else "N/A"
        },
        "timeline": "Improvements can be achieved by re-generating data with recommended parameters",
        "effort": "LOW" if len(param_recommendations) <= 2 else "MEDIUM"
    }

    return recommendations
