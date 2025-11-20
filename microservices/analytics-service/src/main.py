"""
Analytics Service - Clinical Trial Statistics and Reporting
Handles statistics, RBQM, CSR generation, SDTM export
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import uvicorn
import os

from stats import (
    calculate_week12_statistics,
    calculate_recist_orr,
    ks_distance
)
from rbqm import generate_rbqm_summary
from csr import generate_csr_draft
from sdtm import export_to_sdtm_vs, export_to_sdtm_dm, export_to_sdtm_lb
from db_utils import db, cache, startup_db, shutdown_db
from demographics_analytics import (
    calculate_baseline_characteristics,
    calculate_demographic_summary,
    assess_treatment_arm_balance,
    compare_demographics_quality
)
from labs_analytics import (
    calculate_labs_summary,
    detect_abnormal_labs,
    generate_shift_tables,
    compare_labs_quality,
    detect_safety_signals,
    analyze_labs_longitudinal
)

app = FastAPI(
    title="Analytics Service",
    description="Clinical Trial Analytics, RBQM, CSR, and SDTM Export",
    version="1.0.0"
)

# Database lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup"""
    await startup_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    await shutdown_db()

# CORS configuration
import os
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "")
if ALLOWED_ORIGINS_ENV:
    ALLOWED_ORIGINS = ALLOWED_ORIGINS_ENV.split(",")
else:
    # Default: allow localhost origins for development
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*"  # Allow all for development
    ]

if "*" in ALLOWED_ORIGINS and os.getenv("ENVIRONMENT") == "production":
    import warnings
    warnings.warn("CORS wildcard enabled in production - security risk!", UserWarning)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Pydantic models
class VitalsData(BaseModel):
    data: List[Dict[str, Any]]

class StatisticsRequest(BaseModel):
    vitals_data: List[Dict[str, Any]]

class TreatmentGroupStats(BaseModel):
    n: int
    mean_systolic: float
    std_systolic: float
    se_systolic: float

class TreatmentEffect(BaseModel):
    difference: float
    se_difference: float
    t_statistic: float
    p_value: float
    ci_95_lower: float
    ci_95_upper: float

class Interpretation(BaseModel):
    significant: bool
    effect_size: str
    clinical_relevance: str

class StatisticsResponse(BaseModel):
    treatment_groups: Dict[str, TreatmentGroupStats]
    treatment_effect: TreatmentEffect
    interpretation: Interpretation

class RECISTRequest(BaseModel):
    vitals_data: List[Dict[str, Any]]
    p_active: float = Field(default=0.35, ge=0, le=1)
    p_placebo: float = Field(default=0.20, ge=0, le=1)
    seed: int = Field(default=777)

class RECISTResponse(BaseModel):
    recist_data: List[Dict[str, Any]]
    orr_active: float
    orr_placebo: float
    orr_difference: float
    p_value: float

class RBQMRequest(BaseModel):
    vitals_data: List[Dict[str, Any]]
    queries_data: List[Dict[str, Any]]
    ae_data: Optional[List[Dict[str, Any]]] = None
    thresholds: Dict[str, float] = Field(default={"q_rate_site": 6.0, "missing_subj": 3, "serious_related": 5})
    site_size: int = Field(default=20)

class RBQMResponse(BaseModel):
    summary_markdown: str
    site_summary: List[Dict[str, Any]]
    kris: Dict[str, Any]

class CSRRequest(BaseModel):
    statistics: Dict[str, Any]
    ae_data: Optional[List[Dict[str, Any]]] = None
    n_rows: int

class CSRResponse(BaseModel):
    csr_markdown: str

class SDTMRequest(BaseModel):
    vitals_data: List[Dict[str, Any]]

class SDTMResponse(BaseModel):
    sdtm_data: List[Dict[str, Any]]
    rows: int

class PCAComparisonRequest(BaseModel):
    original_data: List[Dict[str, Any]] = Field(..., description="Original/pilot data")
    synthetic_data: List[Dict[str, Any]] = Field(..., description="Synthetic data to compare")

class PCAComparisonResponse(BaseModel):
    original_pca: List[Dict[str, float]] = Field(..., description="PCA coordinates for original data")
    synthetic_pca: List[Dict[str, float]] = Field(..., description="PCA coordinates for synthetic data")
    explained_variance: List[float] = Field(..., description="Explained variance ratio per component")
    quality_score: float = Field(..., description="Similarity score (0-1, higher is better)")

class ComprehensiveQualityRequest(BaseModel):
    original_data: List[Dict[str, Any]] = Field(..., description="Original/real clinical trial data")
    synthetic_data: List[Dict[str, Any]] = Field(..., description="Synthetic data to validate")
    k: int = Field(default=5, ge=1, le=20, description="Number of nearest neighbors")

