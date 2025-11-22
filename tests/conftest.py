"""
Fixtures compartidos para todos los tests de Ticket Home.
Proporciona app, cliente, base de datos, usuarios, clínicas y datos de prueba.
"""
import pytest
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Configurar variables de entorno para testing ANTES de importar app
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['ENABLE_IAP'] = 'false'
os.environ['ENABLE_DEMO_LOGIN'] = 'true'
os.environ['SKIP_AUTH_FOR_TESTING'] = 'true'

from app import create_app
from models import (
    db, User, Clinic, Specialty, Surgery, Doctor,
    StandardizedReason, Patient, Ticket,
    FpaModification, Superuser, LoginAudit, ActionAudit,
    ROLE_ADMIN, ROLE_CLINICAL, ROLE_VISUALIZADOR,
    TICKET_STATUS_VIGENTE, TICKET_STATUS_ANULADO,
    REASON_CATEGORY_INITIAL, REASON_CATEGORY_MODIFICATION, REASON_CATEGORY_ANNULMENT
)


@pytest.fixture(scope='session')
def app():
    """
    Fixture que crea la aplicación Flask configurada para testing.
    Scope: session - se crea una vez por sesión de tests.
    """
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    # app.config['WTF_CSRF_ENABLED'] = False # Enable CSRF to ensure csrf_token is in context
    app.config['SERVER_NAME'] = 'localhost.localdomain'

    return app


