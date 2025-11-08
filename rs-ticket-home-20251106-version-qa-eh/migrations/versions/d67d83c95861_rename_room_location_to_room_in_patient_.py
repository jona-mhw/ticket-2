"""Rename room_location to room in Patient model

Revision ID: d67d83c95861
Revises: a1b2c3d4e5f6
Create Date: 2025-10-20 16:14:38.601395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd67d83c95861'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('patient', schema=None) as batch_op:
        batch_op.alter_column('room_location', new_column_name='room')

def downgrade():
    with op.batch_alter_table('patient', schema=None) as batch_op:
        batch_op.alter_column('room', new_column_name='room_location')
