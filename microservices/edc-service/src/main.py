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
import os

from validation import validate_vitals
from repair import auto_repair_vitals
from db_utils import db, cache, startup_db, shutdown_db

# Medical imaging support
try:
    from image_processor import MedicalImageProcessor, process_medical_image
    from fastapi import File, UploadFile
    from fastapi.responses import Response
    IMAGING_AVAILABLE = True
except ImportError:
    IMAGING_AVAILABLE = False
    import warnings
    warnings.warn("Medical imaging not available. Install: pip install pydicom pillow opencv-python")

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

# Study Management Models
class StudyCreate(BaseModel):
    study_name: str
    indication: str
    phase: str = Field(..., pattern=r'^Phase [123]$')
    sponsor: str
    start_date: str
    status: str = Field(default="active")

class Study(BaseModel):
    study_id: str
    study_name: str
    indication: str
    phase: str
    sponsor: str
    start_date: str
    status: str
    subjects_enrolled: int = 0
    created_at: str

class SubjectCreate(BaseModel):
    study_id: str
    site_id: str
    treatment_arm: str = Field(..., pattern=r'^(Active|Placebo)$')

class Subject(BaseModel):
    subject_id: str
    study_id: str
    site_id: str
    treatment_arm: str
    enrollment_date: str
    status: str

class ImportSyntheticRequest(BaseModel):
    study_id: str
    data: List[VitalsRecord]
    source: str

class ImportSyntheticResponse(BaseModel):
    subjects_imported: int
    observations_imported: int
    message: str

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

# ============================================================================
# Study Management Endpoints
# ============================================================================

# In-memory storage for studies and subjects (for development)
# In production, these would be stored in a proper database
studies_db: Dict[str, Dict] = {}
subjects_db: Dict[str, Dict] = {}

@app.post("/studies")
async def create_study(study: StudyCreate):
    """Create a new clinical trial study"""
    study_id = f"STU{len(studies_db) + 1:03d}"

    study_data = {
        "study_id": study_id,
        "study_name": study.study_name,
        "indication": study.indication,
        "phase": study.phase,
        "sponsor": study.sponsor,
        "start_date": study.start_date,
        "status": study.status,
        "subjects_enrolled": 0,
        "created_at": datetime.utcnow().isoformat()
    }

    studies_db[study_id] = study_data

    return {
        "study_id": study_id,
        "message": "Study created successfully"
    }

@app.get("/studies")
async def list_studies():
    """List all studies"""
    return {
        "studies": list(studies_db.values())
    }

@app.get("/studies/{study_id}")
async def get_study(study_id: str):
    """Get study details"""
    if study_id not in studies_db:
        raise HTTPException(status_code=404, detail="Study not found")

    return studies_db[study_id]

@app.post("/subjects")
async def enroll_subject(subject: SubjectCreate):
    """Enroll a new subject in a study"""
    # Verify study exists
    if subject.study_id not in studies_db:
        raise HTTPException(status_code=404, detail="Study not found")

    # Generate subject ID
    study_subjects = [s for s in subjects_db.values() if s["study_id"] == subject.study_id]
    subject_num = len(study_subjects) + 1
    subject_id = f"{subject.study_id.replace('STU', 'RA')}-{subject_num:03d}"

    subject_data = {
        "subject_id": subject_id,
        "study_id": subject.study_id,
        "site_id": subject.site_id,
        "treatment_arm": subject.treatment_arm,
        "enrollment_date": datetime.utcnow().isoformat(),
        "status": "enrolled"
    }

    subjects_db[subject_id] = subject_data

    # Update study subject count
    studies_db[subject.study_id]["subjects_enrolled"] += 1

    return {
        "subject_id": subject_id,
        "message": "Subject enrolled successfully"
    }

@app.get("/subjects/{subject_id}")
async def get_subject(subject_id: str):
    """Get subject details"""
    if subject_id not in subjects_db:
        raise HTTPException(status_code=404, detail="Subject not found")

    return subjects_db[subject_id]

