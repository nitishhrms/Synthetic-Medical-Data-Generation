"""
Security Service - Critical for HIPAA Compliance
Handles authentication, authorization, encryption, audit logging, and PHI detection
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import uvicorn
from sqlalchemy.orm import Session

import auth
import models
import database
from encryption import encrypt_phi, decrypt_phi
from audit import log_audit_event, get_audit_logs
from phi_detection import lint_for_phi

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Security Service",
    description="HIPAA-Compliant Security, Authentication, and Audit Logging",
    version="1.0.0"
)

# CORS configuration - use environment variable for allowed origins
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "*"  # Default to wildcard for development, but should be restricted in production
).split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]

# Warn if using wildcard in production
if "*" in ALLOWED_ORIGINS and os.getenv("ENVIRONMENT") == "production":
    import warnings
    warnings.warn(
        "WARNING: CORS wildcard (*) is enabled in production. "
        "This is a security risk. Set ALLOWED_ORIGINS environment variable.",
        UserWarning
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

security = HTTPBearer()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current authenticated user"""
    try:
        payload = auth.verify_token(credentials.credentials)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    roles: List[str]

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    roles: Optional[List[str]] = None
    expires_at: Optional[datetime] = None

class EncryptRequest(BaseModel):
    data: str = Field(..., description="PHI data to encrypt")

class EncryptResponse(BaseModel):
    encrypted_data: str
    algorithm: str = "Fernet (AES-128 CBC)"

class DecryptRequest(BaseModel):
    encrypted_data: str = Field(..., description="Encrypted data to decrypt")

class DecryptResponse(BaseModel):
    decrypted_data: str

class PHIDetectionRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to check for PHI (dict or list of dicts)")

class PHIDetectionResponse(BaseModel):
    has_phi: bool
    findings: List[str]
    safe_to_process: bool

class AuditLogQuery(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "security-service",
        "timestamp": datetime.utcnow().isoformat(),
        "hipaa_compliant": True
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Security Service",
        "version": "1.0.0",
        "features": [
            "JWT Authentication",
            "HIPAA Audit Logging",
            "PHI Encryption",
            "PHI Detection",
            "Authorization"
        ],
        "endpoints": {
            "auth": "/auth/login",
            "validate": "/auth/validate",
            "encrypt": "/encryption/encrypt",
            "decrypt": "/encryption/decrypt",
            "phi_check": "/phi/detect",
            "audit": "/audit/logs",
            "docs": "/docs"
        }
    }

# Authentication Endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token
    
    HIPAA Requirement: All access must be authenticated
    """
    user = auth.authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Log authentication event
    await log_audit_event(
        db=db,
        user_id=str(user["user_id"]),
        action="LOGIN",
        resource="security-service",
        details={"ip": "0.0.0.0"}  # Would extract from request in production
    )
    
    token = auth.create_access_token(user)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=str(user["user_id"]),
        roles=user.get("roles", [])
    )

@app.post("/auth/validate", response_model=TokenValidationResponse)
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate JWT token
    
    Used by API Gateway to verify tokens
    """
    try:
        payload = auth.verify_token(credentials.credentials)
        return TokenValidationResponse(
            valid=True,
            user_id=payload.get("sub"),
            roles=payload.get("roles", []),
            expires_at=datetime.fromtimestamp(payload.get("exp", 0))
        )
    except Exception as e:
        return TokenValidationResponse(valid=False)

@app.get("/auth/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "user_id": current_user.get("sub"),
        "roles": current_user.get("roles", []),
        "authenticated": True
    }

# Encryption Endpoints
@app.post("/encryption/encrypt", response_model=EncryptResponse)
async def encrypt_data(
    request: EncryptRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Encrypt PHI (Protected Health Information)
    
    HIPAA Requirement: Encryption at rest for PHI
    """
    try:
        encrypted = encrypt_phi(request.data)
        
        # Log encryption event
        await log_audit_event(
            db=db,
            user_id=current_user.get("sub"),
            action="ENCRYPT",
            resource="phi_data",
            details={"algorithm": "Fernet (AES-128 CBC)"}
        )
        
        return EncryptResponse(encrypted_data=encrypted)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption failed: {str(e)}"
        )

@app.post("/encryption/decrypt", response_model=DecryptResponse)
async def decrypt_data(
    request: DecryptRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Decrypt PHI data
    
    HIPAA Requirement: Decryption requires authentication and authorization
    """
    try:
        # Check authorization (only authorized users can decrypt)
        if "data_analyst" not in current_user.get("roles", []) and "admin" not in current_user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to decrypt PHI"
            )
        
        decrypted = decrypt_phi(request.encrypted_data)
        
        # Log decryption event (critical audit requirement)
        await log_audit_event(
            db=db,
            user_id=current_user.get("sub"),
            action="DECRYPT",
            resource="phi_data",
            details={"algorithm": "Fernet (AES-128 CBC)"}
        )
        
        return DecryptResponse(decrypted_data=decrypted)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decryption failed: {str(e)}"
        )

# PHI Detection Endpoint
@app.post("/phi/detect", response_model=PHIDetectionResponse)
async def detect_phi(
    request: PHIDetectionRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect potential PHI in data
    
    HIPAA Requirement: Block PHI uploads to prevent accidental exposure
    """
    try:
        has_phi, findings = lint_for_phi(request.data)
        
        # Log PHI check event
        await log_audit_event(
            db=db,
            user_id=current_user.get("sub"),
            action="PHI_CHECK",
            resource="data_upload",
            details={"has_phi": has_phi, "findings_count": len(findings)}
        )
        
        return PHIDetectionResponse(
            has_phi=not has_phi,  # lint_for_phi returns (ok, findings)
            findings=findings,
            safe_to_process=has_phi
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PHI detection failed: {str(e)}"
        )

# Audit Logging Endpoints
@app.post("/audit/log")
async def create_audit_log(
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create audit log entry
    
    HIPAA Requirement: Immutable audit trail of all access
    """
    await log_audit_event(
        db=db,
        user_id=current_user.get("sub"),
        action=action,
        resource=resource,
        details=details or {}
    )
    return {"status": "logged", "timestamp": datetime.utcnow().isoformat()}

@app.get("/audit/logs")
async def get_audit_logs_endpoint(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    limit: int = 100,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit logs
    
    HIPAA Requirement: Audit logs must be accessible for compliance reviews
    """
    # Only admins can view audit logs
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )
    
    logs = await get_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        resource=resource,
        limit=limit
    )
    return logs

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
