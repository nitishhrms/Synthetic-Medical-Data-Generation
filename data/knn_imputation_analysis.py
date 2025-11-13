"""
K-Nearest Neighbor Imputation Analysis
======================================

Implements MAR (Missing at Random) imputation analysis:
1. Takes complete real data
2. Artificially introduces missing values (MAR pattern)
3. Uses K-NN to impute missing values
4. Generates multi-panel visualization comparing:
   - Actual (complete data)
   - Imputed (K-NN imputed values)
   - Observed (data before imputation)

Based on the image: "MAR - Imputed vs Actual"
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder
from pathlib import Path
from scipy.stats import wasserstein_distance
from typing import Dict, Tuple


def introduce_mar_missingness(df: pd.DataFrame,
                               missing_rate: float = 0.25,
                               seed: int = 42) -> pd.DataFrame:
    """
    Introduce Missing at Random (MAR) pattern

    MAR: Missingness depends on observed variables
    Example: Higher BP values are more likely to be missing

    Args:
        df: Complete dataframe
        missing_rate: Proportion of values to make missing (0-1)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with MAR missingness introduced
    """
    rng = np.random.default_rng(seed)
    df_mar = df.copy()

    vitals = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']

    for vital in vitals:
        if vital not in df_mar.columns:
            continue

        n = len(df_mar)
        n_missing = int(n * missing_rate)

        # MAR: Higher values more likely to be missing
        # Create probability weights based on value magnitude
        values = df_mar[vital].values
        normalized = (values - values.min()) / (values.max() - values.min())
        weights = normalized ** 2  # Square to emphasize high values
        weights = weights / weights.sum()

        # Select indices to make missing based on weights
        missing_indices = rng.choice(n, size=n_missing, replace=False, p=weights)
        df_mar.loc[missing_indices, vital] = np.nan

    return df_mar


def prepare_data_for_knn(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Prepare data for KNN imputation by encoding categorical variables

    Args:
        df: DataFrame with mixed types

    Returns:
        Tuple of (encoded_df, encoder_dict)
    """
    df_encoded = df.copy()
    encoders = {}

    # Encode categorical columns
    categorical_cols = ['VisitName', 'TreatmentArm']
    for col in categorical_cols:
        if col in df_encoded.columns:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            encoders[col] = le

    return df_encoded, encoders


def knn_impute(df_with_missing: pd.DataFrame,
               k: int = 5) -> pd.DataFrame:
    """
    Perform K-NN imputation on data with missing values

    Args:
        df_with_missing: DataFrame with NaN values
        k: Number of nearest neighbors

    Returns:
        DataFrame with imputed values
    """
    # Prepare data
    df_encoded, encoders = prepare_data_for_knn(df_with_missing)

    # Select columns for imputation (numeric + encoded categorical)
    impute_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    if 'VisitName' in df_encoded.columns:
        impute_cols.insert(0, 'VisitName')
    if 'TreatmentArm' in df_encoded.columns:
        impute_cols.insert(1, 'TreatmentArm')

    # Filter to existing columns
    impute_cols = [c for c in impute_cols if c in df_encoded.columns]

    # Perform K-NN imputation
    imputer = KNNImputer(n_neighbors=k, weights='distance', metric='nan_euclidean')
    df_imputed = df_encoded.copy()
    df_imputed[impute_cols] = imputer.fit_transform(df_encoded[impute_cols])

    # Decode categorical columns back
    for col, encoder in encoders.items():
        df_imputed[col] = encoder.inverse_transform(df_imputed[col].astype(int))

    return df_imputed


def calculate_imputation_metrics(actual: pd.Series,
                                  imputed: pd.Series,
                                  missing_mask: pd.Series) -> Dict:
    """
    Calculate quality metrics for imputation

    Args:
        actual: Original complete values
        imputed: K-NN imputed values
        missing_mask: Boolean mask indicating which values were missing

    Returns:
        Dictionary of metrics
    """
    # Only compare values that were imputed
    actual_missing = actual[missing_mask]
    imputed_missing = imputed[missing_mask]

    # RMSE on imputed values
    rmse = np.sqrt(np.mean((actual_missing - imputed_missing) ** 2))

    # MAE on imputed values
    mae = np.mean(np.abs(actual_missing - imputed_missing))

    # Wasserstein distance (distribution similarity)
    wasserstein = wasserstein_distance(actual_missing, imputed_missing)

    # Correlation between actual and imputed
    correlation = np.corrcoef(actual_missing, imputed_missing)[0, 1]

    # Bias (mean difference)
    bias = np.mean(imputed_missing - actual_missing)

    return {
        'rmse': rmse,
        'mae': mae,
        'wasserstein': wasserstein,
        'correlation': correlation,
        'bias': bias,
        'n_imputed': missing_mask.sum()
    }


