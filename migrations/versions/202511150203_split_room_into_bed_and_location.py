"""Split room into bed_number and location

Revision ID: 202511150203
Revises: e7f8g9h0i1j2
Create Date: 2025-11-15 02:03:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202511150203'
down_revision = 'e7f8g9h0i1j2'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns
    op.add_column('ticket', sa.Column('bed_number', sa.String(length=10), nullable=True))
    op.add_column('ticket', sa.Column('location', sa.String(length=50), nullable=True))

    # Migrate existing data from 'room' to 'bed_number' (first 10 characters)
    # Using SUBSTRING for PostgreSQL compatibility
    op.execute("""
        UPDATE ticket
        SET bed_number = SUBSTRING(room FROM 1 FOR 10)
        WHERE room IS NOT NULL
    """)

    # Drop old column
    op.drop_column('ticket', 'room')


def downgrade():
    # Add back the old 'room' column
    op.add_column('ticket', sa.Column('room', sa.String(length=100), nullable=True))

    # Restore data from 'bed_number' to 'room'
    op.execute("""
        UPDATE ticket
        SET room = bed_number
        WHERE bed_number IS NOT NULL
    """)

    # Drop new columns
    op.drop_column('ticket', 'location')
    op.drop_column('ticket', 'bed_number')
