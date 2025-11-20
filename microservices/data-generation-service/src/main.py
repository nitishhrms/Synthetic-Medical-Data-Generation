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
    # AACT v4.0 enhanced generators
    generate_vitals_mvn_aact,
    generate_vitals_bootstrap_aact,
    generate_vitals_rules_aact,
    generate_demographics_aact,
    generate_vitals_bayesian_aact,
    generate_vitals_mice_aact,
    generate_labs_aact,
    generate_oncology_ae_aact,
    generate_visit_schedule
)
from realistic_trial import RealisticTrialGenerator
from db_utils import db, cache, startup_db, shutdown_db

# Daft imports for million-scale generation
try:
    from daft_generators import DaftDataGenerator, generate_vitals_million_scale
    DAFT_AVAILABLE = True
except ImportError:
    DAFT_AVAILABLE = False
    import warnings
    warnings.warn("Daft not available. Million-scale generation disabled. Install: pip install getdaft==0.3.0")

# Bayesian Network generator imports
try:
    from bayesian_generator import generate_vitals_bayesian
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    import warnings
    warnings.warn("Bayesian generator not available. Install: pip install pgmpy")

# MICE (Multiple Imputation) generator imports
try:
    from mice_generator import generate_vitals_mice
    MICE_AVAILABLE = True
except ImportError:
    MICE_AVAILABLE = False
    import warnings
    warnings.warn("MICE generator not available. Install: pip install scikit-learn")

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

class GenerateBayesianRequest(BaseModel):
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Number of subjects per arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg)")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    learn_structure: bool = Field(default=False, description="Learn Bayesian network structure from data (vs expert-defined)")

class GenerateMICERequest(BaseModel):
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Number of subjects per arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg)")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    missing_rate: float = Field(default=0.10, ge=0.0, le=0.5, description="Fraction of values to make missing (0.10 = 10%)")
    estimator: str = Field(default="bayesian_ridge", description="Imputation estimator: 'bayesian_ridge' or 'random_forest'")
    n_imputations: int = Field(default=1, ge=1, le=10, description="Number of imputations (1 for single, 5-10 for multiple)")

class GenerateDiffusionRequest(BaseModel):
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Number of subjects per arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg)")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    n_steps: int = Field(default=10, ge=1, le=100, description="Number of diffusion steps")

# ======================== AACT v4.0 Enhanced Request Models ========================
class GenerateAACTRequest(BaseModel):
    """Base request model for AACT-enhanced generators"""
    indication: str = Field(default="hypertension", description="Disease indication (e.g., 'hypertension', 'diabetes', 'cancer')")
    phase: str = Field(default="Phase 3", description="Trial phase (e.g., 'Phase 3')")
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Number of subjects per arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg)")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    use_duration: bool = Field(default=True, description="Use AACT actual duration for visit scheduling")

class GenerateMVNAACTRequest(GenerateAACTRequest):
    """Request model for MVN with AACT real-world data"""
    pass

class GenerateBootstrapAACTRequest(GenerateAACTRequest):
    """Request model for Bootstrap with AACT real-world data"""
    jitter_frac: float = Field(default=0.05, ge=0, le=0.5, description="Fraction of std for numeric noise")

class GenerateRulesAACTRequest(GenerateAACTRequest):
    """Request model for Rules with AACT real-world data"""
    pass

class GenerateDemographicsAACTRequest(BaseModel):
    """Request model for Demographics with AACT real-world distributions"""
    indication: str = Field(default="hypertension", description="Disease indication")
    phase: str = Field(default="Phase 3", description="Trial phase")
    n_subjects: int = Field(default=100, ge=1, le=1000, description="Number of subjects")
    seed: int = Field(default=42, description="Random seed")

class GenerateBayesianAACTRequest(GenerateAACTRequest):
    """Request model for Bayesian Network with AACT real-world data"""
    learn_structure: bool = Field(default=False, description="Learn Bayesian network structure from data")
    real_data_path: Optional[str] = Field(default=None, description="Path to real data for network training")

class GenerateMICEAACTRequest(GenerateAACTRequest):
    """Request model for MICE with AACT real-world data"""
    missing_rate: float = Field(default=0.10, ge=0.0, le=0.5, description="Fraction of values to make missing")
    estimator: str = Field(default="bayesian_ridge", description="Imputation estimator: 'bayesian_ridge' or 'random_forest'")
    real_data_path: Optional[str] = Field(default=None, description="Path to real data for MICE training")

class GenerateLabsAACTRequest(BaseModel):
    """Request model for Labs with AACT real-world data"""
    indication: str = Field(default="hypertension", description="Disease indication")
    phase: str = Field(default="Phase 3", description="Trial phase")
    n_subjects: int = Field(default=100, ge=1, le=1000, description="Number of subjects")
    seed: int = Field(default=42, description="Random seed")
    use_duration: bool = Field(default=True, description="Use AACT actual duration for visit scheduling")

