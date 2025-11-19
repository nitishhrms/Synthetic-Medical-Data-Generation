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
from sdtm import export_to_sdtm_vs
from db_utils import db, cache, startup_db, shutdown_db

# Daft imports for distributed data processing
try:
    import daft
    from daft_processor import DaftMedicalDataProcessor
    from daft_aggregations import DaftAggregator
    from daft_udfs import MedicalUDFs, AdvancedMedicalUDFs
    DAFT_AVAILABLE = True
except ImportError:
    DAFT_AVAILABLE = False
    import warnings
    warnings.warn("Daft library not available. Install with: pip install getdaft==0.3.0")

# Method comparison module
try:
    from method_comparison_daft import compare_generation_methods
    METHOD_COMPARISON_AVAILABLE = True
except ImportError:
    METHOD_COMPARISON_AVAILABLE = False
    print("Warning: Method comparison module not available")

# Trial planning module
try:
    from trial_planning import (
        VirtualControlArmGenerator,
        WhatIfScenarioSimulator,
        TrialFeasibilityEstimator,
        TrialParameters,
        generate_virtual_control_arm,
        run_what_if_enrollment_analysis,
        estimate_trial_feasibility
    )
    TRIAL_PLANNING_AVAILABLE = True
except ImportError:
    TRIAL_PLANNING_AVAILABLE = False
    print("Warning: Trial planning module not available")

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
        "version": "1.1.0",
        "features": [
            "Week-12 Statistics (t-test)",
            "RECIST + ORR Analysis",
            "RBQM Summary",
            "CSR Draft Generation",
            "SDTM Export",
            "Daft Distributed Data Processing (NEW)"
        ],
        "endpoints": {
            "health": "/health",
            "stats": "/stats/week12",
            "recist": "/stats/recist",
            "rbqm": "/rbqm/summary",
            "csr": "/csr/draft",
            "sdtm": "/sdtm/export",
            "daft_status": "/daft/status",
            "daft_endpoints": "/daft/* (treatment-effect, change-from-baseline, responder-analysis, etc.)",
            "docs": "/docs"
        },
        "daft_available": DAFT_AVAILABLE
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
<<<<<<< HEAD
# DAFT-POWERED ENDPOINTS - Distributed Data Processing
# ============================================================================

@app.get("/daft/status")
async def daft_status():
    """Check if Daft is available and get version info"""
    if not DAFT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Daft library not available. Install with: pip install getdaft==0.3.0"
        )
    return {
        "daft_available": True,
        "daft_version": daft.__version__,
        "message": "Daft distributed dataframe processing is ready"
    }


