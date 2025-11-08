"""
Script para crear índices de base de datos para optimizar performance.

Ejecutar con: flask db migrate -m "Agregar índices de performance"
"""

from alembic import op
import sqlalchemy as sa


def create_performance_indexes():
    """Crea índices en columnas frecuentemente consultadas."""

    # Index en tickets para búsquedas por clínica + estado
    op.create_index(
        'idx_tickets_clinic_status',
        'ticket',
        ['clinic_id', 'status']
    )

    # Index en tickets para ordenamiento por FPA
    op.create_index(
        'idx_tickets_current_fpa',
        'ticket',
        ['current_fpa']
    )

    # Index en tickets para búsqueda por fecha de creación
    op.create_index(
        'idx_tickets_created_at',
        'ticket',
        ['created_at']
    )

    # Index en patients para búsqueda por RUT
    op.create_index(
        'idx_patients_rut',
        'patient',
        ['rut']
    )

    # Index en patients para búsqueda por nombre
    op.create_index(
        'idx_patients_names',
        'patient',
        ['primer_nombre', 'apellido_paterno']
    )

    # Index en action_audit para consultas por usuario + fecha
    op.create_index(
        'idx_action_audit_user_date',
        'action_audit',
        ['user_id', sa.text('timestamp DESC')]
    )

    # Index en login_audit para consultas por usuario
    op.create_index(
        'idx_login_audit_user',
        'login_audit',
        ['user_id']
    )

    # Index en tickets para búsqueda por ID (frecuente en búsquedas)
    op.create_index(
        'idx_tickets_id_pattern',
        'ticket',
        [sa.text('id varchar_pattern_ops')]
    )

    print("✅ Índices de performance creados exitosamente")


def drop_performance_indexes():
    """Elimina los índices creados (para rollback)."""

    op.drop_index('idx_tickets_clinic_status', 'ticket')
    op.drop_index('idx_tickets_current_fpa', 'ticket')
    op.drop_index('idx_tickets_created_at', 'ticket')
    op.drop_index('idx_patients_rut', 'patient')
    op.drop_index('idx_patients_names', 'patient')
    op.drop_index('idx_action_audit_user_date', 'action_audit')
    op.drop_index('idx_login_audit_user', 'login_audit')
    op.drop_index('idx_tickets_id_pattern', 'ticket')

    print("✅ Índices de performance eliminados")


# Para ejecutar manualmente:
if __name__ == '__main__':
    print("""
    Este script debe ejecutarse como migración de Alembic.

    Pasos:
    1. flask db migrate -m "Agregar índices de performance"
    2. flask db upgrade

    Los índices mejorarán significativamente el performance de:
    - Nursing board (filtros por clínica y estado)
    - Búsqueda de pacientes por RUT y nombre
    - Ordenamiento por FPA
    - Auditoría de acciones y logins
    """)