class GenerateAEAACTRequest(BaseModel):
    """Request model for Adverse Events with AACT real-world data"""
    indication: str = Field(default="cancer", description="Disease indication")
    phase: str = Field(default="Phase 2", description="Trial phase")
    n_subjects: int = Field(default=30, ge=10, le=100, description="Number of subjects")
    seed: int = Field(default=7, description="Random seed")

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
            "Bayesian Network (NEW!) - probabilistic graphical models",
            "MICE (NEW!) - Multiple Imputation by Chained Equations",
            "Oncology AE generation",
            "Demographics generation",
            "Lab results generation"
        ],
        "endpoints": {
            "health": "/health",
            "rules": "/generate/rules",
            "mvn": "/generate/mvn",
            "llm": "/generate/llm",
            "bootstrap": "/generate/bootstrap",
            "realistic_trial": "/generate/realistic-trial (NEW!)",
            "ae": "/generate/ae",
            "demographics": "/generate/demographics",
            "labs": "/generate/labs",
            "compare": "/compare",
            "pilot_data": "/data/pilot",
            "docs": "/docs"
        },
        "features": {
            "bayesian_available": BAYESIAN_AVAILABLE,
            "mice_available": MICE_AVAILABLE
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

# ======================== AACT v4.0 Enhanced Endpoints ========================

@app.post("/generate/mvn-aact", response_model=VitalsResponse)
async def generate_mvn_aact_based(request: GenerateMVNAACTRequest):
    """
    Generate synthetic vitals using MVN with AACT real-world data (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics from 557K+ Trials:**
    - ✅ Real baseline vitals by indication/phase (SBP, DBP, HR, Temperature)
    - ✅ Real study duration for realistic visit schedules
    - ✅ Maintains all MVN quality (covariance structure)
    - ✅ Graceful fallback to defaults if AACT unavailable

    **What's Different from Standard MVN:**
    - Uses real mean/std from AACT instead of hardcoded values
    - Adapts visit schedule to actual trial duration (e.g., 17 months for Hypertension Phase 3)
    - Generates data matching real clinical trial patterns

    **Example:**
    For Hypertension Phase 3:
    - Baseline SBP: 140.2 mmHg (from 1,025 real trials)
    - Study duration: 17 months (median from AACT)
    - Visits: Screening, Day 1, Month 6, Month 17

    **Parameters:**
    - indication: Disease (e.g., 'hypertension', 'diabetes', 'cancer')
    - phase: Trial phase (e.g., 'Phase 3')
    - n_per_arm: Subjects per arm (default: 50)
    - target_effect: Target SBP reduction (default: -5.0 mmHg)
    - use_duration: Use real study duration (default: True)
    - seed: Random seed (default: 42)
    """
    try:
        df = generate_vitals_mvn_aact(
            indication=request.indication,
            phase=request.phase,
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            seed=request.seed,
            use_duration=request.use_duration
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT MVN generation failed: {str(e)}"
        )

@app.post("/generate/bootstrap-aact", response_model=VitalsResponse)
async def generate_bootstrap_aact_based(request: GenerateBootstrapAACTRequest):
    """
    Generate synthetic vitals using Bootstrap with AACT real-world data (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics:**
    - ✅ Enriches pilot data with AACT patterns
    - ✅ Real study duration for visit scheduling
    - ✅ Maintains all Bootstrap quality (resampling preserves correlations)

    **Best for:**
    - Expanding existing datasets with real-world context
    - When you need both pilot data characteristics AND industry benchmarks

    **Parameters:**
    - indication: Disease indication
    - phase: Trial phase
    - n_per_arm: Subjects per arm (default: 50)
    - target_effect: Target SBP reduction (default: -5.0 mmHg)
    - jitter_frac: Noise level (default: 0.05)
    - use_duration: Use real study duration (default: True)
    - seed: Random seed (default: 42)
    """
    try:
        df = generate_vitals_bootstrap_aact(
            indication=request.indication,
            phase=request.phase,
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            jitter_frac=request.jitter_frac,
            seed=request.seed,
            use_duration=request.use_duration
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT Bootstrap generation failed: {str(e)}"
        )

@app.post("/generate/rules-aact", response_model=VitalsResponse)
async def generate_rules_aact_based(request: GenerateRulesAACTRequest):
    """
    Generate synthetic vitals using Rules with AACT real-world data (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics:**
    - ✅ Real baseline vitals replace hardcoded values
    - ✅ Real study duration for visit scheduling
    - ✅ Maintains deterministic rules-based approach

    **Example:**
    For Diabetes Phase 3:
    - Baseline SBP: 145.1 mmHg (from AACT, not hardcoded 130)
    - Study duration: 19 months (from AACT, not hardcoded 12)
    - Visits adapt to real trial timelines

    **Parameters:**
    - indication: Disease indication
    - phase: Trial phase
    - n_per_arm: Subjects per arm (default: 50)
    - target_effect: Target SBP reduction (default: -5.0 mmHg)
    - use_duration: Use real study duration (default: True)
    - seed: Random seed (default: 42)
    """
    try:
        df = generate_vitals_rules_aact(
            indication=request.indication,
            phase=request.phase,
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            seed=request.seed,
            use_duration=request.use_duration
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT Rules generation failed: {str(e)}"
        )

@app.post("/generate/demographics-aact", response_model=List[Dict[str, Any]])
async def generate_demographics_aact_based(request: GenerateDemographicsAACTRequest):
    """
    Generate demographics using AACT real-world distributions (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics:**
    - ✅ Real age distributions (median, mean from 557K+ trials)
    - ✅ Real gender ratios by indication/phase
    - ✅ Real race distributions from baseline characteristics
    - ✅ Falls back to defaults if AACT unavailable

    **What's Different from Standard Demographics:**
    - Age distribution matches real trials (e.g., Hypertension median: 58 years)
    - Gender ratio matches real enrollment (e.g., Cancer: 47% female)
    - Race distribution from actual baseline counts

    **Example Output:**
    For Hypertension Phase 3 (100 subjects):
    - Age: Median 58 years (from 1,025 trials)
    - Gender: 52% Male, 48% Female (real ratio)
    - Race: Matches real baseline distributions

    **Parameters:**
    - indication: Disease indication (default: 'hypertension')
    - phase: Trial phase (default: 'Phase 3')
    - n_subjects: Number of subjects (default: 100)
    - seed: Random seed (default: 42)
    """
    try:
        df = generate_demographics_aact(
            indication=request.indication,
            phase=request.phase,
            n_subjects=request.n_subjects,
            seed=request.seed
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT Demographics generation failed: {str(e)}"
        )

@app.post("/generate/labs-aact", response_model=List[Dict[str, Any]])
async def generate_labs_aact_based(request: GenerateLabsAACTRequest):
    """
    Generate lab results with AACT real-world data (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics from 557K+ Trials:**
    - ✅ Real study duration for realistic visit schedules
    - ✅ Indication-specific lab abnormalities
    - ✅ Dynamic visit names based on AACT duration
    - ✅ Falls back to defaults if AACT unavailable

    **What's Different from Standard Labs:**
    - Visit schedule adapts to actual study duration (e.g., diabetes Phase 3: 18 months)
    - Lab values adjusted for indication (e.g., higher glucose for diabetes)
    - Realistic visit timing based on real-world trials

    **Lab Panels Included:**
    - Hematology: Hemoglobin, Hematocrit, WBC, Platelets
    - Chemistry: Glucose, Creatinine, BUN, ALT, AST, Bilirubin
    - Lipids: Total Cholesterol, LDL, HDL, Triglycerides

    **Example Output:**
    For Diabetes Phase 3 (100 subjects):
    - 300 lab records (3 visits per subject)
    - Higher baseline glucose (~140 vs ~90 for other indications)
    - Visit schedule: Screening, Month 6, Month 18

    **Parameters:**
    - indication: Disease indication (default: 'hypertension')
    - phase: Trial phase (default: 'Phase 3')
    - n_subjects: Number of subjects (default: 100)
    - seed: Random seed (default: 42)
    - use_duration: Use AACT actual duration (default: True)
    """
    try:
        df = generate_labs_aact(
            indication=request.indication,
            phase=request.phase,
            n_subjects=request.n_subjects,
            seed=request.seed,
            use_duration=request.use_duration
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT Labs generation failed: {str(e)}"
        )


@app.post("/generate/ae-aact", response_model=AEResponse)
async def generate_ae_aact_based(request: GenerateAEAACTRequest):
    """
    Generate adverse events with AACT real-world data (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics from 557K+ Trials:**
    - ✅ Indication-specific AE terms (cancer, hypertension, diabetes)
    - ✅ Phase-specific severity distributions
    - ✅ Real-world AE rates and patterns
    - ✅ Falls back to defaults if AACT unavailable

    **What's Different from Standard AE:**
    - AE terms match indication (e.g., "Hypoglycemia" for diabetes)
    - Severity rates match phase (Phase 1/2: 30% serious, Phase 3/4: 15% serious)
    - Realistic AE frequencies based on real trials

    **Indication-Specific AE Terms:**
    - **Cancer**: Neutropenia, Anemia, Myelosuppression, Peripheral neuropathy
    - **Hypertension**: Dizziness, Headache, Hypotension, Peripheral edema
    - **Diabetes**: Hypoglycemia, Weight gain, Nausea, Diarrhea

    **Example Output:**
    For Cancer Phase 2 (30 subjects):
    - ~21 AE records (~70% of subjects have at least one AE)
    - Higher serious AE rate (30% for early phase)
    - Cancer-specific terms (Myelosuppression, Neutropenia)

    **Parameters:**
    - indication: Disease indication (default: 'cancer')
    - phase: Trial phase (default: 'Phase 2')
    - n_subjects: Number of subjects (default: 30)
    - seed: Random seed (default: 7)
    """
    try:
        df = generate_oncology_ae_aact(
            indication=request.indication,
            phase=request.phase,
            n_subjects=request.n_subjects,
            seed=request.seed
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT AE generation failed: {str(e)}"
        )


@app.post("/generate/bayesian-aact", response_model=VitalsResponse)
async def generate_bayesian_aact_based(request: GenerateBayesianAACTRequest):
    """
    Generate synthetic vitals using Bayesian Network with AACT real-world data (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics from 557K+ Trials:**
    - ✅ Real baseline vitals by indication/phase
    - ✅ Real study duration for realistic visit schedules
    - ✅ Sophisticated dependency modeling (Bayesian networks)
    - ✅ Captures non-linear relationships between variables
    - ✅ Interpretable structure (DAG shows causal relationships)

    **What's Different from Standard Bayesian:**
    - Visit names adapt to actual study duration (e.g., hypertension Phase 3: 17 months)
    - Baseline vitals match real-world distributions
    - Combines Bayesian network sophistication with AACT realism

    **Method:**
    1. Learn or use expert-defined Bayesian network structure
    2. Fit conditional probability distributions (CPDs) from real data
    3. Sample from the network using forward sampling
    4. Apply AACT-informed visit scheduling

    **Use Cases:**
    - When variable relationships are known (e.g., clinical pathways)
    - For explainable AI (DAG shows causal structure)
    - When you need to preserve complex dependencies with real-world parameters

    **Parameters:**
    - indication: Disease indication (default: 'hypertension')
    - phase: Trial phase (default: 'Phase 3')
    - n_per_arm: Subjects per arm (default: 50)
    - target_effect: Target SBP reduction (default: -5.0 mmHg)
    - use_duration: Use AACT actual duration (default: True)
    - seed: Random seed (default: 42)
    """
    if not BAYESIAN_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Bayesian generator not available. Install pgmpy: pip install pgmpy"
        )

    try:
        df = generate_vitals_bayesian_aact(
            indication=request.indication,
            phase=request.phase,
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            seed=request.seed,
            use_duration=request.use_duration,
            real_data_path=request.real_data_path
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT Bayesian generation failed: {str(e)}"
        )


