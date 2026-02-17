"""
Tests de regresión para los fixes de la sesión 2026-02-16.

1. Creación de ticket con paciente nuevo (fix flush prematuro en PatientRepository)
2. Detalle de ticket sin error 500 (fix compute_state en ruta detail)
3. Dashboard: filtros aplicados a tabla de médicos con modificaciones FPA
"""
import pytest
from datetime import datetime, timedelta
from flask_login import login_user
from models import (
    db, Ticket, Patient, FpaModification, Doctor, Surgery, Specialty, Clinic,
    StandardizedReason, TICKET_STATUS_VIGENTE,
    REASON_CATEGORY_MODIFICATION
)
from repositories.patient_repository import PatientRepository


def do_login(client, app, user):
    """Helper: autenticar usuario usando test_request_context (patrón probado)."""
    with app.test_request_context():
        login_user(user)


# ============================================================
# 1. PatientRepository.get_or_create - fix flush prematuro
# ============================================================

class TestPatientRepositoryGetOrCreate:
    """Verifica que get_or_create funciona sin flush prematuro."""

    def test_create_new_patient_returns_created_true(self, app, db_session, sample_clinic):
        """Un paciente nuevo se crea correctamente (created=True)."""
        with app.app_context():
            patient, created = PatientRepository.get_or_create(
                rut='99999999-9', clinic_id=sample_clinic.id
            )
            # Simular lo que hace la ruta: setear campos obligatorios antes del commit
            patient.primer_nombre = 'María'
            patient.apellido_paterno = 'López'
            patient.age = 30
            patient.sex = 'F'
            db.session.commit()

            assert created is True
            assert patient.id is not None
            assert patient.rut == '99999999-9'
            assert patient.primer_nombre == 'María'

    def test_get_existing_patient_returns_created_false(self, app, db_session, sample_patient):
        """Un paciente existente se recupera sin duplicar (created=False)."""
        with app.app_context():
            patient, created = PatientRepository.get_or_create(
                rut=sample_patient.rut, clinic_id=sample_patient.clinic_id
            )
            assert created is False
            assert patient.id == sample_patient.id

    def test_create_patient_same_rut_different_clinic(self, app, db_session, sample_clinic, sample_patient):
        """Mismo RUT en otra clínica crea paciente nuevo (multi-tenant)."""
        with app.app_context():
            clinic_b = Clinic(name='Clínica B', is_active=True)
            db.session.add(clinic_b)
            db.session.commit()

            patient, created = PatientRepository.get_or_create(
                rut=sample_patient.rut, clinic_id=clinic_b.id
            )
            patient.primer_nombre = 'Otro'
            patient.apellido_paterno = 'Paciente'
            patient.age = 50
            patient.sex = 'M'
            db.session.commit()

            assert created is True
            assert patient.id != sample_patient.id
            assert patient.clinic_id == clinic_b.id


# ============================================================
# 2. Ticket detail - fix compute_state (error 500)
# ============================================================

class TestTicketDetailNoError500:
    """Verifica que la página de detalle de ticket carga sin error 500."""

    def test_detail_page_loads_successfully(self, client, app, db_session,
                                            sample_ticket, sample_user_admin, sample_reasons):
        """El detalle de un ticket carga con status 200 (no 500)."""
        with client:
            do_login(client, app, sample_user_admin)
            response = client.get(f'/tickets/{sample_ticket.id}')
            assert response.status_code == 200
            content = response.data.decode('utf-8')
            assert 'Error Interno del Servidor' not in content

    def test_detail_shows_admission_time(self, client, app, db_session,
                                         sample_ticket, sample_user_admin, sample_reasons):
        """El detalle muestra hora de admisión calculada, no 'Calculando...'."""
        with client:
            do_login(client, app, sample_user_admin)
            response = client.get(f'/tickets/{sample_ticket.id}')
            content = response.data.decode('utf-8')
            assert response.status_code == 200
            assert 'Calculando...' not in content

    def test_compute_state_sets_admission_time(self, app, db_session, sample_ticket):
        """compute_state() asigna admission_time correctamente."""
        with app.app_context():
            sample_ticket.compute_state()

            assert sample_ticket.admission_time is not None
            assert hasattr(sample_ticket, 'urgency_level')
            assert sample_ticket.urgency_level in (
                'scheduled', 'expired', 'critical', 'warning', 'normal', 'unknown'
            )

    def test_compute_state_handles_all_urgency_levels(self, app, db_session, sample_ticket):
        """compute_state() produce atributos transitorios consistentes."""
        with app.app_context():
            sample_ticket.compute_state()

            # Siempre debe tener estos atributos después de compute_state
            assert hasattr(sample_ticket, 'admission_time')
            assert hasattr(sample_ticket, 'is_scheduled')
            assert hasattr(sample_ticket, 'time_remaining')
            assert hasattr(sample_ticket, 'urgency_level')
            assert isinstance(sample_ticket.is_scheduled, bool)


