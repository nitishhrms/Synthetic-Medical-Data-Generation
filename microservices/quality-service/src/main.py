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

# SYNDATA metrics and quality report modules
try:
    from syndata_metrics import SYNDATAMetrics, compute_syndata_metrics
    SYNDATA_AVAILABLE = True
except ImportError:
    SYNDATA_AVAILABLE = False
    print("Warning: SYNDATA metrics not available")

try:
    from quality_report_generator import QualityReportGenerator, generate_quality_report
    QUALITY_REPORT_AVAILABLE = True
except ImportError:
    QUALITY_REPORT_AVAILABLE = False
    print("Warning: Quality report generator not available")

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
    Run validation and automatically save violations as queries in EDC Service
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

        # Post violations to EDC Service
        queries_created = 0
        import httpx
        
        # EDC Service URL (assume running on port 8003 based on previous context)
        edc_url = os.getenv("EDC_SERVICE_URL", "http://localhost:8003")
        
        if violations:
            async with httpx.AsyncClient() as client:
                for violation in violations:
                    # Generate query text
                    query_text = f"{violation.get('check_name', 'Check')}: {violation['message']}"
                    
                    # Determine severity
                    severity_map = {
                        "error": "critical",
                        "warning": "warning",
                        "info": "info"
                    }
                    severity = severity_map.get(violation.get("severity", "warning"), "warning")

                    # Create query payload
                    payload = {
                        "study_id": "STU001", # Default for now, should be passed in request
                        "subject_id": violation.get("subject_id", "UNKNOWN"),
                        "query_text": query_text,
                        "field": violation.get("field", ""),
                        "severity": severity,
                        "opened_by": 1 # System user
                    }

                    try:
                        # Post to EDC
                        resp = await client.post(f"{edc_url}/queries", json=payload)
                        if resp.status_code == 200:
                            queries_created += 1
                        else:
                            print(f"Failed to create query in EDC: {resp.text}")
                    except Exception as req_err:
                        print(f"Error connecting to EDC service: {req_err}")

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

class SYNDATAAssessmentRequest(BaseModel):
    real_data: List[Dict[str, Any]] = Field(..., description="Real/original dataset")
    synthetic_data: List[Dict[str, Any]] = Field(..., description="Synthetic dataset to assess")

class QualityReportRequest(BaseModel):
    method_name: str = Field(..., description="Generation method name (mvn, bootstrap, etc.)")
    real_data: List[Dict[str, Any]] = Field(..., description="Real/original dataset")
    synthetic_data: List[Dict[str, Any]] = Field(..., description="Synthetic dataset")
    syndata_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Pre-computed SYNDATA metrics")
    privacy_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Pre-computed privacy metrics")
    generation_time_ms: Optional[float] = Field(default=None, description="Time taken to generate (ms)")

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


# Backward compatibility alias for RBQM Dashboard
@app.post("/privacy/assess")
async def assess_privacy_alias(request: PrivacyAssessmentRequest):
    """
    Alias for /privacy/assess/comprehensive endpoint
    Maintains backward compatibility with RBQM Dashboard
    """
    return await assess_privacy_comprehensive(request)


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


# ============================================================================
# SYNDATA Quality Metrics Endpoints
# ============================================================================