@app.post("/generate/mice-aact", response_model=VitalsResponse)
async def generate_mice_aact_based(request: GenerateMICEAACTRequest):
    """
    Generate synthetic vitals using MICE with AACT real-world data (v4.0) ⭐ NEW!

    **Enhanced with AACT Statistics from 557K+ Trials:**
    - ✅ Real baseline vitals by indication/phase
    - ✅ Real study duration for realistic visit schedules
    - ✅ Sophisticated missing data handling (MICE)
    - ✅ Realistic missing data patterns
    - ✅ Multiple imputation for uncertainty quantification

    **What's Different from Standard MICE:**
    - Visit names adapt to actual study duration (e.g., cancer Phase 2: 8 months)
    - Baseline vitals match real-world distributions
    - Combines MICE sophistication with AACT realism

    **Method:**
    1. Create template dataset with structure
    2. Introduce realistic missing data pattern (MAR - Missing At Random)
    3. Use iterative imputation to fill missing values
    4. Apply AACT-informed visit scheduling
    5. Optionally create multiple imputations for uncertainty

    **Use Cases:**
    - Simulating trials with dropout/missing data
    - Testing missing data handling algorithms
    - Creating diverse synthetic datasets with controlled missingness
    - Demonstrating MICE methodology with real-world parameters

    **Parameters:**
    - indication: Disease indication (default: 'hypertension')
    - phase: Trial phase (default: 'Phase 3')
    - n_per_arm: Subjects per arm (default: 50)
    - target_effect: Target SBP reduction (default: -5.0 mmHg)
    - use_duration: Use AACT actual duration (default: True)
    - missing_rate: Fraction of missing values (default: 0.10 = 10%)
    - estimator: 'bayesian_ridge' (fast) or 'random_forest' (slower, non-linear)
    - seed: Random seed (default: 42)
    """
    if not MICE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="MICE generator not available. Install sklearn: pip install scikit-learn"
        )

    try:
        df = generate_vitals_mice_aact(
            indication=request.indication,
            phase=request.phase,
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            seed=request.seed,
            use_duration=request.use_duration,
            missing_rate=request.missing_rate,
            estimator=request.estimator,
            real_data_path=request.real_data_path
        )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AACT MICE generation failed: {str(e)}"
        )


@app.post("/generate/diffusion", response_model=VitalsResponse)
async def generate_diffusion_based(request: GenerateDiffusionRequest):
    """
    Generate synthetic vitals data using Diffusion-style iterative refinement

    **Method:** Lightweight diffusion-inspired generation with statistical methods

    **Best for:**
    - High-quality synthetic data generation
    - Capturing complex data distributions
    - Realistic correlation preservation
    - Advanced statistical modeling

    **Advantages:**
    - 🎯 State-of-the-art generative modeling approach
    - 🔬 Learns complex patterns from real data
    - 📊 Preserves statistical properties and correlations
    - 🔧 Iterative refinement for better quality
    - ⚡ Fast inference (no deep learning frameworks needed)
    - 💰 No API costs
    - ✅ Enforces clinical constraints

    **How it works:**
    1. Learns statistical distribution from pilot data
    2. Samples from multivariate normal with learned correlations
    3. Applies iterative refinement steps (diffusion-inspired)
    4. Each step moves data towards conditional distributions
    5. Gradually reduces noise while maintaining correlations
    6. Enforces physiological constraints at each step
    7. Applies target treatment effect for Active arm

    **Parameters:**
    - n_per_arm: Subjects per arm (default: 50)
    - target_effect: Target SystolicBP reduction at Week 12 (default: -5.0 mmHg)
    - n_steps: Number of refinement iterations (default: 50, range: 10-200)
    - seed: Random seed for reproducibility (default: 42)

    **Quality:**
    - High fidelity to original data distribution
    - Excellent correlation preservation
    - Smooth, realistic value distributions
    - Better than simple bootstrap for diverse datasets
    """
    try:
        # Path to pilot data (fixed path in container)
        import os
        # Try multiple possible paths
        possible_paths = [
            "/app/data/pilot_trial_cleaned.csv",
            "../../data/pilot_trial_cleaned.csv",
            "/home/user/Synthetic-Medical-Data-Generation/data/pilot_trial_cleaned.csv",
            os.path.join(os.path.dirname(__file__), "../../data/pilot_trial_cleaned.csv")
        ]

        data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_path = path
                break

        if data_path is None:
            raise FileNotFoundError("Pilot data file not found. Please ensure pilot_trial_cleaned.csv exists.")

        # Generate synthetic data
        df = generate_with_simple_diffusion(
            data_path=data_path,
            n_per_arm=request.n_per_arm,
            n_steps=request.n_steps,
            target_effect=request.target_effect,
            seed=request.seed
        )

        # Return just the data array for compatibility with EDC validation service
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diffusion generation failed: {str(e)}"
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
        # Use Path for robust path resolution (works in both local and Docker)
        from pathlib import Path
        # In Docker: /app/src/main.py -> parents[1] = /app
        # Locally: .../microservices/data-generation-service/src/main.py -> parents[3] = project root
        current_file = Path(__file__).resolve()
        if str(current_file).startswith("/app/"):
            # Running in Docker
            base_path = current_file.parents[1]  # /app
        else:
            # Running locally
            base_path = current_file.parents[3]  # project root
        pilot_path = base_path / "data" / "pilot_trial_cleaned.csv"
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
        # Use Path for robust path resolution (works in both local and Docker)
        from pathlib import Path
        # In Docker: /app/src/main.py -> parents[1] = /app
        # Locally: .../microservices/data-generation-service/src/main.py -> parents[3] = project root
        current_file = Path(__file__).resolve()
        if str(current_file).startswith("/app/"):
            # Running in Docker
            base_path = current_file.parents[1]  # /app
        else:
            # Running locally
            base_path = current_file.parents[3]  # project root
        pilot_path = base_path / "data" / "pilot_trial_cleaned.csv"

        # Check if file exists
        if not pilot_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"UPDATED_CODE: Pilot data file not found at: {pilot_path}. Expected at: {base_path}/data/pilot_trial_cleaned.csv"
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

@app.get("/data/real-vitals")
async def get_real_vital_signs():
    """
    Get full CDISC SDTM Vital Signs dataset

    Returns 29,644 vital signs records from the CDISC Pilot Study.
    Full SDTM VS domain with multiple measurements per visit.
    """
    try:
        from pathlib import Path
        current_file = Path(__file__).resolve()
        base_path = current_file.parents[1] if str(current_file).startswith("/app/") else current_file.parents[3]
        vitals_path = base_path / "data" / "vital_signs.csv"

        if not vitals_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {vitals_path}")

        df = pd.read_csv(vitals_path)
        return df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vital signs: {str(e)}")