# ============================================================
# 3. Dashboard - filtros en tabla de médicos con modificaciones
# ============================================================

class TestDashboardDoctorModificationsFilters:
    """Verifica que la tabla de médicos con modificaciones respeta los filtros."""

    @pytest.fixture
    def dashboard_data(self, app, db_session, sample_clinic, sample_specialty):
        """Crea datos: 2 doctores, 2 cirugías, tickets con modificaciones en distintas fechas."""
        with app.app_context():
            doctor_a = Doctor(name='Dr. Alpha', specialty='General', rut='11111111-1',
                              clinic_id=sample_clinic.id, is_active=True)
            doctor_b = Doctor(name='Dr. Beta', specialty='Traumatología', rut='22222222-2',
                              clinic_id=sample_clinic.id, is_active=True)
            db.session.add_all([doctor_a, doctor_b])
            db.session.flush()

            surgery_x = Surgery(name='Cirugía X', base_stay_hours=12,
                                specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
                                is_active=True, applies_ticket_home=True, is_ambulatory=False)
            surgery_y = Surgery(name='Cirugía Y', base_stay_hours=24,
                                specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
                                is_active=True, applies_ticket_home=True, is_ambulatory=False)
            db.session.add_all([surgery_x, surgery_y])
            db.session.flush()

            patient = Patient(rut='33333333-3', primer_nombre='Test', apellido_paterno='Patient',
                              age=40, sex='M', clinic_id=sample_clinic.id)
            db.session.add(patient)
            db.session.flush()

            # Ticket A: doctor_a, surgery_x, creado 2026-01-15
            now_a = datetime(2026, 1, 15, 10, 0)
            fpa_a = now_a + timedelta(hours=24)
            ticket_a = Ticket(
                id='TH-TEST-2026-001', patient_id=patient.id, surgery_id=surgery_x.id,
                doctor_id=doctor_a.id, clinic_id=sample_clinic.id,
                pavilion_end_time=now_a, medical_discharge_date=fpa_a.date(),
                system_calculated_fpa=fpa_a, initial_fpa=fpa_a, current_fpa=fpa_a,
                overnight_stays=1, status=TICKET_STATUS_VIGENTE,
                created_by='test', created_at=now_a,
                surgery_name_snapshot='Cirugía X', surgery_base_hours_snapshot=12
            )

            # Ticket B: doctor_b, surgery_y, creado 2026-02-10
            now_b = datetime(2026, 2, 10, 10, 0)
            fpa_b = now_b + timedelta(hours=24)
            ticket_b = Ticket(
                id='TH-TEST-2026-002', patient_id=patient.id, surgery_id=surgery_y.id,
                doctor_id=doctor_b.id, clinic_id=sample_clinic.id,
                pavilion_end_time=now_b, medical_discharge_date=fpa_b.date(),
                system_calculated_fpa=fpa_b, initial_fpa=fpa_b, current_fpa=fpa_b,
                overnight_stays=1, status=TICKET_STATUS_VIGENTE,
                created_by='test', created_at=now_b,
                surgery_name_snapshot='Cirugía Y', surgery_base_hours_snapshot=24
            )
            db.session.add_all([ticket_a, ticket_b])
            db.session.flush()

            # Modificaciones: 3 para ticket_a (doctor_a), 1 para ticket_b (doctor_b)
            for i in range(3):
                mod = FpaModification(
                    ticket_id=ticket_a.id, clinic_id=sample_clinic.id,
                    previous_fpa=fpa_a, new_fpa=fpa_a + timedelta(hours=i + 1),
                    reason='Observación', modified_by='test',
                    modified_at=now_a + timedelta(hours=i)
                )
                db.session.add(mod)

            mod_b = FpaModification(
                ticket_id=ticket_b.id, clinic_id=sample_clinic.id,
                previous_fpa=fpa_b, new_fpa=fpa_b + timedelta(hours=1),
                reason='Observación', modified_by='test',
                modified_at=now_b + timedelta(hours=1)
            )
            db.session.add(mod_b)
            db.session.commit()

            return {
                'doctor_a_name': doctor_a.name, 'doctor_b_name': doctor_b.name,
                'surgery_x_id': surgery_x.id, 'surgery_y_id': surgery_y.id,
            }

    def test_no_filters_shows_all_doctors(self, client, app, db_session,
                                           sample_user_admin, dashboard_data):
        """Sin filtros, ambos doctores aparecen en la tabla."""
        with client:
            do_login(client, app, sample_user_admin)
            response = client.get('/dashboard/')
            assert response.status_code == 200
            content = response.data.decode('utf-8')
            assert 'Dr. Alpha' in content
            assert 'Dr. Beta' in content

    def test_date_filter_excludes_doctor(self, client, app, db_session,
                                          sample_user_admin, dashboard_data):
        """Filtro de fecha que solo incluye enero excluye al Dr. Beta (ticket en febrero)."""
        with client:
            do_login(client, app, sample_user_admin)
            response = client.get('/dashboard/?date_from=2026-01-01&date_to=2026-01-31')
            assert response.status_code == 200
            content = response.data.decode('utf-8')
            assert 'Dr. Alpha' in content
            assert 'Dr. Beta' not in content

    def test_surgery_filter_excludes_doctor(self, client, app, db_session,
                                             sample_user_admin, dashboard_data):
        """Filtro por cirugía Y solo muestra al Dr. Beta."""
        with client:
            do_login(client, app, sample_user_admin)
            response = client.get(f'/dashboard/?surgery_id={dashboard_data["surgery_y_id"]}')
            assert response.status_code == 200
            content = response.data.decode('utf-8')
            assert 'Dr. Beta' in content
            assert 'Dr. Alpha' not in content


