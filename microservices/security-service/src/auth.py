"""
JWT Authentication and Authorization
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from jose import jwt, JWTError
import os
import bcrypt
from sqlalchemy.orm import Session
import models
import database

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Validate JWT secret key - fail fast if default or missing in production
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            "CRITICAL: JWT_SECRET_KEY environment variable not set in production! "
            "This is a security risk. Set a secure random key."
        )
    else:
        import warnings
        warnings.warn(
            "JWT_SECRET_KEY not set. Using default for development only. "
            "This will NOT work in production!",
            UserWarning
        )
        SECRET_KEY = "your-secret-key-change-in-production"

# Validate that default key is not being used in production
DEFAULT_SECRET = "your-secret-key-change-in-production"
if SECRET_KEY == DEFAULT_SECRET and os.getenv("ENVIRONMENT") == "production":
    raise ValueError(
        "CRITICAL: Default JWT secret key detected in production! "
        "You MUST set a secure JWT_SECRET_KEY environment variable. "
        "Generate with: openssl rand -hex 32"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def authenticate_user(db: Session, username: str, password: str) -> Optional[Dict]:
    """Authenticate user credentials"""
    user = get_user(db, username)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return {
        "user_id": user.id,
        "username": user.username,
        "roles": user.roles.split(",") if user.roles else []
    }

def create_access_token(user: Dict) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user["user_id"]),
        "username": user["username"],
        "roles": user["roles"],
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Token validation failed: {str(e)}")

# Note: get_current_user is implemented in main.py as FastAPI dependency
