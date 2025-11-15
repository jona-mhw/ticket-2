"""Drop discharge_time_slot table and FK (Issue #54)

Revision ID: 202511151930
Revises: 202511151800
Create Date: 2025-11-15 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202511151930'
down_revision = '202511151800'
branch_labels = None
depends_on = None


def upgrade():
    """
    Issue #54: Eliminar tabla discharge_time_slot y FK discharge_slot_id.

    Los bloques horarios son FIJOS (24 bloques de 2h) y se generan dinámicamente
    usando TimeBlockHelper. No requieren almacenamiento en BD.

    Esto elimina:
    1. FK ticket.discharge_slot_id → discharge_time_slot.id
    2. Columna ticket.discharge_slot_id
    3. Tabla discharge_time_slot
    """

    # 1. Eliminar FK constraint
    # Nota: El nombre exacto del constraint puede variar por BD
    # PostgreSQL usa el patrón: tabla_columna_fkey
    try:
        op.drop_constraint('ticket_discharge_slot_id_fkey', 'ticket', type_='foreignkey')
    except Exception as e:
        # Si el constraint no existe o tiene otro nombre, continuar
        print(f"Warning: No se pudo eliminar FK constraint: {e}")

    # 2. Eliminar columna discharge_slot_id de ticket
    op.drop_column('ticket', 'discharge_slot_id')

    # 3. Eliminar tabla discharge_time_slot completamente
    op.drop_table('discharge_time_slot')


def downgrade():
    """
    Rollback: Recrear tabla discharge_time_slot y FK (no recomendado).

    NOTA: Esto NO restaura los datos que existían en la tabla.
    Solo recrea la estructura vacía.
    """

    # 1. Recrear tabla discharge_time_slot
    op.create_table(
        'discharge_time_slot',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('clinic_id', sa.Integer(), sa.ForeignKey('clinic.id'), nullable=False)
    )

    # 2. Recrear columna discharge_slot_id en ticket
    op.add_column('ticket', sa.Column('discharge_slot_id', sa.Integer(), nullable=True))

    # 3. Recrear FK constraint
    op.create_foreign_key(
        'ticket_discharge_slot_id_fkey',
        'ticket',
        'discharge_time_slot',
        ['discharge_slot_id'],
        ['id']
    )
