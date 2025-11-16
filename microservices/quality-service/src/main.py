"""
Quality Service - Edit Checks and Data Quality Validation
Handles YAML edit checks, validation, and query generation
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import uvicorn
import os

from edit_checks import run_edit_checks_yaml, load_default_rules, simulate_entry_noise
from db_utils import db, cache, startup_db, shutdown_db

app = FastAPI(
    title="Quality Service",
    description="Data Quality Checks and YAML Edit Check Engine",
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
class EditChecksRequest(BaseModel):
    data: List[Dict[str, Any]]
    rules_yaml: Optional[str] = None

class EditChecksResponse(BaseModel):
    total_records: int
    total_checks: int
    violations: List[Dict[str, Any]]
    quality_score: float
    passed: bool

class NoiseRequest(BaseModel):
    data: List[Dict[str, Any]]
    typo_rate: float = Field(default=0.02, ge=0, le=1)
    temp_unit_flip_rate: float = Field(default=0.01, ge=0, le=1)
    seed: int = Field(default=123)

class NoiseResponse(BaseModel):
    noisy_data: List[Dict[str, Any]]
    rows: int

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db.pool else "disconnected"
    cache_status = "connected" if cache.enabled and cache.client else "disconnected"

    return {
        "status": "healthy",
        "service": "quality-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "cache": cache_status
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Quality Service",
        "version": "1.0.0",
        "features": [
            "YAML Edit Check Engine",
            "Range checks",
            "Allowed values validation",
            "Regex pattern matching",
            "Subject-level consistency",
            "Visit completeness checks",
            "Duplicate detection",
            "Entry noise simulation"
        ],
        "endpoints": {
            "health": "/health",
            "checks": "/checks/validate",
            "rules": "/checks/rules",
            "noise": "/quality/simulate-noise",
            "docs": "/docs"
        }
    }

@app.get("/checks/rules")
async def get_default_rules():
    """
    Get default YAML edit check rules

    Returns the built-in rule set for clinical trial vitals data
    """
    return {
        "rules_yaml": load_default_rules()
    }

@app.post("/checks/validate", response_model=EditChecksResponse)
async def validate_with_edit_checks(request: EditChecksRequest):
    """
    Run YAML-based edit checks on data

    Supports multiple check types:
    - range: Value must be within [min, max]
    - allowed_values: Value must be in allowed list
    - regex: Value must match pattern
    - diff_at_least: One field must exceed another by minimum delta
    - constant_within_subject: Field must be constant per subject
    - required_visits: All subjects must have required visits
    - unique_combo: Field combination must be unique
    """
    try:
        df = pd.DataFrame(request.data)
        total_records = len(df)

        # Use default rules if none provided
        rules_yaml = request.rules_yaml or load_default_rules()

        # Run edit checks
        queries_df = run_edit_checks_yaml(df, rules_yaml)

        # Count total checks run (from YAML rules)
        import yaml
        spec = yaml.safe_load(rules_yaml)
        if isinstance(spec, list):
            total_checks = len(spec)
        elif isinstance(spec, dict):
            total_checks = len(spec.get("rules", []))
        else:
            total_checks = 0

        # Format violations
        violations = []
        if not queries_df.empty:
            for _, row in queries_df.iterrows():
                violations.append({
                    "record": row.get("SubjectID", ""),
                    "rule": row.get("CheckID", ""),
                    "severity": row.get("Severity", "").lower(),
                    "message": row.get("Message", "")
                })

        # Calculate quality score (1.0 = perfect, 0.0 = all checks failed)
        # Score = (total_checks - violations) / total_checks
        num_violations = len(violations)
        if total_checks > 0:
            quality_score = max(0.0, (total_records * total_checks - num_violations) / (total_records * total_checks))
        else:
            quality_score = 1.0

        # Passed = no violations
        passed = num_violations == 0

        return EditChecksResponse(
            total_records=total_records,
            total_checks=total_checks,
            violations=violations,
            quality_score=round(quality_score, 2),
            passed=passed
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Edit checks failed: {str(e)}"
        )

@app.post("/quality/simulate-noise", response_model=NoiseResponse)
async def add_entry_noise(request: NoiseRequest):
    """
    Simulate data entry errors (noise)

    Adds realistic entry errors:
    - Random ±1 jitter on vitals
    - 10-90% scaling errors
    - Temperature unit conversion errors (C to F)

    Useful for testing quality control systems
    """
    try:
        df = pd.DataFrame(request.data)

        noisy_df = simulate_entry_noise(
            df,
            typo_rate=request.typo_rate,
            temp_unit_flip_rate=request.temp_unit_flip_rate,
            seed=request.seed
        )

        return NoiseResponse(
            noisy_data=noisy_df.to_dict(orient="records"),
            rows=len(noisy_df)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Noise simulation failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
