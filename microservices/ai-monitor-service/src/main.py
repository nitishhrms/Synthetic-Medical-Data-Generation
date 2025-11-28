from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from datetime import datetime

app = FastAPI(title="AI Medical Monitor Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
EDC_SERVICE_URL = os.getenv("EDC_SERVICE_URL", "http://localhost:8001")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Use whichever API key is available
USE_OPENAI = bool(OPENAI_API_KEY)
USE_ANTHROPIC = bool(ANTHROPIC_API_KEY) and not USE_OPENAI

# Models
class SubjectReviewRequest(BaseModel):
    study_id: str
    subject_id: str

class StudyReviewRequest(BaseModel):
    study_id: str
    max_subjects: Optional[int] = 10  # Limit for demo purposes

class AIFinding(BaseModel):
    subject_id: str
    issue_description: str
    severity: str  # "info", "warning", "error", "critical"
    suggested_action: str
    field_name: Optional[str] = None

class ReviewResponse(BaseModel):
    study_id: str
    reviewed_at: str
    findings: List[AIFinding]
    subjects_reviewed: int

# Simple LLM integration
async def call_llm(prompt: str) -> str:
    """Call LLM API (OpenAI or Anthropic) with simple error handling"""
    
    if USE_OPENAI:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "You are an expert medical monitor reviewing clinical trial data. Identify potential issues, inconsistencies, or safety concerns."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    
    elif USE_ANTHROPIC:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 500,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "system": "You are an expert medical monitor reviewing clinical trial data. Identify potential issues, inconsistencies, or safety concerns."
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()["content"][0]["text"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")
    
    else:
        # Fallback: return mock findings for demo without API key
        return """FINDINGS:
1. Subject vital signs show BP of 250/140 - CRITICAL - Requires immediate verification
2. Heart rate of 45 bpm is below normal range - WARNING - Check if patient is on beta blockers
3. Temperature reading missing for Visit 2 - INFO - Request data completion"""

def parse_llm_response(llm_output: str, subject_id: str) -> List[AIFinding]:
    """Parse LLM output into structured findings"""
    findings = []
    
    # Simple parsing logic
    lines = llm_output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.lower().startswith('findings'):
            continue
        
        # Try to extract severity
        severity = "warning"
        if "CRITICAL" in line.upper() or "SEVERE" in line.upper():
            severity = "critical"
        elif "ERROR" in line.upper() or "INVALID" in line.upper():
            severity = "error"
        elif "WARNING" in line.upper() or "CONCERN" in line.upper():
            severity = "warning"
        elif "INFO" in line.upper() or "NOTE" in line.upper():
            severity = "info"
        
        # Extract description (remove numbering and severity tags)
        description = line
        for prefix in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-", "*"]:
            if description.startswith(prefix):
                description = description[len(prefix):].strip()
        
        for tag in ["CRITICAL", "ERROR", "WARNING", "INFO", "SEVERE"]:
            description = description.replace(f" - {tag} - ", " - ")
            description = description.replace(f"- {tag} -", "-")
        
        if description:
            findings.append(AIFinding(
                subject_id=subject_id,
                issue_description=description,
                severity=severity,
                suggested_action="Review and verify data accuracy"
            ))
    
    return findings

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "llm_provider": "openai" if USE_OPENAI else "anthropic" if USE_ANTHROPIC else "mock",
        "edc_service": EDC_SERVICE_URL
    }

@app.post("/review/subject", response_model=ReviewResponse)
async def review_subject(request: SubjectReviewRequest):
    """AI reviews a single subject's data"""
    
    # Fetch subject data from EDC
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EDC_SERVICE_URL}/subjects/{request.subject_id}",
                timeout=10.0
            )
            response.raise_for_status()
            subject_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subject data: {str(e)}")
    
    # Create prompt for LLM
    prompt = f"""Review the following clinical trial subject data and identify any issues:

Subject ID: {subject_data.get('subject_id')}
Study ID: {subject_data.get('study_id')}
Site: {subject_data.get('site_id')}
Enrollment Date: {subject_data.get('enrollment_date')}
Status: {subject_data.get('status')}

Please list any potential issues, concerns, or data quality problems. Format each finding on a new line.
Focus on: missing data, out-of-range values, inconsistencies, safety concerns.
"""
    
    # Call LLM
    llm_response = await call_llm(prompt)
    
    # Parse findings
    findings = parse_llm_response(llm_response, request.subject_id)
    
    return ReviewResponse(
        study_id=request.study_id,
        reviewed_at=datetime.utcnow().isoformat(),
        findings=findings,
        subjects_reviewed=1
    )