@app.get("/data/real-demographics")
async def get_real_demographics():
    """
    Get full CDISC SDTM Demographics dataset

    Returns 307 subject demographics from the CDISC Pilot Study.
    """
    try:
        from pathlib import Path
        current_file = Path(__file__).resolve()
        base_path = current_file.parents[1] if str(current_file).startswith("/app/") else current_file.parents[3]
        demo_path = base_path / "data" / "demographics.csv"

        if not demo_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {demo_path}")

        df = pd.read_csv(demo_path)
        return df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demographics: {str(e)}")

@app.get("/data/real-ae")
async def get_real_adverse_events():
    """
    Get full CDISC SDTM Adverse Events dataset

    Returns 1,192 adverse events from the CDISC Pilot Study.
    """
    try:
        from pathlib import Path
        current_file = Path(__file__).resolve()
        base_path = current_file.parents[1] if str(current_file).startswith("/app/") else current_file.parents[3]
        ae_path = base_path / "data" / "adverse_events.csv"

        if not ae_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {ae_path}")

        df = pd.read_csv(ae_path)
        return df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load adverse events: {str(e)}")


# ============================================================================
# Advanced Generation Methods - Bayesian Network & MICE
# ============================================================================

@app.post("/generate/bayesian", response_model=VitalsResponse)
async def generate_bayesian_network(request: GenerateBayesianRequest):
    """
    Generate synthetic vitals data using Bayesian Network approach

    **Key Advantages**:
    - Captures complex conditional dependencies between variables
    - Preserves non-linear relationships (e.g., TreatmentArm → SBP)
    - Interpretable structure (DAG shows causal relationships)
    - Handles mixed continuous/categorical data

    **Method**:
    1. Learn or use expert-defined Bayesian network structure
    2. Fit conditional probability distributions (CPDs) from real data
    3. Sample from the network using forward sampling

    **Use Cases**:
    - When variable relationships are known (e.g., clinical pathways)
    - For explainable AI (DAG shows causal structure)
    - When you need to preserve complex dependencies
    """
    if not BAYESIAN_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Bayesian generator not available. Install pgmpy: pip install pgmpy"
        )

    try:
        df = generate_vitals_bayesian(
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            seed=request.seed
        )

        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bayesian generation failed: {str(e)}"
        )


@app.post("/generate/mice", response_model=VitalsResponse)
async def generate_mice_imputation(request: GenerateMICERequest):
    """
    Generate synthetic vitals data using MICE (Multiple Imputation by Chained Equations)

    **Key Advantages**:
    - Naturally handles missing data (realistic for clinical trials)
    - Preserves uncertainty through multiple imputations
    - Flexible - works with various base estimators
    - Good for small-medium datasets

    **Method**:
    1. Create template dataset with structure
    2. Introduce realistic missing data pattern (MAR - Missing At Random)
    3. Use iterative imputation to fill missing values
    4. Optionally create multiple imputations for uncertainty quantification

    **Use Cases**:
    - Simulating trials with dropout/missing data
    - Testing missing data handling algorithms
    - Creating diverse synthetic datasets with controlled missingness
    - Demonstrating MICE methodology

    **Parameters**:
    - `missing_rate`: 0.10 means 10% of values will be missing and imputed
    - `estimator`: 'bayesian_ridge' (fast, linear) or 'random_forest' (slower, non-linear)
    - `n_imputations`: 1 for single imputation, 5-10 for multiple imputations with pooling
    """
    if not MICE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="MICE generator not available. Install sklearn: pip install scikit-learn"
        )

    try:
        if request.n_imputations == 1:
            # Single imputation
            df = generate_vitals_mice(
                n_per_arm=request.n_per_arm,
                target_effect=request.target_effect,
                seed=request.seed,
                missing_rate=request.missing_rate,
                estimator=request.estimator
            )

            return df.to_dict(orient="records")
        else:
            # Multiple imputations - return first one for now
            # TODO: In future, could return all imputations or pooled results
            df = generate_vitals_mice(
                n_per_arm=request.n_per_arm,
                target_effect=request.target_effect,
                seed=request.seed,
                missing_rate=request.missing_rate,
                estimator=request.estimator
            )

            return df.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MICE generation failed: {str(e)}"
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

class ComprehensiveStudyRequest(BaseModel):
    """Request model for comprehensive study data generation with AACT enhancements"""
    n_per_arm: int = Field(default=50, ge=10, le=200, description="Number of subjects per treatment arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect for vitals (mmHg)")
    method: str = Field(default="mvn", description="Generation method: 'mvn', 'rules', or 'bootstrap'")
    indication: str = Field(default="hypertension", description="Disease indication for AACT-enhanced generation")
    phase: str = Field(default="Phase 3", description="Trial phase for AACT-enhanced generation")
    include_vitals: bool = Field(default=True, description="Generate vitals data")
    include_demographics: bool = Field(default=True, description="Generate demographics data")
    include_ae: bool = Field(default=True, description="Generate adverse events data")
    include_labs: bool = Field(default=True, description="Generate lab results data")
    use_aact: bool = Field(default=True, description="Use AACT-enhanced generators (recommended)")
    seed: int = Field(default=42, description="Random seed for reproducibility")

class ComprehensiveStudyResponse(BaseModel):
    """Response model for comprehensive study data"""
    vitals: Optional[List[Dict[str, Any]]] = Field(None, description="Vitals data")
    demographics: Optional[List[Dict[str, Any]]] = Field(None, description="Demographics data")
    adverse_events: Optional[List[Dict[str, Any]]] = Field(None, description="Adverse events data")
    labs: Optional[List[Dict[str, Any]]] = Field(None, description="Lab results data")
    metadata: Dict[str, Any] = Field(..., description="Generation metadata and summary")

class RealisticTrialRequest(BaseModel):
    """Request model for realistic trial generation with imperfections"""
    n_per_arm: int = Field(default=50, ge=10, le=200, description="Number of subjects per treatment arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect (mmHg)")
    indication: Optional[str] = Field(default=None, description="Disease indication (e.g., 'hypertension') - enables AACT-informed defaults")
    phase: Optional[str] = Field(default=None, description="Trial phase (e.g., 'Phase 3') - enables AACT-informed defaults")
    n_sites: Optional[int] = Field(default=None, ge=1, le=30, description="Number of study sites (auto from AACT if None)")
    site_heterogeneity: float = Field(default=0.3, ge=0.0, le=1.0, description="Site heterogeneity (0=uniform, 1=very skewed)")
    missing_data_rate: Optional[float] = Field(default=None, ge=0.0, le=0.3, description="Missing data rate (auto from AACT if None)")
    dropout_rate: Optional[float] = Field(default=None, ge=0.0, le=0.5, description="Subject dropout rate (auto from AACT if None)")
    protocol_deviation_rate: float = Field(default=0.05, ge=0.0, le=0.3, description="Protocol deviation rate (0-0.3)")
    enrollment_pattern: str = Field(default="exponential", description="Enrollment pattern: 'linear', 'exponential', 'seasonal'")
    enrollment_duration_months: Optional[int] = Field(default=None, ge=1, le=36, description="Enrollment duration in months (auto from AACT if None)")
    seed: int = Field(default=42, description="Random seed for reproducibility")

class RealisticTrialResponse(BaseModel):
    """Response model for realistic trial data"""
    vitals: List[Dict[str, Any]] = Field(..., description="Vitals data with realistic patterns")
    adverse_events: List[Dict[str, Any]] = Field(..., description="Adverse events correlated with vitals")
    protocol_deviations: List[Dict[str, Any]] = Field(..., description="Protocol deviations and compliance issues")
    metadata: Dict[str, Any] = Field(..., description="Generation metadata including realism scores")

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

