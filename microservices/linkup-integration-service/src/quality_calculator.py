"""
Quality Calculator Wrapper

This module provides wrappers for quality calculation functions,
integrating with the existing analytics service or implementing
standalone calculations when needed.
"""

import logging
import numpy as np
from typing import Dict, List, Any
from scipy import stats
from scipy.spatial.distance import euclidean
from sklearn.neighbors import NearestNeighbors

logger = logging.getLogger(__name__)


async def calculate_comprehensive_quality(
    original_data: List[Dict[str, Any]],
    synthetic_data: List[Dict[str, Any]],
    k: int = 5
) -> Dict[str, Any]:
    """
    Calculate comprehensive quality metrics between original and synthetic data

    This function replicates the analytics service quality assessment
    to avoid tight coupling while the linkup service is in development.

    Args:
        original_data: Original/real data records
        synthetic_data: Synthetic data records
        k: Number of nearest neighbors for K-NN analysis

    Returns:
        Dictionary of quality metrics
    """
    try:
        logger.info(
            f"Calculating quality metrics: "
            f"{len(original_data)} original, {len(synthetic_data)} synthetic"
        )

        # Convert to numeric arrays
        orig_array = _records_to_array(original_data)
        synth_array = _records_to_array(synthetic_data)

        # Calculate metrics
        metrics = {}

        # 1. Wasserstein distances (per column)
        metrics["wasserstein_distances"] = _calculate_wasserstein_distances(
            orig_array, synth_array
        )

        # 2. RMSE by column
        metrics["rmse_by_column"] = _calculate_rmse_by_column(
            orig_array, synth_array
        )

        # 3. Correlation preservation
        metrics["correlation_preservation"] = _calculate_correlation_preservation(
            orig_array, synth_array
        )

        # 4. K-NN imputation score
        metrics["knn_imputation_score"] = _calculate_knn_score(
            orig_array, synth_array, k
        )

        # 5. Euclidean distances
        metrics["euclidean_distances"] = _calculate_euclidean_distances(
            orig_array, synth_array
        )

        # 6. Overall quality score
        metrics["overall_quality_score"] = _calculate_overall_score(metrics)

        # 7. Summary
        metrics["summary"] = _generate_quality_summary(metrics)

        logger.info(
            f"Quality assessment complete. Overall score: "
            f"{metrics['overall_quality_score']:.3f}"
        )

        return metrics

    except Exception as e:
        logger.error(f"Error calculating quality metrics: {str(e)}")
        raise


def _records_to_array(records: List[Dict[str, Any]]) -> np.ndarray:
    """
    Convert list of vitals records to numpy array

    Args:
        records: List of record dictionaries

    Returns:
        Numpy array with numeric columns [SystolicBP, DiastolicBP, HeartRate, Temperature]
    """
    numeric_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']

    data = []
    for record in records:
        row = [float(record.get(col, np.nan)) for col in numeric_cols]
        data.append(row)

    return np.array(data)


def _calculate_wasserstein_distances(
    orig: np.ndarray,
    synth: np.ndarray
) -> Dict[str, float]:
    """Calculate Wasserstein distance for each column"""
    col_names = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    distances = {}

    for i, col_name in enumerate(col_names):
        orig_col = orig[:, i][~np.isnan(orig[:, i])]
        synth_col = synth[:, i][~np.isnan(synth[:, i])]

        if len(orig_col) > 0 and len(synth_col) > 0:
            dist = stats.wasserstein_distance(orig_col, synth_col)
            distances[col_name] = float(dist)
        else:
            distances[col_name] = np.nan

    return distances


def _calculate_rmse_by_column(
    orig: np.ndarray,
    synth: np.ndarray
) -> Dict[str, float]:
    """Calculate RMSE for each column"""
    col_names = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    rmse_values = {}

    # Use mean absolute difference as proxy for RMSE
    for i, col_name in enumerate(col_names):
        orig_col = orig[:, i][~np.isnan(orig[:, i])]
        synth_col = synth[:, i][~np.isnan(synth[:, i])]

        if len(orig_col) > 0 and len(synth_col) > 0:
            # Calculate RMSE between distributions
            orig_mean = np.mean(orig_col)
            synth_mean = np.mean(synth_col)
            orig_std = np.std(orig_col)
            synth_std = np.std(synth_col)

            rmse = np.sqrt((orig_mean - synth_mean)**2 + (orig_std - synth_std)**2)
            rmse_values[col_name] = float(rmse)
        else:
            rmse_values[col_name] = np.nan

    return rmse_values


def _calculate_correlation_preservation(
    orig: np.ndarray,
    synth: np.ndarray
) -> float:
    """Calculate how well correlations are preserved"""
    try:
        # Remove NaN rows
        orig_clean = orig[~np.isnan(orig).any(axis=1)]
        synth_clean = synth[~np.isnan(synth).any(axis=1)]

        if len(orig_clean) < 2 or len(synth_clean) < 2:
            return 0.0

        # Calculate correlation matrices
        orig_corr = np.corrcoef(orig_clean.T)
        synth_corr = np.corrcoef(synth_clean.T)

        # Calculate similarity between correlation matrices
        # Use Frobenius norm
        diff = np.abs(orig_corr - synth_corr)
        preservation_score = 1.0 - (np.mean(diff) / 2.0)  # Normalize to 0-1

        return float(max(0.0, min(1.0, preservation_score)))

    except Exception as e:
        logger.warning(f"Error calculating correlation preservation: {e}")
        return 0.0