@app.post("/review/study", response_model=ReviewResponse)
async def review_study(request: StudyReviewRequest):
    """AI reviews all subjects in a study"""
    
    # Fetch subjects from EDC
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EDC_SERVICE_URL}/studies/{request.study_id}/subjects",
                timeout=10.0
            )
            response.raise_for_status()
            subjects_data = response.json()
            subjects = subjects_data.get("subjects", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch study subjects: {str(e)}")
    
    # Limit subjects for demo
    subjects = subjects[:request.max_subjects]
    
    all_findings = []
    
    # Review each subject
    for subject in subjects:
        subject_id = subject.get("subject_id")
        
        # Create simple prompt
        prompt = f"""Review this clinical trial subject:

Subject ID: {subject_id}
Site: {subject.get('site_id')}
Status: {subject.get('status')}
Enrollment: {subject.get('enrollment_date')}

Identify any issues (1-2 sentences max). Focus on data quality and safety."""
        
        # Call LLM
        llm_response = await call_llm(prompt)
        
        # Parse findings
        findings = parse_llm_response(llm_response, subject_id)
        all_findings.extend(findings)
    
    return ReviewResponse(
        study_id=request.study_id,
        reviewed_at=datetime.utcnow().isoformat(),
        findings=all_findings,
        subjects_reviewed=len(subjects)
    )

@app.post("/review/study/post-queries")
async def review_and_post_queries(request: StudyReviewRequest):
    """AI reviews study and automatically posts queries to EDC"""
    
    # Get review findings
    review = await review_study(request)
    
    # Post each finding as a query to EDC
    posted_queries = []
    errors = []
    
    async with httpx.AsyncClient() as client:
        for finding in review.findings:
            try:
                # 1. Check if subject exists
                try:
                    subject_check = await client.get(
                        f"{EDC_SERVICE_URL}/subjects/{finding.subject_id}",
                        timeout=5.0
                    )
                    subject_exists = subject_check.status_code == 200
                except:
                    subject_exists = False
                
                # 2. Create subject if doesn't exist (Placeholder)
                if not subject_exists:
                    print(f"Subject {finding.subject_id} not found. Creating placeholder.")
                    try:
                        await client.post(
                            f"{EDC_SERVICE_URL}/subjects",
                            json={
                                "study_id": request.study_id,
                                "subject_id": finding.subject_id, # This might be ignored by EDC if it generates IDs, but good to try
                                "site_id": "AI-MONITOR",
                                "treatment_arm": "Unknown"
                            },
                            timeout=5.0
                        )
                    except Exception as e:
                        print(f"Failed to create placeholder subject: {e}")
                        # Continue anyway, query creation might fail but we tried
                
                # 3. Post Query
                query_payload = {
                    "study_id": request.study_id,
                    "subject_id": finding.subject_id,
                    "query_text": f"[AI Monitor] {finding.issue_description}",
                    "severity": finding.severity,
                    "field": finding.field_name or "general"
                }
                
                response = await client.post(
                    f"{EDC_SERVICE_URL}/queries",
                    json=query_payload,
                    timeout=10.0
                )
                response.raise_for_status()
                posted_queries.append(response.json())
            except Exception as e:
                error_msg = f"Failed to post query for {finding.subject_id}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
    
    return {
        "review": review,
        "queries_posted": len(posted_queries),
        "queries": posted_queries,
        "errors": errors
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
