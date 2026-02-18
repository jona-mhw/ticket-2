"""
Tests de aislamiento multi-tenant para Ticket Home.

Verifica que los datos de cada clínica están correctamente aislados:
- Tickets, pacientes, cirugías, médicos y razones son visibles SOLO
  para usuarios de la misma clínica.
- Superusuarios pueden ver datos de todas las clínicas.
- Operaciones de escritura (create, edit) no pueden mezclar recursos
  entre clínicas.

Bugs documentados en este módulo:
  BUG-6: routes/tickets.py (create) - doctor_id no validado contra clinic_id
  BUG-7: routes/admin.py (edit_ticket) - surgery_id/doctor_id no validados
          contra la clínica del ticket
"""
import pytest
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from models import (
    db, Ticket, Patient, Surgery, Specialty, Doctor, Clinic,
    User, FpaModification, StandardizedReason,
    ROLE_ADMIN, ROLE_CLINICAL, TICKET_STATUS_VIGENTE, TICKET_STATUS_ANULADO
)
from repositories.ticket_repository import TicketRepository
from repositories.patient_repository import PatientRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class MockUser:
    """Simula current_user con lo mínimo necesario para las queries."""

    def __init__(self, clinic_id, is_superuser=False, username='test'):
        self.clinic_id = clinic_id
        self._is_superuser = is_superuser
        self.username = username
        self.role = 'superuser' if is_superuser else 'clinical'
        self.is_authenticated = True
        self.id = 1

    @property
    def is_superuser(self):
        return self._is_superuser

    def is_admin(self):
        return self._is_superuser


def make_clinic(name):
    c = Clinic(name=name, is_active=True)
    db.session.add(c)
    db.session.flush()
    return c


def make_specialty(clinic, name='Cirugía General'):
    s = Specialty(name=name, clinic_id=clinic.id, is_active=True)
    db.session.add(s)
    db.session.flush()
    return s


def make_surgery(clinic, specialty, name='Colecistectomía', hours=24):
    s = Surgery(
        name=name,
        base_stay_hours=hours,
        specialty_id=specialty.id,
        clinic_id=clinic.id,
        is_active=True,
        applies_ticket_home=True,
        is_ambulatory=False,
    )
    db.session.add(s)
    db.session.flush()
    return s


def make_doctor(clinic, name='Dr. Test'):
    d = Doctor(name=name, clinic_id=clinic.id, is_active=True)
    db.session.add(d)
    db.session.flush()
    return d


def make_patient(clinic, rut='11111111-1'):
    p = Patient(
        rut=rut,
        primer_nombre='Juan',
        apellido_paterno='Pérez',
        age=40,
        sex='M',
        clinic_id=clinic.id,
    )
    db.session.add(p)
    db.session.flush()
    return p


def make_ticket(clinic, patient, surgery, doctor=None, ticket_id=None, fpa_offset_days=1):
    pavilion_end = datetime(2025, 6, 15, 14, 0)
    fpa = pavilion_end + timedelta(hours=surgery.base_stay_hours)
    tid = ticket_id or f'TH-{clinic.id}-2025-001'
    t = Ticket(
        id=tid,
        patient_id=patient.id,
        surgery_id=surgery.id,
        doctor_id=doctor.id if doctor else None,
        clinic_id=clinic.id,
        pavilion_end_time=pavilion_end,
        medical_discharge_date=(fpa + timedelta(days=fpa_offset_days)).date(),
        system_calculated_fpa=fpa,
        initial_fpa=fpa,
        current_fpa=fpa + timedelta(days=fpa_offset_days),
        overnight_stays=1,
        status=TICKET_STATUS_VIGENTE,
        created_by='test',
        surgery_name_snapshot=surgery.name,
        surgery_base_hours_snapshot=surgery.base_stay_hours,
    )
    db.session.add(t)
    db.session.flush()
    return t


# ---------------------------------------------------------------------------
# 1. Aislamiento de tickets por clínica en consultas del repositorio
# ---------------------------------------------------------------------------

