"""
Analytics Service - Clinical Trial Statistics and Reporting
Handles statistics, RBQM, CSR generation, SDTM export
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
import uvicorn
import os
import json

def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to native Python types for JSON serialization.
    Handles dicts, lists, numpy arrays, and individual numpy values.
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_)):
        return bool(obj)
    elif isinstance(obj, np.void):
        return None
    elif pd.isna(obj):
        return None
    else:
        return obj

from stats import (
    calculate_week12_statistics,
    calculate_recist_orr,
    ks_distance
)
from rbqm import generate_rbqm_summary
from csr import generate_csr_draft
from sdtm import export_to_sdtm_vs, export_to_sdtm_dm, export_to_sdtm_lb, export_to_sdtm_ae
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
from ae_analytics import (
    calculate_ae_summary,
    analyze_treatment_emergent_aes,
    analyze_soc_distribution,
    compare_ae_quality
)
from aact_integration import (
    compare_study_to_aact,
    benchmark_demographics,
    benchmark_adverse_events
)
from study_analytics import (
    generate_comprehensive_summary,
    analyze_cross_domain_correlations,
    generate_trial_dashboard
)
from benchmarking import (
    compare_generation_methods,
    aggregate_quality_scores,
    generate_recommendations
)
from survival_analysis import (
    generate_survival_data,
    calculate_kaplan_meier,
    log_rank_test,
    calculate_hazard_ratio,
    export_survival_sdtm_tte,
    comprehensive_survival_analysis
)
from adam_generation import (
    generate_adsl,
    generate_adtte,
    generate_adae,
    generate_bds_vitals,
    generate_bds_labs,
    generate_all_adam_datasets
)
from tlf_automation import (
    generate_table1_demographics,
    generate_ae_summary_table,
    generate_efficacy_table,
    generate_all_tlf_tables
)

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
    description="Clinical Trial Analytics, RBQM, CSR, SDTM Export, Survival Analysis, ADaM Generation, TLF Automation",
    version="2.0.0"
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
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "")
if ALLOWED_ORIGINS_ENV:
    ALLOWED_ORIGINS = ALLOWED_ORIGINS_ENV.split(",")
else:
    # Default: allow all origins for development (use specific origins in production)
    ALLOWED_ORIGINS = ["*"]

if "*" in ALLOWED_ORIGINS and os.getenv("ENVIRONMENT") == "production":
    import warnings
    warnings.warn("CORS wildcard enabled in production - security risk!", UserWarning)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Pydantic models
class VitalsData(BaseModel):
    data: List[Dict[str, Any]]

class StatisticsRequest(BaseModel):
    vitals_data: List[Dict[str, Any]]
    visit_name: Optional[str] = "Week 12"  # Default to Week 12 for backward compatibility

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

# AE models
class AERequest(BaseModel):
    ae_data: List[Dict[str, Any]]
    treatment_start_date: Optional[str] = None

class AECompareRequest(BaseModel):
    real_ae: List[Dict[str, Any]]
    synthetic_ae: List[Dict[str, Any]]

# AACT Integration models
class AACTCompareStudyRequest(BaseModel):
    n_subjects: int = Field(..., description="Total number of subjects enrolled")
    indication: str = Field(..., description="Disease indication (e.g., 'hypertension', 'diabetes')")
    phase: str = Field(..., description="Trial phase (e.g., 'Phase 3')")
    treatment_effect: float = Field(..., description="Primary endpoint treatment effect")
    vitals_data: Optional[List[Dict[str, Any]]] = Field(None, description="Optional vitals data")

class AACTBenchmarkDemographicsRequest(BaseModel):
    demographics_data: List[Dict[str, Any]] = Field(..., description="Demographics with Age, Gender, Race, TreatmentArm")
    indication: str = Field(..., description="Disease indication")
    phase: str = Field(..., description="Trial phase")

class AACTBenchmarkAERequest(BaseModel):
    ae_data: List[Dict[str, Any]] = Field(..., description="AE data with PreferredTerm, Severity, Serious")
    indication: str = Field(..., description="Disease indication")
    phase: str = Field(..., description="Trial phase")

# Study Analytics models
class ComprehensiveStudyRequest(BaseModel):
    demographics_data: Optional[List[Dict[str, Any]]] = Field(None, description="Demographics data")
    vitals_data: Optional[List[Dict[str, Any]]] = Field(None, description="Vitals data")
    labs_data: Optional[List[Dict[str, Any]]] = Field(None, description="Labs data")
    ae_data: Optional[List[Dict[str, Any]]] = Field(None, description="AE data")
    indication: str = Field(default="hypertension", description="Disease indication")
    phase: str = Field(default="Phase 3", description="Trial phase")

class CrossDomainRequest(BaseModel):
    demographics_data: Optional[List[Dict[str, Any]]] = Field(None, description="Demographics data")
    vitals_data: Optional[List[Dict[str, Any]]] = Field(None, description="Vitals data")
    labs_data: Optional[List[Dict[str, Any]]] = Field(None, description="Labs data")
    ae_data: Optional[List[Dict[str, Any]]] = Field(None, description="AE data")

class TrialDashboardRequest(BaseModel):
    demographics_data: Optional[List[Dict[str, Any]]] = Field(None, description="Demographics data")
    vitals_data: Optional[List[Dict[str, Any]]] = Field(None, description="Vitals data")
    labs_data: Optional[List[Dict[str, Any]]] = Field(None, description="Labs data")
    ae_data: Optional[List[Dict[str, Any]]] = Field(None, description="AE data")
    indication: str = Field(default="hypertension", description="Disease indication")
    phase: str = Field(default="Phase 3", description="Trial phase")

# Benchmarking models
class MethodComparisonRequest(BaseModel):
    methods_data: Dict[str, Dict[str, Any]] = Field(..., description="Method performance data by method name")

class AggregateQualityRequest(BaseModel):
    demographics_quality: Optional[float] = Field(None, description="Demographics quality score (0-1)")
    vitals_quality: Optional[float] = Field(None, description="Vitals quality score (0-1)")
    labs_quality: Optional[float] = Field(None, description="Labs quality score (0-1)")
    ae_quality: Optional[float] = Field(None, description="AE quality score (0-1)")
    aact_similarity: Optional[float] = Field(None, description="AACT similarity score (0-1)")

class RecommendationsRequest(BaseModel):
    current_quality: float = Field(..., description="Current overall quality score (0-1)")
    aact_similarity: Optional[float] = Field(None, description="AACT similarity score (0-1)")
    generation_method: Optional[str] = Field(None, description="Generation method used")
    n_subjects: Optional[int] = Field(None, description="Number of subjects")
    indication: Optional[str] = Field(None, description="Disease indication")
    phase: Optional[str] = Field(None, description="Trial phase")

# ===== Phase 7: Survival Analysis Models =====
class SurvivalAnalysisRequest(BaseModel):
    demographics_data: List[Dict[str, Any]] = Field(..., description="Subject demographics")
    indication: str = Field(default="oncology", description="Therapeutic area")
    median_survival_active: float = Field(default=18.0, description="Median survival for active arm (months)")
    median_survival_placebo: float = Field(default=12.0, description="Median survival for placebo arm (months)")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")

# ===== Phase 8: ADaM Generation Models =====
class AdamGenerationRequest(BaseModel):
    demographics_data: List[Dict[str, Any]] = Field(..., description="Demographics records")
    vitals_data: Optional[List[Dict[str, Any]]] = Field(None, description="Vitals records")
    labs_data: Optional[List[Dict[str, Any]]] = Field(None, description="Labs records (long format)")
    ae_data: Optional[List[Dict[str, Any]]] = Field(None, description="Adverse event records")
    survival_data: Optional[List[Dict[str, Any]]] = Field(None, description="Survival/TTE records")
    study_id: str = Field(default="STUDY001", description="Study identifier")

# ===== Phase 9: TLF Automation Models =====
class TLFRequest(BaseModel):
    demographics_data: List[Dict[str, Any]] = Field(..., description="Demographics records")
    ae_data: Optional[List[Dict[str, Any]]] = Field(None, description="Adverse event records")
    vitals_data: Optional[List[Dict[str, Any]]] = Field(None, description="Vitals records")
    survival_data: Optional[List[Dict[str, Any]]] = Field(None, description="Survival records")

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
        "version": "1.6.0",
        "features": [
            "Week-12 Statistics (t-test)",
            "RECIST + ORR Analysis",
            "RBQM Summary",
            "CSR Draft Generation",
            "SDTM Export (Vitals + Demographics + Labs + AE)",
            "Demographics Analytics (Baseline, Balance, Quality)",
            "Labs Analytics (Summary, Abnormal Detection, Shift Tables, Safety Signals, Longitudinal)",
            "AE Analytics (Frequency Tables, TEAEs, SOC Analysis, Quality)",
            "Quality Assessment (PCA, K-NN, Wasserstein)",
            "AACT Integration (Compare Study, Benchmark Demographics, Benchmark AEs)",
            "Comprehensive Study Analytics (Summary, Cross-Domain Correlations, Trial Dashboard)",
            "Benchmarking & Extensions (Performance Comparison, Quality Aggregation, Recommendations)"
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
            "ae_summary": "/stats/ae/summary",
            "ae_teae": "/stats/ae/treatment-emergent",
            "ae_soc": "/stats/ae/soc-analysis",
            "rbqm": "/rbqm/summary",
            "csr": "/csr/draft",
            "sdtm_vitals": "/sdtm/export",
            "sdtm_demographics": "/sdtm/demographics/export",
            "sdtm_labs": "/sdtm/labs/export",
            "sdtm_ae": "/sdtm/ae/export",
            "quality_pca": "/quality/pca-comparison",
            "quality_comprehensive": "/quality/comprehensive",
            "quality_demographics": "/quality/demographics/compare",
            "quality_labs": "/quality/labs/compare",
            "quality_ae": "/quality/ae/compare",
            "aact_compare_study": "/aact/compare-study",
            "aact_benchmark_demographics": "/aact/benchmark-demographics",
            "aact_benchmark_ae": "/aact/benchmark-ae",
            "study_comprehensive_summary": "/study/comprehensive-summary",
            "study_cross_domain_correlations": "/study/cross-domain-correlations",
            "study_trial_dashboard": "/study/trial-dashboard",
            "benchmark_performance": "/benchmark/performance",
            "benchmark_quality_scores": "/benchmark/quality-scores",
            "study_recommendations": "/study/recommendations",
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
        stats = calculate_week12_statistics(df, visit_name=request.visit_name)

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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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
        return convert_numpy_types(result)
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


# ============================================================================
# AE (ADVERSE EVENTS) ANALYTICS ENDPOINTS (Phase 3)
# ============================================================================

@app.post("/stats/ae/summary")
async def ae_summary(request: AERequest):
    """
    Calculate AE frequency tables by SOC, PT, severity, relationship

    **Purpose:**
    Provides comprehensive adverse event frequency tables for clinical study reports,
    stratified by MedDRA System Organ Class (SOC), Preferred Term (PT), severity,
    and relationship to treatment.

    **MedDRA Classification:**
    - SOC (System Organ Class): Primary classification (17 major categories)
    - PT (Preferred Term): Specific AE term

    **Returns:**
    - overall_summary: Total AEs, subjects with AEs, unique PTs/SOCs
    - by_soc: AE count and subject count per SOC
    - by_pt: Top 20 most frequent PTs with incidence rates
    - by_severity: Distribution (Mild, Moderate, Severe)
    - by_relationship: Distribution (Related, Not Related, Possibly Related)
    - sae_summary: Serious AE statistics
    - by_arm: AE comparison by treatment arm (if available)

    **Use Case:**
    - Safety section of Clinical Study Reports (CSR)
    - Regulatory submission (IND, NDA, BLA)
    - DSMB safety reports
    - Investigator Brochure updates
    """
    try:
        df = pd.DataFrame(request.ae_data)
        result = calculate_ae_summary(df)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AE summary calculation failed: {str(e)}"
        )


@app.post("/stats/ae/treatment-emergent")
async def ae_treatment_emergent(request: AERequest):
    """
    Analyze treatment-emergent adverse events (TEAEs)

    **Purpose:**
    Identifies and analyzes TEAEs - adverse events that start on or after
    first dose of study treatment, which are critical for safety assessment.

    **TEAE Definition:**
    - Onset on or after first dose of study treatment
    - Were not present at baseline, or worsened after treatment start
    - Required for all regulatory submissions

    **Returns:**
    - teae_summary: Total TEAEs, subjects with TEAEs, TEAE rate, median onset day
    - time_to_first_ae: Distribution of time to first AE
      - 0-7 days: Immediate onset
      - 8-30 days: Early onset
      - 31-90 days: Intermediate onset
      - >90 days: Late onset
    - teae_by_arm: TEAE comparison by treatment arm
    - early_vs_late: Early (≤30 days) vs late (>30 days) TEAEs

    **Clinical Interpretation:**
    - High early TEAE rate: May indicate acute toxicity
    - High late TEAE rate: May indicate cumulative toxicity
    - Median onset: Typical time to first AE (guides safety monitoring)

    **Use Case:**
    - Safety assessment for DSMB
    - Regulatory submissions (required analysis)
    - Protocol amendment decisions
    - Patient counseling (expected onset timing)
    - Safety labeling
    """
    try:
        df = pd.DataFrame(request.ae_data)
        treatment_start = request.treatment_start_date
        result = analyze_treatment_emergent_aes(df, treatment_start_date=treatment_start)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Treatment-emergent AE analysis failed: {str(e)}"
        )


@app.post("/stats/ae/soc-analysis")
async def ae_soc_analysis(request: AERequest):
    """
    Analyze System Organ Class (SOC) distribution per MedDRA

    **Purpose:**
    Provides MedDRA System Organ Class (SOC) analysis, which is the primary
    classification for adverse events in clinical trials. Required for all
    regulatory submissions.

    **MedDRA SOC Categories (17 total):**
    - Gastrointestinal disorders
    - Nervous system disorders
    - Skin and subcutaneous tissue disorders
    - General disorders and administration site conditions
    - Infections and infestations
    - Cardiac disorders
    - Respiratory, thoracic and mediastinal disorders
    - Musculoskeletal and connective tissue disorders
    - Psychiatric disorders
    - Blood and lymphatic system disorders
    - Metabolism and nutrition disorders
    - And 6 more...

    **Returns:**
    - soc_ranking: SOCs ranked by AE frequency and subject count
    - soc_by_arm: SOC distribution by treatment arm
    - soc_details: Top 5 PTs within each SOC
    - sae_by_soc: Serious AE distribution by SOC
    - statistical_tests: Fisher's exact test for arm comparisons
      - odds_ratio: Relative risk between arms
      - p_value: Statistical significance
      - significant: Boolean (p < 0.05)

    **Clinical Interpretation:**
    - Odds ratio > 2: Meaningful increase in active vs placebo
    - P-value < 0.05: Statistically significant difference
    - SAEs concentrated in specific SOC: Organ-specific toxicity

    **Use Case:**
    - Safety section of CSR (required table)
    - Regulatory submissions (FDA, EMA)
    - Identifying organ-specific toxicities
    - Benefit-risk assessment
    - Prescribing information (Adverse Reactions section)
    """
    try:
        df = pd.DataFrame(request.ae_data)
        result = analyze_soc_distribution(df)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SOC analysis failed: {str(e)}"
        )


@app.post("/quality/ae/compare")
async def ae_quality(request: AECompareRequest):
    """
    Compare real vs synthetic AE data quality

    **Purpose:**
    Validates that synthetic adverse event data matches real-world clinical trial
    AE patterns using distribution similarity metrics.

    **Metrics Computed:**
    1. **SOC Distribution Similarity** - Chi-square test
       - Tests if SOC frequencies match between real and synthetic
       - P-value > 0.05 indicates similar distributions

    2. **PT Distribution Similarity** - Top 20 PT overlap
       - Jaccard similarity: Overlap of most common PTs
       - > 0.6: Good overlap
       - 0.4-0.6: Fair overlap
       - < 0.4: Poor overlap

    3. **Severity Distribution** - Chi-square test
       - Tests Mild/Moderate/Severe distribution match
       - P-value > 0.05 indicates similar severity patterns

    4. **Relationship Distribution** - Chi-square test
       - Tests Related/Not Related/Possibly Related match
       - Ensures causality assessment patterns are realistic

    5. **Overall Quality Score** (0-1 scale)
       - Average of all metric scores
       - ≥ 0.85: Excellent - Production ready
       - 0.70-0.85: Good - Minor adjustments
       - < 0.70: Needs improvement

    **Returns:**
    - soc_distribution_similarity: Chi-square test results
    - pt_distribution_similarity: Jaccard similarity and overlap count
    - severity_distribution: Chi-square test results
    - relationship_distribution: Chi-square test results
    - overall_quality_score: Aggregate quality (0-1)
    - interpretation: Clinical quality assessment

    **Use Case:**
    - Validating AE data generation methods
    - Quality assurance before using synthetic data
    - Method comparison (Rules vs LLM vs Historical sampling)
    - Parameter tuning for synthetic data generation
    """
    try:
        real_df = pd.DataFrame(request.real_ae)
        synthetic_df = pd.DataFrame(request.synthetic_ae)
        result = compare_ae_quality(real_df, synthetic_df)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AE quality comparison failed: {str(e)}"
        )


@app.post("/sdtm/ae/export")
async def ae_sdtm_export(request: AERequest):
    """
    Export AE to SDTM AE (Adverse Events) domain format

    **Purpose:**
    Converts adverse event data to CDISC SDTM AE domain format for regulatory submission.

    **SDTM AE Domain Variables:**
    - STUDYID: Study identifier
    - DOMAIN: AE (Adverse Events)
    - USUBJID: Unique subject identifier
    - SUBJID: Subject identifier within study
    - AESEQ: Sequence number
    - AETERM: Verbatim AE term (as reported)
    - AEDECOD: MedDRA Preferred Term (dictionary-derived)
    - AESOC: MedDRA System Organ Class
    - AESEV: Severity (MILD, MODERATE, SEVERE)
    - AESER: Serious flag (Y/N)
    - AEREL: Relationship to treatment (RELATED, NOT RELATED, POSSIBLY RELATED)
    - AEACN: Action taken with study treatment
    - AEOUT: Outcome of AE
    - AESTDTC: Start date/time
    - AEENDTC: End date/time
    - AESTDY: Study day at AE start
    - AEENDY: Study day at AE end

    **Severity Mapping (CDISC Controlled Terminology):**
    - Mild → MILD
    - Moderate → MODERATE
    - Severe → SEVERE

    **Serious Flag Mapping:**
    - True/Yes/Y → Y
    - False/No/N → N

    **Relationship Mapping:**
    - Related → RELATED
    - Not Related → NOT RELATED
    - Possibly Related → POSSIBLY RELATED
    - Probably Related → PROBABLY RELATED

    **Compliance:**
    - Follows CDISC SDTM-IG v3.4
    - FDA/EMA submission ready
    - All required AE domain variables included
    - Proper variable ordering per SDTM-IG
    - MedDRA dictionary compliance

    **Use Case:**
    - Regulatory submission (IND, NDA, BLA)
    - Data package preparation
    - SDTM validation testing
    - Define.xml generation
    - Safety database integration
    """
    try:
        df = pd.DataFrame(request.ae_data)
        sdtm_df = export_to_sdtm_ae(df)

        return {
            "sdtm_data": sdtm_df.to_dict(orient="records"),
            "rows": len(sdtm_df),
            "domain": "AE",
            "compliance": "SDTM-IG v3.4",
            "unique_pts": sdtm_df["AEDECOD"].nunique() if len(sdtm_df) > 0 else 0,
            "unique_socs": sdtm_df["AESOC"].nunique() if len(sdtm_df) > 0 else 0,
            "serious_count": (sdtm_df["AESER"] == "Y").sum() if len(sdtm_df) > 0 else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SDTM AE export failed: {str(e)}"
        )


# ===== AACT INTEGRATION ENDPOINTS =====

@app.post("/aact/compare-study")
async def aact_compare_study(request: AACTCompareStudyRequest):
    """
    Compare synthetic trial characteristics with AACT real-world benchmarks

    **Purpose:**
    Validates that synthetic trial structure (enrollment, treatment effect)
    matches real-world patterns from ClinicalTrials.gov (AACT database).

    **AACT Database:**
    - 557,805+ studies from ClinicalTrials.gov
    - Processed and cached using daft
    - Statistics by indication and phase
    - Enrollment, treatment effects, demographics, AEs

    **Comparison Metrics:**
    - **Enrollment Benchmark**: How trial size compares to real trials
      - Percentile within AACT distribution
      - Z-score relative to mean
      - Interpretation (Small/Median/Large)
    - **Treatment Effect Benchmark**: How effect size compares
      - Percentile within AACT distribution
      - Z-score relative to mean
      - Clinical interpretation
    - **Similarity Score**: Overall realism (0-1, higher = more realistic)
      - 0.8+: Highly realistic
      - 0.6-0.8: Realistic
      - 0.4-0.6: Moderately realistic
      - <0.4: Low realism

    **Request Parameters:**
    - n_subjects: Total enrolled (e.g., 100)
    - indication: "hypertension", "diabetes", "cancer", etc.
    - phase: "Phase 1", "Phase 2", "Phase 3", "Phase 4"
    - treatment_effect: Primary endpoint value (e.g., -5.0 mmHg SBP reduction)
    - vitals_data: Optional vitals for additional analysis

    **Response:**
    - enrollment_benchmark: Statistics comparing trial size
    - treatment_effect_benchmark: Statistics comparing effect size
    - aact_reference: Reference data from AACT
    - similarity_score: 0-1 realism score
    - interpretation: Human-readable assessment + recommendations

    **Available Indications:**
    hypertension, diabetes, cancer, oncology, cardiovascular,
    heart failure, asthma, copd

    **Use Case:**
    - Validate synthetic trial parameters before generation
    - Justify sample size and effect size choices
    - Benchmark against industry standards
    - Support regulatory discussions with real-world context
    """
    try:
        result = compare_study_to_aact(
            n_subjects=request.n_subjects,
            indication=request.indication,
            phase=request.phase,
            treatment_effect=request.treatment_effect,
            vitals_data=request.vitals_data
        )
        return convert_numpy_types(result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AACT cache not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT comparison failed: {str(e)}"
        )


@app.post("/aact/benchmark-demographics")
async def aact_benchmark_demographics(request: AACTBenchmarkDemographicsRequest):
    """
    Benchmark demographics against AACT real-world trial patterns

    **Purpose:**
    Compares synthetic demographics (age, gender, race) distributions
    against typical patterns from real-world ClinicalTrials.gov trials.

    **Demographics Analysis:**
    - **Age Distribution**: Mean, median, range
    - **Gender Split**: Male/Female percentages
    - **Race Distribution**: Racial/ethnic composition
    - **Treatment Arms**: Arm balance and sizes

    **Current Limitations:**
    - AACT cache provides limited demographic distributions
    - Full age/gender/race distributions require additional AACT processing
    - Qualitative assessment provided based on clinical trial knowledge

    **Qualitative Benchmarks (by Indication):**

    **Hypertension:**
    - Typical age: 45-65 years
    - Gender: 55-60% male
    - Common in diverse racial groups

    **Diabetes (Type 2):**
    - Typical age: 50-65 years
    - Gender: 50-55% male
    - Higher prevalence in certain ethnic groups

    **Response:**
    - demographics_summary: Statistics from synthetic data
    - aact_benchmarks: Available AACT data (study duration)
    - qualitative_assessment: Expert-based assessment
    - limitations: What's not available in current cache
    - future_enhancements: Planned improvements

    **Use Case:**
    - Validate demographic realism
    - Ensure trial population is representative
    - Identify potential bias in synthetic data
    - Support diversity and inclusion goals
    """
    try:
        demographics_df = pd.DataFrame(request.demographics_data)
        result = benchmark_demographics(
            demographics_df=demographics_df,
            indication=request.indication,
            phase=request.phase
        )
        return convert_numpy_types(result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AACT cache not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demographics benchmarking failed: {str(e)}"
        )


@app.post("/aact/benchmark-ae")
async def aact_benchmark_ae(request: AACTBenchmarkAERequest):
    """
    Benchmark adverse events patterns against AACT real-world trials

    **Purpose:**
    Compares synthetic AE patterns (frequency, top events) against
    real-world AE patterns from ClinicalTrials.gov trials.

    **AE Pattern Analysis:**
    - **Top Events Overlap**: Jaccard similarity of top AE terms
    - **Frequency Matching**: How well synthetic AE rates match real trials
    - **Event Coverage**: Which common events are present/missing
    - **Overall Similarity**: 0-1 score combining overlap + frequency

    **AACT AE Benchmarks (by Indication/Phase):**
    - Top 15 most common adverse events
    - Event frequencies (% of subjects affected)
    - Number of trials contributing data
    - Subjects affected per event

    **Similarity Scoring:**
    - **0.7+**: Highly realistic - Patterns closely match real trials
    - **0.5-0.7**: Realistic - Within expected range
    - **0.3-0.5**: Moderately realistic - Some deviations
    - **<0.3**: Low realism - Significant differences

    **Comparison Components:**
    - **Jaccard Similarity (70%)**: Overlap of top events
    - **Frequency Matching (30%)**: How well rates match

    **Example - Hypertension Phase 3 Top AEs:**
    1. Headache (23% of subjects)
    2. Dizziness (3.8%)
    3. Nausea (6.0%)
    4. Fatigue (3.5%)
    5. Back pain (3.5%)

    **Response:**
    - ae_summary: Statistics from synthetic AEs
    - aact_benchmarks: Top events from AACT
    - comparison: Matching events, unique events, frequency diffs
    - similarity_score: 0-1 overall realism score
    - interpretation: Assessment + recommendations

    **Use Case:**
    - Validate AE generation algorithms
    - Ensure realistic safety profiles
    - Compare different generation methods
    - Support regulatory readiness
    """
    try:
        ae_df = pd.DataFrame(request.ae_data)
        result = benchmark_adverse_events(
            ae_df=ae_df,
            indication=request.indication,
            phase=request.phase
        )
        return convert_numpy_types(result)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AACT cache not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AE benchmarking failed: {str(e)}"
        )


# ===== COMPREHENSIVE STUDY ANALYTICS ENDPOINTS (Phase 5) =====

@app.post("/study/comprehensive-summary")
async def study_comprehensive_summary(request: ComprehensiveStudyRequest):
    """
    Generate comprehensive study summary across all domains

    **Purpose:**
    Integrates demographics, vitals, labs, and AEs into a unified study summary
    suitable for Clinical Study Reports (CSR) and regulatory submissions.

    **Integration:**
    - **Demographics**: Baseline characteristics and randomization balance
    - **Efficacy**: Vitals-based endpoint analysis
    - **Safety**: Labs abnormalities + AE frequency
    - **AACT Benchmark**: Industry comparison for credibility
    - **Data Quality**: Completeness and regulatory readiness assessment

    **Returns:**
    - study_overview: Basic study statistics (n_subjects, data domains, total observations)
    - demographics_summary: Age, gender, treatment arms, randomization balance
    - efficacy_summary: Endpoint visit, treatment effect (SBP), by-arm results
    - safety_summary:
      - labs_safety: Abnormal rates, Grade 3-4 count, Hy's Law cases
      - ae_safety: Total AEs, SAE rate, top events, most common SOC
      - overall_safety_assessment: Aggregated safety flags
    - aact_benchmark: Similarity score, enrollment/effect percentiles, recommendations
    - data_quality: Completeness scores, quality assessment (Excellent/Good/Fair/Poor)
    - regulatory_readiness: Requirements met/pending, readiness score, submission status

    **Quality Assessment:**
    - Data completeness score (0-1): Proportion of key domains with data
    - Quality grades:
      - ≥0.95: EXCELLENT - All key data fields complete
      - ≥0.80: GOOD - Minor data gaps
      - ≥0.60: FAIR - Some data fields missing
      - <0.60: POOR - Significant data gaps

    **Regulatory Readiness:**
    - Checks for: Demographics Table 1, Efficacy data, Safety data, AACT benchmark
    - Readiness score (0-1): Proportion of requirements met
    - Status:
      - ≥0.90: SUBMISSION READY
      - ≥0.70: NEAR READY
      - ≥0.50: IN PROGRESS
      - <0.50: NOT READY

    **Use Case:**
    - Executive summary for sponsor/CRO
    - CSR appendix (integrated analysis)
    - Regulatory briefing document
    - DSMB interim reports
    - Portfolio review for multiple trials
    """
    try:
        # Convert lists to DataFrames
        demographics_df = pd.DataFrame(request.demographics_data) if request.demographics_data else None
        vitals_df = pd.DataFrame(request.vitals_data) if request.vitals_data else None
        labs_df = pd.DataFrame(request.labs_data) if request.labs_data else None
        ae_df = pd.DataFrame(request.ae_data) if request.ae_data else None

        result = generate_comprehensive_summary(
            demographics_data=demographics_df,
            vitals_data=vitals_df,
            labs_data=labs_df,
            ae_data=ae_df,
            indication=request.indication,
            phase=request.phase
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive summary generation failed: {str(e)}"
        )


@app.post("/study/cross-domain-correlations")
async def study_cross_domain_correlations(request: CrossDomainRequest):
    """
    Analyze correlations between different data domains

    **Purpose:**
    Identifies relationships across domains (demographics, vitals, labs, AEs)
    to uncover clinically meaningful patterns, potential confounders, and
    subgroup effects.

    **Cross-Domain Analyses:**

    1. **Demographics-Vitals Correlations:**
       - Age vs Blood Pressure (Pearson correlation)
       - Gender vs Blood Pressure (t-test)
       - Identifies age-dependent or gender-specific treatment effects

    2. **Demographics-AE Correlations:**
       - Age vs AE rate (Pearson correlation)
       - Gender vs AE rate (Mann-Whitney U test)
       - Detects demographic risk factors for adverse events

    3. **Labs-AE Overlap:**
       - Subjects with abnormal labs vs subjects with AEs
       - Overlap rate: What % of abnormal labs also had AEs
       - Assesses whether lab monitoring captures safety events

    4. **Vitals-Labs Correlations:**
       - Systolic BP vs Creatinine (Pearson correlation)
       - Identifies physiological relationships
       - Useful for mixed models and multivariate analysis

    **Statistical Methods:**
    - Pearson correlation: Linear relationships between continuous variables
    - Welch's t-test: Group differences (e.g., male vs female)
    - Mann-Whitney U: Non-parametric group comparisons (AE rates)
    - Overlap analysis: Set intersection (labs ∩ AEs)

    **Returns:**
    - demographics_vitals:
      - age_vs_sbp: Correlation, p-value, significance, interpretation
      - gender_vs_sbp: Mean differences, t-statistic, p-value
    - demographics_ae:
      - age_vs_ae_rate: Correlation, p-value, significance
      - gender_vs_ae_rate: Mean AE counts, U-statistic, p-value
    - labs_ae:
      - Subjects with abnormal labs, AEs, both, or either only
      - Overlap rate (0-1)
      - Association strength interpretation
    - vitals_labs:
      - sbp_vs_creatinine: Correlation, p-value, n_observations
    - clinical_insights: List of key findings and recommendations

    **Clinical Insights Examples:**
    - "Age significantly correlates with blood pressure (r=0.45), suggesting age-dependent efficacy"
    - "Significant gender difference in blood pressure (Δ=8.2 mmHg), consider gender-stratified analysis"
    - "Strong association between lab abnormalities and AEs suggests lab monitoring is capturing safety events"

    **Use Case:**
    - Subgroup analysis planning
    - Covariate identification for adjusted analyses
    - Safety signal investigation
    - Understanding mechanism of action
    - Protocol refinement for future studies
    """
    try:
        # Convert lists to DataFrames
        demographics_df = pd.DataFrame(request.demographics_data) if request.demographics_data else None
        vitals_df = pd.DataFrame(request.vitals_data) if request.vitals_data else None
        labs_df = pd.DataFrame(request.labs_data) if request.labs_data else None
        ae_df = pd.DataFrame(request.ae_data) if request.ae_data else None

        result = analyze_cross_domain_correlations(
            demographics_data=demographics_df,
            vitals_data=vitals_df,
            labs_data=labs_df,
            ae_data=ae_df
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cross-domain correlation analysis failed: {str(e)}"
        )


@app.post("/study/trial-dashboard")
async def study_trial_dashboard(request: TrialDashboardRequest):
    """
    Generate executive trial dashboard with key performance indicators

    **Purpose:**
    Creates a high-level dashboard suitable for executive review, DSMB reports,
    and regulatory briefing documents. Integrates all domains with AACT context
    for industry benchmark comparison.

    **Dashboard Sections:**

    1. **Executive Summary:**
       - Total subjects enrolled
       - Data domains available (Demographics, Vitals, Labs, AEs)
       - Data completeness (X/4 domains)

    2. **Enrollment Status:**
       - Total enrolled vs target
       - By treatment arm (Active vs Placebo)
       - Randomization balance assessment (Well-balanced / Imbalanced)

    3. **Efficacy Metrics:**
       - Primary endpoint visit (e.g., Week 12)
       - Mean SBP by treatment arm
       - Treatment effect (Active - Placebo)
       - Efficacy assessment:
         - <-10 mmHg: STRONG EFFECT
         - -10 to -5 mmHg: MODERATE EFFECT
         - -5 to 0 mmHg: WEAK EFFECT
         - >0 mmHg: NO EFFECT

    4. **Safety Metrics:**
       - Total AEs, SAEs
       - AE rate (% subjects with any AE)
       - SAE rate (% of all AEs)
       - Top 5 most common AEs
       - Hy's Law cases (DILI)
       - Kidney decline cases
       - Overall safety assessment (flags for high SAE rate, Hy's Law)

    5. **Quality Metrics:**
       - Data completeness score (0-1)
       - SDTM compliance status
       - AACT similarity score
       - Quality assessment (High/Good/Limited)

    6. **AACT Context:**
       - Enrollment percentile (industry comparison)
       - Treatment effect percentile
       - Similarity score (0-1)
       - Industry assessment (e.g., "HIGHLY REALISTIC")
       - Number of reference trials from AACT

    7. **Risk Flags:**
       - Severity levels: CRITICAL, HIGH, MEDIUM
       - Categories: Enrollment, Efficacy, Safety, Data Quality
       - Issue description + Recommendation
       - Example: "CRITICAL - 2 Hy's Law cases → Immediate DSMB notification"

    8. **Recommendations:**
       - Actionable next steps based on risk flags
       - AACT-based recommendations for parameter adjustments
       - Overall trial status (progressing well / needs attention)

    **Risk Flag Criteria:**
    - **Enrollment**: Treatment arm imbalance >10%
    - **Efficacy**: Weak or no effect detected
    - **Safety**: Hy's Law cases (CRITICAL), SAE rate >15% (HIGH)
    - **Data Quality**: Completeness <50% (MEDIUM)

    **Use Case:**
    - Executive briefings (C-suite, Board)
    - DSMB interim reports
    - Regulatory authority meetings (FDA, EMA)
    - Portfolio review dashboards
    - Real-time trial monitoring
    - Quarterly business reviews (QBR)
    """
    try:
        # Convert lists to DataFrames
        demographics_df = pd.DataFrame(request.demographics_data) if request.demographics_data else None
        vitals_df = pd.DataFrame(request.vitals_data) if request.vitals_data else None
        labs_df = pd.DataFrame(request.labs_data) if request.labs_data else None
        ae_df = pd.DataFrame(request.ae_data) if request.ae_data else None

        result = generate_trial_dashboard(
            demographics_data=demographics_df,
            vitals_data=vitals_df,
            labs_data=labs_df,
            ae_data=ae_df,
            indication=request.indication,
            phase=request.phase
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trial dashboard generation failed: {str(e)}"
        )


# ===== BENCHMARKING & EXTENSIONS ENDPOINTS (Phase 6) =====

@app.post("/benchmark/performance")
async def benchmark_performance(request: MethodComparisonRequest):
    """
    Compare performance of different data generation methods

    **Purpose:**
    Compares MVN, Bootstrap, Rules, and LLM data generation methods across
    multiple dimensions: speed, quality, AACT similarity, memory usage.

    **Comparison Dimensions:**

    1. **Speed (records/second):**
       - MVN: ~29,000 rec/sec (fastest statistical method)
       - Bootstrap: ~140,000 rec/sec (fastest overall)
       - Rules: ~80,000 rec/sec (fast deterministic)
       - LLM: ~70 rec/sec (slowest, API latency)

    2. **Quality Score (0-1):**
       - Comprehensive quality assessment score
       - Based on Wasserstein distance, correlation preservation, K-NN
       - Higher = better match to real data

    3. **AACT Similarity (0-1):**
       - How well method matches real-world trial patterns
       - Based on enrollment, treatment effects, AE patterns
       - Higher = more realistic

    4. **Memory Usage (MB):**
       - Peak memory consumption during generation
       - Important for large-scale generation (millions of records)

    **Scoring:**
    - Weighted overall score: 40% quality + 40% speed + 20% AACT
    - Ranking: Methods ranked 1-4 by overall score

    **Request Format:**
    ```json
    {
      "methods_data": {
        "mvn": {
          "records_per_second": 29000,
          "quality_score": 0.87,
          "aact_similarity": 0.91,
          "memory_mb": 45
        },
        "bootstrap": {
          "records_per_second": 140000,
          "quality_score": 0.92,
          "aact_similarity": 0.88,
          "memory_mb": 38
        },
        "rules": { ... },
        "llm": { ... }
      }
    }
    ```

    **Response:**
    - method_comparison: Performance table with all metrics
    - ranking: Methods ranked by overall score
    - recommendations: Which method to use for different scenarios
    - tradeoffs: Speed vs quality vs realism considerations

    **Recommendations by Use Case:**
    - **Production (millions of records)**: Bootstrap (fastest + high quality)
    - **Research (highest quality)**: LLM (creative, context-aware)
    - **Regulatory (highest realism)**: Method with highest AACT similarity
    - **Testing (fast iteration)**: Bootstrap or Rules

    **Use Case:**
    - Method selection for data generation pipeline
    - Performance benchmarking
    - Resource planning (memory, compute)
    - Method comparison for publications
    - Justifying method choice to stakeholders
    """
    try:
        result = compare_generation_methods(request.methods_data)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Method comparison failed: {str(e)}"
        )


@app.post("/benchmark/quality-scores")
async def benchmark_quality_scores(request: AggregateQualityRequest):
    """
    Aggregate quality scores across all data domains

    **Purpose:**
    Combines quality assessments from demographics, vitals, labs, AEs, and AACT
    into a single overall quality score with detailed breakdown.

    **Domain Quality Scores (0-1):**

    1. **Demographics Quality (20% weight):**
       - Wasserstein distance for Age, Weight, Height, BMI
       - Chi-square tests for Gender, Race, Ethnicity
       - Correlation preservation

    2. **Vitals Quality (25% weight):**
       - Distribution similarity for SBP, DBP, HR, Temp
       - K-NN imputation score
       - Temporal pattern preservation

    3. **Labs Quality (25% weight):**
       - Wasserstein distance for all lab tests
       - KS test pass rate
       - Mean differences vs real data

    4. **AE Quality (20% weight):**
       - SOC distribution similarity
       - PT overlap (Jaccard)
       - Severity/relationship distribution match

    5. **AACT Similarity (10% weight):**
       - Enrollment realism
       - Treatment effect realism
       - Overall trial structure match

    **Weighted Formula:**
    ```
    Overall = 0.20×Demographics + 0.25×Vitals + 0.25×Labs + 0.20×AE + 0.10×AACT
    ```

    **Quality Grades:**
    - **A+ (≥0.95)**: Exceptional - Publication quality
    - **A (0.90-0.95)**: Excellent - Production ready
    - **B+ (0.85-0.90)**: Very Good - Minor improvements possible
    - **B (0.80-0.85)**: Good - Usable with minor adjustments
    - **C+ (0.75-0.80)**: Fair - Some improvements needed
    - **C (0.70-0.75)**: Acceptable - Moderate improvements needed
    - **D (0.60-0.70)**: Poor - Significant improvements needed
    - **F (<0.60)**: Failing - Not recommended for use

    **Completeness Score:**
    - Proportion of domains with quality data (0-1)
    - 5/5 domains = 1.0 (fully comprehensive)
    - 3/5 domains = 0.6 (partial)

    **Response:**
    - domain_scores: Individual scores for each domain
    - overall_quality: Weighted aggregate score (0-1)
    - quality_grade: Letter grade (A+ to F)
    - completeness: Data domain coverage (0-1)
    - interpretation: Human-readable assessment
    - benchmarks: How score compares to industry standards
    - recommendations: Specific improvements by domain

    **Interpretation Examples:**
    - **0.92 (A)**: "Excellent synthetic data quality across all domains.
       Production-ready for regulatory submissions and publications."
    - **0.78 (C+)**: "Fair quality. Demographics and vitals are good (>0.85),
       but AE patterns need improvement. Consider adjusting AE generation parameters."
    - **0.65 (D)**: "Poor quality. Significant deviations in labs (0.58) and AEs (0.62).
       Review generation method and parameters."

    **Use Case:**
    - Comprehensive quality validation
    - Method comparison across all domains
    - Quality assurance before production use
    - Regulatory documentation (quality evidence)
    - Identifying which domains need improvement
    - Portfolio-level quality tracking
    """
    try:
        result = aggregate_quality_scores(
            demographics_quality=request.demographics_quality,
            vitals_quality=request.vitals_quality,
            labs_quality=request.labs_quality,
            ae_quality=request.ae_quality,
            aact_similarity=request.aact_similarity
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality score aggregation failed: {str(e)}"
        )


@app.post("/study/recommendations")
async def study_recommendations(request: RecommendationsRequest):
    """
    Generate data generation parameter recommendations

    **Purpose:**
    Analyzes current quality scores and provides specific, actionable recommendations
    for improving synthetic data quality and realism. Uses AACT benchmarks to
    suggest optimal parameter values.

    **Analysis Inputs:**
    - current_quality: Overall quality score (0-1)
    - aact_similarity: AACT benchmark similarity (0-1)
    - generation_method: "mvn", "bootstrap", "rules", "llm"
    - n_subjects: Current sample size
    - indication: Disease indication (e.g., "hypertension")
    - phase: Trial phase (e.g., "Phase 3")

    **Recommendation Categories:**

    1. **Quality Improvements:**
       - If quality < 0.85: Suggests parameter tuning
       - Specific recommendations per generation method:
         - MVN: Adjust covariance matrix, increase correlation realism
         - Bootstrap: Increase jitter fraction, adjust resampling strategy
         - Rules: Add variability, incorporate clinical ranges
         - LLM: Refine prompts, add clinical context

    2. **AACT Alignment:**
       - If AACT similarity < 0.7: Trial structure needs adjustment
       - Enrollment recommendations (based on AACT percentiles):
         - Too small: Suggest industry-typical enrollment (e.g., 225 for HTN Phase 3)
         - Too large: Flag unrealistic enrollment
       - Treatment effect recommendations:
         - Compare to AACT mean/median for indication/phase
         - Suggest realistic effect sizes

    3. **Method Recommendations:**
       - If quality consistently low: Suggest switching methods
       - Performance trade-offs (speed vs quality)
       - Method-specific best practices

    4. **Parameter Optimization:**
       - n_subjects: Industry-typical enrollment
       - target_effect: Realistic treatment effect size
       - jitter_frac (Bootstrap): Optimal noise level
       - correlation_strength (MVN): Realistic inter-variable correlation

    **Priority Levels:**
    - **HIGH**: Critical issues impacting quality/realism (Δ quality >0.15)
    - **MEDIUM**: Moderate improvements possible (Δ quality 0.05-0.15)
    - **LOW**: Minor refinements (Δ quality <0.05)

    **Response:**
    - current_status: Assessment of current quality and realism
    - improvement_opportunities: Prioritized list of improvements
    - parameter_recommendations: Specific parameter values to try
    - method_recommendations: Alternative methods to consider
    - expected_improvements: Estimated quality boost per recommendation
    - aact_context: Industry benchmarks for comparison

    **Example Recommendations:**

    **Scenario 1 - Quality 0.72, AACT 0.65:**
    ```
    Priority: HIGH
    Issue: Quality below production threshold (0.72 < 0.85)
    AACT similarity low (0.65 < 0.70)

    Recommendations:
    1. Increase n_subjects from 50 to 225 (AACT median for HTN Phase 3)
    2. Adjust treatment effect from -3.0 to -5.2 mmHg (AACT mean)
    3. Switch from Rules to Bootstrap for better quality (expect +0.15)
    4. Increase bootstrap jitter_frac from 0.05 to 0.08 (more variability)

    Expected outcome: Quality 0.87, AACT 0.82
    ```

    **Scenario 2 - Quality 0.90, AACT 0.88:**
    ```
    Priority: MEDIUM
    Issue: Good quality but can optimize further

    Recommendations:
    1. Fine-tune MVN covariance for correlation preservation (+0.03)
    2. Add temporal trends to match longitudinal patterns (+0.02)
    3. Enrollment (100) is reasonable but 225 is more typical (AACT)

    Expected outcome: Quality 0.95 (A+), AACT 0.92
    ```

    **Use Case:**
    - Parameter tuning for data generation
    - Quality improvement roadmap
    - Method selection guidance
    - AACT-based trial design validation
    - Regulatory readiness preparation
    - Continuous quality improvement
    """
    try:
        result = generate_recommendations(
            current_quality=request.current_quality,
            aact_similarity=request.aact_similarity,
            generation_method=request.generation_method,
            n_subjects=request.n_subjects,
            indication=request.indication,
            phase=request.phase
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendations generation failed: {str(e)}"
        )


# =============================================================================
# PHASE 7: SURVIVAL ANALYSIS ENDPOINTS
# =============================================================================

@app.post("/survival/comprehensive")
async def analyze_survival_comprehensive(request: SurvivalAnalysisRequest):
    """
    Comprehensive survival analysis including KM curves, log-rank test, and hazard ratios.

    **What It Does:**
    1. Generates time-to-event data from demographics
    2. Calculates Kaplan-Meier survival curves for each arm
    3. Performs log-rank test for difference between arms
    4. Calculates hazard ratio with 95% CI
    5. Exports data in CDISC SDTM TTE domain format

    **Use Cases:**
    - Oncology trials (Overall Survival, Progression-Free Survival)
    - Time-to-event endpoints in any therapeutic area
    - CSR survival analysis tables
    - Regulatory submission packages (SDTM TTE domain)
    """
    try:
        result = comprehensive_survival_analysis(
            demographics_data=request.demographics_data,
            indication=request.indication,
            median_survival_active=request.median_survival_active,
            median_survival_placebo=request.median_survival_placebo,
            seed=request.seed
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Survival analysis failed: {str(e)}"
        )


@app.post("/survival/kaplan-meier")
async def calculate_km_curves(request: Dict[str, Any]):
    """
    Calculate Kaplan-Meier survival curves with confidence intervals.

    **Inputs:**
    - survival_data: List of survival records with EventTime, EventOccurred, Censored
    - treatment_arm: Optional specific arm to analyze (None = all)

    **Outputs:**
    - km_curve: Time points with survival probability and CI
    - median_survival: Median survival time
    - n_subjects, n_events, n_censored
    """
    try:
        survival_data = request.get("survival_data", [])
        treatment_arm = request.get("treatment_arm")

        result = calculate_kaplan_meier(survival_data, treatment_arm)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KM calculation failed: {str(e)}"
        )


@app.post("/survival/log-rank-test")
async def perform_log_rank_test(request: Dict[str, Any]):
    """
    Perform log-rank test to compare survival curves between two treatment arms.

    **Statistical Test:**
    - Null hypothesis: No difference in survival between arms
    - Test statistic: Chi-square with 1 df
    - Significance level: α = 0.05

    **Outputs:**
    - test_statistic: Chi-square value
    - p_value: Two-sided p-value
    - significant: Boolean (p < 0.05)
    - interpretation: Text summary
    """
    try:
        survival_data = request.get("survival_data", [])
        arm1 = request.get("arm1", "Active")
        arm2 = request.get("arm2", "Placebo")

        result = log_rank_test(survival_data, arm1, arm2)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Log-rank test failed: {str(e)}"
        )


@app.post("/survival/hazard-ratio")
async def calculate_hr(request: Dict[str, Any]):
    """
    Calculate hazard ratio comparing treatment to reference arm.

    **Hazard Ratio Interpretation:**
    - HR < 1: Treatment reduces risk (favors treatment)
    - HR = 1: No difference between arms
    - HR > 1: Treatment increases risk (favors control)

    **Example:**
    HR = 0.75 (95% CI: 0.58, 0.97)
    Treatment reduces risk of death by 25% vs control (p=0.032)

    **Outputs:**
    - hazard_ratio: HR value
    - ci_lower, ci_upper: 95% confidence interval
    - interpretation: Clinical benefit assessment
    """
    try:
        survival_data = request.get("survival_data", [])
        reference_arm = request.get("reference_arm", "Placebo")
        treatment_arm = request.get("treatment_arm", "Active")

        result = calculate_hazard_ratio(survival_data, reference_arm, treatment_arm)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hazard ratio calculation failed: {str(e)}"
        )


# =============================================================================
# PHASE 8: ADAM DATASET GENERATION ENDPOINTS
# =============================================================================

@app.post("/adam/generate-all")
async def generate_all_adam(request: AdamGenerationRequest):
    """
    Generate all CDISC ADaM datasets from source data.

    **What It Generates:**
    1. **ADSL** - Subject-Level Analysis Dataset (one row per subject)
    2. **ADTTE** - Time-to-Event Analysis Dataset (survival endpoints)
    3. **ADAE** - Adverse Event Analysis Dataset (safety analysis)
    4. **BDS Vitals** - Basic Data Structure for vitals (longitudinal)
    5. **BDS Labs** - Basic Data Structure for labs (longitudinal)

    **Why ADaM?**
    - FDA/EMA require ADaM for regulatory submissions
    - ADaM is analysis-ready (vs SDTM which is collected data)
    - Biostatisticians work directly with ADaM datasets
    - ADaM includes derived variables (BASE, CHG, analysis flags)

    **Use Cases:**
    - Regulatory submission packages
    - Statistical analysis programming
    - Biostatistician training
    - Method validation
    """
    try:
        result = generate_all_adam_datasets(
            demographics_data=request.demographics_data,
            vitals_data=request.vitals_data,
            labs_data=request.labs_data,
            ae_data=request.ae_data,
            survival_data=request.survival_data,
            study_id=request.study_id
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ADaM generation failed: {str(e)}"
        )


@app.post("/adam/adsl")
async def generate_adsl_dataset(request: AdamGenerationRequest):
    """
    Generate ADSL (Subject-Level Analysis Dataset).

    **ADSL is the cornerstone dataset containing:**
    - Demographics (age, sex, race, ethnicity)
    - Treatment assignment (planned and actual)
    - Important dates (screening, randomization, treatment start/end)
    - Disposition (completed, discontinued, reason)
    - Analysis population flags (ITT, Safety, Per-Protocol)
    - Baseline values
    - Derived variables for analysis

    **One record per subject** - All other ADaM datasets link to ADSL via USUBJID.
    """
    try:
        adsl = generate_adsl(
            demographics_data=request.demographics_data,
            vitals_data=request.vitals_data,
            ae_data=request.ae_data,
            study_id=request.study_id
        )
        return convert_numpy_types({"ADSL": adsl, "n_subjects": len(adsl)})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ADSL generation failed: {str(e)}"
        )


# =============================================================================
# PHASE 9: TLF AUTOMATION ENDPOINTS
# =============================================================================

@app.post("/tlf/generate-all")
async def generate_all_tlf(request: TLFRequest):
    """
    Generate all standard TLF (Tables, Listings, Figures) for clinical study report.

    **What It Generates:**
    1. **Table 1** - Demographics and Baseline Characteristics
    2. **Table 2** - Adverse Event Summary by SOC and Preferred Term
    3. **Table 3** - Efficacy Endpoints Summary

    **Why This Matters:**
    - Biostatisticians spend 30-40% of time creating these tables manually
    - Automation saves weeks of work per study
    - Ensures consistency across trials
    - Publication-ready format (markdown + structured data)

    **Output Formats:**
    - Structured table data (for programmatic use)
    - Markdown format (for Word/PDF export)
    - Ready for regulatory submission

    **Use Cases:**
    - CSR table generation
    - Manuscript preparation
    - Protocol amendments (sample tables)
    - Training (showing expected output format)
    """
    try:
        result = generate_all_tlf_tables(
            demographics_data=request.demographics_data,
            ae_data=request.ae_data,
            vitals_data=request.vitals_data,
            survival_data=request.survival_data
        )
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TLF generation failed: {str(e)}"
        )


@app.post("/tlf/table1-demographics")
async def generate_table1(request: Dict[str, Any]):
    """
    Generate Table 1: Demographics and Baseline Characteristics.

    **Standard Table 1 Format:**
    - Age (mean, SD, min, max, categories)
    - Gender (n, %)
    - Race (n, %)
    - Ethnicity (n, %)
    - Weight, Height, BMI
    - By treatment arm + total column

    **Statistical Tests:**
    - Continuous: t-test or Wilcoxon
    - Categorical: Chi-square or Fisher's exact
    - Assesses baseline comparability between arms

    **Output:**
    - Table data (JSON)
    - Markdown format (for Word export)
    - Statistical test results (if requested)
    """
    try:
        demographics_data = request.get("demographics_data", [])
        include_stats = request.get("include_stats", True)

        result = generate_table1_demographics(demographics_data, include_stats)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Table 1 generation failed: {str(e)}"
        )


@app.post("/tlf/table2-adverse-events")
async def generate_table2_ae(request: Dict[str, Any]):
    """
    Generate Table 2: Adverse Event Summary by SOC and Preferred Term.

    **Standard AE Table Format:**
    - Any Adverse Event (overall incidence)
    - Any Serious Adverse Event
    - Any Related Adverse Event
    - By System Organ Class (MedDRA SOC)
      - Preferred Terms within each SOC
    - Shows n (%) for each treatment arm
    - Only AEs occurring in ≥5% of subjects (configurable)

    **Use Cases:**
    - CSR safety section
    - SAE reporting
    - Risk-benefit assessment
    - Regulatory review
    """
    try:
        ae_data = request.get("ae_data", [])
        by_soc = request.get("by_soc", True)
        min_incidence = request.get("min_incidence", 5.0)

        result = generate_ae_summary_table(ae_data, by_soc, min_incidence)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AE table generation failed: {str(e)}"
        )


@app.post("/tlf/table3-efficacy")
async def generate_table3_efficacy(request: Dict[str, Any]):
    """
    Generate Table 3: Efficacy Endpoints Summary.

    **For Vitals Endpoints:**
    - Primary: Systolic BP at Week 12 (mean, SD by arm)
    - Secondary: Diastolic BP, Heart Rate
    - Treatment effect (difference with 95% CI)
    - P-value from t-test

    **For Survival Endpoints:**
    - Median survival by arm
    - Hazard ratio (95% CI)
    - P-value from log-rank test
    - Events/censored counts

    **Output:**
    - Formatted efficacy table
    - Statistical test results
    - Clinical interpretation
    """
    try:
        vitals_data = request.get("vitals_data")
        survival_data = request.get("survival_data")
        endpoint_type = request.get("endpoint_type", "vitals")

        result = generate_efficacy_table(vitals_data, survival_data, endpoint_type)
        return convert_numpy_types(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Efficacy table generation failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
