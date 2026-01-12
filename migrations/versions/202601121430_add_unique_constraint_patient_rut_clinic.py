"""Add unique constraint on patient (rut, clinic_id)

Revision ID: 202601121430
Revises: 202511150203
Create Date: 2026-01-12 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202601121430'
down_revision = '202511150203'
branch_labels = None
depends_on = None


def upgrade():
    # Create unique constraint on patient (rut, clinic_id)
    op.create_unique_constraint(
        'uq_patient_rut_clinic',
        'patient',
        ['rut', 'clinic_id']
    )


def downgrade():
    # Drop unique constraint
    op.drop_constraint('uq_patient_rut_clinic', 'patient', type_='unique')