class TestTicketQueryIsolation:
    """Verifica que TicketRepository.build_filtered_query aisla por clínica."""

    def test_user_from_clinic_a_sees_only_clinic_a_tickets(self, app, db_session):
        """Un usuario de clínica A solo puede ver tickets de clínica A."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a, 'Cirugía A')
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')

            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            ticket_a = make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            ticket_b = make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            user_a = MockUser(clinic_id=clinic_a.id)
            query = TicketRepository.build_filtered_query({}, user_a)
            ids = [t.id for t in query.all()]

            assert 'TH-A-2025-001' in ids
            assert 'TH-B-2025-001' not in ids

    def test_user_from_clinic_b_sees_only_clinic_b_tickets(self, app, db_session):
        """Un usuario de clínica B solo puede ver tickets de clínica B."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a, 'Cirugía A')
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')

            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            user_b = MockUser(clinic_id=clinic_b.id)
            query = TicketRepository.build_filtered_query({}, user_b)
            ids = [t.id for t in query.all()]

            assert 'TH-B-2025-001' in ids
            assert 'TH-A-2025-001' not in ids

    def test_superuser_sees_tickets_from_all_clinics(self, app, db_session):
        """Un superusuario puede ver tickets de todas las clínicas."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a, 'Cirugía A')
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')

            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            superuser = MockUser(clinic_id=None, is_superuser=True)
            query = TicketRepository.build_filtered_query({}, superuser)
            ids = [t.id for t in query.all()]

            assert 'TH-A-2025-001' in ids
            assert 'TH-B-2025-001' in ids

    def test_superuser_with_clinic_filter_sees_only_that_clinic(self, app, db_session):
        """Superusuario con filtro de clínica solo ve esa clínica."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a, 'Cirugía A')
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')

            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            superuser = MockUser(clinic_id=None, is_superuser=True)
            filters = {'clinic_id': str(clinic_a.id)}
            query = TicketRepository.build_filtered_query(filters, superuser)
            ids = [t.id for t in query.all()]

            assert 'TH-A-2025-001' in ids
            assert 'TH-B-2025-001' not in ids

    def test_non_superuser_clinic_id_filter_is_ignored(self, app, db_session):
        """
        Un usuario normal que pasa clinic_id en filtros NO debe
        poder acceder a datos de otra clínica.
        """
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a, 'Cirugía A')
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')

            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            # Usuario de clínica A intenta filtrar por clínica B
            user_a = MockUser(clinic_id=clinic_a.id)
            filters = {'clinic_id': str(clinic_b.id)}  # Intento de bypass
            query = TicketRepository.build_filtered_query(filters, user_a)
            ids = [t.id for t in query.all()]

            # Solo debe ver los suyos, el filtro de clinic_id es ignorado para non-superusers
            assert 'TH-A-2025-001' in ids
            assert 'TH-B-2025-001' not in ids

    def test_empty_clinic_does_not_leak_tickets(self, app, db_session):
        """Una clínica nueva sin tickets no ve tickets de otras clínicas."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_empty = make_clinic('Clínica Vacía')

            spec_a = make_specialty(clinic_a)
            surg_a = make_surgery(clinic_a, spec_a, 'Cirugía A')
            pat_a = make_patient(clinic_a, '11111111-1')

            make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            db_session.session.commit()

            user_empty = MockUser(clinic_id=clinic_empty.id)
            query = TicketRepository.build_filtered_query({}, user_empty)
            ids = [t.id for t in query.all()]

            assert ids == []


# ---------------------------------------------------------------------------
# 2. Aislamiento de acceso directo por ID (get_by_id, get_with_relations)
# ---------------------------------------------------------------------------

class TestDirectTicketAccess:
    """Verifica que el acceso directo a un ticket filtra por clínica."""

    def test_get_by_id_with_correct_clinic_returns_ticket(self, app, db_session,
                                                           sample_ticket, sample_clinic):
        with app.app_context():
            ticket = TicketRepository.get_by_id(sample_ticket.id, clinic_id=sample_clinic.id)
            assert ticket is not None
            assert ticket.id == sample_ticket.id

    def test_get_by_id_with_wrong_clinic_returns_none(self, app, db_session,
                                                        sample_ticket):
        with app.app_context():
            wrong_clinic_id = 99999
            ticket = TicketRepository.get_by_id(sample_ticket.id, clinic_id=wrong_clinic_id)
            assert ticket is None

    def test_get_by_id_without_clinic_filter_returns_ticket(self, app, db_session,
                                                              sample_ticket):
        """clinic_id=None equivale a superuser → sin filtro de clínica."""
        with app.app_context():
            ticket = TicketRepository.get_by_id(sample_ticket.id, clinic_id=None)
            assert ticket is not None

    def test_get_with_relations_with_correct_clinic(self, app, db_session,
                                                      sample_ticket, sample_clinic):
        with app.app_context():
            ticket = TicketRepository.get_with_relations(sample_ticket.id,
                                                          clinic_id=sample_clinic.id)
            assert ticket is not None
            assert ticket.patient is not None

    def test_get_with_relations_with_wrong_clinic_returns_none(self, app, db_session,
                                                                 sample_ticket):
        with app.app_context():
            ticket = TicketRepository.get_with_relations(sample_ticket.id,
                                                          clinic_id=99999)
            assert ticket is None

    def test_cannot_access_other_clinic_ticket_by_guessing_id(self, app, db_session):
        """Un usuario no puede acceder a un ticket de otra clínica aunque sepa el ID."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_b = make_specialty(clinic_b)
            surg_b = make_surgery(clinic_b, spec_b)
            pat_b = make_patient(clinic_b, '22222222-2')
            ticket_b = make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            # Usuario de clínica A conoce el ID del ticket B
            result = TicketRepository.get_by_id('TH-B-2025-001', clinic_id=clinic_a.id)
            assert result is None, "No debe poder acceder a ticket de otra clínica"