def create_mar_imputation_visualization(df_actual: pd.DataFrame,
                                        df_observed: pd.DataFrame,
                                        df_imputed: pd.DataFrame,
                                        output_file: str = 'mar_imputation_analysis.png'):
    """
    Create multi-panel histogram visualization comparing:
    - Actual (complete data)
    - Imputed (K-NN imputed)
    - Observed (before imputation)

    Similar to the image: "MAR - Imputed vs Actual"

    Args:
        df_actual: Complete original data
        df_observed: Data with missing values
        df_imputed: Data after K-NN imputation
        output_file: Output filename
    """
    vitals = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    vitals = [v for v in vitals if v in df_actual.columns]

    # Create figure with 2x2 grid (or 2x4 if you have 8 features)
    n_features = len(vitals)
    n_cols = 2
    n_rows = (n_features + 1) // 2

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 10))
    fig.suptitle('K-nearest Neighbor Imputation\nMAR - Imputed vs Actual',
                 fontsize=16, fontweight='bold', y=0.995)

    axes = axes.flatten() if n_features > 1 else [axes]

    for idx, vital in enumerate(vitals):
        ax = axes[idx]

        # Get data
        actual_vals = df_actual[vital].values
        observed_vals = df_observed[vital].dropna().values
        imputed_vals = df_imputed[vital].values

        # Create bins based on actual data range
        bins = np.linspace(actual_vals.min(), actual_vals.max(), 30)

        # Plot histograms with transparency
        ax.hist(actual_vals, bins=bins, alpha=0.4, color='gray',
                label='Actual (complete)', density=True, edgecolor='black', linewidth=0.5)
        ax.hist(imputed_vals, bins=bins, alpha=0.5, color='red',
                label='Imputed', density=True, edgecolor='darkred', linewidth=0.5)
        ax.hist(observed_vals, bins=bins, alpha=0.5, color='teal',
                label='Observed (original)', density=True, edgecolor='darkcyan', linewidth=0.5)

        # Calculate metrics for title
        missing_mask = df_observed[vital].isna()
        metrics = calculate_imputation_metrics(df_actual[vital], df_imputed[vital], missing_mask)

        # Title with feature name and key metric
        ax.set_title(f'{vital}\n(RMSE: {metrics["rmse"]:.2f}, Corr: {metrics["correlation"]:.3f})',
                     fontsize=11, fontweight='bold')
        ax.set_xlabel('Value', fontsize=9)
        ax.set_ylabel('Density', fontsize=9)
        ax.legend(fontsize=8, loc='upper right')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.tick_params(labelsize=8)

    # Hide unused subplots
    for idx in range(len(vitals), len(axes)):
        axes[idx].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved visualization: {output_file}")

    return fig