def _calculate_knn_score(
    orig: np.ndarray,
    synth: np.ndarray,
    k: int
) -> float:
    """
    Calculate K-NN imputation quality score

    Measures how well synthetic data can be used to impute missing values
    in real data using K-nearest neighbors.
    """
    try:
        # Remove NaN rows
        orig_clean = orig[~np.isnan(orig).any(axis=1)]
        synth_clean = synth[~np.isnan(synth).any(axis=1)]

        if len(orig_clean) < k or len(synth_clean) < k:
            return 0.0

        # Fit K-NN on synthetic data
        knn = NearestNeighbors(n_neighbors=min(k, len(synth_clean)))
        knn.fit(synth_clean)

        # Find distances from original data to synthetic data
        distances, _ = knn.kneighbors(orig_clean[:100])  # Sample 100 points

        # Calculate score based on average distance
        # Lower distance = better quality
        avg_distance = np.mean(distances)

        # Convert to 0-1 score (inverse relationship)
        # Normalize by typical vital signs scale (~100)
        score = 1.0 / (1.0 + avg_distance / 10.0)

        return float(max(0.0, min(1.0, score)))

    except Exception as e:
        logger.warning(f"Error calculating K-NN score: {e}")
        return 0.0


def _calculate_euclidean_distances(
    orig: np.ndarray,
    synth: np.ndarray
) -> Dict[str, float]:
    """Calculate Euclidean distance statistics between datasets"""
    try:
        # Remove NaN rows
        orig_clean = orig[~np.isnan(orig).any(axis=1)]
        synth_clean = synth[~np.isnan(synth).any(axis=1)]

        if len(orig_clean) == 0 or len(synth_clean) == 0:
            return {
                "mean_distance": np.nan,
                "median_distance": np.nan,
                "min_distance": np.nan,
                "max_distance": np.nan,
                "std_distance": np.nan
            }

        # Calculate pairwise distances (sample for efficiency)
        sample_size = min(100, len(orig_clean), len(synth_clean))
        orig_sample = orig_clean[:sample_size]
        synth_sample = synth_clean[:sample_size]

        distances = []
        for orig_point in orig_sample:
            min_dist = min(euclidean(orig_point, synth_point)
                          for synth_point in synth_sample)
            distances.append(min_dist)

        distances = np.array(distances)

        return {
            "mean_distance": float(np.mean(distances)),
            "median_distance": float(np.median(distances)),
            "min_distance": float(np.min(distances)),
            "max_distance": float(np.max(distances)),
            "std_distance": float(np.std(distances))
        }

    except Exception as e:
        logger.warning(f"Error calculating Euclidean distances: {e}")
        return {
            "mean_distance": np.nan,
            "median_distance": np.nan,
            "min_distance": np.nan,
            "max_distance": np.nan,
            "std_distance": np.nan
        }


def _calculate_overall_score(metrics: Dict[str, Any]) -> float:
    """
    Calculate overall quality score from individual metrics

    Weighted combination of:
    - Wasserstein distance (lower is better)
    - RMSE (lower is better)
    - Correlation preservation (higher is better)
    - K-NN score (higher is better)
    """
    try:
        # Wasserstein component (normalize and invert)
        wasserstein_vals = list(metrics["wasserstein_distances"].values())
        wasserstein_avg = np.mean([v for v in wasserstein_vals if not np.isnan(v)])
        wasserstein_score = 1.0 / (1.0 + wasserstein_avg / 5.0)  # Normalize

        # RMSE component (normalize and invert)
        rmse_vals = list(metrics["rmse_by_column"].values())
        rmse_avg = np.mean([v for v in rmse_vals if not np.isnan(v)])
        rmse_score = 1.0 / (1.0 + rmse_avg / 10.0)  # Normalize

        # Correlation preservation (already 0-1)
        corr_score = metrics["correlation_preservation"]

        # K-NN score (already 0-1)
        knn_score = metrics["knn_imputation_score"]

        # Weighted average
        weights = [0.25, 0.25, 0.25, 0.25]  # Equal weights
        overall = (
            weights[0] * wasserstein_score +
            weights[1] * rmse_score +
            weights[2] * corr_score +
            weights[3] * knn_score
        )

        return float(max(0.0, min(1.0, overall)))

    except Exception as e:
        logger.warning(f"Error calculating overall score: {e}")
        return 0.0


def _generate_quality_summary(metrics: Dict[str, Any]) -> str:
    """Generate human-readable quality summary"""
    score = metrics["overall_quality_score"]

    if score >= 0.85:
        level = "✅ EXCELLENT"
        desc = "Quality score: {:.2f} - Production ready".format(score)
    elif score >= 0.70:
        level = "✓ GOOD"
        desc = "Quality score: {:.2f} - Minor adjustments needed".format(score)
    else:
        level = "⚠ NEEDS IMPROVEMENT"
        desc = "Quality score: {:.2f} - Review parameters".format(score)

    return f"{level} - {desc}"
