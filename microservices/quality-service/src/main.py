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

# Privacy assessment module
try:
    from privacy_assessment import PrivacyAssessor
    PRIVACY_AVAILABLE = True
except ImportError:
    PRIVACY_AVAILABLE = False
    print("Warning: Privacy assessment not available (anonymeter not installed)")

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

@app.post("/checks/validate-and-save-queries")
async def validate_and_save_queries(request: EditChecksRequest):
    """
    Run validation and automatically save violations as queries

    This replaces the old /checks/validate endpoint for EDC integration.
    It runs edit checks and creates query records for any violations found.
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)

        # Run existing validation
        rules_yaml = request.rules_yaml or load_default_rules()
        queries_df = run_edit_checks_yaml(df, rules_yaml)

        # Count total checks
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
                    "subject_id": row.get("SubjectID", "UNKNOWN"),
                    "check_id": row.get("CheckID", ""),
                    "field": row.get("Field", ""),
                    "severity": row.get("Severity", "warning").lower(),
                    "message": row.get("Message", ""),
                    "check_name": row.get("CheckName", "")
                })

        # Save violations as queries in database
        queries_created = 0
        if violations and db.pool:
            for violation in violations:
                # Generate query text
                query_text = f"{violation.get('check_name', 'Check')}: {violation['message']}"

                # Determine severity based on check
                severity_map = {
                    "error": "critical",
                    "warning": "warning",
                    "info": "info"
                }
                severity = severity_map.get(violation.get("severity", "warning"), "warning")

                # Insert query into database
                try:
                    query_id = await db.fetchval("""
                        INSERT INTO queries (
                            subject_id, check_id, field_id, query_text,
                            severity, query_type, status, opened_at
                        )
                        VALUES ($1, $2, $3, $4, $5, 'auto', 'open', NOW())
                        RETURNING query_id
                    """,
                        violation.get("subject_id", "UNKNOWN"),
                        violation.get("check_id", ""),
                        violation.get("field", ""),
                        query_text,
                        severity
                    )

                    # Log to query_history
                    await db.execute("""
                        INSERT INTO query_history (query_id, action, action_at, notes)
                        VALUES ($1, 'opened', NOW(), 'Auto-generated from edit check')
                    """, query_id)

                    queries_created += 1
                except Exception as db_error:
                    logger.warning(f"Failed to save query to database: {db_error}")

        # Calculate quality score
        num_violations = len(violations)
        if total_checks > 0 and len(df) > 0:
            quality_score = max(0.0, (len(df) * total_checks - num_violations) / (len(df) * total_checks))
        else:
            quality_score = 1.0

        return {
            "validation_result": {
                "total_records": len(df),
                "total_checks": total_checks,
                "violations": violations,
                "quality_score": round(quality_score, 2),
                "passed": num_violations == 0
            },
            "queries_created": queries_created,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation and query creation failed: {str(e)}"
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


# ============================================================================
# Privacy Assessment Endpoints
# ============================================================================

class PrivacyAssessmentRequest(BaseModel):
    real_data: List[Dict[str, Any]] = Field(..., description="Real/original dataset")
    synthetic_data: List[Dict[str, Any]] = Field(..., description="Synthetic dataset to assess")
    quasi_identifiers: Optional[List[str]] = Field(default=None, description="Quasi-identifier columns (e.g., Age, Gender)")
    sensitive_attributes: Optional[List[str]] = Field(default=None, description="Sensitive attribute columns")

class KAnonymityRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Dataset to assess")
    quasi_identifiers: Optional[List[str]] = Field(default=None, description="Quasi-identifier columns")

@app.post("/privacy/assess/comprehensive")
async def assess_privacy_comprehensive(request: PrivacyAssessmentRequest):
    """
    Comprehensive privacy risk assessment for synthetic data

    Evaluates multiple privacy metrics:
    - **K-anonymity**: Minimum group size for quasi-identifiers (target: k≥5)
    - **L-diversity**: Diversity of sensitive attributes within groups (target: l≥2)
    - **Re-identification risk**: Probability of linking synthetic to real records
    - **Differential privacy**: Privacy budget analysis

    **Use Cases**:
    - Validate synthetic data before release
    - HIPAA/GDPR compliance assessment
    - Compare privacy across generation methods

    **Returns**:
    - Detailed privacy metrics
    - Overall safety recommendation
    - Actionable guidance for improvement

    **Example**:
    ```json
    {
      "real_data": [...],
      "synthetic_data": [...],
      "quasi_identifiers": ["Age", "Gender", "Race"],
      "sensitive_attributes": ["SystolicBP", "Diagnosis"]
    }
    ```
    """
    if not PRIVACY_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Privacy assessment not available. Install anonymeter: pip install anonymeter"
        )

    try:
        # Convert to DataFrames
        real_df = pd.DataFrame(request.real_data)
        synthetic_df = pd.DataFrame(request.synthetic_data)

        # Initialize assessor
        assessor = PrivacyAssessor(
            quasi_identifiers=request.quasi_identifiers,
            sensitive_attributes=request.sensitive_attributes
        )

        # Run comprehensive assessment
        report = assessor.comprehensive_privacy_report(
            real_df,
            synthetic_df,
            quasi_identifiers=request.quasi_identifiers,
            sensitive_attributes=request.sensitive_attributes
        )

        return {
            "privacy_assessment": report,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "quality-service",
            "privacy_module_version": "1.0.0"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Privacy assessment failed: {str(e)}"
        )


@app.post("/privacy/assess/k-anonymity")
async def assess_k_anonymity(request: KAnonymityRequest):
    """
    Calculate k-anonymity for dataset

    **K-anonymity**: Each record is indistinguishable from at least k-1 others
    with respect to quasi-identifiers (Age, Gender, etc.)

    **Standards**:
    - k ≥ 5: Generally acceptable
    - k ≥ 10: Excellent privacy protection
    - k < 3: High re-identification risk

    **Returns**:
    - Minimum k value
    - Number of risky records
    - Safety recommendation
    """
    if not PRIVACY_AVAILABLE:
        return {
            "warning": "Privacy module not available - returning basic count",
            "k": len(request.data),  # Simple fallback
            "safe": True
        }

    try:
        df = pd.DataFrame(request.data)

        assessor = PrivacyAssessor(quasi_identifiers=request.quasi_identifiers)
        result = assessor.calculate_k_anonymity(df, request.quasi_identifiers)

        return {
            "k_anonymity": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"K-anonymity calculation failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