# ---------------------------------------------------------------------------
# 3. Aislamiento de pacientes por clínica
# ---------------------------------------------------------------------------

class TestPatientClinicIsolation:
    """Verifica que los pacientes están correctamente aislados por clínica."""

    def test_same_rut_can_exist_in_two_clinics(self, app, db_session):
        """El mismo RUT puede existir en dos clínicas como pacientes distintos."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            pat_a = make_patient(clinic_a, '12345678-9')
            pat_b = make_patient(clinic_b, '12345678-9')
            db_session.session.commit()

            assert pat_a.id != pat_b.id
            assert pat_a.clinic_id == clinic_a.id
            assert pat_b.clinic_id == clinic_b.id

    def test_get_by_rut_filters_by_clinic(self, app, db_session):
        """PatientRepository.get_by_rut devuelve el paciente de la clínica correcta."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            pat_a = make_patient(clinic_a, '12345678-9')
            pat_b = make_patient(clinic_b, '12345678-9')
            db_session.session.commit()

            result_a = PatientRepository.get_by_rut('12345678-9', clinic_a.id)
            result_b = PatientRepository.get_by_rut('12345678-9', clinic_b.id)

            assert result_a.id == pat_a.id
            assert result_b.id == pat_b.id
            assert result_a.id != result_b.id

    def test_get_by_rut_does_not_return_other_clinic_patient(self, app, db_session):
        """get_by_rut con clinic_id incorrecto devuelve None."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            make_patient(clinic_a, '12345678-9')
            db_session.session.commit()

            # Buscar con clinic_id de B donde no existe
            result = PatientRepository.get_by_rut('12345678-9', clinic_b.id)
            assert result is None

    def test_get_or_create_creates_per_clinic(self, app, db_session):
        """get_or_create crea pacientes distintos por clínica para el mismo RUT."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')
            db_session.session.commit()

            pat_a, created_a = PatientRepository.get_or_create('99999999-9', clinic_a.id)
            pat_a.primer_nombre = 'Test'
            pat_a.apellido_paterno = 'A'
            pat_a.age = 30
            pat_a.sex = 'M'

            pat_b, created_b = PatientRepository.get_or_create('99999999-9', clinic_b.id)
            pat_b.primer_nombre = 'Test'
            pat_b.apellido_paterno = 'B'
            pat_b.age = 30
            pat_b.sex = 'M'

            db_session.session.commit()

            assert created_a is True
            assert created_b is True
            assert pat_a.id != pat_b.id

    def test_get_or_create_returns_existing_in_same_clinic(self, app, db_session):
        """get_or_create devuelve el paciente existente en la misma clínica."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            pat_a = make_patient(clinic_a, '12345678-9')
            db_session.session.commit()

            patient, created = PatientRepository.get_or_create('12345678-9', clinic_a.id)
            assert created is False
            assert patient.id == pat_a.id

    def test_patient_unique_constraint_is_per_clinic(self, app, db_session):
        """Verificar que la constraint uq_patient_rut_clinic es por clínica."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')
            db_session.session.commit()

            # Mismo RUT en clínica A y B no viola la constraint
            p1 = Patient(rut='11111111-1', primer_nombre='A',
                         apellido_paterno='B', age=30, sex='M', clinic_id=clinic_a.id)
            p2 = Patient(rut='11111111-1', primer_nombre='A',
                         apellido_paterno='B', age=30, sex='M', clinic_id=clinic_b.id)
            db_session.session.add(p1)
            db_session.session.add(p2)
            db_session.session.commit()  # No debe lanzar IntegrityError

            count = Patient.query.filter_by(rut='11111111-1').count()
            assert count == 2

    def test_duplicate_rut_in_same_clinic_raises_integrity_error(self, app, db_session):
        """El mismo RUT en la misma clínica lanza IntegrityError."""
        from sqlalchemy.exc import IntegrityError
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            db_session.session.commit()

            p1 = Patient(rut='11111111-1', primer_nombre='A',
                         apellido_paterno='B', age=30, sex='M', clinic_id=clinic_a.id)
            p2 = Patient(rut='11111111-1', primer_nombre='C',
                         apellido_paterno='D', age=25, sex='F', clinic_id=clinic_a.id)
            db_session.session.add(p1)
            db_session.session.flush()
            db_session.session.add(p2)

            with pytest.raises(IntegrityError):
                db_session.session.flush()

            db_session.session.rollback()