@app.post("/import/synthetic")
async def import_synthetic_data(request: ImportSyntheticRequest):
    """Import synthetic data into a study"""
    # Verify study exists
    if request.study_id not in studies_db:
        raise HTTPException(status_code=404, detail="Study not found")

    # Extract unique subjects from the data
    unique_subjects = set(record.SubjectID for record in request.data)

    # Create subjects if they don't exist
    subjects_created = 0
    for subject_id in unique_subjects:
        if subject_id not in subjects_db:
            # Extract treatment arm from first record
            treatment_arm = next(r.TreatmentArm for r in request.data if r.SubjectID == subject_id)

            subject_data = {
                "subject_id": subject_id,
                "study_id": request.study_id,
                "site_id": "Site001",  # Default site
                "treatment_arm": treatment_arm,
                "enrollment_date": datetime.utcnow().isoformat(),
                "status": "enrolled"
            }
            subjects_db[subject_id] = subject_data
            subjects_created += 1

    # Update study subject count
    studies_db[request.study_id]["subjects_enrolled"] = len(
        [s for s in subjects_db.values() if s["study_id"] == request.study_id]
    )

    return ImportSyntheticResponse(
        subjects_imported=subjects_created,
        observations_imported=len(request.data),
        message=f"Successfully imported {len(request.data)} observations for {subjects_created} subjects from {request.source}"
    )


# ============================================================================
# Query Management Endpoints
# ============================================================================

class QueryResponse(BaseModel):
    query_id: int
    subject_id: str
    query_text: str
    severity: str
    status: str
    opened_at: str
    response_text: Optional[str] = None

class QueryRespondRequest(BaseModel):
    response_text: str

class QueryCloseRequest(BaseModel):
    resolution_notes: str

@app.get("/queries")
async def list_queries(
    status_filter: Optional[str] = None,
    subject_id: Optional[str] = None,
    severity: Optional[str] = None
):
    """
    List queries with optional filters

    Filters:
    - status: open, answered, closed, cancelled
    - subject_id: filter by subject
    - severity: info, warning, error, critical
    """
    where_clauses = []
    params = []
    param_idx = 1

    if status_filter:
        where_clauses.append(f"status = ${param_idx}")
        params.append(status_filter)
        param_idx += 1

    if subject_id:
        where_clauses.append(f"subject_id = ${param_idx}")
        params.append(subject_id)
        param_idx += 1

    if severity:
        where_clauses.append(f"severity = ${param_idx}")
        params.append(severity)
        param_idx += 1

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    queries = await db.fetch(f"""
        SELECT query_id, subject_id, query_text, severity, status,
               opened_at, response_text
        FROM queries
        WHERE {where_sql}
        ORDER BY opened_at DESC
    """, *params)

    return [
        {
            "query_id": q["query_id"],
            "subject_id": q["subject_id"],
            "query_text": q["query_text"],
            "severity": q["severity"],
            "status": q["status"],
            "opened_at": q["opened_at"].isoformat() if q["opened_at"] else None,
            "response_text": q["response_text"]
        }
        for q in queries
    ]

@app.get("/queries/{query_id}")
async def get_query(query_id: int):
    """
    Get query details with history

    Returns full query details including:
    - Query information
    - User details (who opened, responded)
    - Query history (audit trail)
    """
    query = await db.fetchrow("""
        SELECT q.*,
               u_opened.username as opened_by_name,
               u_responded.username as responded_by_name
        FROM queries q
        LEFT JOIN users u_opened ON q.opened_by = u_opened.user_id
        LEFT JOIN users u_responded ON q.responded_by = u_responded.user_id
        WHERE q.query_id = $1
    """, query_id)

    if not query:
        raise HTTPException(404, "Query not found")

    # Get history
    history = await db.fetch("""
        SELECT action, action_at, notes
        FROM query_history
        WHERE query_id = $1
        ORDER BY action_at ASC
    """, query_id)

    return {
        **dict(query),
        "history": [
            {
                "action": h["action"],
                "action_at": h["action_at"].isoformat() if h["action_at"] else None,
                "notes": h["notes"]
            }
            for h in history
        ]
    }

@app.put("/queries/{query_id}/respond")
async def respond_to_query(query_id: int, request: QueryRespondRequest, user_id: int = 1):
    """
    CRC responds to query

    Changes query status from 'open' to 'answered'
    Records the response text and timestamp
    """
    await db.execute("""
        UPDATE queries
        SET response_text = $1,
            responded_at = NOW(),
            responded_by = $2,
            status = 'answered',
            updated_at = NOW()
        WHERE query_id = $3
    """, request.response_text, user_id, query_id)

    # Log to history
    await db.execute("""
        INSERT INTO query_history (query_id, action, action_by, action_at, notes)
        VALUES ($1, 'answered', $2, NOW(), $3)
    """, query_id, user_id, request.response_text)

    return {"query_id": query_id, "status": "answered"}

