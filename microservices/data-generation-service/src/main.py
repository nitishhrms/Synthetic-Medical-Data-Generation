"""
Data Generation Service - Synthetic Clinical Trial Data
Handles rules-based, MVN, and LLM-based data generation
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import uvicorn
import os

from generators import (
    generate_vitals_rules,
    generate_vitals_mvn,
    generate_vitals_llm_with_repair,
    generate_oncology_ae,
    generate_vitals_bootstrap,
    generate_demographics,
    generate_labs,
    # AACT-enhanced generators
    generate_vitals_mvn_aact,
    generate_vitals_bootstrap_aact,
    generate_vitals_rules_aact,
    generate_demographics_aact,
    generate_labs_aact,
    generate_oncology_ae_aact
)
from db_utils import db, cache, startup_db, shutdown_db

app = FastAPI(
    title="Data Generation Service",
    description="Synthetic Clinical Trial Data Generation (Rules/LLM/MVN)",
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
class GenerateRulesRequest(BaseModel):
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Number of subjects per arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg)")
    seed: int = Field(default=42, description="Random seed for reproducibility")

class GenerateMVNRequest(BaseModel):
    n_per_arm: int = Field(default=50, ge=1, le=500)
    target_effect: float = Field(default=-5.0)
    seed: int = Field(default=123)
    train_source: str = Field(default="pilot", description="Training data source: 'pilot' or 'current'")
    current_df_json: Optional[str] = None

class GenerateLLMRequest(BaseModel):
    indication: str = Field(default="Solid Tumor (Immuno-Oncology)")
    n_per_arm: int = Field(default=50, ge=1, le=100)
    target_effect: float = Field(default=-5.0)
    api_key: Optional[str] = None
    model: str = Field(default="gpt-4o-mini")
    extra_instructions: str = Field(default="")
    max_repair_iters: int = Field(default=2, ge=0, le=5)

class GenerateAERequest(BaseModel):
    n_subjects: int = Field(default=30, ge=10, le=100)
    seed: int = Field(default=7)

class GenerateBootstrapRequest(BaseModel):
    training_data: List[Dict[str, Any]] = Field(..., description="Pilot/existing data to bootstrap from")
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Number of subjects per arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg)")
    jitter_frac: float = Field(default=0.05, ge=0, le=0.5, description="Fraction of std for numeric noise")
    cat_flip_prob: float = Field(default=0.05, ge=0, le=0.3, description="Probability of categorical flip")
    seed: int = Field(default=42, description="Random seed")

# Response model - returns array directly for compatibility with EDC validation service
VitalsResponse = List[Dict[str, Any]]

AEResponse = List[Dict[str, Any]]

class LLMGenerationResponse(BaseModel):
    data: List[Dict[str, Any]]
    rows: int
    columns: List[str]
    validation_report: Dict[str, Any]
    prompt_used: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db.pool else "disconnected"
    cache_status = "connected" if cache.enabled and cache.client else "disconnected"

    return {
        "status": "healthy",
        "service": "data-generation-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "cache": cache_status
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Data Generation Service",
        "version": "3.0.0",
        "methods": [
            "Rules-based generation",
            "MVN (Multivariate Normal) generation",
            "LLM-based generation with auto-repair",
            "Bootstrap sampling - fast augmentation from pilot data",
            "AACT-enhanced generators (NEW!) - using 557K+ real trials",
            "Comprehensive study generation (NEW!)",
            "Multi-study portfolio generation (NEW!)",
            "Oncology AE generation"
        ],
        "endpoints": {
            "health": "/health",
            "rules": "/generate/rules",
            "mvn": "/generate/mvn",
            "llm": "/generate/llm",
            "bootstrap": "/generate/bootstrap",
            "ae": "/generate/ae",
            "demographics": "/generate/demographics",
            "labs": "/generate/labs",
            "comprehensive_study": "/generate/comprehensive-study",
            "multi_study_portfolio": "/generate/multi-study-portfolio",
            "compare": "/compare",
            "benchmark": "/benchmark/performance",
            "stress_test": "/stress-test/concurrent",
            "portfolio_analytics": "/analytics/portfolio",
            "pilot_data": "/data/pilot",
            "real_vitals": "/data/real-vitals",
            "real_demographics": "/data/real-demographics",
            "real_ae": "/data/real-ae",
            "docs": "/docs"
        },
        "scalability_features": {
            "comprehensive_study": "Generate complete trial (vitals+demographics+labs+AE) in one call",
            "multi_study_portfolio": "Generate multiple studies concurrently",
            "performance_benchmark": "Compare generation methods (MVN, Bootstrap, Rules)",
            "stress_test": "Test concurrent generation capacity",
            "portfolio_analytics": "Organization-wide analytics dashboard"
        },
        "aact_enhanced": True,
        "aact_trials_count": 557805
    }

@app.post("/generate/rules", response_model=VitalsResponse)
async def generate_rules_based(request: GenerateRulesRequest):
    """
    Generate synthetic vitals data using rules-based approach

    This method uses normal distributions with clinical constraints:
    - SystolicBP ~ N(130, 10)
    - DiastolicBP ~ N(80, 8)
    - HeartRate ~ Uniform(60, 100)
    - Temperature ~ N(36.8, 0.3)
    """
    try:
        df = generate_vitals_rules(
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            seed=request.seed
        )

        # Return just the data array for compatibility with EDC validation service
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )

@app.post("/generate/mvn", response_model=VitalsResponse)
async def generate_mvn_based(request: GenerateMVNRequest):
    """
    Generate synthetic vitals data using Multivariate Normal approach

    Learns mean and covariance from pilot data per (Visit, Arm) combination,
    then samples from fitted distributions.
    """
    try:
        current_df = None
        if request.train_source == "current" and request.current_df_json:
            import json
            current_df = pd.DataFrame(json.loads(request.current_df_json))

        df = generate_vitals_mvn(
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            seed=request.seed,
            train_source=request.train_source,
            current_df=current_df
        )

        # Return just the data array for compatibility with EDC validation service
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MVN generation failed: {str(e)}"
        )

@app.post("/generate/llm", response_model=LLMGenerationResponse)
async def generate_llm_based(request: GenerateLLMRequest):
    """
    Generate synthetic vitals data using LLM (OpenAI GPT)

    Uses prompt engineering to generate CSV data, with automatic
    validation and repair loop to ensure clinical constraints.
    """
    try:
        df, validation_report, prompt_used = generate_vitals_llm_with_repair(
            indication=request.indication,
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            api_key=request.api_key,
            model=request.model,
            extra_instructions=request.extra_instructions,
            max_iters=request.max_repair_iters
        )

        return LLMGenerationResponse(
            data=df.to_dict(orient="records"),
            rows=len(df),
            columns=df.columns.tolist(),
            validation_report=validation_report,
            prompt_used=prompt_used
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}"
        )

@app.post("/generate/ae", response_model=AEResponse)
async def generate_adverse_events(request: GenerateAERequest):
    """
    Generate synthetic oncology adverse events (SDTM AE domain)

    Includes realistic AE terms, body systems, and severity classifications.
    """
    try:
        df = generate_oncology_ae(
            n_subjects=request.n_subjects,
            seed=request.seed
        )

        # Return just the data array
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AE generation failed: {str(e)}"
        )

@app.post("/generate/bootstrap", response_model=VitalsResponse)
async def generate_bootstrap_based(request: GenerateBootstrapRequest):
    """
    Generate synthetic vitals data using bootstrap sampling (NEW!)

    **Method:** Row-based bootstrap with intelligent augmentation

    **Best for:**
    - Quick augmentation from pilot study data
    - Expanding existing datasets
    - Preserving real data characteristics
    - When you have sample data but need more

    **Advantages:**
    - ⚡ Fast - no training required
    - 💰 Free - no API costs
    - 🎯 Preserves correlations from real data
    - 🔧 Highly configurable noise/diversity
    - ✅ Enforces clinical constraints
    - 🎲 Treatment effect control

    **How it works:**
    1. Bootstrap samples complete rows with replacement
    2. Adds Gaussian jitter to numeric columns (scaled by std)
    3. Respects clinical ranges (BP, HR, Temp)
    4. Randomly flips categorical values for diversity
    5. Ensures complete visit sequences per subject
    6. Applies target treatment effect at Week 12
    7. Regenerates proper SubjectIDs (RA###-###)

    **Parameters:**
    - training_data: Your pilot/existing data (required)
    - n_per_arm: Subjects per arm (default: 50)
    - target_effect: Target SystolicBP reduction at Week 12 (default: -5.0 mmHg)
    - jitter_frac: Noise level as fraction of std (default: 0.05 = 5%)
    - cat_flip_prob: Categorical flip probability (default: 0.05 = 5%)
    - seed: Random seed for reproducibility (default: 42)
    """
    try:
        # Convert request data to DataFrame
        training_df = pd.DataFrame(request.training_data)

        # Generate synthetic data
        df = generate_vitals_bootstrap(
            training_df=training_df,
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            jitter_frac=request.jitter_frac,
            cat_flip_prob=request.cat_flip_prob,
            seed=request.seed
        )

        # Return just the data array for compatibility with EDC validation service
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bootstrap generation failed: {str(e)}"
        )

@app.get("/compare")
async def compare_methods(
    n_per_arm: int = 50,
    target_effect: float = -5.0,
    seed: int = 42
):
    """
    Compare all generation methods (MVN, Bootstrap, Rules)

    Returns generated data from each method along with performance metrics.
    Useful for evaluating which method produces the best quality synthetic data.

    Query Parameters:
    - n_per_arm: Number of subjects per treatment arm (default: 50)
    - target_effect: Target treatment effect in mmHg (default: -5.0)
    - seed: Random seed for reproducibility (default: 42)

    Returns:
    - mvn_data: Synthetic data from MVN method
    - bootstrap_data: Synthetic data from Bootstrap method
    - rules_data: Synthetic data from Rules method
    - comparison: Performance metrics and statistics for each method
    """
    try:
        import time

        # Load pilot data for bootstrap
        # Use dynamic path resolution to work in any environment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        pilot_path = os.path.join(project_root, "data/pilot_trial_cleaned.csv")
        pilot_df = pd.read_csv(pilot_path)

        # Generate with MVN
        start_mvn = time.time()
        mvn_df = generate_vitals_mvn(
            n_per_arm=n_per_arm,
            target_effect=target_effect,
            seed=seed
        )
        mvn_time_ms = (time.time() - start_mvn) * 1000

        # Generate with Bootstrap
        start_bootstrap = time.time()
        bootstrap_df = generate_vitals_bootstrap(
            training_df=pilot_df,
            n_per_arm=n_per_arm,
            target_effect=target_effect,
            seed=seed
        )
        bootstrap_time_ms = (time.time() - start_bootstrap) * 1000

        # Generate with Rules
        start_rules = time.time()
        rules_df = generate_vitals_rules(
            n_per_arm=n_per_arm,
            target_effect=target_effect,
            seed=seed
        )
        rules_time_ms = (time.time() - start_rules) * 1000

        # Calculate basic statistics for comparison
        def get_stats(df):
            week12 = df[df['VisitName'] == 'Week 12']
            active = week12[week12['TreatmentArm'] == 'Active']['SystolicBP']
            placebo = week12[week12['TreatmentArm'] == 'Placebo']['SystolicBP']

            return {
                "total_records": len(df),
                "total_subjects": df['SubjectID'].nunique(),
                "week12_mean_active": float(active.mean()) if len(active) > 0 else None,
                "week12_mean_placebo": float(placebo.mean()) if len(placebo) > 0 else None,
                "week12_effect": float(active.mean() - placebo.mean()) if len(active) > 0 and len(placebo) > 0 else None
            }

        return {
            "mvn": {
                "data": mvn_df.to_dict(orient="records"),
                "stats": get_stats(mvn_df),
                "generation_time_ms": round(mvn_time_ms, 2)
            },
            "bootstrap": {
                "data": bootstrap_df.to_dict(orient="records"),
                "stats": get_stats(bootstrap_df),
                "generation_time_ms": round(bootstrap_time_ms, 2)
            },
            "rules": {
                "data": rules_df.to_dict(orient="records"),
                "stats": get_stats(rules_df),
                "generation_time_ms": round(rules_time_ms, 2)
            },
            "comparison": {
                "fastest_method": min(
                    [("mvn", mvn_time_ms), ("bootstrap", bootstrap_time_ms), ("rules", rules_time_ms)],
                    key=lambda x: x[1]
                )[0],
                "performance": {
                    "mvn_time_ms": round(mvn_time_ms, 2),
                    "bootstrap_time_ms": round(bootstrap_time_ms, 2),
                    "rules_time_ms": round(rules_time_ms, 2)
                },
                "parameters": {
                    "n_per_arm": n_per_arm,
                    "target_effect": target_effect,
                    "seed": seed
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Method comparison failed: {str(e)}"
        )

@app.get("/data/pilot", response_model=VitalsResponse)
async def get_pilot_data():
    """
    Get real pilot trial data (CDISC SDTM Pilot Study)

    Returns the cleaned and validated pilot data used for training/comparison.
    This is real clinical trial data that has been cleaned and validated.

    Returns:
    - Array of VitalsRecords from the pilot study (945 records)
    - Same schema as generated synthetic data
    - Used by frontend for quality assessment and comparison
    """
    try:
        # Use dynamic path resolution to work in any environment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        pilot_path = os.path.join(project_root, "data/pilot_trial_cleaned.csv")

        # Check if file exists
        if not os.path.exists(pilot_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pilot data file not found at: {pilot_path}"
            )

        # Read and return pilot data
        pilot_df = pd.read_csv(pilot_path)

        return pilot_df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load pilot data: {str(e)}"
        )


@app.get("/data/real-vitals", response_model=VitalsResponse)
async def get_real_vitals_data():
    """
    Get real vitals signs data from clinical trials

    Returns comprehensive vitals data from real clinical trials including:
    - Systolic and Diastolic Blood Pressure
    - Heart Rate
    - Temperature
    - Multiple visits per subject

    Returns:
    - Array of vitals records from real clinical trial data
    - Used by frontend for comparison and quality assessment
    """
    try:
        # Use dynamic path resolution to work in any environment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        vitals_path = os.path.join(project_root, "data/vital_signs.csv")

        # Check if file exists
        if not os.path.exists(vitals_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Real vitals data file not found at: {vitals_path}"
            )

        # Read and return vitals data
        vitals_df = pd.read_csv(vitals_path)

        return vitals_df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load real vitals data: {str(e)}"
        )


@app.get("/data/real-demographics", response_model=VitalsResponse)
async def get_real_demographics_data():
    """
    Get real demographics data from clinical trials

    Returns demographic information from real clinical trials including:
    - Age, Gender, Race, Ethnicity
    - Physical measurements (Height, Weight, BMI)
    - Smoking status and medical history

    Returns:
    - Array of demographic records from real clinical trial data
    - Used by frontend for baseline characteristics and quality assessment
    """
    try:
        # Use dynamic path resolution to work in any environment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        demographics_path = os.path.join(project_root, "data/demographics.csv")

        # Check if file exists
        if not os.path.exists(demographics_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Real demographics data file not found at: {demographics_path}"
            )

        # Read and return demographics data
        demographics_df = pd.read_csv(demographics_path)

        return demographics_df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load real demographics data: {str(e)}"
        )


@app.get("/data/real-ae", response_model=VitalsResponse)
async def get_real_adverse_events_data():
    """
    Get real adverse events (AE) data from clinical trials

    Returns adverse event information from real clinical trials including:
    - AE description and severity
    - Relationship to study drug
    - Onset and resolution dates
    - Serious AE classification

    Returns:
    - Array of adverse event records from real clinical trial data
    - Used by frontend for safety analysis and RBQM
    """
    try:
        # Use dynamic path resolution to work in any environment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        ae_path = os.path.join(project_root, "data/adverse_events.csv")

        # Check if file exists
        if not os.path.exists(ae_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Real adverse events data file not found at: {ae_path}"
            )

        # Read and return adverse events data
        ae_df = pd.read_csv(ae_path)

        return ae_df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load real adverse events data: {str(e)}"
        )


# ============================================================================
# Demographics and Lab Results Generation
# ============================================================================

class GenerateDemographicsRequest(BaseModel):
    n_subjects: int = Field(default=100, ge=1, le=1000, description="Number of subjects")
    seed: int = Field(default=42, description="Random seed for reproducibility")

class GenerateLabsRequest(BaseModel):
    n_subjects: int = Field(default=100, ge=1, le=1000, description="Number of subjects")
    seed: int = Field(default=42, description="Random seed for reproducibility")

@app.post("/generate/demographics")
async def generate_demographics_endpoint(request: GenerateDemographicsRequest):
    """
    Generate synthetic demographics data

    Creates realistic demographic profiles including:
    - Age (18-85, normally distributed around 55)
    - Gender (Male/Female, 50/50 split)
    - Race (White, Black, Asian, Other - US demographics)
    - Ethnicity (Hispanic/Latino, Not Hispanic/Latino)
    - Physical measurements (height, weight, BMI)
    - Smoking status (age-correlated)

    Returns:
        List of demographic records with calculated BMI
    """
    try:
        df = generate_demographics(n_subjects=request.n_subjects, seed=request.seed)

        return {
            "data": df.to_dict(orient="records"),
            "metadata": {
                "records": len(df),
                "subjects": request.n_subjects,
                "method": "statistical",
                "columns": list(df.columns)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demographics generation failed: {str(e)}"
        )

@app.post("/generate/labs")
async def generate_labs_endpoint(request: GenerateLabsRequest):
    """
    Generate synthetic lab results data

    Creates realistic lab results for multiple visits including:
    - Hematology: Hemoglobin, Hematocrit, WBC, Platelets
    - Chemistry: Glucose, Creatinine, BUN, ALT, AST, Bilirubin
    - Lipids: Total Cholesterol, LDL, HDL, Triglycerides

    Each subject has lab results for multiple visits:
    - Screening
    - Week 4
    - Week 12

    Returns:
        List of lab result records with all measurements
    """
    try:
        df = generate_labs(n_subjects=request.n_subjects, seed=request.seed)

        return {
            "data": df.to_dict(orient="records"),
            "metadata": {
                "records": len(df),
                "subjects": request.n_subjects,
                "visits_per_subject": 3,
                "method": "statistical",
                "columns": list(df.columns)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lab results generation failed: {str(e)}"
        )


# ============================================================================
# Scalability Features - AACT-Enhanced Comprehensive Study Generation
# ============================================================================

class ComprehensiveStudyRequest(BaseModel):
    """Request model for comprehensive study generation using AACT data"""
    indication: str = Field(default="hypertension", description="Disease indication (e.g., 'hypertension', 'diabetes', 'cancer')")
    phase: str = Field(default="Phase 3", description="Trial phase (e.g., 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4')")
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Number of subjects per treatment arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg for vitals)")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    method: str = Field(default="mvn", description="Generation method: 'mvn', 'bootstrap', or 'rules'")
    use_duration: bool = Field(default=True, description="Use AACT actual study duration for visit schedules")

class ComprehensiveStudyResponse(BaseModel):
    """Response model for comprehensive study generation"""
    vitals: List[Dict[str, Any]]
    demographics: List[Dict[str, Any]]
    labs: List[Dict[str, Any]]
    adverse_events: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@app.post("/generate/comprehensive-study", response_model=ComprehensiveStudyResponse)
async def generate_comprehensive_study(request: ComprehensiveStudyRequest):
    """
    Generate a complete clinical trial study using AACT real-world data

    This endpoint generates all datasets needed for a complete clinical trial:
    - Vitals signs (using AACT baseline statistics)
    - Demographics (using AACT age/gender distributions)
    - Lab results (using AACT study duration for visits)
    - Adverse events (using AACT indication-specific patterns)

    All datasets are coordinated:
    - Same subject IDs across all domains
    - Same visit schedules
    - Same treatment arm assignments
    - Consistent study parameters from AACT

    **Use Case**: Generate a complete, realistic clinical trial dataset in one API call

    **AACT Enhancement**: Uses real-world statistics from 557K+ trials for maximum realism
    """
    try:
        import time
        start_time = time.time()

        # Step 1: Generate subject IDs and treatment arms (coordination layer)
        n_total = request.n_per_arm * 2
        subject_ids = [f"RA001-{i:03d}" for i in range(1, n_total + 1)]
        treatment_arms = {}
        for i, sid in enumerate(subject_ids):
            treatment_arms[sid] = "Active" if i < request.n_per_arm else "Placebo"

        # Step 2: Generate visit schedule using AACT duration
        from generators import generate_visit_schedule
        if request.use_duration:
            try:
                from aact_utils import get_demographics as aact_get_demographics
                demographics_data = aact_get_demographics(request.indication, request.phase)
                duration_months = int(demographics_data.get('actual_duration', {}).get('median_months', 12))
            except:
                duration_months = 12
            visit_schedule, _ = generate_visit_schedule(duration_months, n_visits=4)
        else:
            visit_schedule = ["Screening", "Day 1", "Week 4", "Week 12"]

        # Step 3: Generate coordinated vitals using selected method
        vitals_start = time.time()
        if request.method == "mvn":
            vitals_df = generate_vitals_mvn_aact(
                indication=request.indication,
                phase=request.phase,
                n_per_arm=request.n_per_arm,
                target_effect=request.target_effect,
                seed=request.seed,
                use_duration=request.use_duration,
                subject_ids=subject_ids,
                visit_schedule=visit_schedule,
                treatment_arms=treatment_arms
            )
        elif request.method == "bootstrap":
            vitals_df = generate_vitals_bootstrap_aact(
                indication=request.indication,
                phase=request.phase,
                n_per_arm=request.n_per_arm,
                target_effect=request.target_effect,
                seed=request.seed,
                use_duration=request.use_duration,
                subject_ids=subject_ids,
                visit_schedule=visit_schedule,
                treatment_arms=treatment_arms
            )
        elif request.method == "rules":
            vitals_df = generate_vitals_rules_aact(
                indication=request.indication,
                phase=request.phase,
                n_per_arm=request.n_per_arm,
                target_effect=request.target_effect,
                seed=request.seed,
                use_duration=request.use_duration,
                subject_ids=subject_ids,
                visit_schedule=visit_schedule,
                treatment_arms=treatment_arms
            )
        else:
            raise ValueError(f"Unknown method: {request.method}")
        vitals_time = time.time() - vitals_start

        # Step 4: Generate coordinated demographics
        demographics_start = time.time()
        demographics_df = generate_demographics_aact(
            indication=request.indication,
            phase=request.phase,
            n_subjects=n_total,
            seed=request.seed + 1,  # Different seed for diversity
            subject_ids=subject_ids,
            treatment_arms=treatment_arms
        )
        demographics_time = time.time() - demographics_start

        # Step 5: Generate coordinated labs
        labs_start = time.time()
        labs_df = generate_labs_aact(
            indication=request.indication,
            phase=request.phase,
            n_subjects=n_total,
            seed=request.seed + 2,
            use_duration=request.use_duration,
            subject_ids=subject_ids,
            visit_schedule=visit_schedule,
            treatment_arms=treatment_arms
        )
        labs_time = time.time() - labs_start

        # Step 6: Generate coordinated adverse events
        ae_start = time.time()
        ae_df = generate_oncology_ae_aact(
            indication=request.indication,
            phase=request.phase,
            n_subjects=n_total,
            seed=request.seed + 3,
            subject_ids=subject_ids,
            visit_schedule=visit_schedule,
            treatment_arms=treatment_arms
        )
        ae_time = time.time() - ae_start

        total_time = time.time() - start_time

        # Return comprehensive study
        return ComprehensiveStudyResponse(
            vitals=vitals_df.to_dict(orient="records"),
            demographics=demographics_df.to_dict(orient="records"),
            labs=labs_df.to_dict(orient="records"),
            adverse_events=ae_df.to_dict(orient="records"),
            metadata={
                "indication": request.indication,
                "phase": request.phase,
                "n_subjects": n_total,
                "n_per_arm": request.n_per_arm,
                "method": request.method,
                "visit_schedule": visit_schedule,
                "total_records": len(vitals_df) + len(demographics_df) + len(labs_df) + len(ae_df),
                "vitals_records": len(vitals_df),
                "demographics_records": len(demographics_df),
                "labs_records": len(labs_df),
                "ae_records": len(ae_df),
                "generation_time_ms": round(total_time * 1000, 2),
                "timing_breakdown": {
                    "vitals_ms": round(vitals_time * 1000, 2),
                    "demographics_ms": round(demographics_time * 1000, 2),
                    "labs_ms": round(labs_time * 1000, 2),
                    "ae_ms": round(ae_time * 1000, 2)
                },
                "aact_enhanced": True,
                "seed": request.seed
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive study generation failed: {str(e)}"
        )


class MultiStudyPortfolioRequest(BaseModel):
    """Request model for multi-study portfolio generation"""
    studies: List[Dict[str, Any]] = Field(
        ...,
        description="List of study configurations, each with: indication, phase, n_per_arm, target_effect"
    )
    seed: int = Field(default=42, description="Base random seed")
    method: str = Field(default="mvn", description="Generation method for all studies")

@app.post("/generate/multi-study-portfolio")
async def generate_multi_study_portfolio(request: MultiStudyPortfolioRequest):
    """
    Generate multiple complete clinical trial studies concurrently

    **Realistic Scalability Scenario**:
    A pharmaceutical company runs multiple trials simultaneously across different indications.
    This endpoint simulates that real-world scenario.

    **Example Use Case**:
    - Portfolio of 10 Phase 3 trials
    - Each with 100 subjects (50 per arm)
    - Different indications (hypertension, diabetes, oncology)
    - All using AACT-enhanced realistic baselines

    **Performance Target**: Generate 10 complete studies in < 5 seconds

    Returns:
    - All studies with coordinated datasets
    - Portfolio-level analytics
    - Generation performance metrics
    """
    try:
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        start_time = time.time()
        results = []

        def generate_single_study(study_config, index):
            """Generate a single study (for parallel execution)"""
            indication = study_config.get("indication", "hypertension")
            phase = study_config.get("phase", "Phase 3")
            n_per_arm = study_config.get("n_per_arm", 50)
            target_effect = study_config.get("target_effect", -5.0)

            # Use different seed for each study
            study_seed = request.seed + (index * 1000)

            # Generate study components directly (sync execution for thread pool)
            import time as time_module
            study_start = time_module.time()

            # Step 1: Generate subject IDs and treatment arms
            n_total = n_per_arm * 2
            subject_ids = [f"STUDY{index+1:03d}-{i:03d}" for i in range(1, n_total + 1)]
            treatment_arms = {}
            for i, sid in enumerate(subject_ids):
                treatment_arms[sid] = "Active" if i < n_per_arm else "Placebo"

            # Step 2: Generate visit schedule
            from generators import generate_visit_schedule
            try:
                from aact_utils import get_demographics as aact_get_demographics
                demographics_data = aact_get_demographics(indication, phase)
                duration_months = int(demographics_data.get('actual_duration', {}).get('median_months', 12))
            except:
                duration_months = 12
            visit_schedule, _ = generate_visit_schedule(duration_months, n_visits=4)

            # Step 3: Generate vitals
            if request.method == "mvn":
                vitals_df = generate_vitals_mvn_aact(
                    indication=indication, phase=phase, n_per_arm=n_per_arm,
                    target_effect=target_effect, seed=study_seed,
                    subject_ids=subject_ids, visit_schedule=visit_schedule,
                    treatment_arms=treatment_arms
                )
            elif request.method == "bootstrap":
                vitals_df = generate_vitals_bootstrap_aact(
                    indication=indication, phase=phase, n_per_arm=n_per_arm,
                    target_effect=target_effect, seed=study_seed,
                    subject_ids=subject_ids, visit_schedule=visit_schedule,
                    treatment_arms=treatment_arms
                )
            else:  # rules
                vitals_df = generate_vitals_rules_aact(
                    indication=indication, phase=phase, n_per_arm=n_per_arm,
                    target_effect=target_effect, seed=study_seed,
                    subject_ids=subject_ids, visit_schedule=visit_schedule,
                    treatment_arms=treatment_arms
                )

            # Step 4: Generate demographics
            demographics_df = generate_demographics_aact(
                indication=indication, phase=phase, n_subjects=n_total,
                seed=study_seed + 1, subject_ids=subject_ids,
                treatment_arms=treatment_arms
            )

            # Step 5: Generate labs
            labs_df = generate_labs_aact(
                indication=indication, phase=phase, n_subjects=n_total,
                seed=study_seed + 2, subject_ids=subject_ids,
                visit_schedule=visit_schedule, treatment_arms=treatment_arms
            )

            # Step 6: Generate AEs
            ae_df = generate_oncology_ae_aact(
                indication=indication, phase=phase, n_subjects=n_total,
                seed=study_seed + 3, subject_ids=subject_ids,
                visit_schedule=visit_schedule, treatment_arms=treatment_arms
            )

            study_time = time_module.time() - study_start

            return {
                "study_id": f"STUDY-{index+1:03d}",
                "study_config": study_config,
                "vitals": vitals_df.to_dict(orient="records"),
                "demographics": demographics_df.to_dict(orient="records"),
                "labs": labs_df.to_dict(orient="records"),
                "adverse_events": ae_df.to_dict(orient="records"),
                "metadata": {
                    "indication": indication,
                    "phase": phase,
                    "n_subjects": n_total,
                    "n_per_arm": n_per_arm,
                    "total_records": len(vitals_df) + len(demographics_df) + len(labs_df) + len(ae_df),
                    "generation_time_ms": round(study_time * 1000, 2)
                }
            }

        # Generate all studies in parallel
        with ThreadPoolExecutor(max_workers=min(len(request.studies), 10)) as executor:
            futures = {
                executor.submit(generate_single_study, study, idx): idx
                for idx, study in enumerate(request.studies)
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other studies
                    results.append({
                        "error": str(e),
                        "study_index": futures[future]
                    })

        total_time = time.time() - start_time

        # Calculate portfolio-level analytics
        total_subjects = sum(r["metadata"]["n_subjects"] for r in results if "metadata" in r)
        total_records = sum(r["metadata"]["total_records"] for r in results if "metadata" in r)

        return {
            "studies": results,
            "portfolio_summary": {
                "total_studies": len(request.studies),
                "successful_studies": len([r for r in results if "metadata" in r]),
                "failed_studies": len([r for r in results if "error" in r]),
                "total_subjects": total_subjects,
                "total_records": total_records,
                "generation_time_ms": round(total_time * 1000, 2),
                "records_per_second": round(total_records / total_time, 2) if total_time > 0 else 0,
                "avg_time_per_study_ms": round((total_time / len(request.studies)) * 1000, 2) if len(request.studies) > 0 else 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-study portfolio generation failed: {str(e)}"
        )


@app.get("/benchmark/performance")
async def benchmark_performance(
    n_per_arm: int = 50,
    methods: str = "mvn,bootstrap,rules",
    indication: str = "hypertension",
    phase: str = "Phase 3"
):
    """
    Benchmark performance of AACT-enhanced generators

    Compares generation speed and quality across different methods:
    - MVN (Multivariate Normal)
    - Bootstrap
    - Rules-based

    **Metrics Tracked**:
    - Generation time (ms)
    - Records per second
    - Memory usage
    - Data quality (basic statistics)

    **Use Case**: Help users choose the best method for their scalability needs
    """
    try:
        import time

        method_list = methods.split(",")
        results = {}

        for method in method_list:
            method = method.strip()

            # Run generation 3 times and take average
            times = []
            for run in range(3):
                start = time.time()

                if method == "mvn":
                    df = generate_vitals_mvn_aact(
                        indication=indication,
                        phase=phase,
                        n_per_arm=n_per_arm,
                        seed=42 + run
                    )
                elif method == "bootstrap":
                    df = generate_vitals_bootstrap_aact(
                        indication=indication,
                        phase=phase,
                        n_per_arm=n_per_arm,
                        seed=42 + run
                    )
                elif method == "rules":
                    df = generate_vitals_rules_aact(
                        indication=indication,
                        phase=phase,
                        n_per_arm=n_per_arm,
                        seed=42 + run
                    )
                else:
                    continue

                elapsed = time.time() - start
                times.append(elapsed)

            # Calculate statistics
            avg_time = sum(times) / len(times)
            records = len(df)

            results[method] = {
                "avg_time_ms": round(avg_time * 1000, 2),
                "min_time_ms": round(min(times) * 1000, 2),
                "max_time_ms": round(max(times) * 1000, 2),
                "records_generated": records,
                "records_per_second": round(records / avg_time, 2),
                "runs": 3
            }

        # Rank by performance
        ranked = sorted(results.items(), key=lambda x: x[1]["avg_time_ms"])

        return {
            "benchmark_results": results,
            "ranking": [{"method": m, "avg_time_ms": r["avg_time_ms"]} for m, r in ranked],
            "fastest_method": ranked[0][0] if ranked else None,
            "parameters": {
                "n_per_arm": n_per_arm,
                "indication": indication,
                "phase": phase
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance benchmark failed: {str(e)}"
        )


@app.post("/stress-test/concurrent")
async def stress_test_concurrent(
    n_concurrent_requests: int = 10,
    n_per_arm: int = 50,
    indication: str = "hypertension",
    phase: str = "Phase 3"
):
    """
    Stress test: Generate multiple studies concurrently

    **Realistic Scalability Test**: Simulate multiple researchers generating data simultaneously

    **Test Scenario**:
    - 10 concurrent generation requests
    - Each generating a complete vitals dataset
    - Measure total time, failures, and throughput

    **Performance Target**:
    - 10 concurrent studies (50 subjects each) in < 3 seconds
    - Zero failures
    - > 1000 records/second aggregate throughput

    **Use Case**: Validate system can handle multiple simultaneous users
    """
    try:
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        start_time = time.time()
        results = []
        errors = []

        def generate_single():
            """Generate a single vitals dataset"""
            try:
                import random
                df = generate_vitals_mvn_aact(
                    indication=indication,
                    phase=phase,
                    n_per_arm=n_per_arm,
                    seed=random.randint(1, 10000)
                )
                return {
                    "success": True,
                    "records": len(df)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=n_concurrent_requests) as executor:
            futures = [executor.submit(generate_single) for _ in range(n_concurrent_requests)]

            for future in as_completed(futures):
                result = future.result()
                if result["success"]:
                    results.append(result)
                else:
                    errors.append(result)

        total_time = time.time() - start_time
        total_records = sum(r["records"] for r in results)

        return {
            "stress_test_results": {
                "total_requests": n_concurrent_requests,
                "successful_requests": len(results),
                "failed_requests": len(errors),
                "success_rate": round(len(results) / n_concurrent_requests * 100, 2),
                "total_time_seconds": round(total_time, 2),
                "total_records_generated": total_records,
                "aggregate_throughput_records_per_second": round(total_records / total_time, 2) if total_time > 0 else 0,
                "avg_time_per_request_ms": round((total_time / n_concurrent_requests) * 1000, 2),
                "errors": errors if errors else None
            },
            "pass_criteria": {
                "target_time_seconds": 3,
                "target_throughput": 1000,
                "achieved_time": round(total_time, 2),
                "achieved_throughput": round(total_records / total_time, 2) if total_time > 0 else 0,
                "passed": (total_time < 3 and (total_records / total_time) > 1000 and len(errors) == 0) if total_time > 0 else False
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stress test failed: {str(e)}"
        )


@app.get("/analytics/portfolio")
async def portfolio_analytics():
    """
    Portfolio-level analytics across all generated studies

    **Use Case**: Executive dashboard showing organization-wide trial generation activity

    Returns:
    - Total studies generated
    - Total subjects across portfolio
    - Breakdown by indication
    - Breakdown by phase
    - Quality metrics summary
    - Resource utilization

    **Note**: This endpoint reads from database/cache to show historical data
    """
    try:
        # This would query database in production
        # For now, return mock portfolio data
        return {
            "portfolio_summary": {
                "total_studies": 127,
                "total_subjects": 12750,
                "total_records": 51000,
                "studies_by_indication": {
                    "hypertension": 45,
                    "diabetes": 32,
                    "oncology": 28,
                    "cardiovascular": 22
                },
                "studies_by_phase": {
                    "Phase 1": 15,
                    "Phase 2": 38,
                    "Phase 3": 62,
                    "Phase 4": 12
                },
                "average_subjects_per_study": 100.4,
                "average_generation_time_ms": 287.5,
                "total_generation_time_hours": 10.1
            },
            "quality_metrics": {
                "average_quality_score": 0.89,
                "studies_meeting_quality_threshold": 121,
                "quality_threshold": 0.85
            },
            "resource_utilization": {
                "cache_hit_rate": 0.94,
                "aact_lookup_rate": 0.98,
                "fallback_rate": 0.02
            },
            "note": "This is mock data. In production, this would query the database for real portfolio statistics."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio analytics failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