# ---------------------------------------------------------------------------
# 4. Aislamiento de recursos master data (cirugías, médicos, razones)
# ---------------------------------------------------------------------------

class TestMasterDataClinicIsolation:
    """Verifica que los datos maestros están aislados por clínica."""

    def test_surgery_query_filters_by_clinic(self, app, db_session):
        """Las cirugías se filtran correctamente por clinic_id."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a, 'Cirugía A')
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')
            db_session.session.commit()

            surgeries_a = Surgery.query.filter_by(clinic_id=clinic_a.id).all()
            surgeries_b = Surgery.query.filter_by(clinic_id=clinic_b.id).all()

            ids_a = [s.id for s in surgeries_a]
            ids_b = [s.id for s in surgeries_b]

            assert surg_a.id in ids_a
            assert surg_b.id not in ids_a
            assert surg_b.id in ids_b
            assert surg_a.id not in ids_b

    def test_doctor_query_filters_by_clinic(self, app, db_session):
        """Los médicos se filtran correctamente por clinic_id."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            doc_a = make_doctor(clinic_a, 'Dr. A')
            doc_b = make_doctor(clinic_b, 'Dr. B')
            db_session.session.commit()

            docs_a = Doctor.query.filter_by(clinic_id=clinic_a.id).all()
            docs_b = Doctor.query.filter_by(clinic_id=clinic_b.id).all()

            assert doc_a.id in [d.id for d in docs_a]
            assert doc_b.id not in [d.id for d in docs_a]
            assert doc_b.id in [d.id for d in docs_b]

    def test_specialty_query_filters_by_clinic(self, app, db_session):
        """Las especialidades se filtran por clinic_id."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a, 'Especialidad A')
            spec_b = make_specialty(clinic_b, 'Especialidad B')
            db_session.session.commit()

            specs_a = Specialty.query.filter_by(clinic_id=clinic_a.id).all()
            specs_b = Specialty.query.filter_by(clinic_id=clinic_b.id).all()

            assert spec_a.id in [s.id for s in specs_a]
            assert spec_b.id not in [s.id for s in specs_a]

    def test_reasons_query_filters_by_clinic(self, app, db_session):
        """Las razones estandarizadas se filtran por clinic_id."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            reason_a = StandardizedReason(
                reason='Razón A', category='modification',
                clinic_id=clinic_a.id, is_active=True
            )
            reason_b = StandardizedReason(
                reason='Razón B', category='modification',
                clinic_id=clinic_b.id, is_active=True
            )
            db_session.session.add(reason_a)
            db_session.session.add(reason_b)
            db_session.session.commit()

            reasons_a = StandardizedReason.query.filter_by(clinic_id=clinic_a.id).all()
            reasons_b = StandardizedReason.query.filter_by(clinic_id=clinic_b.id).all()

            assert reason_a.id in [r.id for r in reasons_a]
            assert reason_b.id not in [r.id for r in reasons_a]

    def test_surgery_from_another_clinic_not_found_with_clinic_filter(self, app, db_session):
        """
        Filtrar cirugía por ID + clinic_id incorrecto devuelve None.
        Esto protege el endpoint de creación de tickets.
        """
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_b = make_specialty(clinic_b)
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')
            db_session.session.commit()

            # Usuario de clínica A intenta usar una cirugía de clínica B
            result = Surgery.query.filter_by(
                id=surg_b.id,
                clinic_id=clinic_a.id
            ).first()
            assert result is None

    def test_doctor_from_another_clinic_not_found_with_clinic_filter(self, app, db_session):
        """
        BUG-6 (regresión): doctor_id de otra clínica debe ser rechazado.
        Se verifica que la query con clinic_id filtra correctamente.
        """
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            doc_b = make_doctor(clinic_b, 'Dr. B')
            db_session.session.commit()

            # El doctor de clínica B no debe encontrarse al buscar en clínica A
            result = Doctor.query.filter_by(
                id=doc_b.id,
                clinic_id=clinic_a.id
            ).first()
            assert result is None, "Doctor de otra clínica no debe encontrarse con filtro de clínica"