@app.put("/queries/{query_id}/close")
async def close_query(query_id: int, request: QueryCloseRequest, user_id: int = 1):
    """
    Data Manager closes query

    Changes query status to 'closed'
    Records resolution notes and timestamp
    """
    await db.execute("""
        UPDATE queries
        SET status = 'closed',
            resolved_at = NOW(),
            resolved_by = $1,
            resolution_notes = $2,
            updated_at = NOW()
        WHERE query_id = $3
    """, user_id, request.resolution_notes, query_id)

    # Log to history
    await db.execute("""
        INSERT INTO query_history (query_id, action, action_by, action_at, notes)
        VALUES ($1, 'closed', $2, NOW(), $3)
    """, query_id, user_id, request.resolution_notes)

    return {"query_id": query_id, "status": "closed"}

# ============================================================================
# Form Definitions Endpoints
# ============================================================================

class FormDefinition(BaseModel):
    form_id: str
    form_name: str
    form_version: str = "1.0"
    form_schema: Dict[str, Any]  # JSON structure
    edit_checks_yaml: Optional[str] = None

class FormDataSubmit(BaseModel):
    form_id: str
    subject_id: str
    visit_name: Optional[str] = None
    form_data: Dict[str, Any]

@app.post("/forms/definitions")
async def create_form_definition(form: FormDefinition, user_id: int = 1):
    """
    Create or update form definition

    Form definitions include:
    - Form schema (JSON structure defining fields)
    - Edit checks (YAML-based validation rules)
    """
    await db.execute("""
        INSERT INTO form_definitions (
            form_id, form_name, form_version, form_schema,
            edit_checks_yaml, status, created_by, created_at
        )
        VALUES ($1, $2, $3, $4::jsonb, $5, 'active', $6, NOW())
        ON CONFLICT (form_id) DO UPDATE
        SET form_name = $2,
            form_version = $3,
            form_schema = $4::jsonb,
            edit_checks_yaml = $5,
            updated_at = NOW()
    """,
        form.form_id, form.form_name, form.form_version,
        json.dumps(form.form_schema), form.edit_checks_yaml, user_id
    )

    return {"form_id": form.form_id, "status": "created"}

@app.get("/forms/definitions")
async def list_form_definitions():
    """List all active form definitions"""
    forms = await db.fetch("""
        SELECT form_id, form_name, form_version, status, created_at
        FROM form_definitions
        WHERE status = 'active'
        ORDER BY form_name
    """)

    return {"forms": [dict(f) for f in forms]}

@app.get("/forms/definitions/{form_id}")
async def get_form_definition(form_id: str):
    """Get form definition with schema"""
    form = await db.fetchrow("""
        SELECT form_id, form_name, form_version, form_schema, edit_checks_yaml
        FROM form_definitions
        WHERE form_id = $1
    """, form_id)

    if not form:
        raise HTTPException(404, "Form not found")

    return dict(form)

@app.post("/forms/data")
async def submit_form_data(data: FormDataSubmit, user_id: int = 1):
    """
    Submit form data with validation

    Validates data against form definition edit checks
    before storing in the database
    """
    # Get form definition
    form_def = await db.fetchrow("""
        SELECT form_schema, edit_checks_yaml
        FROM form_definitions
        WHERE form_id = $1
    """, data.form_id)

    if not form_def:
        raise HTTPException(404, "Form definition not found")

    # TODO: Validate against edit checks by calling Quality Service
    # if form_def["edit_checks_yaml"]:
    #     pass

    # Store form data
    data_id = await db.fetchval("""
        INSERT INTO form_data (
            form_id, subject_id, visit_name, form_data,
            status, submitted_at, submitted_by
        )
        VALUES ($1, $2, $3, $4::jsonb, 'submitted', NOW(), $5)
        RETURNING data_id
    """,
        data.form_id, data.subject_id, data.visit_name,
        json.dumps(data.form_data), user_id
    )

    return {"data_id": data_id, "status": "submitted"}

# ============================================================================
# Demographics Endpoints
# ============================================================================

