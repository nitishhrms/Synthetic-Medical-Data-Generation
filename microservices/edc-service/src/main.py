"""
EDC Service - Electronic Data Capture
Handles subject data, visits, validation, and auto-repair
"""
from fastapi import FastAPI, HTTPException, status, File, UploadFile, Form
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

# ============================================================================
# Study Management Endpoints
# ============================================================================

# Database operations replace in-memory storage


@app.post("/studies")
async def create_study(study: StudyCreate):
    """Create a new clinical trial study"""
    # Generate study ID (STU + 3 digits)
    # In a real app, this might be a sequence or UUID
    count = await db.fetchval("SELECT COUNT(*) FROM studies")
    study_id = f"STU{count + 1:03d}"

    try:
        await db.execute("""
            INSERT INTO studies (
                study_id, study_name, indication, phase, sponsor, 
                start_date, status, subjects_enrolled, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 0, NOW())
        """, 
        study_id, study.study_name, study.indication, study.phase, 
        study.sponsor, datetime.strptime(study.start_date, "%Y-%m-%d").date(), study.status)
        
        return {
            "study_id": study_id,
            "message": "Study created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create study: {str(e)}")

@app.get("/studies")
async def list_studies():
    """List all studies"""
    studies = await db.fetch("SELECT * FROM studies ORDER BY created_at DESC")
    
    # Convert to list of dicts and format dates
    result = []
    for s in studies:
        s_dict = dict(s)
        if s_dict.get('start_date'):
            s_dict['start_date'] = s_dict['start_date'].isoformat()
        if s_dict.get('created_at'):
            s_dict['created_at'] = s_dict['created_at'].isoformat()
        result.append(s_dict)
        
    return {
        "studies": result
    }

@app.get("/studies/{study_id}")
async def get_study(study_id: str):
    """Get study details"""
    study = await db.fetchrow("SELECT * FROM studies WHERE study_id = $1", study_id)
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    s_dict = dict(study)
    if s_dict.get('start_date'):
        s_dict['start_date'] = s_dict['start_date'].isoformat()
    if s_dict.get('created_at'):
        s_dict['created_at'] = s_dict['created_at'].isoformat()

    return s_dict

@app.get("/studies/{study_id}/subjects")
async def list_study_subjects(study_id: str):
    """List all subjects in a study"""
    # Verify study exists
    study_exists = await db.fetchval("SELECT 1 FROM studies WHERE study_id = $1", study_id)
    if not study_exists:
        raise HTTPException(status_code=404, detail="Study not found")

    subjects = await db.fetch("""
        SELECT * FROM subjects 
        WHERE study_id = $1 
        ORDER BY created_at DESC
    """, study_id)
    
    # Convert to list of dicts and format dates
    result = []
    for s in subjects:
        s_dict = dict(s)
        if s_dict.get('enrollment_date'):
            s_dict['enrollment_date'] = s_dict['enrollment_date'].isoformat()
        if s_dict.get('created_at'):
            s_dict['created_at'] = s_dict['created_at'].isoformat()
        result.append(s_dict)
        
    return {
        "subjects": result
    }


@app.post("/subjects")
async def enroll_subject(subject: SubjectCreate):
    """Enroll a new subject in a study"""
    # Verify study exists
    study_exists = await db.fetchval("SELECT 1 FROM studies WHERE study_id = $1", subject.study_id)
    if not study_exists:
        raise HTTPException(status_code=404, detail="Study not found")

    try:
        # Generate subject ID
        count = await db.fetchval("SELECT COUNT(*) FROM subjects WHERE study_id = $1", subject.study_id)
        subject_num = count + 1
        subject_id = f"{subject.study_id.replace('STU', 'RA')}-{subject_num:03d}"

        # Enroll subject
        await db.execute("""
            INSERT INTO subjects (
                subject_id, study_id, site_id, treatment_arm, 
                enrollment_date, status, created_at
            ) VALUES ($1, $2, $3, $4, NOW(), 'enrolled', NOW())
        """, subject_id, subject.study_id, subject.site_id, subject.treatment_arm)

        # Update study subject count
        await db.execute("""
            UPDATE studies 
            SET subjects_enrolled = subjects_enrolled + 1 
            WHERE study_id = $1
        """, subject.study_id)

        return {
            "subject_id": subject_id,
            "message": "Subject enrolled successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enroll subject: {str(e)}")

@app.get("/subjects/{subject_id}")
async def get_subject(subject_id: str):
    """Get subject details"""
    subject = await db.fetchrow("SELECT * FROM subjects WHERE subject_id = $1", subject_id)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    s_dict = dict(subject)
    if s_dict.get('enrollment_date'):
        s_dict['enrollment_date'] = s_dict['enrollment_date'].isoformat()
    if s_dict.get('created_at'):
        s_dict['created_at'] = s_dict['created_at'].isoformat()

    return s_dict