@app.post("/generate/realistic-trial", response_model=RealisticTrialResponse)
async def generate_realistic_trial(request: RealisticTrialRequest):
    """
    Generate a REALISTIC clinical trial with imperfections and patterns found in real studies

    **NEW in v2.0** - This is a game-changer for trial simulation!

    **What Makes This Different:**
    Unlike other methods that generate "perfect" synthetic data, this creates trials with
    realistic imperfections, heterogeneity, and patterns observed in real clinical studies:

    **Realistic Features:**
    - 📅 **Variable Enrollment**: Exponential/seasonal patterns instead of instant enrollment
    - 🏥 **Site Heterogeneity**: Uneven site distribution (some sites enroll 2x others)
    - 📊 **Site Effects**: Each site has slightly different baselines and response rates
    - 🚪 **Dropout**: Subjects drop out over time (configurable rate)
    - ❌ **Missing Data**: MAR (Missing At Random) patterns - more common at later visits
    - ⚠️ **Protocol Deviations**: Visit window violations, consent issues, non-compliance
    - 💊 **Correlated AEs**: Adverse events triggered by vitals (high BP → headache)
    - 🎯 **Individual Variability**: Each subject has unique response trajectory

    **Use Cases:**
    - 🔬 **Trial Planning**: Simulate realistic scenarios with dropout and missing data
    - 🎓 **Training**: Show data managers what real-world messiness looks like
    - 🧪 **RBQM Testing**: Generate site-level quality metrics for testing dashboards
    - 📈 **Analytics Validation**: Test statistical methods on realistic imperfect data
    - 🤖 **ML Training**: Train predictive models on realistic trial data

    **Parameters:**
    - `n_per_arm`: Subjects per treatment arm (default: 50)
    - `target_effect`: Target SBP reduction at Week 12 in mmHg (default: -5.0)
    - `n_sites`: Number of study sites (default: 5)
    - `site_heterogeneity`: 0=all sites equal, 1=very uneven (default: 0.3)
    - `missing_data_rate`: Fraction of data missing (default: 0.08 = 8%)
    - `dropout_rate`: Fraction of subjects dropping out (default: 0.15 = 15%)
    - `protocol_deviation_rate`: Rate of protocol violations (default: 0.05 = 5%)
    - `enrollment_pattern`: "linear", "exponential", or "seasonal" (default: "exponential")
    - `enrollment_duration_months`: Enrollment duration (default: 12 months)
    - `seed`: Random seed for reproducibility

    **Returns:**
    - `vitals`: DataFrame with enrollment dates, site assignments, dropout flags
    - `adverse_events`: AEs correlated with vitals patterns
    - `protocol_deviations`: Visit window violations, consent issues, etc.
    - `metadata`: Realism scores, site statistics, quality metrics

    **Example Request:**
    ```json
    {
      "n_per_arm": 50,
      "target_effect": -5.0,
      "n_sites": 8,
      "site_heterogeneity": 0.4,
      "missing_data_rate": 0.10,
      "dropout_rate": 0.18,
      "protocol_deviation_rate": 0.07,
      "enrollment_pattern": "exponential",
      "enrollment_duration_months": 14,
      "seed": 42
    }
    ```

    **Quality Score:**
    The response includes a `realism_score` (0-100) that evaluates how realistic the
    generated data is based on:
    - Missing data patterns (MAR vs MCAR)
    - Correlation structure preservation
    - Dropout patterns over time
    - AE rates and severity distribution
    - Site heterogeneity metrics
    """
    try:
        # Initialize the realistic trial generator
        generator = RealisticTrialGenerator(seed=request.seed)

        # Generate the complete trial - NOW WITH AACT PARAMETERS
        trial_data = generator.generate_realistic_trial(
            n_per_arm=request.n_per_arm,
            target_effect=request.target_effect,
            indication=request.indication,
            phase=request.phase,
            n_sites=request.n_sites,
            site_heterogeneity=request.site_heterogeneity,
            missing_data_rate=request.missing_data_rate,
            dropout_rate=request.dropout_rate,
            protocol_deviation_rate=request.protocol_deviation_rate,
            enrollment_pattern=request.enrollment_pattern,
            enrollment_duration_months=request.enrollment_duration_months
        )

        # Convert vitals DataFrame to records, replacing NaN with None for JSON
        vitals_df = trial_data['vitals'].copy()
        # Replace NaN and Inf with None for JSON serialization
        vitals_df = vitals_df.replace([float('inf'), float('-inf')], None)
        vitals_df = vitals_df.where(pd.notnull(vitals_df), None)
        vitals_records = vitals_df.to_dict(orient='records')

        # Return the response
        return RealisticTrialResponse(
            vitals=vitals_records,
            adverse_events=trial_data['adverse_events'],
            protocol_deviations=trial_data['protocol_deviations'],
            metadata=trial_data['metadata']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Realistic trial generation failed: {str(e)}"
        )

# ============================================================================
# AACT INTEGRATION ENDPOINTS - Industry benchmarks from 400K+ trials
# ============================================================================

@app.get("/aact/indications")
async def get_available_indications():
    """
    Get list of disease indications with AACT data from 400,000+ ClinicalTrials.gov trials

    This endpoint provides access to industry benchmarks derived from the AACT
    (Aggregate Analysis of ClinicalTrials.gov) database, which contains comprehensive
    data from over 400,000 real clinical trials.

    **Returns:**
    - `indications`: List of available disease indications with trial counts by phase
    - `total`: Total number of indications available
    - `source`: Data source information (AACT ClinicalTrials.gov)

    **Example Response:**
    ```json
    {
      "indications": [
        {
          "name": "hypertension",
          "total_trials": 1247,
          "by_phase": {
            "Phase 1": 156,
            "Phase 2": 384,
            "Phase 3": 428,
            "Phase 4": 279
          }
        },
        {
          "name": "diabetes",
          "total_trials": 2156,
          "by_phase": {...}
        }
      ],
      "total": 8,
      "source": "AACT ClinicalTrials.gov"
    }
    ```

    **Use Cases:**
    - Discover available indications for realistic trial generation
    - Understand trial volume by therapeutic area
    - Select appropriate indication for your simulation
    """
    try:
        from aact_utils import get_aact_loader

        aact = get_aact_loader()
        indications = aact.get_available_indications()

        # Build detailed indication list with trial counts
        indication_details = []
        for indication in indications:
            phase_dist = aact.get_phase_distribution(indication)
            total = sum(phase_dist.values())
            indication_details.append({
                "name": indication,
                "total_trials": total,
                "by_phase": phase_dist
            })

        # Sort by total trials (descending)
        indication_details.sort(key=lambda x: x['total_trials'], reverse=True)

        return {
            "indications": indication_details,
            "total": len(indications),
            "source": "AACT ClinicalTrials.gov",
            "cache_info": aact.get_source_info()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load AACT indications: {str(e)}"
        )

@app.get("/aact/stats/{indication}")
async def get_indication_stats(
    indication: str,
    phase: str = "Phase 3"
):
    """
    Get industry statistics for a specific indication from 400K+ real trials

    This endpoint provides detailed enrollment statistics and recommended defaults
    for trial simulation based on real-world data from ClinicalTrials.gov.

    **Parameters:**
    - `indication`: Disease indication (e.g., 'hypertension', 'diabetes', 'cancer')
    - `phase`: Trial phase (default: 'Phase 3'). Options: 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'

    **Returns:**
    - `enrollment_statistics`: Real-world enrollment data (mean, median, std, quartiles)
    - `recommended_defaults`: Auto-calculated parameters for realistic trial generation
    - `phase_distribution`: Number of trials by phase for this indication

    **Example Response:**
    ```json
    {
      "indication": "hypertension",
      "phase": "Phase 3",
      "enrollment_statistics": {
        "n_trials": 428,
        "mean": 285.4,
        "median": 150,
        "std": 342.1,
        "q25": 80,
        "q75": 320
      },
      "recommended_defaults": {
        "dropout_rate": 0.15,
        "missing_data_rate": 0.08,
        "n_sites": 10,
        "enrollment_duration_months": 12,
        "target_enrollment": 150
      },
      "phase_distribution": {
        "Phase 1": 156,
        "Phase 2": 384,
        "Phase 3": 428,
        "Phase 4": 279
      }
    }
    ```

    **Use Cases:**
    - Get realistic parameters before generating trials
    - Benchmark your protocol against industry standards
    - Understand typical enrollment for your indication/phase
    - Auto-populate parameters in /generate/realistic-trial endpoint
    """
    try:
        from aact_utils import get_aact_loader

        aact = get_aact_loader()

        # Get enrollment statistics
        enrollment_stats = aact.get_enrollment_stats(indication.lower(), phase)

        # Get recommended defaults
        defaults = aact.get_realistic_defaults(indication.lower(), phase)

        # Get phase distribution
        phase_dist = aact.get_phase_distribution(indication.lower())

        return {
            "indication": indication.lower(),
            "phase": phase,
            "enrollment_statistics": enrollment_stats,
            "recommended_defaults": defaults,
            "phase_distribution": phase_dist,
            "source": "AACT ClinicalTrials.gov"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load AACT statistics for {indication}: {str(e)}"
        )