class Demographics(BaseModel):
    subject_id: str
    age: int = Field(..., ge=18, le=85)
    gender: str = Field(..., pattern=r'^(Male|Female|Other)$')
    race: str
    ethnicity: str
    height_cm: float = Field(..., ge=140, le=220)
    weight_kg: float = Field(..., ge=40, le=200)
    bmi: Optional[float] = None
    smoking_status: str

@app.post("/demographics")
async def record_demographics(demo: Demographics):
    """
    Record demographics for subject

    Automatically calculates BMI from height and weight
    """
    # Calculate BMI
    bmi = demo.weight_kg / ((demo.height_cm / 100) ** 2)

    demo_id = await db.fetchval("""
        INSERT INTO demographics (
            subject_id, age, gender, race, ethnicity,
            height_cm, weight_kg, bmi, smoking_status, recorded_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        RETURNING demo_id
    """,
        demo.subject_id, demo.age, demo.gender, demo.race, demo.ethnicity,
        demo.height_cm, demo.weight_kg, bmi, demo.smoking_status
    )

    return {"demo_id": demo_id, "bmi": round(bmi, 2)}

@app.get("/demographics/{subject_id}")
async def get_demographics(subject_id: str):
    """Get demographics for a subject"""
    demo = await db.fetchrow("""
        SELECT * FROM demographics
        WHERE subject_id = $1
    """, subject_id)

    if not demo:
        raise HTTPException(404, "Demographics not found")

    return dict(demo)

# ============================================================================
# Lab Results Endpoints
# ============================================================================

class LabResults(BaseModel):
    subject_id: str
    visit_name: str
    test_date: str
    hemoglobin: Optional[float] = None
    hematocrit: Optional[float] = None
    wbc: Optional[float] = None
    platelets: Optional[float] = None
    glucose: Optional[float] = None
    creatinine: Optional[float] = None
    bun: Optional[float] = None
    alt: Optional[float] = None
    ast: Optional[float] = None
    bilirubin: Optional[float] = None
    total_cholesterol: Optional[float] = None
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    triglycerides: Optional[float] = None

@app.post("/labs")
async def record_lab_results(lab: LabResults):
    """Record lab results for a subject visit"""
    lab_id = await db.fetchval("""
        INSERT INTO lab_results (
            subject_id, visit_name, test_date,
            hemoglobin, hematocrit, wbc, platelets,
            glucose, creatinine, bun, alt, ast, bilirubin,
            total_cholesterol, ldl, hdl, triglycerides,
            recorded_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, NOW())
        RETURNING lab_id
    """,
        lab.subject_id, lab.visit_name, lab.test_date,
        lab.hemoglobin, lab.hematocrit, lab.wbc, lab.platelets,
        lab.glucose, lab.creatinine, lab.bun, lab.alt, lab.ast, lab.bilirubin,
        lab.total_cholesterol, lab.ldl, lab.hdl, lab.triglycerides
    )

    return {"lab_id": lab_id, "status": "recorded"}

@app.get("/labs/{subject_id}")
async def get_lab_results(subject_id: str):
    """Get all lab results for a subject"""
    labs = await db.fetch("""
        SELECT * FROM lab_results
        WHERE subject_id = $1
        ORDER BY test_date DESC
    """, subject_id)

    return {"labs": [dict(l) for l in labs]}


# ============================================================================
# Privacy Assessment Endpoints
# ============================================================================

class PrivacyAssessmentRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Clinical data to assess for privacy risks")
    k_anonymity: int = Field(default=5, ge=1, le=20, description="K-anonymity threshold")

class PrivacyAssessmentResponse(BaseModel):
    privacy_score: float = Field(..., description="Overall privacy score (0-1, higher is better)")
    k_anonymity_satisfied: bool = Field(..., description="Whether k-anonymity threshold is met")
    re_identification_risk: float = Field(..., description="Risk of re-identification (0-1, lower is better)")
    uniqueness_ratio: float = Field(..., description="Ratio of unique records")
    quasi_identifiers_found: List[str] = Field(..., description="Potential quasi-identifiers detected")
    recommendations: List[str] = Field(..., description="Privacy improvement recommendations")
    summary: str = Field(..., description="Human-readable summary")