@app.post("/daft/aggregate/by-treatment-arm")
async def daft_aggregate_by_treatment_arm(data: VitalsData):
    """
    Aggregate data by treatment arm using Daft's distributed processing

    Returns comprehensive statistics for each vital sign by treatment arm.
    Faster than pandas for large datasets (>10k records).
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.groupby_treatment_arm()

        return {
            "status": "success",
            "aggregations": results,
            "row_count": len(data.data),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")


@app.post("/daft/aggregate/by-visit")
async def daft_aggregate_by_visit(data: VitalsData):
    """
    Aggregate data by visit using Daft

    Returns mean values for each vital sign at each visit timepoint.
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.groupby_visit()

        return {
            "status": "success",
            "aggregations": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")


@app.post("/daft/treatment-effect")
async def daft_treatment_effect(data: VitalsData, endpoint: str = "SystolicBP", visit: str = "Week 12"):
    """
    Compute treatment effect with statistical testing using Daft

    Performs t-test comparing active vs placebo at specified visit.
    Uses Daft's distributed processing for faster computation on large datasets.

    Args:
        data: Vitals data
        endpoint: Vital sign to analyze (default: SystolicBP)
        visit: Visit to analyze (default: Week 12)
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_treatment_effect(endpoint=endpoint, visit=visit)

        return {
            "status": "success",
            "treatment_effect": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Treatment effect calculation failed: {str(e)}")


@app.post("/daft/change-from-baseline")
async def daft_change_from_baseline(data: VitalsData):
    """
    Compute change from baseline for all subjects using Daft

    Returns data with baseline values and change calculations for each vital sign.
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_change_from_baseline()

        return {
            "status": "success",
            "data": results.to_dict('records'),
            "row_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Change from baseline failed: {str(e)}")


@app.post("/daft/responder-analysis")
async def daft_responder_analysis(data: VitalsData, threshold: float = -10.0, endpoint: str = "SystolicBP"):
    """
    Perform responder analysis using Daft

    Identifies subjects achieving a specified threshold change from baseline.

    Args:
        data: Vitals data
        threshold: Threshold for response (e.g., -10 mmHg reduction)
        endpoint: Vital sign to analyze (default: SystolicBP)
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_responder_analysis(threshold=threshold, endpoint=endpoint)

        return {
            "status": "success",
            "responder_analysis": results,
            "threshold": threshold,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Responder analysis failed: {str(e)}")


@app.post("/daft/longitudinal-summary")
async def daft_longitudinal_summary(data: VitalsData):
    """
    Compute longitudinal summary across all visits using Daft

    Shows trajectories of vital signs over time for each treatment arm.
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_longitudinal_summary()

        return {
            "status": "success",
            "longitudinal_summary": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Longitudinal summary failed: {str(e)}")


@app.post("/daft/outlier-detection")
async def daft_outlier_detection(data: VitalsData, column: str = "SystolicBP", method: str = "iqr"):
    """
    Detect outliers using Daft

    Args:
        data: Vitals data
        column: Column to check for outliers (default: SystolicBP)
        method: Method to use - 'iqr' or 'zscore' (default: iqr)
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_outliers(column=column, method=method)

        return {
            "status": "success",
            "outlier_detection": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outlier detection failed: {str(e)}")


@app.post("/daft/add-medical-features")
async def daft_add_medical_features(data: VitalsData):
    """
    Add medical-specific derived features using Daft:
    - Pulse Pressure (SBP - DBP)
    - Mean Arterial Pressure (MAP)
    - Hypertension Category

    Returns data with additional calculated columns.
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(data.data)

        # Add derived features
        processor.add_pulse_pressure()
        processor.add_mean_arterial_pressure()
        processor.add_hypertension_category()

        result_df = processor.collect()

        return {
            "status": "success",
            "data": result_df.to_dict('records'),
            "features_added": [
                "PulsePressure",
                "MeanArterialPressure",
                "HypertensionCategory"
            ],
            "row_count": len(result_df),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adding features failed: {str(e)}")


@app.post("/daft/correlation-matrix")
async def daft_correlation_matrix(data: VitalsData):
    """
    Compute correlation matrix for vital signs using Daft

    Returns correlation matrix showing relationships between vitals.
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_correlation_matrix()

        return {
            "status": "success",
            "correlation_analysis": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")
=======
# Method Comparison Using Daft
# ============================================================================

class MethodComparisonRequest(BaseModel):
    real_data: List[Dict[str, Any]] = Field(..., description="Real/baseline dataset")
    synthetic_datasets: Dict[str, List[Dict[str, Any]]] = Field(
        ...,
        description="Dictionary of {method_name: synthetic_data}"
    )
    generation_times: Dict[str, float] = Field(
        default={},
        description="Dictionary of {method_name: generation_time_ms}"
    )


@app.post("/quality/compare-methods")
async def compare_all_methods(request: MethodComparisonRequest):
    """
    Compare all 6 generation methods using Daft

    **Comprehensive comparison across multiple dimensions:**

    1. **Distribution Similarity** (Wasserstein Distance)
       - Measures how close synthetic distributions are to real
       - Lower distance = better match
       - Computed for SystolicBP, DiastolicBP, HeartRate, Temperature

    2. **Correlation Preservation**
       - Checks if variable relationships are maintained
       - Frobenius norm of correlation matrix difference
       - Score 0-1, higher is better

    3. **Statistical Utility** (Kolmogorov-Smirnov Tests)
       - Tests if distributions are statistically indistinguishable
       - Proportion of KS tests that pass (p>0.05)
       - Higher proportion = higher utility

    4. **Privacy Risk** (Simple Assessment)
       - Checks for duplicate records (potential memorization)
       - For full assessment, use /privacy/assess/comprehensive

    5. **Generation Performance**
       - Time to generate dataset
       - Throughput (records/second)

    **Methods Compared:**
    - MVN (Multivariate Normal)
    - Bootstrap
    - Rules-based
    - LLM (GPT-4o-mini)
    - Bayesian Network
    - MICE (Multiple Imputation)

    **Returns:**
    - Overall quality scores (0-100) for each method
    - Rankings (1st, 2nd, 3rd, etc.)
    - Detailed metrics for each dimension
    - Recommendations for method selection

    **Use Cases:**
    - Validate which method works best for your data
    - Compare privacy/utility tradeoffs
    - Benchmark new generation methods
    - Select method based on specific needs (speed vs quality)

    **Example Request:**
    ```json
    {
      "real_data": [...],  // Your real clinical data
      "synthetic_datasets": {
        "mvn": [...],      // Generated with MVN
        "bootstrap": [...], // Generated with Bootstrap
        "bayesian": [...],  // Generated with Bayesian
        "mice": [...]       // Generated with MICE
      },
      "generation_times": {
        "mvn": 28.5,
        "bootstrap": 15.2,
        "bayesian": 45.3,
        "mice": 38.1
      }
    }
    ```

    **Example Response:**
    ```json
    {
      "rankings": {
        "bootstrap": {"rank": 1, "score": 87.5, "best_for": ["Fastest generation", "Best distribution similarity"]},
        "bayesian": {"rank": 2, "score": 85.2, "best_for": ["Best correlation preservation"]},
        "mvn": {"rank": 3, "score": 82.1, "best_for": ["Balanced performance"]},
        "mice": {"rank": 4, "score": 78.9, "best_for": []}
      },
      "recommendations": {
        "best_overall": "bootstrap",
        "fastest": "bootstrap",
        "highest_quality": "bayesian",
        "general_guidance": "Choose based on your needs: Bootstrap for speed and realism..."
      }
    }
    ```
    """
    if not METHOD_COMPARISON_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Method comparison not available. Check method_comparison_daft module."
        )

    try:
        # Convert to DataFrames
        real_df = pd.DataFrame(request.real_data)

        synthetic_dfs = {}
        for method, data in request.synthetic_datasets.items():
            synthetic_dfs[method] = pd.DataFrame(data)

        # Run comparison
        results = compare_generation_methods(
            real_df,
            synthetic_dfs,
            request.generation_times
        )

        return {
            "comparison_results": results,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "analytics-service",
            "comparison_engine": "daft" if METHOD_COMPARISON_AVAILABLE else "pandas_fallback"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Method comparison failed: {str(e)}"
        )


# ============================================================================
# Trial Planning Endpoints
# ============================================================================

class VirtualControlArmRequest(BaseModel):
    n_subjects: int = Field(default=50, description="Number of virtual control subjects")
    real_control_data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional real control data to match")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")

class AugmentControlArmRequest(BaseModel):
    real_control_data: List[Dict[str, Any]] = Field(..., description="Small real control arm data")
    target_n: int = Field(default=50, description="Target total sample size")
    seed: Optional[int] = Field(default=None, description="Random seed")

class WhatIfEnrollmentRequest(BaseModel):
    baseline_data: List[Dict[str, Any]] = Field(..., description="Baseline trial data")
    enrollment_sizes: Optional[List[int]] = Field(default=None, description="List of n_per_arm values to test")
    target_effect: float = Field(default=-5.0, description="Expected treatment effect")
    n_simulations: int = Field(default=1000, description="Monte Carlo simulations")
    seed: Optional[int] = Field(default=None, description="Random seed")

class WhatIfPatientMixRequest(BaseModel):
    baseline_data: List[Dict[str, Any]] = Field(..., description="Baseline trial data")
    severity_shifts: Optional[List[float]] = Field(default=None, description="Baseline SBP shifts (e.g., [-10, 0, +10])")
    n_per_arm: int = Field(default=50, description="Sample size per arm")
    target_effect: float = Field(default=-5.0, description="Expected treatment effect")
    n_simulations: int = Field(default=1000, description="Monte Carlo simulations")
    seed: Optional[int] = Field(default=None, description="Random seed")

class FeasibilityAssessmentRequest(BaseModel):
    baseline_data: List[Dict[str, Any]] = Field(..., description="Baseline trial data")
    target_effect: float = Field(default=-5.0, description="Expected treatment effect")
    power: float = Field(default=0.80, description="Desired statistical power")
    dropout_rate: float = Field(default=0.10, description="Expected dropout rate")
    alpha: float = Field(default=0.05, description="Significance level")


@app.post("/trial-planning/virtual-control-arm")
async def create_virtual_control_arm(request: VirtualControlArmRequest):
    """
    Generate virtual control arm to augment or replace real control data

    **Use Cases** (addressing professor's feedback):
    - Reduce placebo patients needed in trial
    - Augment small historical control groups
    - Simulate control arm for trial planning
    - Ethical alternative when placebo is problematic

    **Inspired by**: Medidata's Synthetic Control Arms product

    **How it works**:
    1. Learn characteristics from real control data (if provided)
    2. Generate virtual subjects matching those characteristics
    3. Simulate realistic progression (placebo effect, regression to mean)

    **Parameters**:
    - n_subjects: Number of virtual control subjects to generate
    - real_control_data: Optional real control data to match (learns from it)
    - seed: Random seed for reproducibility

    **Returns**:
    - Virtual control arm data (same format as real data)
    - Can be combined with real control or used standalone

    **Example**:
    ```json
    {
      "n_subjects": 50,
      "real_control_data": [...],  // Optional
      "seed": 42
    }
    ```
    """
    if not TRIAL_PLANNING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Trial planning module not available"
        )

    try:
        # Convert real control data if provided
        real_control_df = None
        if request.real_control_data:
            real_control_df = pd.DataFrame(request.real_control_data)

        # Generate virtual control arm
        virtual_arm = generate_virtual_control_arm(
            n_subjects=request.n_subjects,
            real_control_data=real_control_df,
            seed=request.seed
        )

        return {
            "virtual_control_arm": virtual_arm.to_dict(orient="records"),
            "metadata": {
                "n_subjects": request.n_subjects,
                "total_records": len(virtual_arm),
                "visits": virtual_arm['VisitName'].unique().tolist(),
                "learned_from_real_data": real_control_df is not None
            },
            "timestamp": datetime.utcnow().isoformat(),
            "service": "analytics-service"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Virtual control arm generation failed: {str(e)}"
        )


@app.post("/trial-planning/augment-control-arm")
async def augment_control_arm(request: AugmentControlArmRequest):
    """
    Augment a small real control arm with virtual subjects

    **Use Case**: You have only 20 real control subjects but need 50 for power.
    This generates 30 virtual controls matching the real data characteristics.

    **Benefits**:
    - Reduce number of patients receiving placebo
    - Achieve adequate statistical power
    - Maintain data quality by learning from real subjects

    **How it works**:
    1. Analyzes real control data characteristics
    2. Generates virtual subjects to reach target sample size
    3. Combines real and virtual data seamlessly

    **Parameters**:
    - real_control_data: Your small real control arm
    - target_n: Desired total sample size
    - seed: Random seed

    **Returns**:
    - Augmented control arm (real + virtual)
    - Statistics on augmentation (n_real, n_virtual, ratio)

    **Example**:
    ```json
    {
      "real_control_data": [...],  // 20 real subjects
      "target_n": 50,              // Want 50 total
      "seed": 42                   // Will add 30 virtual
    }
    ```
    """
    if not TRIAL_PLANNING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Trial planning module not available"
        )

    try:
        # Convert to DataFrame
        real_control_df = pd.DataFrame(request.real_control_data)

        # Create generator and augment
        generator = VirtualControlArmGenerator()
        augmented_df, stats = generator.augment_small_control_arm(
            real_control=real_control_df,
            target_n=request.target_n,
            seed=request.seed
        )

        return {
            "augmented_control_arm": augmented_df.to_dict(orient="records"),
            "augmentation_statistics": stats,
            "metadata": {
                "total_records": len(augmented_df),
                "visits": augmented_df['VisitName'].unique().tolist()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "service": "analytics-service"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Control arm augmentation failed: {str(e)}"
        )


@app.post("/trial-planning/what-if/enrollment")
async def run_enrollment_what_if_analysis(request: WhatIfEnrollmentRequest):
    """
    What-if analysis: How does enrollment size affect trial outcomes?

    **Question**: "What if we enroll only 30 patients per arm instead of 50?"

    **Professor's Feedback**: Run "what-if" scenarios like varying enrollment size
    and seeing outcome differences.

    **How it works**:
    - Runs Monte Carlo simulations (default: 1000 per scenario)
    - Tests different enrollment sizes (e.g., 25, 50, 75, 100 per arm)
    - Calculates statistical power for each scenario
    - Recommends minimum sample size for adequate power

    **Parameters**:
    - baseline_data: Your baseline trial data
    - enrollment_sizes: List of sample sizes to test (e.g., [25, 50, 75, 100])
    - target_effect: Expected treatment effect (e.g., -5 mmHg SBP reduction)
    - n_simulations: Monte Carlo simulations (default: 1000)

    **Returns**:
    - Power analysis for each enrollment scenario
    - Sample size recommendation for 80% power
    - Feasibility assessment

    **Example**:
    ```json
    {
      "baseline_data": [...],
      "enrollment_sizes": [25, 50, 75, 100],
      "target_effect": -5.0,
      "n_simulations": 1000
    }
    ```

    **Typical output**:
    - n=25: 45% power (insufficient)
    - n=50: 82% power (adequate)
    - n=75: 95% power (excellent)
    - **Recommendation**: Minimum 50 per arm for 80% power
    """
    if not TRIAL_PLANNING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Trial planning module not available"
        )

    try:
        # Convert to DataFrame
        baseline_df = pd.DataFrame(request.baseline_data)

        # Run what-if analysis
        results = run_what_if_enrollment_analysis(
            baseline_data=baseline_df,
            enrollment_sizes=request.enrollment_sizes,
            target_effect=request.target_effect,
            seed=request.seed
        )

        return {
            "what_if_analysis": results,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "analytics-service"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"What-if enrollment analysis failed: {str(e)}"
        )


@app.post("/trial-planning/what-if/patient-mix")
async def run_patient_mix_what_if_analysis(request: WhatIfPatientMixRequest):
    """
    What-if analysis: How does patient population affect trial outcomes?

    **Question**: "What if we enroll more severe patients (higher baseline BP)?"

    **Professor's Feedback**: Run "what-if" scenarios varying patient mix
    and seeing outcome differences.

    **How it works**:
    - Simulates trials with different patient populations
    - Tests severity shifts (e.g., -10 mmHg, 0, +10 mmHg baseline SBP)
    - Calculates power and effect estimates for each scenario
    - Shows how patient selection affects trial success

    **Parameters**:
    - baseline_data: Your baseline trial data
    - severity_shifts: Baseline SBP shifts (e.g., [-10, -5, 0, 5, 10])
    - n_per_arm: Sample size per arm
    - target_effect: Expected treatment effect
    - n_simulations: Monte Carlo simulations

    **Returns**:
    - Power analysis for each patient population
    - Effect estimate variability
    - Interpretation of results

    **Example**:
    ```json
    {
      "baseline_data": [...],
      "severity_shifts": [-10, 0, 10],
      "n_per_arm": 50,
      "target_effect": -5.0
    }
    ```

    **Typical output**:
    - Milder patients (SBP 132): 75% power
    - Baseline patients (SBP 142): 82% power
    - More severe patients (SBP 152): 88% power
    - **Insight**: More severe patients may show larger effects
    """
    if not TRIAL_PLANNING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Trial planning module not available"
        )

    try:
        # Convert to DataFrame
        baseline_df = pd.DataFrame(request.baseline_data)

        # Create simulator and run analysis
        simulator = WhatIfScenarioSimulator(baseline_df)
        results = simulator.simulate_patient_mix_scenarios(
            severity_shifts=request.severity_shifts,
            n_per_arm=request.n_per_arm,
            n_simulations=request.n_simulations,
            target_effect=request.target_effect,
            seed=request.seed
        )

        return {
            "what_if_analysis": results,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "analytics-service"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"What-if patient mix analysis failed: {str(e)}"
        )


@app.post("/trial-planning/feasibility")
async def assess_trial_feasibility(request: FeasibilityAssessmentRequest):
    """
    Comprehensive trial feasibility assessment

    **Use Case**: Estimate if your trial design is feasible given:
    - Sample size requirements
    - Enrollment timeline
    - Budget constraints
    - Statistical power needs

    **Provides**:
    - Required sample size (with dropout adjustment)
    - Enrollment timeline estimate
    - Feasibility risk assessment
    - Actionable recommendations

    **Parameters**:
    - baseline_data: Your baseline trial data
    - target_effect: Expected treatment effect
    - power: Desired statistical power (default: 0.80)
    - dropout_rate: Expected dropout rate (default: 0.10)
    - alpha: Significance level (default: 0.05)

    **Returns**:
    - Sample size requirements
    - Timeline estimates (enrollment + treatment)
    - Feasibility assessment (feasible/risky/infeasible)
    - Recommendations for improvement

    **Example**:
    ```json
    {
      "baseline_data": [...],
      "target_effect": -5.0,
      "power": 0.80,
      "dropout_rate": 0.10
    }
    ```

    **Typical output**:
    - Required: 50 per arm (56 with dropout)
    - Timeline: 8 months enrollment + 3 months treatment = 11 months
    - Feasibility: ✅ Highly feasible
    - Recommendation: Proceed with trial design
    """
    if not TRIAL_PLANNING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Trial planning module not available"
        )

    try:
        # Convert to DataFrame
        baseline_df = pd.DataFrame(request.baseline_data)

        # Run feasibility assessment
        results = estimate_trial_feasibility(
            baseline_data=baseline_df,
            target_effect=request.target_effect,
            power=request.power,
            dropout_rate=request.dropout_rate
        )

        return {
            "feasibility_assessment": results,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "analytics-service"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feasibility assessment failed: {str(e)}"
        )
>>>>>>> origin/daft


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
