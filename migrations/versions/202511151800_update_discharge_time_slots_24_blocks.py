"""Update discharge time slots from 12 to 24 blocks (Issue #53)

Revision ID: 202511151800
Revises: 202511150203
Create Date: 2025-11-15 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202511151800'
down_revision = '202511150203'
branch_labels = None
depends_on = None


def upgrade():
    """
    CORRECCIÓN Issue #53: Actualizar DischargeTimeSlots de 12 bloques (horas pares) a 24 bloques (todas las horas).

    Antes: 00-02, 02-04, 04-06, ..., 22-00 (12 bloques)
    Después: 22-00, 23-01, 00-02, 01-03, ..., 21-23 (24 bloques)

    La estrategia es:
    1. Eliminar todos los slots existentes (ya que cambia la estructura completa)
    2. Crear 24 nuevos slots para cada clínica existente
    """

    # Obtener lista de clinic_ids antes de eliminar los slots
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT DISTINCT clinic_id FROM discharge_time_slot"))
    clinic_ids = [row[0] for row in result]

    # 1. Eliminar todos los slots existentes
    op.execute("DELETE FROM discharge_time_slot")

    # 2. Crear 24 nuevos slots para cada clínica
    for clinic_id in clinic_ids:
        for end_hour in range(24):  # 0, 1, 2, 3, ..., 23
            # El bloque termina en end_hour y empieza 2 horas antes
            start_hour = (end_hour - 2) % 24

            # Formatear tiempos
            start_time = f'{start_hour:02d}:00:00'
            end_time = f'{end_hour:02d}:00:00'

            # Nombre del bloque
            slot_name = f'{start_hour:02d}:00 - {end_hour:02d}:00'

            # Insertar nuevo slot
            op.execute(
                sa.text("""
                    INSERT INTO discharge_time_slot (name, start_time, end_time, clinic_id)
                    VALUES (:name, :start_time, :end_time, :clinic_id)
                """),
                {
                    'name': slot_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'clinic_id': clinic_id
                }
            )


def downgrade():
    """
    Rollback: Volver a 12 bloques (horas pares).
    """

    # Obtener lista de clinic_ids
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT DISTINCT clinic_id FROM discharge_time_slot"))
    clinic_ids = [row[0] for row in result]

    # 1. Eliminar todos los slots
    op.execute("DELETE FROM discharge_time_slot")

    # 2. Recrear 12 slots originales para cada clínica
    for clinic_id in clinic_ids:
        for i in range(0, 24, 2):  # 0, 2, 4, 6, ..., 22
            start_hour = i
            end_hour = i + 2

            # Formatear tiempos
            start_time = f'{start_hour:02d}:00:00'
            if end_hour >= 24:
                end_time = '23:59:59'
                slot_name = f'{start_hour:02d}:00 - 00:00'
            else:
                end_time = f'{end_hour:02d}:00:00'
                slot_name = f'{start_hour:02d}:00 - {end_hour:02d}:00'

            # Insertar slot
            op.execute(
                sa.text("""
                    INSERT INTO discharge_time_slot (name, start_time, end_time, clinic_id)
                    VALUES (:name, :start_time, :end_time, :clinic_id)
                """),
                {
                    'name': slot_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'clinic_id': clinic_id
                }
            )