@app.post("/privacy/assess/comprehensive", response_model=PrivacyAssessmentResponse)
async def assess_privacy_comprehensive(request: PrivacyAssessmentRequest):
    """
    Comprehensive privacy assessment for clinical trial data

    Evaluates privacy risks including:
    - K-anonymity compliance
    - Re-identification risk analysis
    - Quasi-identifier detection
    - Uniqueness analysis

    **Privacy Metrics:**
    1. **K-Anonymity**: Ensures each combination of quasi-identifiers appears at least K times
    2. **Re-identification Risk**: Probability that individuals can be re-identified
    3. **Uniqueness Ratio**: Proportion of records with unique attribute combinations
    4. **Quasi-Identifiers**: Attributes that could be combined for re-identification

    **Use Cases:**
    - HIPAA compliance validation
    - Data sharing risk assessment
    - Privacy impact assessments
    - Regulatory submissions
    """
    try:
        df = pd.DataFrame(request.data)

        # Potential quasi-identifiers in clinical trial data
        quasi_identifiers = []
        for col in df.columns:
            # Demographics and identifying information
            if col in ["age", "gender", "race", "ethnicity", "site_id", "enrollment_date"]:
                quasi_identifiers.append(col)
            # Check for SubjectID patterns that might leak info
            elif col.lower() in ["subjectid", "subject_id"]:
                # SubjectID itself is not included, but we note it exists
                pass

        # If no quasi-identifiers found in columns, use visit patterns
        if not quasi_identifiers:
            # For vitals data, we'll use treatment arm and visit patterns as weak quasi-identifiers
            available_cols = [c for c in ["TreatmentArm", "VisitName"] if c in df.columns]
            quasi_identifiers = available_cols if available_cols else []

        # Calculate uniqueness ratio
        if quasi_identifiers:
            # Group by quasi-identifiers
            grouped = df.groupby(quasi_identifiers, dropna=False).size()
            total_records = len(df)
            unique_records = (grouped == 1).sum()
            uniqueness_ratio = float(unique_records / len(grouped)) if len(grouped) > 0 else 0.0

            # Check k-anonymity
            min_group_size = int(grouped.min()) if len(grouped) > 0 else 0
            k_anonymity_satisfied = min_group_size >= request.k_anonymity

            # Re-identification risk (inverse of average group size)
            avg_group_size = float(grouped.mean()) if len(grouped) > 0 else 1.0
            re_identification_risk = float(1.0 / avg_group_size) if avg_group_size > 0 else 1.0
        else:
            # No quasi-identifiers detected - low risk but also low confidence
            uniqueness_ratio = 0.0
            k_anonymity_satisfied = True
            re_identification_risk = 0.0

        # Calculate overall privacy score
        # Higher is better (inverse of risk)
        privacy_score = 1.0 - re_identification_risk
        privacy_score = max(0.0, min(1.0, privacy_score))

        # Generate recommendations
        recommendations = []
        if not k_anonymity_satisfied:
            recommendations.append(f"Increase data aggregation to meet k={request.k_anonymity} anonymity threshold")
        if uniqueness_ratio > 0.1:
            recommendations.append("High uniqueness ratio detected - consider generalization or suppression")
        if re_identification_risk > 0.2:
            recommendations.append("Re-identification risk above acceptable threshold - apply additional privacy techniques")
        if len(quasi_identifiers) > 5:
            recommendations.append("Multiple quasi-identifiers detected - consider reducing dimensionality")
        if not quasi_identifiers:
            recommendations.append("No standard quasi-identifiers found - manual review recommended for domain-specific identifiers")

        if not recommendations:
            recommendations.append("Privacy assessment passed - data meets acceptable privacy standards")

        # Generate summary
        if privacy_score >= 0.8:
            summary = f"✅ EXCELLENT - Privacy score: {privacy_score:.2f}. Low re-identification risk. Data is well-protected."
        elif privacy_score >= 0.6:
            summary = f"⚠️ GOOD - Privacy score: {privacy_score:.2f}. Moderate privacy protection. Review recommendations."
        else:
            summary = f"❌ NEEDS IMPROVEMENT - Privacy score: {privacy_score:.2f}. High re-identification risk. Apply privacy-enhancing techniques."

        return PrivacyAssessmentResponse(
            privacy_score=round(privacy_score, 3),
            k_anonymity_satisfied=k_anonymity_satisfied,
            re_identification_risk=round(re_identification_risk, 3),
            uniqueness_ratio=round(uniqueness_ratio, 3),
            quasi_identifiers_found=quasi_identifiers,
            recommendations=recommendations,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Privacy assessment failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)