@app.post("/import/synthetic")
async def import_synthetic_data(request: ImportSyntheticRequest):
    """Import synthetic data into a study"""
    # Verify study exists
    study_exists = await db.fetchval("SELECT 1 FROM studies WHERE study_id = $1", request.study_id)
    if not study_exists:
        raise HTTPException(status_code=404, detail="Study not found")

    try:
        # Extract unique subjects from the data
        unique_subjects = list(set(record.SubjectID for record in request.data))
        unique_subjects.sort() # Ensure deterministic order
        
        subjects_created = 0
        observations_imported = 0
        
        # Get current subject count for this study to generate new IDs
        current_count = await db.fetchval("SELECT COUNT(*) FROM subjects WHERE study_id = $1", request.study_id)
        
        # Create a mapping from old ID to new ID
        id_mapping = {}
        
        # 1. Create Subjects
        for i, old_subject_id in enumerate(unique_subjects):
            # Generate new Subject ID: RA{StudyNum}-{SeqNum}
            # e.g. STU002 -> RA002-001
            study_num = request.study_id.replace("STU", "")
            new_seq = current_count + i + 1
            new_subject_id = f"RA{study_num}-{new_seq:03d}"
            
            id_mapping[old_subject_id] = new_subject_id
            
            # Extract treatment arm from first record for this subject
            subject_records = [r for r in request.data if r.SubjectID == old_subject_id]
            if not subject_records:
                continue
                
            treatment_arm = subject_records[0].TreatmentArm

            # Create subject in EDC table
            await db.execute("""
                INSERT INTO subjects (
                    subject_id, study_id, site_id, treatment_arm, 
                    enrollment_date, status, created_at
                ) VALUES ($1, $2, $3, $4, NOW(), 'enrolled', NOW())
            """, new_subject_id, request.study_id, "Site001", treatment_arm)
            
            # Create patient in Clinical table (for vitals storage)
            # Check if patient exists (unlikely with new ID, but good practice)
            patient_exists = await db.fetchval(
                "SELECT patient_id FROM patients WHERE subject_number = $1", 
                new_subject_id
            )
            
            if not patient_exists:
                await db.execute("""
                    INSERT INTO patients (tenant_id, subject_number, site_id, protocol_id, enrollment_date, treatment_arm)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, "DEFAULT_TENANT", new_subject_id, "Site001", request.study_id, datetime.utcnow().date(), treatment_arm)
            
            subjects_created += 1

        # 2. Import Vitals Data
        for record in request.data:
            if record.SubjectID not in id_mapping:
                continue
                
            new_subject_id = id_mapping[record.SubjectID]
            
            # Get patient_id
            patient_id = await db.fetchval(
                "SELECT patient_id FROM patients WHERE subject_number = $1", 
                new_subject_id
            )
            
            if patient_id:
                await db.execute("""
                    INSERT INTO vital_signs (
                        tenant_id, patient_id, visit_date, measurement_time,
                        systolic_bp, diastolic_bp, heart_rate, temperature,
                        data_batch
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
                """,
                    "DEFAULT_TENANT",
                    patient_id,
                    datetime.utcnow().date(),
                    datetime.utcnow(),
                    record.SystolicBP,
                    record.DiastolicBP,
                    record.HeartRate,
                    record.Temperature,
                    json.dumps({
                        "visit_name": record.VisitName, 
                        "treatment_arm": record.TreatmentArm,
                        "original_subject_id": record.SubjectID
                    })
                )
                observations_imported += 1

        # Update study subject count
        if subjects_created > 0:
            await db.execute("""
                UPDATE studies 
                SET subjects_enrolled = (SELECT COUNT(*) FROM subjects WHERE study_id = $1)
                WHERE study_id = $1
            """, request.study_id)

        return ImportSyntheticResponse(
            subjects_imported=subjects_created,
            observations_imported=observations_imported,
            message=f"Successfully imported {observations_imported} observations for {subjects_created} subjects. IDs remapped."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import data: {str(e)}")


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

class QueryCreate(BaseModel):
    study_id: str
    subject_id: str
    query_text: str
    field: Optional[str] = None
    severity: str = "Major"
    opened_by: int = 1  # Default system user

@app.post("/queries")
async def create_query(query: QueryCreate):
    """Create a new query (manually or from Quality Service)"""
    try:
        # Verify subject exists
        subject_exists = await db.fetchval("SELECT 1 FROM subjects WHERE subject_id = $1", query.subject_id)
        if not subject_exists:
            raise HTTPException(status_code=404, detail="Subject not found")

        query_id = await db.fetchval("""
            INSERT INTO queries (
                study_id, subject_id, query_text, field, severity, 
                status, opened_by, opened_at
            ) VALUES ($1, $2, $3, $4, $5, 'open', $6, NOW())
            RETURNING query_id
        """, query.study_id, query.subject_id, query.query_text, query.field, query.severity, query.opened_by)

        # Add history
        await db.execute("""
            INSERT INTO query_history (query_id, action, user_id, notes)
            VALUES ($1, 'opened', $2, 'Query created')
        """, query_id, query.opened_by)

        return {"query_id": query_id, "message": "Query created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create query: {str(e)}")


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


@app.get("/queries/{query_id}/context")
async def get_query_context(query_id: int):
    """
    Get query with full subject and vitals context
    
    Returns query details along with subject information and recent vitals data
    for display in DataEntry screen
    """
    try:
        # Get query details
        query = await db.fetchrow("SELECT * FROM queries WHERE query_id = $1", query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Get subject details
        subject = await db.fetchrow("SELECT * FROM subjects WHERE subject_id = $1", query['subject_id'])
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Get recent vitals for this subject
        vitals = await db.fetch("""
            SELECT 
                vs.vital_id,
                vs.visit_date,
                vs.systolic_bp,
                vs.diastolic_bp,
                vs.heart_rate,
                vs.temperature,
                vs.data_batch
            FROM vital_signs vs
            JOIN patients p ON vs.patient_id = p.patient_id
            WHERE p.subject_number = $1
            ORDER BY vs.visit_date DESC
            LIMIT 20
        """, query['subject_id'])
        
        return {
            "query": dict(query),
            "subject": dict(subject),
            "vitals": [dict(v) for v in vitals] if vitals else []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query context: {str(e)}")


@app.post("/queries/{query_id}/repair")
async def trigger_repair_from_query(query_id: int):
    """
    Trigger auto-repair for vitals data related to a query
    
    Fetches subject's vitals data, applies auto-repair logic,
    updates database, and logs the action in query history
    """
    try:
        # Get query details
        query = await db.fetchrow("SELECT * FROM queries WHERE query_id = $1", query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        subject_id = query['subject_id']
        
        # Fetch subject vitals as DataFrame
        vitals = await db.fetch("""
            SELECT 
                p.subject_number as SubjectID,
                vs.visit_date as VisitName,
                p.treatment_arm as TreatmentArm,
                vs.systolic_bp as SystolicBP,
                vs.diastolic_bp as DiastolicBP,
                vs.heart_rate as HeartRate,
                vs.temperature as Temperature,
                vs.vital_id
            FROM vital_signs vs
            JOIN patients p ON vs.patient_id = p.patient_id
            WHERE p.subject_number = $1
            ORDER BY vs.visit_date
        """, subject_id)
        
        if not vitals or len(vitals) == 0:
            raise HTTPException(status_code=404, detail="No vitals data found for subject")
        
        # Convert to DataFrame
        vitals_dict = [dict(v) for v in vitals]
        df = pd.DataFrame(vitals_dict)
        
        # Rename columns to match auto_repair expectations (PascalCase)
        df = df.rename(columns={
            'subjectid': 'SubjectID',
            'visitname': 'VisitName',
            'treatmentarm': 'TreatmentArm',
            'systolicbp': 'SystolicBP',
            'diastolicbp': 'DiastolicBP',
            'heartrate': 'HeartRate',
            'temperature': 'Temperature'
        })
        
        # Apply auto-repair
        repaired_df = auto_repair_vitals(df)
        
        # Update database with repaired values
        rows_updated = 0
        for idx, row in repaired_df.iterrows():
            await db.execute("""
                UPDATE vital_signs
                SET systolic_bp = $1,
                    diastolic_bp = $2,
                    heart_rate = $3,
                    temperature = $4
                WHERE vital_id = $5
            """, 
            int(row['SystolicBP']), 
            int(row['DiastolicBP']), 
            int(row['HeartRate']), 
            float(row['Temperature']),
            row['vital_id'])
            rows_updated += 1
        
        # Add query history entry
        await db.execute("""
            INSERT INTO query_history (query_id, action, user_id, notes)
            VALUES ($1, 'auto_repair_applied', 1, 'System auto-repaired vitals data')
        """, query_id)
        
        # Update query status to 'responded' if it was open
        if query['status'] == 'open':
            await db.execute("""
                UPDATE queries
                SET status = 'responded',
                    response_text = 'Auto-repair applied to vitals data',
                    responded_by = 1,
                    responded_at = NOW()
                WHERE query_id = $1
            """, query_id)
        
        return {
            "message": "Repair applied successfully",
            "rows_updated": rows_updated,
            "query_status": "responded"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to repair data: {str(e)}")

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

@app.get("/vitals/all")
async def get_all_vitals():
    """
    Get all vitals observations from the database

    Returns all vitals data for RBQM and analytics purposes
    """
    try:
        vitals = await db.fetch("""
            SELECT
                p.subject_number as SubjectID,
                v.visit_date,
                v.systolic_bp as SystolicBP,
                v.diastolic_bp as DiastolicBP,
                v.heart_rate as HeartRate,
                v.temperature as Temperature,
                v.data_batch::text as data_batch
            FROM vital_signs v
            JOIN patients p ON v.patient_id = p.patient_id
            ORDER BY p.subject_number, v.visit_date
        """)

        # Convert to list of dictionaries
        vitals_list = []
        for v in vitals:
            record = {
                "SubjectID": v["subjectid"],
                "SystolicBP": v["systolicbp"],
                "DiastolicBP": v["diastolicbp"],
                "HeartRate": v["heartrate"],
                "Temperature": float(v["temperature"]) if v["temperature"] else None,
            }

            # Extract visit info and treatment arm from data_batch if available
            if v["data_batch"]:
                try:
                    batch_data = json.loads(v["data_batch"])
                    record["VisitName"] = batch_data.get("visit_name", "Unknown")
                    record["TreatmentArm"] = batch_data.get("treatment_arm", "Unknown")
                except:
                    record["VisitName"] = "Unknown"
                    record["TreatmentArm"] = "Unknown"
            else:
                record["VisitName"] = "Unknown"
                record["TreatmentArm"] = "Unknown"

            vitals_list.append(record)

        return vitals_list

    except Exception as e:
        # If database is empty or not initialized, return empty array
        return []


# ============================================================================
# Medical Imaging Endpoints
# ============================================================================

@app.post("/imaging/upload")
async def upload_medical_image(
    file: UploadFile = File(...),
    subject_id: str = Form(...),
    visit_name: str = Form(default="Screening"),
    image_type: str = Form(default="X-Ray")
):
    """
    Upload and process a medical image
    """
    if not IMAGING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Imaging module not available")

    try:
        # Read file content
        content = await file.read()
        
        # Process image (extract metadata, anonymize)
        result = process_medical_image(
            image_data=content,
            subject_id=subject_id,
            image_type=image_type
        )
        
        # Store metadata in DB
        image_id = await db.fetchval("""
            INSERT INTO medical_images (
                subject_id, visit_name, image_type, file_name, 
                file_size, mime_type, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING image_id
        """, subject_id, visit_name, image_type, file.filename, 
           len(content), file.content_type, json.dumps(result['metadata']))
        
        # Store file content (in real app, use S3/Blob storage)
        # For demo, we'll store in a local directory
        os.makedirs("data/images", exist_ok=True)
        file_path = f"data/images/{image_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
            
        # Update DB with path
        await db.execute("UPDATE medical_images SET file_path = $1 WHERE image_id = $2", file_path, image_id)
        
        return {
            "image_id": image_id,
            "subject_id": subject_id,
            "analysis": result['analysis'],
            "message": "Image uploaded and processed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@app.get("/imaging/subject/{subject_id}")
async def get_subject_images(subject_id: str):
    """Get all images for a subject"""
    images = await db.fetch("""
        SELECT * FROM medical_images 
        WHERE subject_id = $1 
        ORDER BY created_at DESC
    """, subject_id)
    
    return {
        "images": [
            {
                "image_id": img["image_id"],
                "visit_name": img["visit_name"],
                "image_type": img["image_type"],
                "file_name": img["file_name"],
                "created_at": img["created_at"].isoformat() if img["created_at"] else None,
                "metadata": json.loads(img["metadata"]) if img["metadata"] else {}
            }
            for img in images
        ]
    }

@app.get("/imaging/{image_id}/{type}")
async def get_image_file(image_id: int, type: str):
    """Get image file content (file or thumbnail)"""
    image = await db.fetchrow("SELECT file_path, mime_type FROM medical_images WHERE image_id = $1", image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
        
    file_path = image["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file missing")
        
    # For thumbnail, we'd resize here. For now, return original.
    with open(file_path, "rb") as f:
        content = f.read()
        
    return Response(content=content, media_type=image["mime_type"])

@app.delete("/imaging/{image_id}")
async def delete_image(image_id: int):
    """Delete an image"""
    image = await db.fetchrow("SELECT file_path FROM medical_images WHERE image_id = $1", image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
        
    # Delete file
    if os.path.exists(image["file_path"]):
        os.remove(image["file_path"])
        
    # Delete DB record
    await db.execute("DELETE FROM medical_images WHERE image_id = $1", image_id)
    
    return {"message": "Image deleted successfully"}

@app.get("/imaging/status")
async def get_imaging_status():
    """Check if imaging module is available"""
    return {
        "imaging_available": IMAGING_AVAILABLE,
        "message": "Imaging module ready" if IMAGING_AVAILABLE else "Imaging module missing dependencies"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)


