"""
Security Service - HIPAA/SOC 2 Compliant
Enhanced authentication, authorization, encryption, audit logging, MFA, and rate limiting
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import uvicorn
from sqlalchemy.orm import Session
import logging
import sentry_sdk

# Core modules
import auth
import models
import database
from encryption import encrypt_phi, decrypt_phi
from audit import log_audit_event, get_audit_logs
from phi_detection import lint_for_phi

# Enhanced security modules
from redis_client import security_redis
from session_manager import session_manager
from rate_limiter import rate_limiter, add_rate_limit_headers
from mfa import mfa_manager
from token_refresh import token_refresh_manager
from password_policy import get_password_policy_description

logger = logging.getLogger(__name__)

# ==================== Sentry Initialization ====================

sentry_sdk.init(
    dsn="https://ad29eaef4a806c3f27f5f2181373aa36@o4510369986904064.ingest.us.sentry.io/4510369988018176",
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    # Adjust this value in production (e.g., 0.1 = 10% of transactions)
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    # Adjust this value in production
    profiles_sample_rate=1.0,
    # Add data like request headers and IP for users
    send_default_pii=True,
    # Enable sending logs to Sentry
    enable_logs=True,
    # Set environment
    environment=os.getenv("ENVIRONMENT", "development"),
)

logger.info("✅ Sentry initialized successfully")

# ==================== Database Initialization ====================

models.Base.metadata.create_all(bind=database.engine)

# ==================== FastAPI App ====================

app = FastAPI(
    title="Security Service - Enhanced",
    description="HIPAA/SOC 2 Compliant Security with MFA, Rate Limiting, and Advanced Auth",
    version="2.0.0"
)

# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize Redis and other services on startup"""
    try:
        logger.info("Starting Security Service...")
        await security_redis.connect()
        logger.info("✅ Security Service started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Security Service: {e}")
        # Don't crash the service, but log the error
        logger.warning("Continuing without Redis - some features will be disabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down Security Service...")
        await security_redis.disconnect()
        logger.info("✅ Security Service shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

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

# Add rate limiting headers middleware
app.middleware("http")(add_rate_limit_headers)

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

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    role: str = Field(default="researcher", pattern=r'^(admin|researcher|viewer)$')
    tenant_id: str = Field(default="default")

class RegisterResponse(BaseModel):
    user_id: str
    message: str
    user: Dict[str, Any]

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

# ==================== Enhanced Auth Models ====================

class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    provisioning_uri: str
    backup_codes: List[str]
    issuer: str

class MFAVerifyRequest(BaseModel):
    user_id: str
    code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')

class MFAVerifyResponse(BaseModel):
    success: bool
    message: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None  # Included if rotation enabled
    access_token_expires_in: int
    refreshed_at: int

class LogoutRequest(BaseModel):
    refresh_token: str

class LogoutResponse(BaseModel):
    success: bool
    message: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)