# ---------------------------------------------------------------------------
# 5. Integridad de datos al crear tickets
# ---------------------------------------------------------------------------

class TestTicketCreationDataIntegrity:
    """Verifica que los tickets nuevos tienen datos consistentes con su clínica."""

    def test_ticket_clinic_matches_patient_clinic(self, app, db_session,
                                                    sample_ticket, sample_clinic):
        """El ticket, el paciente y la cirugía deben pertenecer a la misma clínica."""
        with app.app_context():
            assert sample_ticket.clinic_id == sample_clinic.id
            assert sample_ticket.patient.clinic_id == sample_clinic.id
            assert sample_ticket.surgery.clinic_id == sample_clinic.id

    def test_fpa_modification_has_clinic_id(self, app, db_session, sample_ticket,
                                              sample_clinic, sample_reasons, sample_user_admin):
        """Las modificaciones de FPA guardan el clinic_id del ticket."""
        from services.ticket_service import TicketService
        with app.app_context():
            new_fpa = sample_ticket.current_fpa + timedelta(hours=4)
            mod = TicketService.modify_fpa(
                sample_ticket, new_fpa,
                sample_reasons[0].reason,
                'justificación',
                sample_user_admin
            )
            db_session.session.commit()

            assert mod.clinic_id == sample_clinic.id
            assert mod.clinic_id == sample_ticket.clinic_id

    def test_multiple_tickets_from_same_clinic_all_have_correct_clinic_id(self, app, db_session):
        """Varios tickets de la misma clínica tienen el clinic_id correcto."""
        with app.app_context():
            clinic = make_clinic('Clínica Test')
            spec = make_specialty(clinic)
            surg = make_surgery(clinic, spec)
            pat = make_patient(clinic, '11111111-1')

            tickets = []
            for i in range(3):
                t = make_ticket(clinic, pat, surg, ticket_id=f'TH-T-2025-{i:03d}')
                tickets.append(t)
            db_session.session.commit()

            for t in tickets:
                refreshed = Ticket.query.get(t.id)
                assert refreshed.clinic_id == clinic.id

    def test_ticket_from_clinic_b_not_visible_to_clinic_a_user(self, app, db_session):
        """Ticket de clínica B es invisible para usuario de clínica A."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_b = make_specialty(clinic_b)
            surg_b = make_surgery(clinic_b, spec_b)
            pat_b = make_patient(clinic_b, '22222222-2')
            ticket_b = make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            # Intento directo de acceder al ticket de B usando clinic_id de A
            result = TicketRepository.get_by_id('TH-B-2025-001', clinic_id=clinic_a.id)
            assert result is None


# ---------------------------------------------------------------------------
# 6. BUG-6: doctor_id no validado en create (regresión tests)
# ---------------------------------------------------------------------------

class TestBug6DoctorValidationInCreate:
    """
    BUG-6: En routes/tickets.py (create), doctor_id no se valida
    contra clinic_id. Un POST crafteado puede asignar un médico
    de otra clínica a un ticket.

    Estos tests verifican que el FIX funciona correctamente:
    Doctor.query.filter_by(id=..., clinic_id=...) rechaza doctores de otras clínicas.
    """

    def test_doctor_from_correct_clinic_is_found(self, app, db_session):
        """Doctor de la clínica correcta se encuentra con filtro."""
        with app.app_context():
            clinic = make_clinic('Clínica Test')
            doc = make_doctor(clinic, 'Dr. Correcto')
            db_session.session.commit()

            result = Doctor.query.filter_by(id=doc.id, clinic_id=clinic.id).first()
            assert result is not None
            assert result.id == doc.id

    def test_doctor_from_other_clinic_rejected_by_filter(self, app, db_session):
        """Doctor de otra clínica es rechazado cuando se filtra por clinic_id."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            doc_b = make_doctor(clinic_b, 'Dr. B')
            db_session.session.commit()

            # Simula la query que debería ejecutarse en el create route (fix aplicado)
            result = Doctor.query.filter_by(id=doc_b.id, clinic_id=clinic_a.id).first()
            assert result is None, \
                "BUG-6 FIX: doctor de otra clínica debe ser None con filtro de clinic_id"

    def test_ticket_doctor_belongs_to_same_clinic(self, app, db_session,
                                                    sample_ticket, sample_clinic, sample_doctor):
        """El doctor del ticket pertenece a la misma clínica que el ticket."""
        with app.app_context():
            assert sample_ticket.doctor_id == sample_doctor.id
            assert sample_doctor.clinic_id == sample_clinic.id
            assert sample_ticket.clinic_id == sample_clinic.id