# ============================================================
# 4. Ticket creation integration test (full route)
# ============================================================

class TestTicketCreationRoute:
    """Verifica que la ruta de creación de ticket funciona end-to-end."""

    def test_create_ticket_new_patient_success(self, client, app, db_session,
                                                sample_clinic, sample_user_clinical,
                                                sample_surgery_normal, sample_doctor,
                                                sample_reasons):
        """Crear ticket con paciente nuevo no produce error 500."""
        with client:
            do_login(client, app, sample_user_clinical)

            tomorrow = datetime.now() + timedelta(days=1)
            pavilion_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

            response = client.post('/tickets/create', data={
                'rut': '88888888-8',
                'primer_nombre': 'Nuevo',
                'segundo_nombre': '',
                'apellido_paterno': 'Paciente',
                'apellido_materno': 'Test',
                'age': '35',
                'sex': 'M',
                'episode_id': 'EP-99999',
                'surgery_id': str(sample_surgery_normal.id),
                'doctor_id': str(sample_doctor.id),
                'pavilion_end_time': pavilion_time.strftime('%Y-%m-%dT%H:%M'),
                'room': '202',
                'location': 'Piso 3',
            }, follow_redirects=True)

            content = response.data.decode('utf-8')
            assert response.status_code == 200
            assert 'Error al crear el ticket' not in content
            assert 'creado exitosamente' in content or 'TH-' in content

    def test_create_ticket_existing_patient_success(self, client, app, db_session,
                                                     sample_clinic, sample_user_clinical,
                                                     sample_patient, sample_surgery_normal,
                                                     sample_doctor, sample_reasons):
        """Crear ticket con paciente existente funciona correctamente."""
        with client:
            do_login(client, app, sample_user_clinical)

            tomorrow = datetime.now() + timedelta(days=1)
            pavilion_time = tomorrow.replace(hour=14, minute=30, second=0, microsecond=0)

            response = client.post('/tickets/create', data={
                'rut': sample_patient.rut,
                'primer_nombre': sample_patient.primer_nombre,
                'segundo_nombre': sample_patient.segundo_nombre or '',
                'apellido_paterno': sample_patient.apellido_paterno,
                'apellido_materno': sample_patient.apellido_materno or '',
                'age': str(sample_patient.age),
                'sex': sample_patient.sex,
                'episode_id': sample_patient.episode_id or '',
                'surgery_id': str(sample_surgery_normal.id),
                'doctor_id': str(sample_doctor.id),
                'pavilion_end_time': pavilion_time.strftime('%Y-%m-%dT%H:%M'),
                'room': '101',
                'location': 'Piso 2',
            }, follow_redirects=True)

            content = response.data.decode('utf-8')
            assert response.status_code == 200
            assert 'Error al crear el ticket' not in content

    def test_created_ticket_has_valid_patient(self, client, app, db_session,
                                               sample_clinic, sample_user_clinical,
                                               sample_surgery_normal, sample_doctor,
                                               sample_reasons):
        """El paciente creado junto al ticket tiene todos los campos correctos."""
        with client:
            do_login(client, app, sample_user_clinical)

            tomorrow = datetime.now() + timedelta(days=1)
            pavilion_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

            client.post('/tickets/create', data={
                'rut': '77777777-7',
                'primer_nombre': 'Carlos',
                'segundo_nombre': 'Andrés',
                'apellido_paterno': 'Martínez',
                'apellido_materno': 'Soto',
                'age': '60',
                'sex': 'M',
                'episode_id': 'EP-77777',
                'surgery_id': str(sample_surgery_normal.id),
                'doctor_id': str(sample_doctor.id),
                'pavilion_end_time': pavilion_time.strftime('%Y-%m-%dT%H:%M'),
                'room': '303',
                'location': 'Piso 4',
            }, follow_redirects=True)

            # Verificar que el paciente se guardó con todos los campos
            patient = Patient.query.filter_by(rut='77777777-7', clinic_id=sample_clinic.id).first()
            assert patient is not None
            assert patient.primer_nombre == 'Carlos'
            assert patient.segundo_nombre == 'Andrés'
            assert patient.apellido_paterno == 'Martínez'
            assert patient.age == 60
            assert patient.sex == 'M'
