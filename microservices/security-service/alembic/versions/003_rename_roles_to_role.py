"""Rename roles column to role for backward compatibility

Revision ID: 003_rename_roles
Revises: 002_email_tenant
Create Date: 2025-11-15

This migration renames the old 'roles' column to 'role' to match the model
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_rename_roles'
down_revision = '002_email_tenant'
branch_labels = None
depends_on = None


def upgrade():
    """Rename roles to role"""

    # Detect if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    is_sqlite = bind.engine.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite doesn't support column rename directly, use batch mode
        with op.batch_alter_table('users') as batch_op:
            batch_op.alter_column('roles', new_column_name='role')
    else:
        # PostgreSQL can rename directly
        op.alter_column('users', 'roles', new_column_name='role')


def downgrade():
    """Rename role back to roles"""

    bind = op.get_bind()
    is_sqlite = bind.engine.dialect.name == 'sqlite'

    if is_sqlite:
        with op.batch_alter_table('users') as batch_op:
            batch_op.alter_column('role', new_column_name='roles')
    else:
        op.alter_column('users', 'role', new_column_name='roles')