class ComprehensiveQualityResponse(BaseModel):
    wasserstein_distances: Dict[str, float] = Field(..., description="Wasserstein distance per numeric column")
    correlation_preservation: float = Field(..., description="How well correlations are preserved (0-1)")
    rmse_by_column: Dict[str, float] = Field(..., description="RMSE for each numeric column")
    knn_imputation_score: float = Field(..., description="K-NN imputation quality score (0-1)")
    overall_quality_score: float = Field(..., description="Aggregate quality score (0-1)")
    euclidean_distances: Dict[str, Any] = Field(..., description="Distance statistics")
    summary: str = Field(..., description="Human-readable quality summary")

# Demographics models
class DemographicsRequest(BaseModel):
    demographics_data: List[Dict[str, Any]]

class DemographicsCompareRequest(BaseModel):
    real_demographics: List[Dict[str, Any]]
    synthetic_demographics: List[Dict[str, Any]]

# Labs models
class LabsRequest(BaseModel):
    labs_data: List[Dict[str, Any]]

class LabsCompareRequest(BaseModel):
    real_labs: List[Dict[str, Any]]
    synthetic_labs: List[Dict[str, Any]]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db.pool else "disconnected"
    cache_status = "connected" if cache.enabled and cache.client else "disconnected"

    return {
        "status": "healthy",
        "service": "analytics-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "cache": cache_status
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Analytics Service",
        "version": "1.2.0",
        "features": [
            "Week-12 Statistics (t-test)",
            "RECIST + ORR Analysis",
            "RBQM Summary",
            "CSR Draft Generation",
            "SDTM Export (Vitals + Demographics + Labs)",
            "Demographics Analytics (Baseline, Balance, Quality)",
            "Labs Analytics (Summary, Abnormal Detection, Shift Tables, Safety Signals, Longitudinal)",
            "Quality Assessment (PCA, K-NN, Wasserstein)"
        ],
        "endpoints": {
            "health": "/health",
            "stats_week12": "/stats/week12",
            "stats_recist": "/stats/recist",
            "demographics_baseline": "/stats/demographics/baseline",
            "demographics_summary": "/stats/demographics/summary",
            "demographics_balance": "/stats/demographics/balance",
            "labs_summary": "/stats/labs/summary",
            "labs_abnormal": "/stats/labs/abnormal",
            "labs_shift_tables": "/stats/labs/shift-tables",
            "labs_safety_signals": "/stats/labs/safety-signals",
            "labs_longitudinal": "/stats/labs/longitudinal",
            "rbqm": "/rbqm/summary",
            "csr": "/csr/draft",
            "sdtm_vitals": "/sdtm/export",
            "sdtm_demographics": "/sdtm/demographics/export",
            "sdtm_labs": "/sdtm/labs/export",
            "quality_pca": "/quality/pca-comparison",
            "quality_comprehensive": "/quality/comprehensive",
            "quality_demographics": "/quality/demographics/compare",
            "quality_labs": "/quality/labs/compare",
            "docs": "/docs"
        }
    }

@app.post("/stats/week12", response_model=StatisticsResponse)
async def calculate_statistics(request: StatisticsRequest):
    """
    Calculate Week-12 statistics (Active vs Placebo)

    Performs Welch's t-test on Week-12 Systolic BP data

    Returns nested structure with:
    - treatment_groups: Statistics for Active and Placebo arms
    - treatment_effect: Difference, t-statistic, p-value, confidence intervals
    - interpretation: Significance, effect size, clinical relevance
    """
    try:
        df = pd.DataFrame(request.vitals_data)
        stats = calculate_week12_statistics(df)

        # Parse nested structure
        return StatisticsResponse(
            treatment_groups={
                "Active": TreatmentGroupStats(**stats["treatment_groups"]["Active"]),
                "Placebo": TreatmentGroupStats(**stats["treatment_groups"]["Placebo"])
            },
            treatment_effect=TreatmentEffect(**stats["treatment_effect"]),
            interpretation=Interpretation(**stats["interpretation"])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistics calculation failed: {str(e)}"
        )

@app.post("/stats/recist", response_model=RECISTResponse)
async def calculate_recist(request: RECISTRequest):
    """
    Simulate RECIST responses and calculate ORR (Objective Response Rate)

    For oncology trials: CR/PR = responders, SD/PD = non-responders
    """
    try:
        df = pd.DataFrame(request.vitals_data)
        result = calculate_recist_orr(
            df,
            p_active=request.p_active,
            p_placebo=request.p_placebo,
            seed=request.seed
        )

        return RECISTResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RECIST calculation failed: {str(e)}"
        )

@app.post("/rbqm/summary", response_model=RBQMResponse)
async def generate_rbqm(request: RBQMRequest):
    """
    Generate Risk-Based Quality Management (RBQM) summary

    Includes:
    - Key Risk Indicators (KRIs)
    - Quality Tolerance Limits (QTL)
    - Site-level quality metrics
    """
    try:
        vitals_df = pd.DataFrame(request.vitals_data)
        queries_df = pd.DataFrame(request.queries_data)
        ae_df = pd.DataFrame(request.ae_data) if request.ae_data else None

        summary_md, site_summary_df, kris = generate_rbqm_summary(
            queries_df=queries_df,
            vitals_df=vitals_df,
            ae_df=ae_df,
            thresholds=request.thresholds,
            site_size=request.site_size
        )

        return RBQMResponse(
            summary_markdown=summary_md,
            site_summary=site_summary_df.to_dict(orient="records"),
            kris=kris
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RBQM generation failed: {str(e)}"
        )