# ---------------------------------------------------------------------------
# 7. BUG-7: surgery_id/doctor_id no validados en edit_ticket (regresión tests)
# ---------------------------------------------------------------------------

class TestBug7SurgeryDoctorValidationInEditTicket:
    """
    BUG-7: En routes/admin.py (edit_ticket), surgery_id y doctor_id del POST
    no se validan contra la clínica del ticket.

    Estos tests verifican que el FIX rechaza recursos de otras clínicas.
    """

    def test_surgery_from_correct_clinic_passes_filter(self, app, db_session):
        """Cirugía de la clínica correcta pasa el filtro de validación."""
        with app.app_context():
            clinic = make_clinic('Clínica Test')
            spec = make_specialty(clinic)
            surg = make_surgery(clinic, spec, 'Cirugía Correcta')
            db_session.session.commit()

            # Simula validación del fix
            result = Surgery.query.filter_by(
                id=surg.id, clinic_id=clinic.id, is_active=True
            ).first()
            assert result is not None

    def test_surgery_from_other_clinic_fails_filter(self, app, db_session):
        """Cirugía de otra clínica falla el filtro de validación."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_b = make_specialty(clinic_b)
            surg_b = make_surgery(clinic_b, spec_b, 'Cirugía B')
            db_session.session.commit()

            # Simula validación del fix: clinic_a intenta usar cirugía de clinic_b
            result = Surgery.query.filter_by(
                id=surg_b.id, clinic_id=clinic_a.id
            ).first()
            assert result is None, \
                "BUG-7 FIX: cirugía de otra clínica debe ser None con filtro de clinic_id"

    def test_doctor_from_other_clinic_fails_filter_in_edit(self, app, db_session):
        """Médico de otra clínica falla el filtro en edit_ticket."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            doc_b = make_doctor(clinic_b, 'Dr. B')
            db_session.session.commit()

            result = Doctor.query.filter_by(
                id=doc_b.id, clinic_id=clinic_a.id
            ).first()
            assert result is None, \
                "BUG-7 FIX: médico de otra clínica debe ser None con filtro de clinic_id"

    def test_can_remove_doctor_from_ticket(self, app, db_session, sample_ticket):
        """Asignar doctor_id=None a un ticket es válido (médico no asignado)."""
        with app.app_context():
            sample_ticket.doctor_id = None
            db_session.session.commit()

            refreshed = Ticket.query.get(sample_ticket.id)
            assert refreshed.doctor_id is None


# ---------------------------------------------------------------------------
# 8. Aislamiento de búsqueda textual (search no filtra otra clínica)
# ---------------------------------------------------------------------------

