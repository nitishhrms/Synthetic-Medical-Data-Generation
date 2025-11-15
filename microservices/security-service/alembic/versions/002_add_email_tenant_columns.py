"""Add email and tenant_id columns to users table

Revision ID: 002_email_tenant
Revises: 001_enhanced_security
Create Date: 2025-11-15

This migration adds missing columns that the User model expects:
- email: User's email address (unique)
- tenant_id: Multi-tenancy support
- created_at: Account creation timestamp

BACKWARD COMPATIBLE: All new fields are nullable initially, then defaults are set
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_email_tenant'
down_revision = '001_enhanced_security'
branch_labels = None
depends_on = None


def upgrade():
    """Add email and tenant_id columns"""

    # Detect if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    is_sqlite = bind.engine.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite-compatible approach: add nullable columns, then set defaults
        with op.batch_alter_table('users') as batch_op:
            batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=True))
            batch_op.add_column(sa.Column('tenant_id', sa.String(length=100), nullable=True))
            batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

        # Set default values for existing rows
        # Email: Generate from username if not exists
        op.execute("""
            UPDATE users
            SET email = username || '@example.com'
            WHERE email IS NULL
        """)

        # Tenant ID: Set default tenant for existing users
        op.execute("""
            UPDATE users
            SET tenant_id = 'default_tenant'
            WHERE tenant_id IS NULL
        """)

        # Created at: Set to current time for existing users
        op.execute("""
            UPDATE users
            SET created_at = datetime('now')
            WHERE created_at IS NULL
        """)

        # Create indexes (SQLite batch mode)
        with op.batch_alter_table('users') as batch_op:
            batch_op.create_index('ix_users_email', ['email'], unique=True)
            batch_op.create_index('ix_users_tenant_id', ['tenant_id'], unique=False)

    else:
        # PostgreSQL approach: add with server defaults
        op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
        op.add_column('users', sa.Column('tenant_id', sa.String(length=100), nullable=True))
        op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))

        # Set default values
        op.execute("""
            UPDATE users
            SET email = username || '@example.com'
            WHERE email IS NULL
        """)

        op.execute("""
            UPDATE users
            SET tenant_id = 'default_tenant'
            WHERE tenant_id IS NULL
        """)

        # Create indexes
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)


def downgrade():
    """Remove email and tenant_id columns"""

    # Drop indexes first
    op.drop_index(op.f('ix_users_tenant_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')

    # Drop columns
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'tenant_id')
    op.drop_column('users', 'email')
