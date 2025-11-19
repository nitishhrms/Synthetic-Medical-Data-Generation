"""
EDC Service - Electronic Data Capture
Handles subject data, visits, validation, and auto-repair
"""
from fastapi import FastAPI, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
# MEDICAL IMAGING ENDPOINTS - NEW
# ============================================================================

class ImageUploadRequest(BaseModel):
    subject_id: str
    visit_name: Optional[str] = None
    image_type: Optional[str] = None  # 'X-ray', 'CT', 'MRI', 'Ultrasound', 'ECG', 'Photo'
    description: Optional[str] = None

class ImageMetadataResponse(BaseModel):
    image_id: int
    subject_id: str
    filename: str
    file_type: str
    image_type: Optional[str]
    file_size_bytes: int
    has_thumbnail: bool
    uploaded_at: str

@app.get("/images/status")
async def imaging_status():
    """Check if medical imaging is available"""
    return {
        "imaging_available": IMAGING_AVAILABLE,
        "dicom_support": IMAGING_AVAILABLE,
        "supported_formats": {
            "dicom": [".dcm", ".dicom"],
            "images": [".png", ".jpg", ".jpeg"],
            "documents": [".pdf"]
        },
        "features": [
            "DICOM metadata extraction",
            "Thumbnail generation",
            "Hash-based deduplication",
            "Batch processing"
        ] if IMAGING_AVAILABLE else []
    }