@app.post("/csr/draft", response_model=CSRResponse)
async def generate_csr(request: CSRRequest):
    """
    Generate Clinical Study Report (CSR) draft

    Includes efficacy, safety, and data quality sections
    """
    try:
        ae_df = pd.DataFrame(request.ae_data) if request.ae_data else None

        csr_md = generate_csr_draft(
            stats=request.statistics,
            ae_df=ae_df,
            n_rows=request.n_rows
        )

        return CSRResponse(csr_markdown=csr_md)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSR generation failed: {str(e)}"
        )

@app.post("/sdtm/export", response_model=SDTMResponse)
async def export_sdtm(request: SDTMRequest):
    """
    Export vitals to SDTM VS domain format

    CDISC SDTM standard for clinical trial data submission
    """
    try:
        df = pd.DataFrame(request.vitals_data)
        sdtm_df = export_to_sdtm_vs(df)

        return SDTMResponse(
            sdtm_data=sdtm_df.to_dict(orient="records"),
            rows=len(sdtm_df)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SDTM export failed: {str(e)}"
        )

@app.post("/quality/pca-comparison", response_model=PCAComparisonResponse)
async def compare_data_with_pca(request: PCAComparisonRequest):
    """
    Compare original vs synthetic data using PCA visualization

    Performs dimensionality reduction to assess how well synthetic data
    matches the distributional characteristics of original data.

    **Use Case:**
    - Validate bootstrap or other generation methods
    - Visual quality assessment
    - Distribution similarity check

    **How it works:**
    1. Combines original + synthetic data
    2. Label-encodes categorical columns (VisitName, TreatmentArm)
    3. Standardizes numeric features
    4. Applies PCA to reduce to 2D
    5. Returns coordinates for plotting
    6. Calculates similarity score

    **Quality Score:**
    - 1.0 = Perfect match (distributions identical)
    - 0.8+ = Excellent similarity
    - 0.6-0.8 = Good similarity
    - <0.6 = Poor match, review generation parameters
    """
    try:
        from sklearn.preprocessing import LabelEncoder, StandardScaler
        from sklearn.decomposition import PCA
        import numpy as np

        # Load datasets
        df_orig = pd.DataFrame(request.original_data)
        df_syn = pd.DataFrame(request.synthetic_data)

        # Add source labels
        df_orig["_Source"] = "Original"
        df_syn["_Source"] = "Synthetic"

        # Combine for uniform encoding
        df_all = pd.concat([df_orig, df_syn], ignore_index=True)

        # Label encode categorical columns
        for col in ["VisitName", "TreatmentArm"]:
            if col in df_all.columns:
                le = LabelEncoder()
                df_all[col] = le.fit_transform(df_all[col].astype(str))

        # Select numeric columns (ignore SubjectID and _Source)
        numeric_cols = ["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]
        if "VisitName" in df_all.columns:
            numeric_cols.insert(0, "VisitName")
        if "TreatmentArm" in df_all.columns:
            numeric_cols.insert(1, "TreatmentArm")

        # Filter to only columns that exist
        numeric_cols = [c for c in numeric_cols if c in df_all.columns]

        X = df_all[numeric_cols].copy()
        y = df_all["_Source"]

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # PCA to 2D
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X_scaled)

        # Attach coordinates
        df_all["PCA1"] = X_pca[:, 0]
        df_all["PCA2"] = X_pca[:, 1]

        # Separate for output
        df_orig_pca = df_all[df_all["_Source"] == "Original"]
        df_syn_pca = df_all[df_all["_Source"] == "Synthetic"]

        # Format output
        original_pca = [
            {"pca1": row["PCA1"], "pca2": row["PCA2"]}
            for _, row in df_orig_pca.iterrows()
        ]
        synthetic_pca = [
            {"pca1": row["PCA1"], "pca2": row["PCA2"]}
            for _, row in df_syn_pca.iterrows()
        ]

        # Calculate quality score (Wasserstein distance in PCA space)
        from scipy.stats import wasserstein_distance

        # Calculate distance in each PC dimension
        dist_pc1 = wasserstein_distance(
            df_orig_pca["PCA1"].values,
            df_syn_pca["PCA1"].values
        )
        dist_pc2 = wasserstein_distance(
            df_orig_pca["PCA2"].values,
            df_syn_pca["PCA2"].values
        )

        # Normalize distances and convert to similarity score (0-1)
        # Lower distance = higher score
        max_dist = max(
            df_all["PCA1"].std() * 2,  # Rough estimate of max expected distance
            df_all["PCA2"].std() * 2
        )
        normalized_dist = (dist_pc1 + dist_pc2) / (2 * max_dist)
        quality_score = max(0.0, 1.0 - normalized_dist)

        return PCAComparisonResponse(
            original_pca=original_pca,
            synthetic_pca=synthetic_pca,
            explained_variance=pca.explained_variance_ratio_.tolist(),
            quality_score=round(float(quality_score), 3)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PCA comparison failed: {str(e)}"
        )