@app.post("/generate/comprehensive-study", response_model=ComprehensiveStudyResponse)
async def generate_comprehensive_study(request: ComprehensiveStudyRequest):
    """
    Generate a complete clinical trial dataset with all data types

    This endpoint generates a consolidated dataset including:
    - **Vitals**: Blood pressure, heart rate, temperature across multiple visits
    - **Demographics**: Age, gender, race, ethnicity, BMI, smoking status
    - **Adverse Events**: Treatment-emergent adverse events with severity and causality
    - **Labs**: Hematology, chemistry, and lipid panels across visits

    All datasets share the same subject IDs for consistency and can be easily joined.

    **Use Cases:**
    - Rapid study simulation and planning
    - End-to-end EDC testing
    - Analytics and RBQM validation
    - Training and demos

    **Example Request:**
    ```json
    {
      "n_per_arm": 50,
      "target_effect": -5.0,
      "method": "mvn",
      "include_vitals": true,
      "include_demographics": true,
      "include_ae": true,
      "include_labs": true,
      "seed": 42
    }
    ```

    Returns:
        ComprehensiveStudyResponse with all requested data types and metadata
    """
    try:
        total_subjects = request.n_per_arm * 2  # Active + Placebo

        # ============================================================================
        # STEP 1: Generate Coordination Metadata FIRST
        # ============================================================================
        # This ensures ALL datasets share the same subjects, visits, and treatment arms

        # 1.1 Generate Subject IDs
        subject_ids = [f"RA001-{i:03d}" for i in range(1, total_subjects + 1)]

        # 1.2 Assign Treatment Arms (stratified: first half Active, second half Placebo)
        treatment_arms = {}
        for i, subj in enumerate(subject_ids):
            treatment_arms[subj] = "Active" if i < request.n_per_arm else "Placebo"

        # 1.3 Determine Visit Schedule from AACT (if using AACT)
        visit_schedule = None
        if request.use_aact:
            try:
                from aact_utils import get_aact_loader
                aact = get_aact_loader()
                demographics = aact.get_demographics(request.indication.lower(), request.phase)

                if demographics and 'actual_duration' in demographics:
                    duration_months = int(demographics['actual_duration'].get('median_months', 12))
                    # Generate visit schedule based on duration
                    from generators import generate_visit_schedule
                    visit_names, visit_days = generate_visit_schedule(duration_months, n_visits=4)
                    visit_schedule = visit_names
            except:
                pass  # Fall back to default

        if visit_schedule is None:
            visit_schedule = ["Screening", "Day 1", "Week 4", "Week 12"]

        # ============================================================================
        # STEP 2: Generate All Datasets with Coordination Metadata
        # ============================================================================

        response_data = {
            "vitals": None,
            "demographics": None,
            "adverse_events": None,
            "labs": None,
            "metadata": {
                "total_subjects": total_subjects,
                "subjects_per_arm": request.n_per_arm,
                "seed": request.seed,
                "method": request.method,
                "generation_timestamp": datetime.utcnow().isoformat(),
                "datasets_generated": [],
                "coordination": {
                    "subject_ids": subject_ids[:5] + ["..."],  # Show first 5
                    "visit_schedule": visit_schedule,
                    "treatment_arms_count": {
                        "Active": request.n_per_arm,
                        "Placebo": request.n_per_arm
                    }
                }
            }
        }

        # Generate Vitals Data
        if request.include_vitals:
            if request.use_aact:
                # Use AACT-enhanced generators with coordination metadata
                if request.method == "mvn":
                    vitals_df = generate_vitals_mvn_aact(
                        indication=request.indication,
                        phase=request.phase,
                        n_per_arm=request.n_per_arm,
                        target_effect=request.target_effect,
                        seed=request.seed,
                        subject_ids=subject_ids,          # 🔑 Coordinated
                        visit_schedule=visit_schedule,     # 🔑 Coordinated
                        treatment_arms=treatment_arms      # 🔑 Coordinated
                    )
                elif request.method == "rules":
                    vitals_df = generate_vitals_rules_aact(
                        indication=request.indication,
                        phase=request.phase,
                        n_per_arm=request.n_per_arm,
                        target_effect=request.target_effect,
                        seed=request.seed,
                        subject_ids=subject_ids,          # 🔑 Coordinated
                        visit_schedule=visit_schedule,     # 🔑 Coordinated
                        treatment_arms=treatment_arms      # 🔑 Coordinated
                    )
                else:  # bootstrap
                    vitals_df = generate_vitals_bootstrap_aact(
                        indication=request.indication,
                        phase=request.phase,
                        n_per_arm=request.n_per_arm,
                        target_effect=request.target_effect,
                        seed=request.seed,
                        subject_ids=subject_ids,          # 🔑 Coordinated
                        visit_schedule=visit_schedule,     # 🔑 Coordinated
                        treatment_arms=treatment_arms      # 🔑 Coordinated
                    )
            else:
                # Use original generators
                if request.method == "mvn":
                    vitals_df = generate_vitals_mvn(
                        n_per_arm=request.n_per_arm,
                        target_effect=request.target_effect,
                        seed=request.seed
                    )
                elif request.method == "rules":
                    vitals_df = generate_vitals_rules(
                        n_per_arm=request.n_per_arm,
                        target_effect=request.target_effect,
                        seed=request.seed
                    )
                else:  # bootstrap
                    vitals_df = generate_vitals_mvn(
                        n_per_arm=request.n_per_arm,
                        target_effect=request.target_effect,
                        seed=request.seed
                    )

            response_data["vitals"] = vitals_df.to_dict(orient="records")
            response_data["metadata"]["datasets_generated"].append("vitals")
            response_data["metadata"]["vitals_records"] = len(vitals_df)

        # Generate Demographics Data
        if request.include_demographics:
            if request.use_aact:
                demographics_df = generate_demographics_aact(
                    indication=request.indication,
                    phase=request.phase,
                    n_subjects=total_subjects,
                    seed=request.seed,
                    subject_ids=subject_ids,          # 🔑 Coordinated
                    treatment_arms=treatment_arms      # 🔑 Coordinated
                )
            else:
                demographics_df = generate_demographics(
                    n_subjects=total_subjects,
                    seed=request.seed
                )

            response_data["demographics"] = demographics_df.to_dict(orient="records")
            response_data["metadata"]["datasets_generated"].append("demographics")
            response_data["metadata"]["demographics_records"] = len(demographics_df)

        # Generate Adverse Events Data
        if request.include_ae:
            if request.use_aact:
                ae_df = generate_oncology_ae_aact(
                    indication=request.indication,
                    phase=request.phase,
                    n_subjects=total_subjects,
                    seed=request.seed + 1,
                    subject_ids=subject_ids,          # 🔑 Coordinated
                    visit_schedule=visit_schedule,     # 🔑 Coordinated
                    treatment_arms=treatment_arms      # 🔑 Coordinated
                )
            else:
                ae_df = generate_oncology_ae(
                    n_subjects=total_subjects,
                    seed=request.seed + 1
                )
            response_data["adverse_events"] = ae_df.to_dict(orient="records")
            response_data["metadata"]["datasets_generated"].append("adverse_events")
            response_data["metadata"]["ae_records"] = len(ae_df)

        # Generate Lab Results Data
        if request.include_labs:
            if request.use_aact:
                labs_df = generate_labs_aact(
                    indication=request.indication,
                    phase=request.phase,
                    n_subjects=total_subjects,
                    seed=request.seed + 2,
                    subject_ids=subject_ids,          # 🔑 Coordinated
                    visit_schedule=visit_schedule,     # 🔑 Coordinated
                    treatment_arms=treatment_arms      # 🔑 Coordinated
                )
            else:
                labs_df = generate_labs(
                    n_subjects=total_subjects,
                    seed=request.seed + 2
                )
            response_data["labs"] = labs_df.to_dict(orient="records")
            response_data["metadata"]["datasets_generated"].append("labs")
            response_data["metadata"]["labs_records"] = len(labs_df)

        # Add summary
        response_data["metadata"]["summary"] = (
            f"Generated comprehensive study data for {total_subjects} subjects "
            f"({request.n_per_arm} per arm) including: "
            f"{', '.join(response_data['metadata']['datasets_generated'])}"
        )

        return ComprehensiveStudyResponse(**response_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive study generation failed: {str(e)}"
        )


