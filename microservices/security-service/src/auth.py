"""
Enhanced JWT Authentication and Authorization
Includes MFA, password policy, account lockout, and session management
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from jose import jwt, JWTError
import os
import bcrypt
from sqlalchemy.orm import Session
import logging
import models
import database
from password_policy import (
    validate_password_policy,
    check_password_history,
    hash_password_for_history,
    is_password_expired
)

logger = logging.getLogger(__name__)

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
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_DURATION_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_MINUTES", "30"))


# ==================== User Retrieval ====================

def get_user(db: Session, username: str):
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()


# ==================== Password Management ====================

def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)  # Increased from default 10 for better security
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def validate_new_password(
    password: str,
    user: models.User
) -> Tuple[bool, List[str]]:
    """
    Validate new password against policy and history

    Args:
        password: New password to validate
        user: User object

    Returns:
        (is_valid, errors) tuple
    """
    errors = []

    # Check password policy
    policy_result = validate_password_policy(password)
    if not policy_result.valid:
        errors.extend(policy_result.errors)

    # Check password history
    password_history = user.password_history or []
    history_ok, history_msg = check_password_history(password, password_history)
    if not history_ok:
        errors.append(history_msg)

    return len(errors) == 0, errors


def update_password(
    db: Session,
    user: models.User,
    new_password: str,
    force_change: bool = False
) -> bool:
    """
    Update user password with history tracking

    Args:
        db: Database session
        user: User object
        new_password: New password (plain text)
        force_change: Whether to require password change on next login

    Returns:
        True if successful
    """
    try:
        # Hash new password
        new_hashed = hash_password(new_password)

        # Update password history
        password_history = user.password_history or []
        current_hash = hash_password_for_history(new_password)
        password_history.append(current_hash)

        # Keep only last 5 passwords
        if len(password_history) > 5:
            password_history = password_history[-5:]

        # Calculate password expiry (90 days from now)
        expiry_days = int(os.getenv("PASSWORD_EXPIRY_DAYS", "90"))
        password_expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        # Update user record
        user.hashed_password = new_hashed
        user.password_history = password_history
        user.password_last_changed = datetime.utcnow()
        user.password_expires_at = password_expires_at
        user.force_password_change = force_change
        user.updated_at = datetime.utcnow()

        db.commit()
        logger.info(f"Password updated for user {user.id}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Password update failed for user {user.id}: {e}")
        return False


def check_password_expiry(user: models.User) -> Tuple[bool, int]:
    """
    Check if user's password has expired

    Returns:
        (is_expired, days_until_expiry) tuple
    """
    if not user.password_last_changed:
        return False, 90

    return is_password_expired(
        user.password_last_changed,
        int(os.getenv("PASSWORD_EXPIRY_DAYS", "90"))
    )


# ==================== Account Lockout ====================

def is_account_locked(user: models.User) -> Tuple[bool, Optional[int]]:
    """
    Check if account is locked

    Returns:
        (is_locked, minutes_remaining) tuple
    """
    if not user.is_locked:
        return False, None

    if user.locked_until and datetime.utcnow() >= user.locked_until:
        # Lock has expired
        return False, None

    if user.locked_until:
        remaining = (user.locked_until - datetime.utcnow()).total_seconds() / 60
        return True, int(remaining)

    return True, None


def lock_account(db: Session, user: models.User, duration_minutes: int = ACCOUNT_LOCKOUT_DURATION_MINUTES):
    """Lock user account for specified duration"""
    try:
        user.is_locked = True
        user.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        user.updated_at = datetime.utcnow()
        db.commit()
        logger.warning(f"Account locked for user {user.id} for {duration_minutes} minutes")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to lock account for user {user.id}: {e}")


def unlock_account(db: Session, user: models.User):
    """Unlock user account"""
    try:
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        user.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Account unlocked for user {user.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to unlock account for user {user.id}: {e}")


def record_failed_login(db: Session, user: models.User):
    """Record failed login attempt and lock if threshold exceeded"""
    try:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        user.last_failed_login = datetime.utcnow()

        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            lock_account(db, user)
            logger.warning(
                f"Account locked for user {user.id} after {user.failed_login_attempts} failed attempts"
            )
        else:
            db.commit()
            logger.warning(
                f"Failed login for user {user.id}. "
                f"Attempts: {user.failed_login_attempts}/{MAX_FAILED_LOGIN_ATTEMPTS}"
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record failed login for user {user.id}: {e}")


def reset_failed_login_attempts(db: Session, user: models.User):
    """Reset failed login counter after successful login"""
    try:
        user.failed_login_attempts = 0
        user.last_failed_login = None
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reset login attempts for user {user.id}: {e}")


# ==================== Authentication ====================

def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Authenticate user credentials with enhanced security checks

    Returns:
        (user_dict, error_message) tuple
    """
    user = get_user(db, username)
    if not user:
        # Don't reveal whether username exists
        return None, "Invalid username or password"

    # Check if account is active
    if not user.is_active:
        return None, "Account is disabled"

    # Check if account is locked
    locked, minutes_remaining = is_account_locked(user)
    if locked:
        if minutes_remaining:
            return None, f"Account is locked. Try again in {minutes_remaining} minutes."
        else:
            # Lock expired, unlock account
            unlock_account(db, user)

    # Verify password
    if not verify_password(password, user.hashed_password):
        record_failed_login(db, user)
        remaining_attempts = MAX_FAILED_LOGIN_ATTEMPTS - (user.failed_login_attempts or 0)
        return None, f"Invalid username or password. {remaining_attempts} attempts remaining."

    # Password correct - reset failed attempts
    reset_failed_login_attempts(db, user)

    # Check if password has expired
    expired, days_remaining = check_password_expiry(user)
    if expired:
        user.force_password_change = True
        db.commit()
        return None, "Password has expired. Please reset your password."

    # Update last login
    user.last_login = datetime.utcnow()
    user.last_activity = datetime.utcnow()
    db.commit()

    # Get user roles (for RBAC - future enhancement)
    roles = [user.role] if user.role else []

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "roles": roles,
        "mfa_enabled": user.mfa_enabled,
        "force_password_change": user.force_password_change
    }, None