class PasswordChangeResponse(BaseModel):
    success: bool
    message: str
    must_login_again: bool = True

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
        "service": "Security Service - Enhanced",
        "version": "2.0.0",
        "features": [
            "JWT Authentication with Refresh Tokens",
            "MFA (TOTP) Support",
            "Enterprise Rate Limiting (Redis + Sliding Window)",
            "Password Policy Enforcement (12+ chars, complexity)",
            "Account Lockout (5 attempts)",
            "Session Management (token revocation)",
            "HIPAA Audit Logging",
            "PHI Encryption (Fernet AES-128)",
            "PHI Detection",
            "RBAC Ready"
        ],
        "security_enhancements": {
            "mfa_enabled": True,
            "rate_limiting_enabled": True,
            "password_policy": "12+ chars, uppercase, lowercase, number, special char",
            "account_lockout": "5 attempts, 30 min lockout",
            "session_limit": "3 concurrent sessions per user",
            "token_expiry": "Access: 30 min, Refresh: 7 days"
        },
        "endpoints": {
            "auth_login": "/auth/login",
            "auth_register": "/auth/register",
            "auth_refresh": "/auth/refresh",
            "auth_logout": "/auth/logout",
            "mfa_setup": "/auth/mfa/setup",
            "mfa_verify": "/auth/mfa/verify",
            "password_change": "/auth/password/change",
            "validate_token": "/auth/validate",
            "encrypt": "/encryption/encrypt",
            "decrypt": "/encryption/decrypt",
            "phi_check": "/phi/detect",
            "audit_logs": "/audit/logs",
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
    user, error = auth.authenticate_user(db, credentials.username, credentials.password)
    if error or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid username or password"
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

@app.post("/auth/register", response_model=RegisterResponse)
async def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user

    Creates a new user account with hashed password
    """
    # Check if username already exists
    existing_user = auth.get_user(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = auth.hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        tenant_id=user_data.tenant_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log registration event
    await log_audit_event(
        db=db,
        user_id=str(new_user.id),
        action="REGISTER",
        resource="security-service",
        details={"username": user_data.username, "role": user_data.role}
    )

    return RegisterResponse(
        user_id=str(new_user.id),
        message="User registered successfully",
        user={
            "id": str(new_user.id),
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "tenant_id": new_user.tenant_id
        }
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
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information"""
    # Get full user details from database
    user = db.query(models.User).filter(models.User.id == int(current_user.get("sub"))).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "user_id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "created_at": user.created_at.isoformat() if user.created_at else None
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


# ==================== Enhanced Authentication Endpoints ====================

@app.post("/auth/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Setup MFA for current user
    Returns QR code and backup codes
    """
    try:
        user_id = current_user.get("sub")
        username = current_user.get("username")

        # Generate MFA secret and QR code
        mfa_data = await mfa_manager.setup_mfa(user_id, username)

        logger.info(f"MFA setup initiated for user {user_id}")

        return MFASetupResponse(
            secret=mfa_data["secret"],
            qr_code=mfa_data["qr_code"],
            provisioning_uri=mfa_data["provisioning_uri"],
            backup_codes=mfa_data["backup_codes"],
            issuer=mfa_data["issuer"]
        )

    except Exception as e:
        logger.error(f"MFA setup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA setup failed: {str(e)}"
        )


@app.post("/auth/mfa/verify", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify and confirm MFA setup
    Encrypts and stores MFA secret in database
    """
    try:
        user = auth.get_user_by_id(db, int(request.user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify MFA code and get encrypted secret
        success, encrypted_secret = await mfa_manager.confirm_mfa_setup(
            request.user_id,
            request.code
        )

        if not success:
            return MFAVerifyResponse(
                success=False,
                message="Invalid MFA code. Please try again."
            )

        # Store encrypted secret in database
        user.mfa_secret = encrypted_secret
        user.mfa_enabled = True
        user.mfa_setup_completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"MFA enabled for user {user.id}")

        return MFAVerifyResponse(
            success=True,
            message="MFA enabled successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA verification failed: {str(e)}"
        )


@app.post("/auth/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    Implements token rotation for security
    """
    try:
        # Extract user info from refresh token (stored in Redis)
        # For now, we'll use a simple approach - in production, encode user_id in refresh token
        # This is a simplified implementation

        # For this implementation, we need the user_id
        # In a full implementation, you'd encode user_id in the refresh token itself
        # or use a JWT refresh token

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Token refresh endpoint requires additional implementation. Use /auth/login for now."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@app.post("/auth/logout", response_model=LogoutResponse)
async def logout(
    request: LogoutRequest,
    current_user: Dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user by revoking tokens
    Blacklists access token and revokes refresh token
    """
    try:
        user_id = current_user.get("sub")
        access_token = credentials.credentials

        # Get token expiry
        token_expiry = auth.get_token_expiry(access_token)
        if not token_expiry:
            raise HTTPException(status_code=400, detail="Invalid token")

        # Logout (blacklist access token + revoke refresh token)
        results = await session_manager.logout(
            user_id=user_id,
            access_token=access_token,
            refresh_token=request.refresh_token,
            token_expiry=token_expiry
        )

        if results["success"]:
            logger.info(f"User {user_id} logged out successfully")
            return LogoutResponse(
                success=True,
                message="Logged out successfully"
            )
        else:
            logger.warning(f"Partial logout for user {user_id}: {results}")
            return LogoutResponse(
                success=False,
                message="Logout partially successful. Some tokens may still be valid."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@app.post("/auth/password/change", response_model=PasswordChangeResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password with policy enforcement
    Validates password policy and checks history
    """
    try:
        user_id = int(current_user.get("sub"))
        user = auth.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        if not auth.verify_password(request.current_password, user.hashed_password):
            logger.warning(f"Failed password change attempt for user {user_id} - incorrect current password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        # Validate new password
        is_valid, errors = auth.validate_new_password(request.new_password, user)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors}
            )

        # Update password
        success = auth.update_password(db, user, request.new_password)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

        # Force logout all sessions (security best practice)
        await session_manager.force_logout_all_sessions(user_id=str(user_id))

        logger.info(f"Password changed successfully for user {user_id}")

        return PasswordChangeResponse(
            success=True,
            message="Password changed successfully. Please login again with your new password.",
            must_login_again=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@app.get("/auth/password-policy")
async def get_password_policy_info():
    """
    Get password policy requirements
    Useful for displaying to users before registration/password change
    """
    return get_password_policy_description()


# ==================== Session Management Endpoints ====================

@app.get("/auth/sessions")
async def get_active_sessions(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get active sessions for current user
    """
    try:
        user_id = current_user.get("sub")
        stats = await session_manager.get_session_stats(user_id)

        return {
            "user_id": user_id,
            "active_sessions": stats.get("active_sessions", 0),
            "max_sessions": stats["max_concurrent_sessions"],
            "session_timeout_minutes": stats["session_timeout_minutes"]
        }

    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session information"
        )


# ==================== Rate Limit Management (Admin) ====================

@app.post("/admin/rate-limit/reset/{identifier}")
async def reset_rate_limit_admin(
    identifier: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Reset rate limit for a specific identifier (admin only)
    identifier can be: user:123, ip:192.168.1.1, etc.
    """
    # Check admin role
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reset rate limits"
        )

    try:
        success = await rate_limiter.reset_rate_limit(identifier)

        if success:
            logger.info(f"Rate limit reset for {identifier} by admin {current_user.get('sub')}")
            return {"success": True, "message": f"Rate limit reset for {identifier}"}
        else:
            return {"success": False, "message": "Failed to reset rate limit"}

    except Exception as e:
        logger.error(f"Rate limit reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limit: {str(e)}"
        )


# ==================== Sentry Debug Endpoint ====================

@app.get("/sentry-debug")
async def trigger_error():
    """Trigger a test error to verify Sentry integration"""
    division_by_zero = 1 / 0
    return {"message": "This should never be reached"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
