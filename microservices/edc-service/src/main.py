"""
EDC Service - Electronic Data Capture
Handles subject data, visits, validation, and auto-repair
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import json
import uvicorn

from validation import validate_vitals
from repair import auto_repair_vitals
from db_utils import db, cache, startup_db, shutdown_db

app = FastAPI(
    title="EDC Service",
    description="Electronic Data Capture for Clinical Trials",
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
class VitalsRecord(BaseModel):
    SubjectID: str = Field(..., description="Subject identifier (format: RA###-###)")
    VisitName: str = Field(..., description="Visit name (Screening, Day 1, Week 4, Week 12)")
    TreatmentArm: str = Field(..., description="Treatment arm (Active or Placebo)")
    SystolicBP: int = Field(..., ge=95, le=200, description="Systolic blood pressure (mmHg)")
    DiastolicBP: int = Field(..., ge=55, le=130, description="Diastolic blood pressure (mmHg)")
    HeartRate: int = Field(..., ge=50, le=120, description="Heart rate (bpm)")
    Temperature: float = Field(..., ge=35.0, le=40.0, description="Temperature (°C)")

class VitalsBulkRequest(BaseModel):
    records: List[VitalsRecord]

# Unvalidated model for repair endpoint - accepts any values to be repaired
class UnvalidatedVitalsRecord(BaseModel):
    SubjectID: str = Field(..., description="Subject identifier")
    VisitName: str = Field(..., description="Visit name")
    TreatmentArm: str = Field(..., description="Treatment arm")
    SystolicBP: int = Field(..., description="Systolic blood pressure (mmHg)")
    DiastolicBP: int = Field(..., description="Diastolic blood pressure (mmHg)")
    HeartRate: int = Field(..., description="Heart rate (bpm)")
    Temperature: float = Field(..., description="Temperature (°C)")

class UnvalidatedVitalsBulkRequest(BaseModel):
    records: List[UnvalidatedVitalsRecord]

class ValidationResponse(BaseModel):
    rows: int
    checks: List[Dict[str, Any]]
    week12_effect: Optional[float] = None
    fever_count: int = 0
    all_passed: bool = False

class RepairResponse(BaseModel):
    repaired_records: List[VitalsRecord]
    validation_after: ValidationResponse

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db.pool else "disconnected"
    cache_status = "connected" if cache.enabled and cache.client else "disconnected"

    return {
        "status": "healthy",
        "service": "edc-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "cache": cache_status
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "EDC Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "validate": "/validate",
            "repair": "/repair",
            "docs": "/docs"
        }
    }

@app.post("/validate", response_model=ValidationResponse)
async def validate_data(request: VitalsBulkRequest):
    """
    Validate vitals data against clinical constraints
    
    Checks:
    - Required columns present
    - Value ranges (BP, HR, Temperature)
    - Fever count (1-2 rows with temp > 38°C)
    - Fever rows have HR >= 67
    - Week-12 effect approximately -5 mmHg (Active - Placebo)
    """
    try:
        # Convert to DataFrame
        records_dict = [r.dict() for r in request.records]
        df = pd.DataFrame(records_dict)
        
        # Run validation
        report = validate_vitals(df)
        
        # Format checks for response
        checks_formatted = [
            {"name": name, "passed": bool(passed)}
            for name, passed in report["checks"]
        ]
        
        all_passed = all(bool(p) for _, p in report["checks"])
        
        return ValidationResponse(
            rows=report["rows"],
            checks=checks_formatted,
            week12_effect=report.get("week12_effect"),
            fever_count=report.get("fever_count", 0),
            all_passed=all_passed
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(e)}"
        )

@app.post("/repair", response_model=RepairResponse)
async def repair_data(request: UnvalidatedVitalsBulkRequest):
    """
    Auto-repair vitals data to fix constraint violations

    Repair actions:
    - Clip values to valid ranges
    - Ensure at least 1 fever row (temp > 38°C)
    - Ensure fever rows have HR >= 67
    - Adjust Week-12 effect to target -5 mmHg

    Note: This endpoint accepts unvalidated data (values outside normal ranges)
    and repairs them to meet clinical constraints.
    """
    try:
        # Convert to DataFrame
        records_dict = [r.dict() for r in request.records]
        df = pd.DataFrame(records_dict)
        
        # Run repair
        repaired_df = auto_repair_vitals(df)
        
        # Validate after repair
        validation_report = validate_vitals(repaired_df)
        checks_formatted = [
            {"name": name, "passed": bool(passed)}
            for name, passed in validation_report["checks"]
        ]
        
        validation_after = ValidationResponse(
            rows=validation_report["rows"],
            checks=checks_formatted,
            week12_effect=validation_report.get("week12_effect"),
            fever_count=validation_report.get("fever_count", 0),
            all_passed=all(bool(p) for _, p in validation_report["checks"])
        )
        
        # Convert back to records
        repaired_records = [
            VitalsRecord(**row.to_dict())
            for _, row in repaired_df.iterrows()
        ]
        
        return RepairResponse(
            repaired_records=repaired_records,
            validation_after=validation_after
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repair failed: {str(e)}"
        )

@app.post("/store-vitals")
async def store_vitals(request: VitalsBulkRequest):
    """
    Store vitals data in the database

    Stores validated vitals records to the vital_signs table
    Returns the count of records stored
    """
    try:
        stored_count = 0

        for record in request.records:
            # Extract patient ID from SubjectID (e.g., "RA001-001")
            # In production, you'd look up the actual patient_id from the patients table
            subject_number = record.SubjectID

            # Default tenant for demo purposes (in production, get from auth context)
            tenant_id = "DEFAULT_TENANT"

            # Check if patient exists, if not create placeholder
            patient = await db.fetchrow(
                "SELECT patient_id FROM patients WHERE tenant_id = $1 AND subject_number = $2",
                tenant_id, subject_number
            )

            if not patient:
                # Create patient record
                patient_id = await db.fetchval("""
                    INSERT INTO patients (tenant_id, subject_number, site_id, protocol_id, enrollment_date, treatment_arm)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING patient_id
                """, tenant_id, subject_number, "SITE001", "PROTO-001", datetime.utcnow().date(), record.TreatmentArm)
            else:
                patient_id = patient["patient_id"]

            # Store vital signs
            await db.execute("""
                INSERT INTO vital_signs (
                    tenant_id, patient_id, visit_date, measurement_time,
                    systolic_bp, diastolic_bp, heart_rate, temperature,
                    data_batch
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
            """,
                tenant_id,
                patient_id,
                datetime.utcnow().date(),
                datetime.utcnow(),
                record.SystolicBP,
                record.DiastolicBP,
                record.HeartRate,
                record.Temperature,
                json.dumps({"visit_name": record.VisitName, "treatment_arm": record.TreatmentArm})
            )

            stored_count += 1

        # Invalidate cache for this patient
        await cache.delete_pattern("patient:*")

        return {
            "success": True,
            "records_stored": stored_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store vitals: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)


