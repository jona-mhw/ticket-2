"""Add initial reason to Ticket model

Revision ID: bdde3be33136
Revises: dc203aedd18f
Create Date: 2025-10-18 00:26:12.188985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bdde3be33136'
down_revision = 'dc203aedd18f'
branch_labels = None
depends_on = None


def upgrade():
    # This migration is redundant because the initial migration
    # already creates these columns. Passing to avoid errors.
    pass


def downgrade():
    # This migration is redundant. Passing to avoid errors.
    pass