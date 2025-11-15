from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# ==================== User Authentication & Profile ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Role (deprecated - use user_roles table for multi-role support)
    role = Column(String(50))  # Kept for backward compatibility

    # Multi-tenancy
    tenant_id = Column(String(100), index=True, nullable=False)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Password management
    password_last_changed = Column(DateTime, default=datetime.utcnow, nullable=False)
    password_expires_at = Column(DateTime, nullable=True)
    password_history = Column(JSON, default=list)  # List of hashed previous passwords
    force_password_change = Column(Boolean, default=False)

    # MFA fields
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(Text, nullable=True)  # Encrypted TOTP secret
    mfa_backup_codes = Column(Text, nullable=True)  # Encrypted backup codes
    mfa_setup_completed_at = Column(DateTime, nullable=True)

    # Failed login tracking
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)

    # Relationships (for RBAC)
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        foreign_keys="UserRole.user_id",
        cascade="all, delete-orphan"
    )


# ==================== RBAC (Role-Based Access Control) ====================

class UserRole(Base):
    """Association table for user-role relationships with metadata"""
    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Optional role expiration

    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])


class Role(Base):
    """Roles define groups of permissions"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "admin", "researcher"
    display_name = Column(String(100), nullable=False)  # e.g., "Administrator"
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)  # System roles cannot be deleted
    tenant_id = Column(String(100), nullable=True)  # Tenant-specific roles

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_assignments = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """Permissions define specific actions users can perform"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)  # e.g., "can_generate_data"
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(50), nullable=True)  # e.g., "data", "study", "user"
    action = Column(String(50), nullable=True)  # e.g., "create", "read", "update", "delete"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    """Association between roles and permissions"""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    granter = relationship("User", foreign_keys=[granted_by])


# ==================== Audit Logging ====================

class AuditLog(Base):
    """Audit logs for HIPAA/SOC 2 compliance"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Who performed the action
    user_id = Column(String(50), index=True, nullable=True)
    username = Column(String(100), nullable=True)

    # What action was performed
    action = Column(String(100), index=True, nullable=False)  # e.g., "LOGIN", "DECRYPT_PHI", "CREATE_STUDY"
    resource = Column(String(100), index=True, nullable=False)  # e.g., "security-service", "patient:123"

    # Details
    details = Column(JSON, nullable=True)

    # Where (network context)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)

    # Why (if applicable)
    reason = Column(Text, nullable=True)

    # Result
    status = Column(String(20), default="success")  # success, failure, error
    error_message = Column(Text, nullable=True)

    # Security
    integrity_hash = Column(String(64), nullable=False)  # SHA-256 hash for immutability check

    # PHI access flag (for HIPAA compliance)
    accessed_phi = Column(Boolean, default=False)

    # Tenant isolation
    tenant_id = Column(String(100), nullable=True, index=True)


# ==================== Security Incidents ====================

class SecurityIncident(Base):
    """Track security incidents for SOC 2 compliance"""
    __tablename__ = "security_incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(50), nullable=False, index=True)  # e.g., "brute_force", "unauthorized_access"
    severity = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL

    # Who/What
    user_id = Column(String(50), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    resource_affected = Column(String(200), nullable=True)

    # Details
    description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    # Status
    status = Column(String(20), default="open")  # open, investigating, resolved, false_positive
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resolver = relationship("User", foreign_keys=[resolved_by])