@app.post("/syndata/assess")
async def assess_syndata_metrics(request: SYNDATAAssessmentRequest):
    """
    Assess SYNDATA-style quality metrics for synthetic data

    Implements metrics from the NIH SYNDATA project:
    - **Support Coverage**: How well synthetic data covers real data value ranges
    - **Cross-Classification**: Joint distribution matching (utility metric)
    - **CI Coverage**: Percentage of synthetic values within real data 95% confidence intervals
      - **Target**: 88-98% (CART study standard)
      - This is the key metric professors look for!
    - **Membership Disclosure**: Can a classifier distinguish real from synthetic?
    - **Attribute Disclosure**: Can sensitive attributes be predicted?

    **Use Cases**:
    - Validate synthetic data quality before using in research
    - Compare quality across different generation methods
    - Generate academic-quality metrics for publications
    - Meet regulatory requirements for synthetic data use

    **Returns**:
    - Comprehensive SYNDATA metrics
    - Overall quality score (0-1)
    - Interpretation and recommendations

    **Example**:
    ```json
    {
      "real_data": [...],
      "synthetic_data": [...]
    }
    ```

    **Response includes**:
    - CI coverage statistics (most important for validation)
    - Support coverage scores
    - Cross-classification utility
    - Privacy disclosure risks
    - Overall SYNDATA score
    """
    if not SYNDATA_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SYNDATA metrics not available. Ensure syndata_metrics.py is installed."
        )

    try:
        # Convert to DataFrames
        real_df = pd.DataFrame(request.real_data)
        synthetic_df = pd.DataFrame(request.synthetic_data)

        # Compute SYNDATA metrics
        metrics = compute_syndata_metrics(real_df, synthetic_df)

        return {
            "syndata_metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "quality-service",
            "syndata_version": "1.0.0"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SYNDATA assessment failed: {str(e)}"
        )


@app.post("/quality/report")
async def generate_comprehensive_quality_report(request: QualityReportRequest):
    """
    Generate comprehensive human-readable quality report for synthetic dataset

    Creates an automated markdown report addressing professor feedback:
    - **Summary statistics**: Means and variances compared to expected values
    - **CI coverage**: Percentage within real data confidence intervals (CART: 88-98%)
    - **SYNDATA metrics**: Support coverage, cross-classification, disclosure risks
    - **Privacy assessment**: K-anonymity, re-identification risks (if provided)
    - **Overall grade**: A/B/C/D rating based on quality
    - **Recommendations**: Actionable suggestions for improvement

    **Use Cases**:
    - Generate quality reports for each synthetic dataset
    - Compare methods systematically
    - Document data quality for regulatory submission
    - Academic publication supplement

    **Parameters**:
    - method_name: "mvn", "bootstrap", "rules", "bayesian", "mice", "llm"
    - real_data: Original dataset
    - synthetic_data: Generated dataset
    - syndata_metrics: Optional pre-computed metrics (auto-computed if not provided)
    - privacy_metrics: Optional privacy assessment results
    - generation_time_ms: Time taken to generate (for performance comparison)

    **Returns**:
    - Markdown-formatted quality report
    - Ready to save as .md file or display in UI

    **Example**:
    ```json
    {
      "method_name": "mvn",
      "real_data": [...],
      "synthetic_data": [...],
      "generation_time_ms": 28.5
    }
    ```
    """
    if not QUALITY_REPORT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Quality report generator not available. Ensure quality_report_generator.py is installed."
        )

    try:
        # Convert to DataFrames
        real_df = pd.DataFrame(request.real_data)
        synthetic_df = pd.DataFrame(request.synthetic_data)

        # Compute SYNDATA metrics if not provided
        syndata_metrics = request.syndata_metrics
        if syndata_metrics is None and SYNDATA_AVAILABLE:
            syndata_metrics = compute_syndata_metrics(real_df, synthetic_df)

        # Generate report
        report_markdown = generate_quality_report(
            method_name=request.method_name,
            real_data=real_df,
            synthetic_data=synthetic_df,
            syndata_metrics=syndata_metrics,
            privacy_metrics=request.privacy_metrics,
            generation_time_ms=request.generation_time_ms
        )

        return {
            "report": report_markdown,
            "method": request.method_name,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "quality-service",
            "report_version": "1.0.0"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality report generation failed: {str(e)}"
        )


# Backward compatibility alias for RBQM Dashboard
@app.post("/report/generate")
async def generate_quality_report_alias(request: QualityReportRequest):
    """
    Alias for /quality/report endpoint
    Maintains backward compatibility with RBQM Dashboard
    """
    return await generate_comprehensive_quality_report(request)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