# ============================================================================
# MILLION-SCALE GENERATION - Daft-Powered
# ============================================================================

class MillionScaleRequest(BaseModel):
    total_subjects: int = Field(..., ge=1000, le=10_000_000, description="Total subjects (both arms)")
    chunk_size: int = Field(default=10_000, ge=100, le=100_000, description="Subjects per chunk")
    target_effect: float = Field(default=-5.0, description="Target treatment effect")
    output_path: Optional[str] = Field(None, description="Output file path (Parquet recommended)")
    format: str = Field(default="parquet", pattern=r"^(parquet|csv)$", description="Output format")
    seed: int = Field(default=42, description="Random seed")

class MillionScaleResponse(BaseModel):
    total_subjects: int
    total_records: int
    num_chunks: int
    time_seconds: float
    records_per_second: float
    output_path: Optional[str]
    format: str
    memory_efficient: bool
    message: str

@app.get("/daft/status")
async def daft_status():
    """Check if Daft is available for million-scale generation"""
    return {
        "daft_available": DAFT_AVAILABLE,
        "million_scale_enabled": DAFT_AVAILABLE,
        "max_subjects": 10_000_000 if DAFT_AVAILABLE else 1000,
        "recommended_chunk_size": 10_000,
        "message": "Daft distributed generation ready" if DAFT_AVAILABLE else "Install getdaft==0.3.0 for million-scale generation"
    }

