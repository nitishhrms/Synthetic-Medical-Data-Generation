"""Add enhanced security fields to users table

Revision ID: 001_enhanced_security
Revises:
Create Date: 2025-11-14

This migration adds:
- MFA support fields
- Password management fields (history, expiry)
- Account lockout fields
- Session tracking fields
- RBAC tables

BACKWARD COMPATIBLE: All new fields are nullable or have defaults
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_enhanced_security'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add new security features (backward compatible)"""

    # Detect if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    is_sqlite = bind.engine.dialect.name == 'sqlite'

    # ==================== Enhance Users Table ====================

    if is_sqlite:
        # SQLite-compatible approach: make columns nullable, then set defaults
        with op.batch_alter_table('users') as batch_op:
            # Account status fields
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))
            batch_op.add_column(sa.Column('is_locked', sa.Boolean(), nullable=True))
            batch_op.add_column(sa.Column('locked_until', sa.DateTime(), nullable=True))

            # Password management fields
            batch_op.add_column(sa.Column('password_last_changed', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('password_expires_at', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('password_history', sa.JSON(), nullable=True))
            batch_op.add_column(sa.Column('force_password_change', sa.Boolean(), nullable=True))

            # MFA fields
            batch_op.add_column(sa.Column('mfa_enabled', sa.Boolean(), nullable=True))
            batch_op.add_column(sa.Column('mfa_secret', sa.Text(), nullable=True))
            batch_op.add_column(sa.Column('mfa_backup_codes', sa.Text(), nullable=True))
            batch_op.add_column(sa.Column('mfa_setup_completed_at', sa.DateTime(), nullable=True))

            # Failed login tracking
            batch_op.add_column(sa.Column('failed_login_attempts', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('last_failed_login', sa.DateTime(), nullable=True))

            # Enhanced timestamps
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('last_activity', sa.DateTime(), nullable=True))

        # Set default values for existing rows (SQLite compatible)
        op.execute("UPDATE users SET is_active = 1 WHERE is_active IS NULL")
        op.execute("UPDATE users SET is_locked = 0 WHERE is_locked IS NULL")
        op.execute("UPDATE users SET password_last_changed = datetime('now') WHERE password_last_changed IS NULL")
        op.execute("UPDATE users SET force_password_change = 0 WHERE force_password_change IS NULL")
        op.execute("UPDATE users SET mfa_enabled = 0 WHERE mfa_enabled IS NULL")
        op.execute("UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL")

    else:
        # PostgreSQL approach: use server defaults
        # Account status fields
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
        op.add_column('users', sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'))
        op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))

        # Password management fields
        op.add_column('users', sa.Column('password_last_changed', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        op.add_column('users', sa.Column('password_expires_at', sa.DateTime(), nullable=True))
        op.add_column('users', sa.Column('password_history', sa.JSON(), nullable=True))
        op.add_column('users', sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='false'))

        # MFA fields
        op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'))
        op.add_column('users', sa.Column('mfa_secret', sa.Text(), nullable=True))
        op.add_column('users', sa.Column('mfa_backup_codes', sa.Text(), nullable=True))
        op.add_column('users', sa.Column('mfa_setup_completed_at', sa.DateTime(), nullable=True))

        # Failed login tracking
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
        op.add_column('users', sa.Column('last_failed_login', sa.DateTime(), nullable=True))

        # Enhanced timestamps
        op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))
        op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
        op.add_column('users', sa.Column('last_activity', sa.DateTime(), nullable=True))

    # ==================== Create RBAC Tables ====================

    # Use appropriate datetime default based on database
    timestamp_default = sa.text("(datetime('now'))") if is_sqlite else sa.text('CURRENT_TIMESTAMP')

    # Roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=timestamp_default),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=timestamp_default),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)

    # User role assignments table
    op.create_table(
        'user_role_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=timestamp_default),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_role_assignments_id'), 'user_role_assignments', ['id'], unique=False)

    # Role permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=timestamp_default),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_permissions_id'), 'role_permissions', ['id'], unique=False)

    # ==================== Enhance Audit Logs Table ====================

    # Add new audit fields if table exists
    # (Some deployments might not have audit_logs yet)
    try:
        op.add_column('audit_logs', sa.Column('username', sa.String(length=100), nullable=True))
        op.add_column('audit_logs', sa.Column('ip_address', sa.String(length=45), nullable=True))
        op.add_column('audit_logs', sa.Column('user_agent', sa.Text(), nullable=True))
        op.add_column('audit_logs', sa.Column('reason', sa.Text(), nullable=True))
        op.add_column('audit_logs', sa.Column('status', sa.String(length=20), nullable=True, server_default='success'))
        op.add_column('audit_logs', sa.Column('error_message', sa.Text(), nullable=True))
        op.add_column('audit_logs', sa.Column('accessed_phi', sa.Boolean(), nullable=False, server_default='false'))
        op.add_column('audit_logs', sa.Column('tenant_id', sa.String(length=100), nullable=True))

        # Create indexes for better query performance
        op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
        op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'], unique=False)
    except Exception as e:
        print(f"Note: Could not enhance audit_logs table (might not exist yet): {e}")

    # ==================== Create Security Incidents Table ====================

    op.create_table(
        'security_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('resource_affected', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=timestamp_default),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=timestamp_default),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_incidents_id'), 'security_incidents', ['id'], unique=False)
    op.create_index(op.f('ix_security_incidents_incident_type'), 'security_incidents', ['incident_type'], unique=False)
    op.create_index(op.f('ix_security_incidents_severity'), 'security_incidents', ['severity'], unique=False)
    op.create_index(op.f('ix_security_incidents_user_id'), 'security_incidents', ['user_id'], unique=False)
    op.create_index(op.f('ix_security_incidents_detected_at'), 'security_incidents', ['detected_at'], unique=False)


def downgrade():
    """Rollback security enhancements (use with caution in production)"""

    # Drop new tables (in reverse order of creation)
    op.drop_table('security_incidents')
    op.drop_table('role_permissions')
    op.drop_table('user_role_assignments')
    op.drop_table('permissions')
    op.drop_table('roles')

    # Remove enhanced audit log fields
    try:
        op.drop_column('audit_logs', 'tenant_id')
        op.drop_column('audit_logs', 'accessed_phi')
        op.drop_column('audit_logs', 'error_message')
        op.drop_column('audit_logs', 'status')
        op.drop_column('audit_logs', 'reason')
        op.drop_column('audit_logs', 'user_agent')
        op.drop_column('audit_logs', 'ip_address')
        op.drop_column('audit_logs', 'username')
    except Exception as e:
        print(f"Note: Could not remove audit_logs enhancements: {e}")

    # Remove users table enhancements
    op.drop_column('users', 'last_activity')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'last_failed_login')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'mfa_setup_completed_at')
    op.drop_column('users', 'mfa_backup_codes')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'force_password_change')
    op.drop_column('users', 'password_history')
    op.drop_column('users', 'password_expires_at')
    op.drop_column('users', 'password_last_changed')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'is_locked')
    op.drop_column('users', 'is_active')