# ==================== JWT Token Management ====================

def create_access_token(user: Dict, include_mfa: bool = False) -> str:
    """
    Create JWT access token

    Args:
        user: User dictionary
        include_mfa: Whether MFA has been verified (for multi-step auth)

    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user["user_id"]),
        "username": user["username"],
        "roles": user["roles"],
        "tenant_id": user.get("tenant_id"),
        "mfa_verified": include_mfa or not user.get("mfa_enabled", False),
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


def get_token_expiry(token: str) -> Optional[int]:
    """Get token expiry timestamp"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("exp")
    except:
        return None


# ==================== User Registration ====================

def register_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str = "researcher",
    tenant_id: str = "default"
) -> Tuple[Optional[models.User], List[str]]:
    """
    Register a new user with password policy validation

    Returns:
        (user, errors) tuple
    """
    errors = []

    # Check if username exists
    if get_user(db, username):
        errors.append("Username already registered")

    # Check if email exists
    if get_user_by_email(db, email):
        errors.append("Email already registered")

    # Validate password policy (without history check for new user)
    policy_result = validate_password_policy(password)
    if not policy_result.valid:
        errors.extend(policy_result.errors)

    if errors:
        return None, errors

    # Create user
    try:
        hashed_password = hash_password(password)
        password_history = [hash_password_for_history(password)]

        # Calculate password expiry
        expiry_days = int(os.getenv("PASSWORD_EXPIRY_DAYS", "90"))
        password_expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        new_user = models.User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            tenant_id=tenant_id,
            password_history=password_history,
            password_last_changed=datetime.utcnow(),
            password_expires_at=password_expires_at
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user registered: {username} (ID: {new_user.id})")
        return new_user, []

    except Exception as e:
        db.rollback()
        logger.error(f"User registration failed: {e}")
        errors.append(f"Registration failed: {str(e)}")
        return None, errors