@pytest.fixture(scope='function')
def client(app):
    """
    Fixture que proporciona un cliente de test para hacer requests.
    Scope: function - se crea uno nuevo para cada test.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """
    Fixture que proporciona una sesión de base de datos limpia para cada test.
    Crea todas las tablas al inicio y las borra al final.
    Scope: function - nueva BD para cada test (aislamiento).
    """
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_clinic(db_session):
    """Crea una clínica de prueba."""
    clinic = Clinic(
        name='Clínica RedSalud Test',
        is_active=True
    )
    db_session.session.add(clinic)
    db_session.session.commit()
    return clinic


@pytest.fixture
def sample_superuser(db_session):
    """Crea un superusuario en la tabla Superuser."""
    superuser = Superuser(email='super@test.com')
    db_session.session.add(superuser)
    db_session.session.commit()
    return superuser


@pytest.fixture
def sample_user_admin(db_session, sample_clinic):
    """Crea un usuario administrador."""
    user = User(
        username='admin_test',
        email='admin@test.com',
        password=generate_password_hash('password123'),
        role=ROLE_ADMIN,
        clinic_id=sample_clinic.id,
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def sample_user_clinical(db_session, sample_clinic):
    """Crea un usuario clínico (rol clinical)."""
    user = User(
        username='clinical_test',
        email='clinical@test.com',
        password=generate_password_hash('password123'),
        role=ROLE_CLINICAL,
        clinic_id=sample_clinic.id,
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def sample_user_visualizador(db_session, sample_clinic):
    """Crea un usuario visualizador (solo lectura)."""
    user = User(
        username='visualizador_test',
        email='visualizador@test.com',
        password=generate_password_hash('password123'),
        role=ROLE_VISUALIZADOR,
        clinic_id=sample_clinic.id,
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def sample_user_super(db_session, sample_superuser):
    """Crea un superusuario (sin clinic_id)."""
    user = User(
        username='super_test',
        email='super@test.com',
        password=generate_password_hash('password123'),
        role=ROLE_ADMIN,
        clinic_id=None,  # Superuser no tiene clínica
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def sample_specialty(db_session, sample_clinic):
    """Crea una especialidad de prueba."""
    specialty = Specialty(
        name='Cirugía General',
        clinic_id=sample_clinic.id,
        is_active=True
    )
    db_session.session.add(specialty)
    db_session.session.commit()
    return specialty


@pytest.fixture
def sample_surgery_normal(db_session, sample_clinic, sample_specialty):
    """Crea una cirugía normal (con estadía nocturna)."""
    surgery = Surgery(
        name='Colecistectomía',
        base_stay_hours=24,
        specialty_id=sample_specialty.id,
        clinic_id=sample_clinic.id,
        is_active=True,
        applies_ticket_home=True,
        is_ambulatory=False
    )
    db_session.session.add(surgery)
    db_session.session.commit()
    return surgery


@pytest.fixture
def sample_surgery_ambulatory(db_session, sample_clinic, sample_specialty):
    """Crea una cirugía ambulatoria con cutoff hour."""
    surgery = Surgery(
        name='Hernia Inguinal',
        base_stay_hours=6,
        specialty_id=sample_specialty.id,
        clinic_id=sample_clinic.id,
        is_active=True,
        applies_ticket_home=True,
        is_ambulatory=True,
        ambulatory_cutoff_hour=14  # 2:00 PM
    )
    db_session.session.add(surgery)
    db_session.session.commit()
    return surgery


@pytest.fixture
def sample_doctor(db_session, sample_clinic):
    """Crea un doctor de prueba."""
    doctor = Doctor(
        name='Dr. Juan Pérez',
        specialty='Cirugía General',
        rut='12345678-9',
        clinic_id=sample_clinic.id,
        is_active=True
    )
    db_session.session.add(doctor)
    db_session.session.commit()
    return doctor


# DischargeTimeSlot removed. This fixture is no longer needed or should return a list of strings if needed.
@pytest.fixture
def sample_discharge_slots(db_session, sample_clinic):
    """
    MOCK: Retorna lista de strings de bloques horarios simulando lo que antes eran objetos DB.
    Ya no se guardan en BD.
    """
    return [
        '08:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00',
        '16:00-18:00', '18:00-20:00', '20:00-22:00', '22:00-00:00',
        '00:00-02:00', '02:00-04:00', '04:00-06:00', '06:00-08:00'
    ]


@pytest.fixture
def sample_reasons(db_session, sample_clinic):
    """Crea razones estandarizadas de prueba."""
    reasons = [
        StandardizedReason(
            reason='Paciente requiere observación adicional',
            category=REASON_CATEGORY_MODIFICATION,
            clinic_id=sample_clinic.id,
            is_active=True
        ),
        StandardizedReason(
            reason='Criterio médico inicial',
            category=REASON_CATEGORY_INITIAL,
            clinic_id=sample_clinic.id,
            is_active=True
        ),
        StandardizedReason(
            reason='Ticket creado por error',
            category=REASON_CATEGORY_ANNULMENT,
            clinic_id=sample_clinic.id,
            is_active=True
        ),
    ]

    for reason in reasons:
        db_session.session.add(reason)

    db_session.session.commit()
    return reasons


@pytest.fixture
def sample_patient(db_session, sample_clinic):
    """Crea un paciente de prueba."""
    patient = Patient(
        rut='11111111-1',
        primer_nombre='Juan',
        segundo_nombre='Carlos',
        apellido_paterno='Pérez',
        apellido_materno='González',
        age=45,
        sex='M',
        episode_id='EP-12345',
        clinic_id=sample_clinic.id
    )
    db_session.session.add(patient)
    db_session.session.commit()
    return patient


@pytest.fixture
def sample_ticket(db_session, sample_clinic, sample_patient, sample_surgery_normal,
                  sample_doctor):
    """Crea un ticket de prueba completo."""
    pavilion_end = datetime(2025, 1, 15, 14, 30)  # 15 Ene 2025, 14:30
    fpa, overnight = sample_surgery_normal.base_stay_hours, 1
    calculated_fpa = pavilion_end + timedelta(hours=fpa)

    ticket = Ticket(
        id='TH-TEST-2025-001',
        patient_id=sample_patient.id,
        surgery_id=sample_surgery_normal.id,
        doctor_id=sample_doctor.id,
        clinic_id=sample_clinic.id,
        pavilion_end_time=pavilion_end,
        medical_discharge_date=calculated_fpa.date(),
        system_calculated_fpa=calculated_fpa,
        initial_fpa=calculated_fpa,
        current_fpa=calculated_fpa,
        overnight_stays=overnight,
        bed_number='101',
        status=TICKET_STATUS_VIGENTE,
        created_by='test_user',
        surgery_name_snapshot=sample_surgery_normal.name,
        surgery_base_hours_snapshot=sample_surgery_normal.base_stay_hours
    )
    db_session.session.add(ticket)
    db_session.session.commit()
    return ticket


@pytest.fixture
def authenticated_client(client, sample_user_admin, app):
    """
    Fixture que proporciona un cliente autenticado con un usuario admin.
    Útil para tests que requieren autenticación.
    """
    with client:
        with app.test_request_context():
            from flask_login import login_user
            login_user(sample_user_admin)
        yield client