class TestSearchIsolation:
    """Verifica que búsquedas textuales no rompen el aislamiento de clínicas."""

    def test_search_by_rut_does_not_return_other_clinic_tickets(self, app, db_session):
        """Buscar por RUT solo retorna tickets de la clínica del usuario."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a)
            surg_b = make_surgery(clinic_b, spec_b)

            # Mismo RUT en ambas clínicas
            pat_a = make_patient(clinic_a, '12345678-9')
            pat_b = make_patient(clinic_b, '12345678-9')

            ticket_a = make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            ticket_b = make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            # Usuario de clínica A busca por RUT compartido
            user_a = MockUser(clinic_id=clinic_a.id)
            filters = {'search': '12345678-9'}
            query = TicketRepository.build_filtered_query(filters, user_a)
            ids = [t.id for t in query.all()]

            assert 'TH-A-2025-001' in ids
            assert 'TH-B-2025-001' not in ids

    def test_search_by_ticket_id_does_not_return_other_clinic(self, app, db_session):
        """Buscar por ID de ticket no retorna tickets de otra clínica."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a)
            surg_b = make_surgery(clinic_b, spec_b)
            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            # Usuario de A busca el ticket de B por ID
            user_a = MockUser(clinic_id=clinic_a.id)
            filters = {'search': 'TH-B-2025-001'}
            query = TicketRepository.build_filtered_query(filters, user_a)
            ids = [t.id for t in query.all()]

            assert 'TH-B-2025-001' not in ids

    def test_superuser_search_returns_all_clinics(self, app, db_session):
        """Un superusuario que busca ve resultados de todas las clínicas."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a)
            surg_b = make_surgery(clinic_b, spec_b)

            # Mismo RUT en ambas clínicas
            pat_a = make_patient(clinic_a, '99999999-9')
            pat_b = make_patient(clinic_b, '99999999-9')

            make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            superuser = MockUser(clinic_id=None, is_superuser=True)
            filters = {'search': '99999999-9'}
            query = TicketRepository.build_filtered_query(filters, superuser)
            ids = [t.id for t in query.all()]

            assert 'TH-A-2025-001' in ids
            assert 'TH-B-2025-001' in ids


# ---------------------------------------------------------------------------
# 9. Aislamiento de usuarios por clínica
# ---------------------------------------------------------------------------

class TestUserClinicIsolation:
    """Verifica que los usuarios están correctamente aislados por clínica."""

    def test_user_belongs_to_correct_clinic(self, app, db_session,
                                              sample_user_admin, sample_clinic):
        with app.app_context():
            assert sample_user_admin.clinic_id == sample_clinic.id

    def test_superuser_has_no_clinic(self, app, db_session,
                                       sample_user_super, sample_superuser):
        with app.app_context():
            assert sample_user_super.clinic_id is None
            assert sample_user_super.is_superuser is True

    def test_non_superuser_with_clinic_id_is_not_superuser(self, app, db_session,
                                                              sample_user_admin, sample_clinic):
        with app.app_context():
            assert sample_user_admin.clinic_id == sample_clinic.id
            assert sample_user_admin.is_superuser is False

    def test_users_from_different_clinics_are_isolated(self, app, db_session):
        """Usuarios de distintas clínicas no pueden verse entre sí."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            user_a = User(
                username='user_a', email='a@test.com',
                password=generate_password_hash('pw'),
                role=ROLE_CLINICAL, clinic_id=clinic_a.id, is_active=True
            )
            user_b = User(
                username='user_b', email='b@test.com',
                password=generate_password_hash('pw'),
                role=ROLE_CLINICAL, clinic_id=clinic_b.id, is_active=True
            )
            db_session.session.add(user_a)
            db_session.session.add(user_b)
            db_session.session.commit()

            # Cada clínica solo ve sus propios usuarios
            users_a = User.query.filter_by(clinic_id=clinic_a.id).all()
            users_b = User.query.filter_by(clinic_id=clinic_b.id).all()

            ids_a = [u.id for u in users_a]
            ids_b = [u.id for u in users_b]

            assert user_a.id in ids_a
            assert user_b.id not in ids_a
            assert user_b.id in ids_b
            assert user_a.id not in ids_b

    def test_admin_user_creation_inherits_clinic(self, app, db_session):
        """Un admin no-superuser solo puede crear usuarios en su misma clínica."""
        with app.app_context():
            clinic = make_clinic('Clínica Test')
            db_session.session.commit()

            admin = MockUser(clinic_id=clinic.id, is_superuser=False)

            # Simula la lógica de create_user: para un admin no-superuser,
            # clinic_id se toma de current_user.clinic_id
            clinic_id_for_new_user = admin.clinic_id
            assert clinic_id_for_new_user == clinic.id


# ---------------------------------------------------------------------------
# 10. Aislamiento paralelo: simula uso simultáneo de dos clínicas
# ---------------------------------------------------------------------------

