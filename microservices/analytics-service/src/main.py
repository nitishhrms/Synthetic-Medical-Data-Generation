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

from stats import (
    calculate_week12_statistics,
    calculate_recist_orr,
    ks_distance
)
from rbqm import generate_rbqm_summary
from csr import generate_csr_draft
from sdtm import export_to_sdtm_vs
from db_utils import db, cache, startup_db, shutdown_db

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
        "version": "1.0.0",
        "features": [
            "Week-12 Statistics (t-test)",
            "RECIST + ORR Analysis",
            "RBQM Summary",
            "CSR Draft Generation",
            "SDTM Export"
        ],
        "endpoints": {
            "health": "/health",
            "stats": "/stats/week12",
            "recist": "/stats/recist",
            "rbqm": "/rbqm/summary",
            "csr": "/csr/draft",
            "sdtm": "/sdtm/export",
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