@app.post("/quality/comprehensive", response_model=ComprehensiveQualityResponse)
async def comprehensive_quality_assessment(request: ComprehensiveQualityRequest):
    """
    Comprehensive quality assessment for synthetic data (Professor's Requirements)

    Implements multiple statistical measures to validate synthetic data quality:

    **Metrics Computed:**
    1. **Wasserstein Distance** - Distribution similarity per column (lower is better)
    2. **Correlation Preservation** - How well inter-variable relationships are maintained
    3. **RMSE** - Root Mean Square Error for numeric columns
    4. **K-NN Imputation Score** - Quality of nearest-neighbor matching
    5. **Euclidean Distance Statistics** - Distance measures between datasets

    **Business Value:**
    - Validates synthetic data is realistic and usable
    - Reduces need for expensive trial re-runs
    - Provides evidence for regulatory submissions
    - Scientific rigor for publications

    **Interpretation:**
    - Overall Score ≥ 0.85: Excellent quality, production-ready
    - Overall Score 0.70-0.85: Good quality, minor adjustments needed
    - Overall Score < 0.70: Review generation parameters
    """
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.neighbors import NearestNeighbors
        from scipy.stats import wasserstein_distance
        import numpy as np

        # Load datasets
        df_orig = pd.DataFrame(request.original_data)
        df_syn = pd.DataFrame(request.synthetic_data)

        # Select numeric columns for analysis
        numeric_cols = ["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]
        numeric_cols = [c for c in numeric_cols if c in df_orig.columns and c in df_syn.columns]

        if not numeric_cols:
            raise ValueError("No common numeric columns found for comparison")

        # ===== 1. Wasserstein Distance (Distribution Similarity) =====
        wasserstein_distances = {}
        for col in numeric_cols:
            orig_vals = df_orig[col].dropna().values
            syn_vals = df_syn[col].dropna().values
            if len(orig_vals) > 0 and len(syn_vals) > 0:
                wasserstein_distances[col] = float(wasserstein_distance(orig_vals, syn_vals))

        # ===== 2. Correlation Preservation =====
        corr_orig = df_orig[numeric_cols].corr()
        corr_syn = df_syn[numeric_cols].corr()

        # Flatten correlation matrices and compute similarity
        corr_diff = np.abs(corr_orig.values - corr_syn.values)
        # Use 1 - mean absolute difference as correlation preservation score
        correlation_preservation = float(1.0 - np.mean(corr_diff[np.triu_indices_from(corr_diff, k=1)]))
        correlation_preservation = max(0.0, min(1.0, correlation_preservation))

        # ===== 3. RMSE by Column (Compared to Nearest Neighbors) =====
        rmse_by_column = {}

        # Standardize data for distance calculations
        scaler = StandardScaler()
        X_orig = scaler.fit_transform(df_orig[numeric_cols].fillna(df_orig[numeric_cols].mean()))
        X_syn = scaler.transform(df_syn[numeric_cols].fillna(df_syn[numeric_cols].mean()))

        # Fit K-NN on original data
        knn = NearestNeighbors(n_neighbors=min(request.k, len(X_orig)), metric='euclidean')
        knn.fit(X_orig)

        # Find nearest neighbors for each synthetic point
        distances, indices = knn.kneighbors(X_syn)

        # For each synthetic row, find its K nearest original rows
        # Calculate RMSE for each column using the nearest neighbor mean
        for col_idx, col in enumerate(numeric_cols):
            syn_vals = df_syn[col].fillna(df_syn[col].mean()).values
            # For each synthetic point, get the mean of its K nearest neighbors
            orig_vals_knn = np.array([
                df_orig[col].iloc[indices[i]].mean()
                for i in range(len(indices))
            ])
            rmse = float(np.sqrt(np.mean((syn_vals - orig_vals_knn) ** 2)))
            rmse_by_column[col] = round(rmse, 3)

        # ===== 4. K-NN Imputation Score =====
        # Lower distance = better match = higher score
        mean_distance = float(np.mean(distances))
        # Normalize by typical distance scale (use max observed distance)
        max_distance = float(np.max(distances))
        if max_distance > 0:
            knn_imputation_score = float(1.0 - (mean_distance / max_distance))
        else:
            knn_imputation_score = 1.0
        knn_imputation_score = max(0.0, min(1.0, knn_imputation_score))

        # ===== 5. Euclidean Distance Statistics =====
        euclidean_distances = {
            "mean_distance": round(mean_distance, 3),
            "median_distance": round(float(np.median(distances)), 3),
            "min_distance": round(float(np.min(distances)), 3),
            "max_distance": round(float(np.max(distances)), 3),
            "std_distance": round(float(np.std(distances)), 3)
        }

        # ===== 6. Overall Quality Score (Weighted Average) =====
        # Wasserstein: normalize and invert (lower is better)
        wasserstein_avg = np.mean(list(wasserstein_distances.values()))
        # Typical Wasserstein for vitals is 0-20 range, normalize to 0-1
        wasserstein_score = max(0.0, 1.0 - (wasserstein_avg / 20.0))

        # RMSE: normalize (lower is better)
        rmse_avg = np.mean(list(rmse_by_column.values()))
        # Typical RMSE is 0-15, normalize
        rmse_score = max(0.0, 1.0 - (rmse_avg / 15.0))

        # Weighted average
        overall_quality_score = float(
            0.25 * wasserstein_score +
            0.30 * correlation_preservation +
            0.20 * rmse_score +
            0.25 * knn_imputation_score
        )
        overall_quality_score = round(max(0.0, min(1.0, overall_quality_score)), 3)

        # ===== 7. Generate Summary =====
        if overall_quality_score >= 0.85:
            summary = f"✅ EXCELLENT - Quality score: {overall_quality_score:.2f}. Synthetic data is production-ready and closely matches original distribution."
        elif overall_quality_score >= 0.70:
            summary = f"✓ GOOD - Quality score: {overall_quality_score:.2f}. Synthetic data is usable with minor differences from original."
        else:
            summary = f"⚠️ NEEDS IMPROVEMENT - Quality score: {overall_quality_score:.2f}. Consider adjusting generation parameters or using a different method."

        summary += f" | Wasserstein avg: {wasserstein_avg:.2f}, Correlation preserved: {correlation_preservation:.2%}, RMSE avg: {rmse_avg:.2f}, K-NN score: {knn_imputation_score:.2f}"

        return ComprehensiveQualityResponse(
            wasserstein_distances={k: round(v, 3) for k, v in wasserstein_distances.items()},
            correlation_preservation=round(correlation_preservation, 3),
            rmse_by_column=rmse_by_column,
            knn_imputation_score=round(knn_imputation_score, 3),
            overall_quality_score=overall_quality_score,
            euclidean_distances=euclidean_distances,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality assessment failed: {str(e)}"
        )


# ============================================================================
# DEMOGRAPHICS ANALYTICS ENDPOINTS (Phase 1)
# ============================================================================

@app.post("/stats/demographics/baseline")
async def demographics_baseline(request: DemographicsRequest):
    """
    Generate baseline characteristics table (Table 1)

    **Purpose:**
    Creates the standard demographics table (Table 1) found in clinical trial reports,
    showing baseline characteristics overall and by treatment arm.

    **Returns:**
    - Overall statistics across all subjects
    - Statistics by treatment arm (Active vs Placebo)
    - P-values for balance tests (t-test for continuous, chi-square for categorical)
    - Clinical interpretation of randomization balance

    **Use Case:**
    - Required for all clinical study reports
    - Demonstrates proper randomization
    - Baseline population description
    """
    try:
        df = pd.DataFrame(request.demographics_data)
        result = calculate_baseline_characteristics(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Baseline characteristics calculation failed: {str(e)}"
        )


@app.post("/stats/demographics/summary")
async def demographics_summary(request: DemographicsRequest):
    """
    Calculate demographic distribution summary for visualization

    **Purpose:**
    Provides aggregated demographic distributions suitable for charts and graphs.

    **Returns:**
    - Age distribution by brackets (18-30, 31-45, 46-60, 61+)
    - Gender distribution (counts and percentages)
    - Race distribution
    - Ethnicity distribution
    - BMI categories (WHO classification)

    **Use Case:**
    - Dashboard visualizations
    - Quick population overview
    - Diversity assessment
    """
    try:
        df = pd.DataFrame(request.demographics_data)
        result = calculate_demographic_summary(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demographic summary calculation failed: {str(e)}"
        )


@app.post("/stats/demographics/balance")
async def demographics_balance(request: DemographicsRequest):
    """
    Assess treatment arm balance (randomization quality check)

    **Purpose:**
    Validates that randomization produced balanced treatment arms across
    all demographic variables. Poor balance may indicate randomization issues.

    **Statistical Tests:**
    - Continuous variables (Age, Weight, Height, BMI): Welch's t-test
    - Categorical variables (Gender, Race, Ethnicity): Chi-square test
    - Effect sizes: Cohen's d (standardized mean difference)

    **Returns:**
    - P-values for each demographic variable
    - Standardized differences (Cohen's d)
    - Overall balance assessment (Well-balanced / Acceptable / Poor)
    - Flags for variables with significant imbalance

    **Interpretation:**
    - P-value > 0.05: Arms are balanced
    - |Cohen's d| < 0.2: Negligible difference
    - |Cohen's d| 0.2-0.5: Small difference
    - |Cohen's d| > 0.5: Moderate-to-large difference (concern)

    **Use Case:**
    - Quality control for trial randomization
    - Regulatory requirement for CSR
    - Identifying covariates for adjusted analysis
    """
    try:
        df = pd.DataFrame(request.demographics_data)
        result = assess_treatment_arm_balance(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Treatment arm balance assessment failed: {str(e)}"
        )


@app.post("/quality/demographics/compare")
async def demographics_quality(request: DemographicsCompareRequest):
    """
    Compare real vs synthetic demographics data quality

    **Purpose:**
    Validates that synthetic demographics match real-world clinical trial demographics
    using multiple statistical metrics.

    **Metrics Computed:**
    1. **Wasserstein Distance** - Distribution similarity for continuous variables (Age, Weight, Height, BMI)
       - Lower is better (0 = identical distributions)
       - Typical acceptable range: < 5.0

    2. **Chi-square Tests** - Distribution match for categorical variables (Gender, Race, Ethnicity)
       - P-value > 0.05 indicates distributions are similar

    3. **Correlation Preservation** - How well inter-variable relationships are maintained
       - 1.0 = perfect preservation
       - > 0.85 = excellent

    4. **Overall Quality Score** (0-1 scale)
       - ≥ 0.85: Excellent - Production ready
       - 0.70-0.85: Good - Minor adjustments may help
       - < 0.70: Needs improvement

    **Returns:**
    - Wasserstein distances for each continuous variable
    - Chi-square test results for each categorical variable
    - Correlation preservation score
    - Overall quality score
    - Detailed interpretation and recommendations

    **Use Case:**
    - Validating synthetic data generation methods
    - Quality assurance before using synthetic data for analysis
    - Regulatory evidence of synthetic data fidelity
    - Method comparison (MVN vs Bootstrap vs LLM)
    """
    try:
        real_df = pd.DataFrame(request.real_demographics)
        synthetic_df = pd.DataFrame(request.synthetic_demographics)
        result = compare_demographics_quality(real_df, synthetic_df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demographics quality comparison failed: {str(e)}"
        )


@app.post("/sdtm/demographics/export")
async def demographics_sdtm_export(request: DemographicsRequest):
    """
    Export demographics to SDTM DM (Demographics) domain format

    **Purpose:**
    Converts demographics data to CDISC SDTM DM domain format for regulatory submission.

    **SDTM DM Domain Variables:**
    - STUDYID: Study identifier
    - DOMAIN: DM (Demographics)
    - USUBJID: Unique subject identifier
    - SUBJID: Subject identifier
    - RFSTDTC: Reference start date
    - RFENDTC: Reference end date
    - SITEID: Site identifier
    - AGE: Age in years
    - AGEU: Age units (YEARS)
    - SEX: Sex (M/F/U)
    - RACE: Race
    - ETHNIC: Ethnicity
    - ARMCD: Planned arm code (ACT/PBO/UNK)
    - ARM: Planned arm description
    - ACTARMCD: Actual arm code
    - ACTARM: Actual arm description

    **Compliance:**
    - Follows CDISC SDTM-IG v3.4
    - FDA/EMA submission ready
    - Includes all required DM domain variables

    **Use Case:**
    - Regulatory submission (IND, NDA, BLA)
    - Data package preparation
    - SDTM validation testing
    """
    try:
        df = pd.DataFrame(request.demographics_data)
        sdtm_df = export_to_sdtm_dm(df)

        return {
            "sdtm_data": sdtm_df.to_dict(orient="records"),
            "rows": len(sdtm_df),
            "domain": "DM",
            "compliance": "SDTM-IG v3.4"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SDTM DM export failed: {str(e)}"
        )


# ============================================================================
# LABS ANALYTICS ENDPOINTS (Phase 2)
# ============================================================================

@app.post("/stats/labs/summary")
async def labs_summary(request: LabsRequest):
    """
    Calculate lab results summary by test, visit, treatment arm

    **Purpose:**
    Provides comprehensive descriptive statistics for all laboratory tests,
    stratified by visit and treatment arm.

    **Returns:**
    - by_test: Summary statistics (mean, median, SD, range, quartiles) for each lab test
    - by_visit: Observation counts and test coverage by visit
    - by_arm: Mean values by treatment arm for each test
    - overall: Total observations, subjects, tests, visits

    **Statistical Metrics:**
    - Mean, median, standard deviation
    - Min, max, 25th and 75th percentiles
    - Sample size (n) per category

    **Use Case:**
    - Laboratory data overview for study reports
    - Identifying data completeness
    - Baseline vs endpoint comparisons
    - Treatment arm comparisons
    """
    try:
        df = pd.DataFrame(request.labs_data)
        result = calculate_labs_summary(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Labs summary calculation failed: {str(e)}"
        )


@app.post("/stats/labs/abnormal")
async def labs_abnormal(request: LabsRequest):
    """
    Detect abnormal lab values with CTCAE grading

    **Purpose:**
    Identifies laboratory abnormalities using CTCAE v5.0 grading criteria
    for safety monitoring and adverse event reporting.

    **CTCAE Grading (Grade 0-4):**
    - Grade 0: Normal
    - Grade 1: Mild abnormality
    - Grade 2: Moderate abnormality
    - Grade 3: Severe abnormality
    - Grade 4: Life-threatening or disabling

    **Supported Tests:**
    - Liver: ALT, AST, Bilirubin
    - Kidney: Creatinine, eGFR
    - Hematology: Hemoglobin, WBC, Platelets

    **Returns:**
    - abnormal_observations: List of all abnormal values with CTCAE grades
    - summary_by_grade: Count of observations per grade (1-4)
    - summary_by_test: Abnormality rates per test
    - high_risk_subjects: Subjects with Grade 3+ abnormalities
    - total_abnormal: Total count of abnormal observations
    - abnormal_rate: Percentage of all observations that are abnormal

    **Use Case:**
    - Safety monitoring (DSMB reports)
    - Identifying subjects requiring dose modification
    - Adverse event reporting
    - Protocol-defined stopping rules
    """
    try:
        df = pd.DataFrame(request.labs_data)
        result = detect_abnormal_labs(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Abnormal labs detection failed: {str(e)}"
        )


@app.post("/stats/labs/shift-tables")
async def labs_shift_tables(request: LabsRequest):
    """
    Generate baseline-to-endpoint shift analysis

    **Purpose:**
    Analyzes how lab values shift from baseline (first visit) to endpoint (last visit),
    showing transitions between Normal and Abnormal categories.

    **Shift Categories:**
    - Normal → Normal: Subject remained normal throughout
    - Normal → Abnormal: Treatment-emergent abnormality
    - Abnormal → Normal: Improvement/normalization
    - Abnormal → Abnormal: Persistent abnormality

    **Returns:**
    - baseline_visit: Name of baseline visit used
    - endpoint_visit: Name of endpoint visit used
    - shift_tables: For each lab test:
      - shift_matrix: 2x2 contingency table
      - percentages: Percentage in each shift category
      - counts: Subject counts in each category
      - total_subjects: Total with paired data
    - chi_square_tests: Statistical tests for shift patterns
      - chi_square: Test statistic
      - p_value: Statistical significance
      - significant: Boolean (p < 0.05)

    **Clinical Interpretation:**
    - High Normal→Abnormal %: Potential safety concern
    - High Abnormal→Normal %: Evidence of treatment benefit or lab fluctuation
    - Chi-square p < 0.05: Shift pattern is non-random

    **Use Case:**
    - Safety assessment (treatment-emergent abnormalities)
    - Efficacy evaluation (lab normalization)
    - Regulatory submissions (shift table requirement)
    - Protocol-defined lab monitoring
    """
    try:
        df = pd.DataFrame(request.labs_data)
        result = generate_shift_tables(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shift table generation failed: {str(e)}"
        )


@app.post("/quality/labs/compare")
async def labs_quality(request: LabsCompareRequest):
    """
    Compare real vs synthetic lab data quality

    **Purpose:**
    Validates that synthetic laboratory data matches real-world clinical trial
    lab distributions using statistical similarity metrics.

    **Metrics Computed:**
    1. **Wasserstein Distance** - Distribution similarity for each lab test
       - Lower is better (0 = identical)
       - Normalized by real mean for relative comparison

    2. **Kolmogorov-Smirnov Tests** - Distribution comparison
       - P-value > 0.05 indicates distributions are similar
       - Statistic: Maximum difference between CDFs

    3. **Mean Differences** - Absolute and percentage differences
       - Shows bias in synthetic data generation
       - Percentage difference helps identify relative errors

    4. **Overall Quality Score** (0-1 scale)
       - 0.6 × Wasserstein similarity + 0.4 × KS test pass rate
       - ≥ 0.85: Excellent
       - 0.70-0.85: Good
       - < 0.70: Needs improvement

    **Returns:**
    - wasserstein_distances: Distance for each test
    - ks_tests: KS statistic, p-value, similarity flag per test
    - mean_differences: Real mean, synthetic mean, absolute and % diff
    - overall_quality_score: Aggregate quality metric
    - interpretation: Clinical quality assessment

    **Use Case:**
    - Validating lab data generation methods
    - Comparing MVN vs Bootstrap vs LLM approaches
    - Quality assurance before using synthetic data
    - Method parameter tuning
    """
    try:
        real_df = pd.DataFrame(request.real_labs)
        synthetic_df = pd.DataFrame(request.synthetic_labs)
        result = compare_labs_quality(real_df, synthetic_df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Labs quality comparison failed: {str(e)}"
        )


@app.post("/stats/labs/safety-signals")
async def labs_safety_signals(request: LabsRequest):
    """
    Detect potential safety signals in lab data

    **Purpose:**
    Identifies clinically significant laboratory-based safety signals
    using established medical criteria.

    **Safety Signals Detected:**

    1. **Hy's Law (Drug-Induced Liver Injury - DILI)**
       - Criteria: ALT or AST >3× ULN AND Bilirubin >2× ULN
       - Significance: 10-50% risk of severe liver injury or death
       - Regulatory: FDA requires reporting, may halt trial

    2. **Kidney Function Decline**
       - Criteria: eGFR decrease >25% from baseline
       - Severity:
         - 25-50% decline: Moderate risk
         - >50% decline: High risk
       - Clinical: May require dose adjustment or discontinuation

    3. **Bone Marrow Suppression**
       - Criteria (any of):
         - Hemoglobin <8 g/dL (severe anemia)
         - WBC <2.0 × 10⁹/L (severe leukopenia)
         - Platelets <50 × 10⁹/L (severe thrombocytopenia)
       - Severity: High risk if ≥2 criteria met
       - Clinical: Infection risk, bleeding risk

    **Returns:**
    - hys_law_cases: Subjects meeting Hy's Law criteria with ALT, bilirubin values
    - kidney_decline_cases: Subjects with significant eGFR decline
    - bone_marrow_cases: Subjects with severe hematologic abnormalities
    - overall_safety_summary:
      - Counts and rates for each safety signal
      - any_safety_signal: Boolean flag

    **Use Case:**
    - DSMB (Data Safety Monitoring Board) reports
    - Protocol-defined stopping rules
    - Regulatory safety updates (IND safety reports)
    - Risk-benefit assessment
    - Subject management (dose holds, discontinuation)
    """
    try:
        df = pd.DataFrame(request.labs_data)
        result = detect_safety_signals(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety signal detection failed: {str(e)}"
        )


@app.post("/stats/labs/longitudinal")
async def labs_longitudinal(request: LabsRequest):
    """
    Time-series analysis of lab trends

    **Purpose:**
    Analyzes how laboratory values change over time (longitudinal trends)
    using linear regression and trend detection.

    **Statistical Methods:**
    - Linear regression (slope, R², p-value)
    - Visit-level mean and standard deviation
    - Trend direction classification (increasing/decreasing/stable)
    - Significance testing (p < 0.05)

    **Returns:**
    - trends_by_test: For each lab test:
      - visit_means: Mean and SD at each visit
      - slope: Rate of change per visit
      - r_squared: Proportion of variance explained by linear trend
      - p_value: Statistical significance of trend
      - trend_direction: "increasing", "decreasing", or "stable"
      - trend_significant: Boolean (p < 0.05)

    - trends_by_arm: Same as above, stratified by treatment arm
      - Allows comparison of temporal patterns between Active and Placebo

    **Clinical Interpretation:**
    - Positive slope: Lab value increasing over time
    - Negative slope: Lab value decreasing over time
    - R² > 0.8: Strong linear trend (predictable change)
    - R² < 0.3: Weak/no trend (fluctuating values)
    - P < 0.05: Statistically significant trend

    **Use Case:**
    - Efficacy assessment (e.g., HbA1c decline in diabetes trial)
    - Safety monitoring (e.g., progressive liver enzyme elevation)
    - Dose-response evaluation
    - Time-to-effect analysis
    - Mixed models for repeated measures (MMRM) preparation
    """
    try:
        df = pd.DataFrame(request.labs_data)
        result = analyze_labs_longitudinal(df)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Longitudinal analysis failed: {str(e)}"
        )