@app.post("/generate/million-scale", response_model=MillionScaleResponse)
async def generate_million_scale(request: MillionScaleRequest):
    """
    Generate million-scale synthetic data using Daft's distributed processing

    Features:
    - Handles 1M+ subjects without memory issues
    - Chunked processing (controlled memory usage)
    - Streaming Parquet writes (efficient storage)
    - Lazy evaluation (optimized performance)

    Example:
        Generate 1 million subjects (4 million records):
        {
            "total_subjects": 1000000,
            "chunk_size": 10000,
            "target_effect": -5.0,
            "output_path": "/data/synthetic_1M.parquet",
            "format": "parquet"
        }

    Performance:
        - 10k subjects: ~2 seconds
        - 100k subjects: ~20 seconds
        - 1M subjects: ~3-5 minutes
        - 10M subjects: ~30-50 minutes

    Note: For datasets > 100k subjects, always use output_path with Parquet format
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Daft not available. Install: pip install getdaft==0.3.0"
        )

    try:
        # Generate
        metadata = generate_vitals_million_scale(
            total_subjects=request.total_subjects,
            chunk_size=request.chunk_size,
            target_effect=request.target_effect,
            output_path=request.output_path,
            seed=request.seed
        )

        return MillionScaleResponse(
            total_subjects=metadata["total_subjects"],
            total_records=metadata["total_records"],
            num_chunks=metadata["num_chunks"],
            time_seconds=metadata["time_seconds"],
            records_per_second=metadata["records_per_second"],
            output_path=metadata["output_path"],
            format=metadata["format"],
            memory_efficient=metadata["memory_efficient"],
            message=f"Successfully generated {metadata['total_records']:,} records in {metadata['time_seconds']:.2f}s"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Million-scale generation failed: {str(e)}"
        )

@app.post("/generate/estimate-memory")
async def estimate_memory_usage(total_subjects: int = 100_000, chunk_size: int = 10_000):
    """
    Estimate memory usage for million-scale generation

    Helps you choose appropriate chunk_size for your available RAM.

    Returns:
        - Total dataset size
        - Memory per chunk
        - Number of chunks
        - Recommendations
    """
    if not DAFT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Daft not available")

    generator = DaftDataGenerator()
    estimates = generator.estimate_memory_usage(total_subjects, chunk_size)

    return {
        "total_subjects": estimates["total_subjects"],
        "total_records": estimates["total_records"],
        "total_size_mb": round(estimates["total_size_mb"], 2),
        "chunk_size": estimates["chunk_size"],
        "records_per_chunk": estimates["records_per_chunk"],
        "chunk_size_mb": round(estimates["chunk_size_mb"], 2),
        "num_chunks": estimates["num_chunks"],
        "recommendation": estimates["recommendation"],
        "suggested_chunk_sizes": {
            "low_memory_2gb": 5_000,
            "medium_memory_8gb": 20_000,
            "high_memory_32gb": 100_000
        }
    }


# ============================================================================
# AACT Integration Endpoints - Industry Benchmarking
# ============================================================================

@app.get("/aact/indications")
async def get_available_indications():
    """
    Get list of disease indications with AACT data
    
    Returns available disease indications from ClinicalTrials.gov database
    (400,000+ trials processed via Daft)
    
    Returns:
        List of indication names with trial counts
    """
    from aact_utils import get_aact_loader
    
    try:
        aact = get_aact_loader()
        indications = aact.get_available_indications()
        
        # Get trial counts for each indication
        indication_details = []
        for indication in indications:
            phase_dist = aact.get_phase_distribution(indication)
            total = sum(phase_dist.values())
            indication_details.append({
                "name": indication,
                "total_trials": total,
                "by_phase": phase_dist
            })
        
        return {
            "indications": indication_details,
            "total": len(indications),
            "source": "AACT ClinicalTrials.gov",
            "total_studies": aact.stats.get("total_studies", 0)
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load AACT data: {str(e)}"
        )


@app.get("/aact/stats/{indication}")
async def get_indication_stats(indication: str, phase: str = "Phase 3"):
    """
    Get industry statistics for a specific indication from AACT
    
    Args:
        indication: Disease indication (e.g., "hypertension", "diabetes")
        phase: Trial phase (default: "Phase 3")
        
    Returns:
        Enrollment statistics, recommended defaults, and phase distribution
        from real ClinicalTrials.gov data
        
    Example:
        GET /aact/stats/hypertension?phase=Phase%203
    """
    from aact_utils import get_aact_loader
    
    try:
        aact = get_aact_loader()
        
        enrollment_stats = aact.get_enrollment_stats(indication, phase)
        defaults = aact.get_realistic_defaults(indication, phase)
        phase_dist = aact.get_phase_distribution(indication)
        
        return {
            "indication": indication,
            "phase": phase,
            "enrollment_statistics": enrollment_stats,
            "recommended_defaults": defaults,
            "phase_distribution": phase_dist,
            "source": "AACT ClinicalTrials.gov"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats for {indication}: {str(e)}"
        )


# ============================================================================
# Scalability Features for College Project
# ============================================================================

class ComprehensiveStudyRequest(BaseModel):
    """Request model for comprehensive study generation using AACT data"""
    indication: str = Field(default="hypertension", description="Disease indication")
    phase: str = Field(default="Phase 3", description="Trial phase")
    n_per_arm: int = Field(default=50, ge=1, le=500, description="Subjects per arm")
    target_effect: float = Field(default=-5.0, description="Target treatment effect")
    seed: int = Field(default=42, description="Random seed")
    method: str = Field(default="mvn", description="Generation method: mvn, bootstrap, or rules")
    use_duration: bool = Field(default=True, description="Use AACT duration for visits")

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
    Generate complete clinical trial with all domains coordinated

    **AACT-Enhanced**: Uses real-world statistics from 557K+ trials
    **Coordinated**: Same subject IDs, visit schedules, treatment arms across all domains
    **Complete**: Returns vitals, demographics, labs, and adverse events in one call
    """
    try:
        import time
        start_time = time.time()

        # Generate coordinated study components
        n_total = request.n_per_arm * 2
        subject_ids = [f"RA001-{i:03d}" for i in range(1, n_total + 1)]
        treatment_arms = {sid: "Active" if i < request.n_per_arm else "Placebo"
                         for i, sid in enumerate(subject_ids)}

        # Get visit schedule
        try:
            from aact_utils import get_demographics as aact_get_demographics
            demographics_data = aact_get_demographics(request.indication, request.phase)
            duration_months = int(demographics_data.get('actual_duration', {}).get('median_months', 12))
        except:
            duration_months = 12
        visit_schedule, _ = generate_visit_schedule(duration_months, n_visits=4) if request.use_duration else (["Screening", "Day 1", "Week 4", "Week 12"], [])

        # Generate vitals
        if request.method == "mvn":
            vitals_df = generate_vitals_mvn_aact(
                indication=request.indication, phase=request.phase, n_per_arm=request.n_per_arm,
                target_effect=request.target_effect, seed=request.seed,
                subject_ids=subject_ids, visit_schedule=visit_schedule, treatment_arms=treatment_arms
            )
        elif request.method == "bootstrap":
            vitals_df = generate_vitals_bootstrap_aact(
                indication=request.indication, phase=request.phase, n_per_arm=request.n_per_arm,
                target_effect=request.target_effect, seed=request.seed,
                subject_ids=subject_ids, visit_schedule=visit_schedule, treatment_arms=treatment_arms
            )
        else:
            vitals_df = generate_vitals_rules_aact(
                indication=request.indication, phase=request.phase, n_per_arm=request.n_per_arm,
                target_effect=request.target_effect, seed=request.seed,
                subject_ids=subject_ids, visit_schedule=visit_schedule, treatment_arms=treatment_arms
            )

        # Generate other domains
        demographics_df = generate_demographics_aact(request.indication, request.phase, n_total, request.seed + 1, subject_ids, treatment_arms)
        labs_df = generate_labs_aact(request.indication, request.phase, n_total, request.seed + 2, request.use_duration, subject_ids, visit_schedule, treatment_arms)
        ae_df = generate_oncology_ae_aact(request.indication, request.phase, n_total, request.seed + 3, subject_ids, visit_schedule, treatment_arms)

        total_time = time.time() - start_time

        return ComprehensiveStudyResponse(
            vitals=vitals_df.to_dict(orient="records"),
            demographics=demographics_df.to_dict(orient="records"),
            labs=labs_df.to_dict(orient="records"),
            adverse_events=ae_df.to_dict(orient="records"),
            metadata={
                "indication": request.indication,
                "phase": request.phase,
                "n_subjects": n_total,
                "total_records": len(vitals_df) + len(demographics_df) + len(labs_df) + len(ae_df),
                "generation_time_ms": round(total_time * 1000, 2),
                "aact_enhanced": True
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive study generation failed: {str(e)}")


@app.get("/benchmark/performance")
async def benchmark_performance(n_per_arm: int = 50, methods: str = "mvn,bootstrap,rules",
                                indication: str = "hypertension", phase: str = "Phase 3"):
    """
    Benchmark AACT-enhanced generator performance

    Compares generation speed across methods (runs each 3 times, averages results)
    **Use Case**: Help users choose optimal method for their scalability needs
    """
    try:
        import time
        method_list = methods.split(",")
        results = {}

        for method in method_list:
            times = []
            for run in range(3):
                start = time.time()
                if method.strip() == "mvn":
                    df = generate_vitals_mvn_aact(indication, phase, n_per_arm, seed=42+run)
                elif method.strip() == "bootstrap":
                    df = generate_vitals_bootstrap_aact(indication, phase, n_per_arm, seed=42+run)
                elif method.strip() == "rules":
                    df = generate_vitals_rules_aact(indication, phase, n_per_arm, seed=42+run)
                else:
                    continue
                times.append(time.time() - start)

            avg_time = sum(times) / len(times)
            results[method.strip()] = {
                "avg_time_ms": round(avg_time * 1000, 2),
                "records_per_second": round(len(df) / avg_time, 2),
                "records_generated": len(df)
            }

        ranked = sorted(results.items(), key=lambda x: x[1]["avg_time_ms"])
        return {
            "benchmark_results": results,
            "fastest_method": ranked[0][0] if ranked else None,
            "ranking": [{"method": m, "avg_time_ms": r["avg_time_ms"]} for m, r in ranked]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@app.post("/stress-test/concurrent")
async def stress_test_concurrent(n_concurrent_requests: int = 10, n_per_arm: int = 50,
                                 indication: str = "hypertension", phase: str = "Phase 3"):
    """
    Stress test: Simulate multiple researchers generating data simultaneously

    **Performance Target**: 10 concurrent studies (50 subjects each) in < 3 seconds
    **Use Case**: Validate system can handle multiple simultaneous users
    """
    try:
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import random

        start_time = time.time()
        results = []
        errors = []

        def generate_single():
            try:
                df = generate_vitals_mvn_aact(indication, phase, n_per_arm, seed=random.randint(1, 10000))
                return {"success": True, "records": len(df)}
            except Exception as e:
                return {"success": False, "error": str(e)}

        with ThreadPoolExecutor(max_workers=n_concurrent_requests) as executor:
            futures = [executor.submit(generate_single) for _ in range(n_concurrent_requests)]
            for future in as_completed(futures):
                result = future.result()
                (results if result["success"] else errors).append(result)

        total_time = time.time() - start_time
        total_records = sum(r["records"] for r in results)

        return {
            "stress_test_results": {
                "total_requests": n_concurrent_requests,
                "successful_requests": len(results),
                "failed_requests": len(errors),
                "total_time_seconds": round(total_time, 2),
                "aggregate_throughput_records_per_second": round(total_records / total_time, 2) if total_time > 0 else 0
            },
            "pass_criteria": {
                "target_time_seconds": 3,
                "achieved_time": round(total_time, 2),
                "passed": total_time < 3 and len(errors) == 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress test failed: {str(e)}")


@app.get("/analytics/portfolio")
async def portfolio_analytics():
    """
    Portfolio-level analytics dashboard

    **Use Case**: Executive summary of organization-wide trial generation activity
    Returns mock data (in production, would query database for real statistics)
    """
    return {
        "portfolio_summary": {
            "total_studies": 127,
            "total_subjects": 12750,
            "studies_by_indication": {"hypertension": 45, "diabetes": 32, "oncology": 28, "cardiovascular": 22},
            "studies_by_phase": {"Phase 1": 15, "Phase 2": 38, "Phase 3": 62, "Phase 4": 12},
            "average_generation_time_ms": 287.5
        },
        "quality_metrics": {"average_quality_score": 0.89, "studies_meeting_quality_threshold": 121},
        "resource_utilization": {"cache_hit_rate": 0.94, "aact_lookup_rate": 0.98},
        "note": "Mock data - in production, queries database for real portfolio statistics"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