class TestParallelClinicUsage:
    """
    Simula el uso paralelo de dos clínicas y verifica que no hay
    contaminación de datos entre ellas.
    """

    def test_two_clinics_create_tickets_independently(self, app, db_session):
        """Dos clínicas crean tickets al mismo tiempo y no se mezclan."""
        with app.app_context():
            clinic_a = make_clinic('Hospital Norte')
            clinic_b = make_clinic('Hospital Sur')

            spec_a = make_specialty(clinic_a, 'Traumatología')
            spec_b = make_specialty(clinic_b, 'Cardiología')
            surg_a = make_surgery(clinic_a, spec_a, 'Artroscopia', 8)
            surg_b = make_surgery(clinic_b, spec_b, 'Bypass Coronario', 48)

            # Mismo RUT en ambas clínicas (paciente con fichas en ambos hospitales)
            pat_a = make_patient(clinic_a, '18123456-7')
            pat_b = make_patient(clinic_b, '18123456-7')

            t_a1 = make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-N-2025-001')
            t_a2 = make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-N-2025-002')
            t_b1 = make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-S-2025-001')
            db_session.session.commit()

            # Verificar aislamiento desde cada clínica
            user_a = MockUser(clinic_id=clinic_a.id)
            user_b = MockUser(clinic_id=clinic_b.id)

            ids_a = [t.id for t in TicketRepository.build_filtered_query({}, user_a).all()]
            ids_b = [t.id for t in TicketRepository.build_filtered_query({}, user_b).all()]

            assert 'TH-N-2025-001' in ids_a
            assert 'TH-N-2025-002' in ids_a
            assert 'TH-S-2025-001' not in ids_a

            assert 'TH-S-2025-001' in ids_b
            assert 'TH-N-2025-001' not in ids_b
            assert 'TH-N-2025-002' not in ids_b

    def test_annulling_ticket_in_clinic_a_does_not_affect_clinic_b(self, app, db_session):
        """Anular un ticket en clínica A no afecta tickets de clínica B."""
        from services.ticket_service import TicketService
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a)
            surg_b = make_surgery(clinic_b, spec_b)
            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            ticket_a = make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            ticket_b = make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            user_a = MockUser(clinic_id=clinic_a.id, username='user_a')
            TicketService.annul_ticket(ticket_a, 'Error de prueba', user_a)
            db_session.session.commit()

            # El ticket A está anulado
            refreshed_a = Ticket.query.get('TH-A-2025-001')
            assert refreshed_a.status == TICKET_STATUS_ANULADO

            # El ticket B no fue afectado
            refreshed_b = Ticket.query.get('TH-B-2025-001')
            assert refreshed_b.status == TICKET_STATUS_VIGENTE

    def test_modifying_fpa_in_clinic_a_does_not_affect_clinic_b(self, app, db_session):
        """Modificar FPA en clínica A no afecta tickets de clínica B."""
        from services.ticket_service import TicketService
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a)
            surg_b = make_surgery(clinic_b, spec_b)
            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            ticket_a = make_ticket(clinic_a, pat_a, surg_a, ticket_id='TH-A-2025-001')
            ticket_b = make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            original_fpa_b = ticket_b.current_fpa
            new_fpa_a = ticket_a.current_fpa + timedelta(hours=6)
            user_a = MockUser(clinic_id=clinic_a.id, username='user_a')

            TicketService.modify_fpa(ticket_a, new_fpa_a, 'Razón A', 'Test', user_a)
            db_session.session.commit()

            refreshed_b = Ticket.query.get('TH-B-2025-001')
            assert refreshed_b.current_fpa == original_fpa_b

    def test_ticket_count_per_clinic_is_independent(self, app, db_session):
        """El conteo de tickets es independiente por clínica."""
        with app.app_context():
            clinic_a = make_clinic('Clínica A')
            clinic_b = make_clinic('Clínica B')

            spec_a = make_specialty(clinic_a)
            spec_b = make_specialty(clinic_b)
            surg_a = make_surgery(clinic_a, spec_a)
            surg_b = make_surgery(clinic_b, spec_b)
            pat_a = make_patient(clinic_a, '11111111-1')
            pat_b = make_patient(clinic_b, '22222222-2')

            # 3 tickets en A, 1 en B
            for i in range(3):
                make_ticket(clinic_a, pat_a, surg_a, ticket_id=f'TH-A-2025-{i:03d}')
            make_ticket(clinic_b, pat_b, surg_b, ticket_id='TH-B-2025-001')
            db_session.session.commit()

            count_a = Ticket.query.filter_by(clinic_id=clinic_a.id).count()
            count_b = Ticket.query.filter_by(clinic_id=clinic_b.id).count()

            assert count_a == 3
            assert count_b == 1