def generate_imputation_report(df_actual: pd.DataFrame,
                               df_observed: pd.DataFrame,
                               df_imputed: pd.DataFrame,
                               output_file: str = 'imputation_report.txt'):
    """
    Generate text report with detailed imputation metrics

    Args:
        df_actual: Complete original data
        df_observed: Data with missing values
        df_imputed: Data after K-NN imputation
        output_file: Output filename
    """
    vitals = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    vitals = [v for v in vitals if v in df_actual.columns]

    report = []
    report.append("=" * 80)
    report.append("K-NEAREST NEIGHBOR IMPUTATION ANALYSIS REPORT")
    report.append("MAR (Missing at Random) Pattern")
    report.append("=" * 80)
    report.append("")

    # Overall statistics
    total_values = len(df_actual) * len(vitals)
    total_missing = df_observed[vitals].isna().sum().sum()
    missing_rate = (total_missing / total_values) * 100

    report.append(f"Dataset: {len(df_actual)} records")
    report.append(f"Total values: {total_values}")
    report.append(f"Missing values introduced: {total_missing} ({missing_rate:.1f}%)")
    report.append("")
    report.append("=" * 80)
    report.append("IMPUTATION QUALITY METRICS BY FEATURE")
    report.append("=" * 80)
    report.append("")

    # Per-feature metrics
    for vital in vitals:
        missing_mask = df_observed[vital].isna()
        metrics = calculate_imputation_metrics(df_actual[vital], df_imputed[vital], missing_mask)

        report.append(f"{vital}:")
        report.append("-" * 40)
        report.append(f"  Values imputed: {metrics['n_imputed']}")
        report.append(f"  RMSE: {metrics['rmse']:.3f}")
        report.append(f"  MAE: {metrics['mae']:.3f}")
        report.append(f"  Wasserstein Distance: {metrics['wasserstein']:.3f}")
        report.append(f"  Correlation: {metrics['correlation']:.3f}")
        report.append(f"  Bias (mean diff): {metrics['bias']:.3f}")
        report.append("")

    # Overall summary
    report.append("=" * 80)
    report.append("OVERALL SUMMARY")
    report.append("=" * 80)
    report.append("")

    all_metrics = []
    for vital in vitals:
        missing_mask = df_observed[vital].isna()
        metrics = calculate_imputation_metrics(df_actual[vital], df_imputed[vital], missing_mask)
        all_metrics.append(metrics)

    avg_rmse = np.mean([m['rmse'] for m in all_metrics])
    avg_mae = np.mean([m['mae'] for m in all_metrics])
    avg_wasserstein = np.mean([m['wasserstein'] for m in all_metrics])
    avg_correlation = np.mean([m['correlation'] for m in all_metrics])

    report.append(f"Average RMSE: {avg_rmse:.3f}")
    report.append(f"Average MAE: {avg_mae:.3f}")
    report.append(f"Average Wasserstein: {avg_wasserstein:.3f}")
    report.append(f"Average Correlation: {avg_correlation:.3f}")
    report.append("")

    # Quality assessment
    if avg_correlation >= 0.85 and avg_rmse <= 5.0:
        quality = "EXCELLENT"
        assessment = "K-NN imputation successfully recovered the missing values with high accuracy."
    elif avg_correlation >= 0.70 and avg_rmse <= 10.0:
        quality = "GOOD"
        assessment = "K-NN imputation performed well with acceptable accuracy."
    else:
        quality = "FAIR"
        assessment = "K-NN imputation shows moderate performance. Consider adjusting K or using alternative methods."

    report.append(f"Quality Assessment: {quality}")
    report.append(f"Summary: {assessment}")
    report.append("")
    report.append("=" * 80)
    report.append("BUSINESS VALUE")
    report.append("=" * 80)
    report.append("")
    report.append("• Reduces trial re-runs by recovering missing data")
    report.append("• Maintains statistical power with complete datasets")
    report.append("• Cost savings from avoiding data collection re-do")
    report.append("• Enables complete case analysis without data loss")
    report.append("")

    # Write report
    report_text = "\n".join(report)
    with open(output_file, 'w') as f:
        f.write(report_text)

    print(f"✓ Saved report: {output_file}")
    print("\n" + report_text)

    return report_text


def main():
    """
    Main execution: MAR imputation analysis pipeline
    """
    print("=" * 80)
    print("K-NEAREST NEIGHBOR IMPUTATION ANALYSIS")
    print("MAR (Missing at Random) Pattern")
    print("=" * 80)
    print()

    # Configuration
    data_path = Path(__file__).parent / "pilot_trial_cleaned.csv"
    missing_rate = 0.25  # 25% missing values
    k_neighbors = 5
    seed = 42

    # Step 1: Load complete real data
    print("Step 1: Loading complete real data...")
    df_actual = pd.read_csv(data_path)
    print(f"  ✓ Loaded {len(df_actual)} records")
    print(f"  ✓ Features: {list(df_actual.columns)}")
    print()

    # Step 2: Introduce MAR missingness
    print(f"Step 2: Introducing MAR missingness ({missing_rate*100:.0f}%)...")
    df_observed = introduce_mar_missingness(df_actual, missing_rate=missing_rate, seed=seed)

    vitals = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    for vital in vitals:
        if vital in df_observed.columns:
            n_missing = df_observed[vital].isna().sum()
            pct = (n_missing / len(df_observed)) * 100
            print(f"  ✓ {vital}: {n_missing} missing ({pct:.1f}%)")
    print()

    # Step 3: Perform K-NN imputation
    print(f"Step 3: Performing K-NN imputation (k={k_neighbors})...")
    df_imputed = knn_impute(df_observed, k=k_neighbors)
    print(f"  ✓ Imputation complete")
    print(f"  ✓ Missing values after imputation: {df_imputed[vitals].isna().sum().sum()}")
    print()

    # Step 4: Generate visualization
    print("Step 4: Generating visualization...")
    create_mar_imputation_visualization(
        df_actual=df_actual,
        df_observed=df_observed,
        df_imputed=df_imputed,
        output_file='mar_imputation_analysis.png'
    )
    print()

    # Step 5: Generate detailed report
    print("Step 5: Generating imputation report...")
    generate_imputation_report(
        df_actual=df_actual,
        df_observed=df_observed,
        df_imputed=df_imputed,
        output_file='imputation_report.txt'
    )
    print()

    print("=" * 80)
    print("✅ MAR IMPUTATION ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Generated files:")
    print("  • mar_imputation_analysis.png - Multi-panel histogram visualization")
    print("  • imputation_report.txt - Detailed quality metrics")
    print()


if __name__ == "__main__":
    main()
