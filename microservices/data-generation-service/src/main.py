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
import sentry_sdk

from generators import (
    generate_vitals_rules,
    generate_vitals_mvn,
    generate_vitals_llm_with_repair,
    generate_oncology_ae,
    generate_vitals_bootstrap
)
from db_utils import db, cache, startup_db, shutdown_db

# ==================== Sentry Initialization ====================

sentry_sdk.init(
    dsn="https://ad29eaef4a806c3f27f5f2181373aa36@o4510369986904064.ingest.us.sentry.io/4510369988018176",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    send_default_pii=True,
    enable_logs=True,
    environment=os.getenv("ENVIRONMENT", "development"),
)

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
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
if "*" in ALLOWED_ORIGINS and os.getenv("ENVIRONMENT") == "production":
    import warnings
    warnings.warn("CORS wildcard enabled in production - security risk!", UserWarning)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
        "version": "2.0.0",
        "methods": [
            "Rules-based generation",
            "MVN (Multivariate Normal) generation",
            "LLM-based generation with auto-repair",
            "Bootstrap sampling (NEW!) - fast augmentation from pilot data",
            "Oncology AE generation"
        ],
        "endpoints": {
            "health": "/health",
            "rules": "/generate/rules",
            "mvn": "/generate/mvn",
            "llm": "/generate/llm",
            "bootstrap": "/generate/bootstrap",
            "ae": "/generate/ae",
            "compare": "/compare",
            "pilot_data": "/data/pilot",
            "docs": "/docs"
        }
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


# ==================== Sentry Debug Endpoint ====================

@app.get("/sentry-debug")
async def trigger_error():
    """Trigger a test error to verify Sentry integration"""
    division_by_zero = 1 / 0
    return {"message": "This should never be reached"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
