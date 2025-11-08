"""Make clinic_id nullable in audit tables for superusers

Revision ID: 78202ac7184e
Revises: bc4a869c97f1
Create Date: 2025-10-24 02:12:35.150589

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78202ac7184e'
down_revision = 'bc4a869c97f1'
branch_labels = None
depends_on = None


def upgrade():
    # Make clinic_id nullable in login_audit table
    op.alter_column('login_audit', 'clinic_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)

    # Make clinic_id nullable in action_audit table
    op.alter_column('action_audit', 'clinic_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade():
    # Revert clinic_id to not nullable in login_audit table
    op.alter_column('login_audit', 'clinic_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)

    # Revert clinic_id to not nullable in action_audit table
    op.alter_column('action_audit', 'clinic_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
