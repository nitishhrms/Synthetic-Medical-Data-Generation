"""
Linkup Integration Service

This service provides AI-powered capabilities using Linkup web search:
1. Evidence Pack Citation Service - Regulatory citations for quality metrics
2. Edit-Check Authoring Assistant - AI-assisted YAML rule generation
3. Compliance/RBQM Watcher - Automated regulatory monitoring

Port: 8008
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import os

from evidence_service import (
    fetch_metric_citations,
    ComprehensiveQualityWithEvidenceRequest,
    ComprehensiveQualityWithEvidenceResponse,
    generate_evidence_summary
)
from edit_check_generator import (
    generate_edit_check_rule,
    EditCheckGenerationRequest,
    EditCheckGenerationResponse
)
from compliance_watcher import (
    scan_all_regulatory_sources,
    ComplianceScanResponse,
    get_recent_updates,
    assess_rule_impact
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Linkup Integration Service",
    description="AI-powered regulatory intelligence and evidence-based quality assessment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Security warning for production
if "*" in ALLOWED_ORIGINS and os.getenv("ENVIRONMENT") == "production":
    import warnings
    warnings.warn(
        "⚠️  SECURITY WARNING: CORS wildcard (*) enabled in production! "
        "Set ALLOWED_ORIGINS environment variable to specific domains.",
        UserWarning
    )
    logger.warning("CORS wildcard enabled in production - security risk!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check & Service Info
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Linkup Integration Service",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "Evidence Pack Citation Service",
            "Edit-Check Authoring Assistant",
            "Compliance/RBQM Watcher"
        ],
        "endpoints": {
            "evidence": "/evidence/*",
            "edit_checks": "/edit-checks/*",
            "compliance": "/compliance/*"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "linkup-integration-service"
    }


# ============================================================================
# Use Case 1: Evidence Pack Citation Service
# ============================================================================

@app.post("/evidence/fetch-citations", response_model=List[Dict])
async def fetch_citations_endpoint(
    metric_name: str,
    metric_value: float,
    context: Optional[str] = None
):
    """
    Fetch authoritative regulatory citations for a quality metric

    Args:
        metric_name: Name of the metric (e.g., "Wasserstein distance")
        metric_value: Value of the metric
        context: Optional context (e.g., "clinical trial data quality")

    Returns:
        List of citations with URLs, snippets, and relevance scores
    """
    try:
        logger.info(f"Fetching citations for metric: {metric_name} = {metric_value}")
        citations = await fetch_metric_citations(metric_name, metric_value, context)
        return citations
    except Exception as e:
        logger.error(f"Error fetching citations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evidence/comprehensive-quality", response_model=ComprehensiveQualityWithEvidenceResponse)
async def comprehensive_quality_with_evidence(
    request: ComprehensiveQualityWithEvidenceRequest
):
    """
    Enhanced quality assessment with regulatory citations

    This endpoint extends the standard quality assessment by adding
    authoritative citations for each metric, making results suitable
    for regulatory submissions.

    Args:
        request: Contains original_data, synthetic_data, and optional k parameter

    Returns:
        Quality metrics with regulatory evidence and citations
    """
    try:
        logger.info("Starting comprehensive quality assessment with evidence")

        # Import analytics functions (these would call the analytics service)
        from quality_calculator import calculate_comprehensive_quality

        # Calculate standard quality metrics
        quality_metrics = await calculate_comprehensive_quality(
            request.original_data,
            request.synthetic_data,
            request.k
        )

        # Fetch citations for key metrics
        citations = {}

        if quality_metrics.get("wasserstein_distances"):
            wasserstein_avg = sum(quality_metrics["wasserstein_distances"].values()) / len(quality_metrics["wasserstein_distances"])
            citations["wasserstein_distance"] = await fetch_metric_citations(
                "Wasserstein distance statistical similarity",
                wasserstein_avg,
                "synthetic data quality validation"
            )

        if quality_metrics.get("rmse_by_column"):
            rmse_avg = sum(quality_metrics["rmse_by_column"].values()) / len(quality_metrics["rmse_by_column"])
            citations["rmse"] = await fetch_metric_citations(
                "RMSE root mean square error clinical validation",
                rmse_avg,
                "synthetic vs real data comparison"
            )

        if quality_metrics.get("correlation_preservation"):
            citations["correlation_preservation"] = await fetch_metric_citations(
                "correlation preservation synthetic data quality",
                quality_metrics["correlation_preservation"],
                "statistical properties preservation"
            )

        if quality_metrics.get("knn_imputation_score"):
            citations["knn_imputation"] = await fetch_metric_citations(
                "K-nearest neighbor imputation missing data MAR",
                quality_metrics["knn_imputation_score"],
                "missing data imputation validation"
            )

        # Generate evidence summary
        evidence_summary = generate_evidence_summary(citations)

        response = ComprehensiveQualityWithEvidenceResponse(
            **quality_metrics,
            regulatory_evidence=citations,
            evidence_summary=evidence_summary,
            evidence_pack_generated_at=datetime.utcnow().isoformat()
        )

        logger.info("Comprehensive quality assessment with evidence completed")
        return response

    except Exception as e:
        logger.error(f"Error in comprehensive quality assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Use Case 2: Edit-Check Authoring Assistant
# ============================================================================

@app.post("/edit-checks/generate-rule", response_model=EditCheckGenerationResponse)
async def generate_rule_endpoint(request: EditCheckGenerationRequest):
    """
    AI-Assisted Edit Check Rule Generation

    Uses Linkup to fetch clinical ranges + citations, returns YAML-ready rule

    Args:
        request: Contains variable name, indication, and optional parameters

    Returns:
        Generated YAML rule with citations and confidence score

    Example:
        POST /edit-checks/generate-rule
        {
            "variable": "systolic_bp",
            "indication": "hypertension",
            "severity": "Major"
        }
    """
    try:
        logger.info(f"Generating edit check rule for variable: {request.variable}")
        result = await generate_edit_check_rule(request)
        return result
    except Exception as e:
        logger.error(f"Error generating edit check rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edit-checks/batch-generate")
async def batch_generate_rules(variables: List[str], indication: str = "general"):
    """
    Generate multiple edit check rules at once

    Args:
        variables: List of variable names
        indication: Clinical indication (default: "general")

    Returns:
        List of generated rules with citations
    """
    try:
        logger.info(f"Batch generating rules for {len(variables)} variables")
        results = []

        for variable in variables:
            request = EditCheckGenerationRequest(
                variable=variable,
                indication=indication
            )
            result = await generate_edit_check_rule(request)
            results.append(result)

        return {
            "total_rules_generated": len(results),
            "rules": results,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in batch rule generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/edit-checks/supported-variables")
async def get_supported_variables():
    """
    Get list of variables with pre-defined patterns for rule generation

    Returns:
        List of supported variables and their descriptions
    """
    return {
        "variables": [
            {"name": "systolic_bp", "description": "Systolic Blood Pressure (mmHg)", "typical_range": "95-200"},
            {"name": "diastolic_bp", "description": "Diastolic Blood Pressure (mmHg)", "typical_range": "55-130"},
            {"name": "heart_rate", "description": "Heart Rate (bpm)", "typical_range": "50-120"},
            {"name": "temperature", "description": "Body Temperature (°C)", "typical_range": "35.0-40.0"},
            {"name": "respiratory_rate", "description": "Respiratory Rate (breaths/min)", "typical_range": "12-20"},
            {"name": "oxygen_saturation", "description": "Oxygen Saturation (%)", "typical_range": "90-100"},
            {"name": "weight", "description": "Body Weight (kg)", "typical_range": "30-200"},
            {"name": "height", "description": "Height (cm)", "typical_range": "100-220"},
            {"name": "bmi", "description": "Body Mass Index", "typical_range": "15-50"}
        ]
    }


# ============================================================================
# Use Case 3: Compliance/RBQM Watcher
# ============================================================================

@app.post("/compliance/scan", response_model=ComplianceScanResponse)
async def scan_regulatory_sources():
    """
    Scan all regulatory sources for updates

    This endpoint performs a deep search across FDA, ICH, CDISC, and
    TransCelerate websites for recent guidance updates.

    Called by: Kubernetes CronJob (nightly at 2 AM)

    Returns:
        Summary of detected updates with impact assessment
    """
    try:
        logger.info("Starting regulatory compliance scan")
        result = await scan_all_regulatory_sources()
        logger.info(f"Compliance scan completed: {result.total_updates} updates found")
        return result
    except Exception as e:
        logger.error(f"Error in compliance scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compliance/recent-updates")
async def get_compliance_updates(
    days: int = 30,
    impact_level: Optional[str] = None,
    source: Optional[str] = None
):
    """
    Get recent regulatory updates from database

    Args:
        days: Look back period in days (default: 30)
        impact_level: Filter by impact (HIGH, MEDIUM, LOW)
        source: Filter by source (FDA, ICH, CDISC, TransCelerate)

    Returns:
        List of regulatory updates matching criteria
    """
    try:
        updates = await get_recent_updates(days, impact_level, source)
        return {
            "updates": updates,
            "count": len(updates),
            "filters": {
                "days": days,
                "impact_level": impact_level,
                "source": source
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving updates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compliance/assess-impact")
async def assess_impact_endpoint(
    update_id: str,
    current_rules: Optional[List[Dict]] = None
):
    """
    Assess impact of a regulatory update on existing edit check rules

    Args:
        update_id: ID of the regulatory update
        current_rules: Optional list of current rules to check against

    Returns:
        Impact assessment with affected rules and recommendations
    """
    try:
        assessment = await assess_rule_impact(update_id, current_rules)
        return assessment
    except Exception as e:
        logger.error(f"Error assessing impact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compliance/dashboard-summary")
async def get_dashboard_summary():
    """
    Get summary statistics for compliance dashboard

    Returns:
        Overview of compliance status, recent scans, and alerts
    """
    try:
        # Get recent scan results
        recent_scans = await get_recent_updates(days=7)

        # Count by impact level
        high_impact = sum(1 for u in recent_scans if u.get("impact_assessment") == "HIGH")
        medium_impact = sum(1 for u in recent_scans if u.get("impact_assessment") == "MEDIUM")
        low_impact = sum(1 for u in recent_scans if u.get("impact_assessment") == "LOW")

        # Count by source
        by_source = {}
        for update in recent_scans:
            source = update.get("source_name", "Unknown")
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "summary": {
                "total_updates_last_7_days": len(recent_scans),
                "high_impact_count": high_impact,
                "medium_impact_count": medium_impact,
                "low_impact_count": low_impact
            },
            "by_source": by_source,
            "last_scan": datetime.utcnow().isoformat(),
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8008))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Linkup Integration Service on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