@app.post("/sdtm/labs/export")
async def labs_sdtm_export(request: LabsRequest):
    """
    Export labs to SDTM LB (Laboratory) domain format

    **Purpose:**
    Converts laboratory data to CDISC SDTM LB domain format for regulatory submission.

    **SDTM LB Domain Variables:**
    - STUDYID: Study identifier
    - DOMAIN: LB (Laboratory)
    - USUBJID: Unique subject identifier
    - SUBJID: Subject identifier within study
    - LBSEQ: Sequence number
    - LBTESTCD: Lab test code (standardized, e.g., "ALT", "CREAT")
    - LBTEST: Lab test name (full text)
    - LBCAT: Lab category (CHEMISTRY, HEMATOLOGY, URINALYSIS)
    - LBORRES: Result as originally received (character)
    - LBORRESU: Original units
    - LBSTRESC: Standardized result (character)
    - LBSTRESN: Standardized result (numeric)
    - LBSTRESU: Standardized units
    - VISITNUM: Visit number
    - VISIT: Visit name
    - LBDTC: Lab collection date/time
    - LBDY: Study day

    **Test Code Mapping (CDISC SDTM standard):**
    - ALT → ALT (Alanine Aminotransferase)
    - AST → AST (Aspartate Aminotransferase)
    - Bilirubin → BILI
    - Creatinine → CREAT
    - eGFR → EGFR
    - Hemoglobin → HGB
    - WBC → WBC
    - Platelets → PLAT
    - And 7 more common tests

    **Lab Categories:**
    - CHEMISTRY: ALT, AST, BILI, CREAT, Glucose, BUN, Albumin, ALP
    - HEMATOLOGY: HGB, WBC, Platelets
    - URINALYSIS: eGFR

    **Compliance:**
    - Follows CDISC SDTM-IG v3.4
    - FDA/EMA submission ready
    - All required LB domain variables included
    - Proper variable ordering per SDTM-IG

    **Use Case:**
    - Regulatory submission (IND, NDA, BLA)
    - Data package preparation
    - SDTM validation testing
    - Define.xml generation
    """
    try:
        df = pd.DataFrame(request.labs_data)
        sdtm_df = export_to_sdtm_lb(df)

        return {
            "sdtm_data": sdtm_df.to_dict(orient="records"),
            "rows": len(sdtm_df),
            "domain": "LB",
            "compliance": "SDTM-IG v3.4",
            "categories": sorted(sdtm_df["LBCAT"].unique().tolist()) if len(sdtm_df) > 0 else []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SDTM LB export failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