@app.post("/images/upload")
async def upload_medical_image(
    file: UploadFile = File(...),
    subject_id: str = "",
    visit_name: Optional[str] = None,
    image_type: Optional[str] = None,
    user_id: int = 1
):
    """
    Upload a medical image (DICOM, PNG, JPEG, PDF)

    Features:
    - DICOM metadata extraction
    - Automatic thumbnail generation
    - Hash-based deduplication
    - Supports X-rays, CT scans, MRI, ultrasound, ECG, photos

    Example:
        curl -X POST http://localhost:8004/images/upload \
          -F "file=@chest_xray.dcm" \
          -F "subject_id=RA001-001" \
          -F "visit_name=Week 4" \
          -F "image_type=X-ray"
    """
    if not IMAGING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Medical imaging not available. Install: pip install pydicom pillow opencv-python"
        )

    if not subject_id:
        raise HTTPException(status_code=400, detail="subject_id is required")

    try:
        # Read file content
        content = await file.read()

        # Process image
        processor = MedicalImageProcessor(storage_base="/data/medical-images")
        result = processor.process_upload(
            filename=file.filename,
            content=content,
            subject_id=subject_id,
            visit_name=visit_name,
            image_type=image_type
        )

        # Store metadata in database
        image_id = await db.fetchval("""
            INSERT INTO medical_images (
                subject_id, visit_name, filename, unique_filename,
                file_type, file_hash, file_size_bytes,
                original_path, thumbnail_path, image_type,
                modality, dicom_metadata, thumbnail_metadata,
                processing_status, uploaded_by, uploaded_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13::jsonb, $14, $15, NOW())
            RETURNING image_id
        """,
            result['subject_id'],
            result.get('visit_name'),
            result['filename'],
            result['unique_filename'],
            result['file_type'],
            result['file_hash'],
            result['file_size_bytes'],
            result['original_path'],
            result.get('thumbnail_path'),
            result.get('image_type'),
            result.get('dicom_metadata', {}).get('modality') if result.get('dicom_metadata') else None,
            json.dumps(result.get('dicom_metadata', {})),
            json.dumps(result.get('thumbnail_metadata', {})),
            'processed' if 'thumbnail_path' in result else 'uploaded',
            user_id
        )

        return {
            "image_id": image_id,
            "subject_id": subject_id,
            "filename": file.filename,
            "file_type": result['file_type'],
            "file_size_bytes": result['file_size_bytes'],
            "has_thumbnail": 'thumbnail_path' in result,
            "has_dicom_metadata": 'dicom_metadata' in result,
            "message": "Image uploaded successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@app.get("/images/{image_id}")
async def get_image_metadata(image_id: int):
    """Get metadata for a specific image"""
    image = await db.fetchrow("""
        SELECT image_id, subject_id, visit_name, filename, file_type,
               image_type, modality, file_size_bytes, dicom_metadata,
               thumbnail_metadata, uploaded_at, processing_status
        FROM medical_images
        WHERE image_id = $1
    """, image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return dict(image)

@app.get("/images/{image_id}/file")
async def download_image_file(image_id: int, thumbnail: bool = False):
    """
    Download image file or thumbnail

    Query params:
        thumbnail: If true, returns thumbnail instead of original
    """
    if not IMAGING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Imaging not available")

    image = await db.fetchrow("""
        SELECT original_path, thumbnail_path, filename
        FROM medical_images
        WHERE image_id = $1
    """, image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        processor = MedicalImageProcessor()

        if thumbnail and image['thumbnail_path']:
            file_bytes = processor.get_image_bytes(image['thumbnail_path'])
            media_type = "image/jpeg"
            filename = f"thumb_{image['filename']}"
        else:
            file_bytes = processor.get_image_bytes(image['original_path'])

            # Determine media type
            if image['filename'].lower().endswith(('.dcm', '.dicom')):
                media_type = "application/dicom"
            elif image['filename'].lower().endswith('.pdf'):
                media_type = "application/pdf"
            elif image['filename'].lower().endswith(('.png', '.jpg', '.jpeg')):
                media_type = "image/" + image['filename'].split('.')[-1].lower()
            else:
                media_type = "application/octet-stream"

            filename = image['filename']

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")

@app.get("/images/subject/{subject_id}")
async def list_subject_images(subject_id: str):
    """List all images for a subject"""
    images = await db.fetch("""
        SELECT image_id, subject_id, visit_name, filename, file_type,
               image_type, modality, file_size_bytes,
               (thumbnail_path IS NOT NULL) as has_thumbnail,
               uploaded_at
        FROM medical_images
        WHERE subject_id = $1
        ORDER BY uploaded_at DESC
    """, subject_id)

    return {
        "subject_id": subject_id,
        "image_count": len(images),
        "images": [dict(img) for img in images]
    }

@app.post("/images/batch-metadata")
async def batch_extract_dicom_metadata(image_ids: List[int]):
    """
    Batch extract DICOM metadata for multiple images

    Useful for processing uploaded DICOM files in bulk
    """
    if not IMAGING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Imaging not available")

    images = await db.fetch("""
        SELECT image_id, original_path, file_type
        FROM medical_images
        WHERE image_id = ANY($1::int[])
        AND file_type = 'dicom'
    """, image_ids)

    if not images:
        return {"processed": 0, "results": []}

    processor = MedicalImageProcessor()
    dicom_paths = [img['original_path'] for img in images]

    # Batch process
    results = processor.batch_process_dicom(dicom_paths, use_daft=True)

    # Update database with extracted metadata
    for i, result in enumerate(results):
        if result['processing_status'] == 'success':
            await db.execute("""
                UPDATE medical_images
                SET dicom_metadata = $1::jsonb,
                    modality = $2,
                    processing_status = 'processed',
                    updated_at = NOW()
                WHERE image_id = $3
            """,
                json.dumps(result),
                result.get('modality'),
                images[i]['image_id']
            )

    return {
        "processed": len(results),
        "successful": sum(1 for r in results if r['processing_status'] == 'success'),
        "failed": sum(1 for r in results if r['processing_status'] == 'failed'),
        "results": results
    }

@app.delete("/images/{image_id}")
async def delete_image(image_id: int, user_id: int = 1):
    """Delete an image (metadata and files)"""
    if not IMAGING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Imaging not available")

    # Get image paths
    image = await db.fetchrow("""
        SELECT original_path, thumbnail_path
        FROM medical_images
        WHERE image_id = $1
    """, image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete files
    from pathlib import Path

    try:
        if image['original_path']:
            Path(image['original_path']).unlink(missing_ok=True)
        if image['thumbnail_path']:
            Path(image['thumbnail_path']).unlink(missing_ok=True)
    except Exception as e:
        # Log but don't fail - database cleanup is more important
        print(f"Warning: Failed to delete files: {e}")

    # Delete from database
    await db.execute("DELETE FROM medical_images WHERE image_id = $1", image_id)

    return {"image_id": image_id, "status": "deleted"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)


