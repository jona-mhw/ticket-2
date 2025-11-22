"""
Tests unitarios para los modelos de Ticket Home.
Prueba los 13 modelos y sus relaciones.
"""
import pytest
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from models import (
    User, Clinic, Specialty, Surgery, Doctor,
    StandardizedReason, Patient, Ticket, FpaModification,
    Superuser, LoginAudit, ActionAudit,
    ROLE_ADMIN, ROLE_CLINICAL, TICKET_STATUS_VIGENTE
)


@pytest.mark.unit
class TestClinicModel:
    """Tests para el modelo Clinic."""

    def test_create_clinic(self, db_session):
        """Test crear una clínica básica."""
        clinic = Clinic(name='Test Clinic', is_active=True)
        db_session.session.add(clinic)
        db_session.session.commit()

        assert clinic.id is not None
        assert clinic.name == 'Test Clinic'
        assert clinic.is_active is True

    def test_clinic_relationships(self, db_session, sample_clinic, sample_user_admin):
        """Test relaciones de la clínica."""
        assert len(sample_clinic.users) == 1
        assert sample_clinic.users[0].id == sample_user_admin.id


@pytest.mark.unit
class TestUserModel:
    """Tests para el modelo User."""

    def test_create_user(self, db_session, sample_clinic):
        """Test crear un usuario."""
        user = User(
            username='testuser',
            email='test@example.com',
            password=generate_password_hash('password'),
            role=ROLE_ADMIN,
            clinic_id=sample_clinic.id
        )
        db_session.session.add(user)
        db_session.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'

    def test_user_is_admin(self, db_session, sample_user_admin):
        """Test método is_admin()."""
        assert sample_user_admin.is_admin() is True

    def test_user_is_superuser(self, db_session, sample_user_super):
        """Test property is_superuser."""
        assert sample_user_super.is_superuser is True
        assert sample_user_super.clinic_id is None

    def test_user_not_superuser(self, db_session, sample_user_admin):
        """Test que usuario normal no sea superuser."""
        assert sample_user_admin.is_superuser is False


@pytest.mark.unit
class TestSuperuserModel:
    """Tests para el modelo Superuser."""

    def test_create_superuser(self, db_session):
        """Test crear entrada en tabla Superuser."""
        superuser = Superuser(email='super@test.com')
        db_session.session.add(superuser)
        db_session.session.commit()

        assert superuser.id is not None
        assert superuser.email == 'super@test.com'


@pytest.mark.unit
class TestSpecialtyModel:
    """Tests para el modelo Specialty."""

    def test_create_specialty(self, db_session, sample_clinic):
        """Test crear especialidad."""
        specialty = Specialty(
            name='Traumatología',
            clinic_id=sample_clinic.id
        )
        db_session.session.add(specialty)
        db_session.session.commit()

        assert specialty.id is not None
        assert specialty.name == 'Traumatología'

    def test_specialty_to_dict(self, db_session, sample_specialty):
        """Test método to_dict()."""
        data = sample_specialty.to_dict()
        assert data['name'] == sample_specialty.name
        assert data['id'] == sample_specialty.id


@pytest.mark.unit
class TestSurgeryModel:
    """Tests para el modelo Surgery."""

    def test_create_surgery(self, db_session, sample_clinic, sample_specialty):
        """Test crear cirugía."""
        surgery = Surgery(
            name='Apendicectomía',
            base_stay_hours=12,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        assert surgery.id is not None
        assert surgery.name == 'Apendicectomía'
        assert surgery.base_stay_hours == 12

    def test_ambulatory_surgery(self, db_session, sample_surgery_ambulatory):
        """Test cirugía ambulatoria con cutoff hour."""
        assert sample_surgery_ambulatory.is_ambulatory is True
        assert sample_surgery_ambulatory.ambulatory_cutoff_hour == 14


@pytest.mark.unit
class TestDoctorModel:
    """Tests para el modelo Doctor."""

    def test_create_doctor(self, db_session, sample_clinic):
        """Test crear doctor."""
        doctor = Doctor(
            name='Dra. Ana López',
            specialty='Traumatología',
            rut='98765432-1',
            clinic_id=sample_clinic.id
        )
        db_session.session.add(doctor)
        db_session.session.commit()

        assert doctor.id is not None
        assert doctor.name == 'Dra. Ana López'


# TestDischargeTimeSlotModel removed as the model was deleted.


@pytest.mark.unit
class TestStandardizedReasonModel:
    """Tests para el modelo StandardizedReason."""

    def test_create_reason(self, db_session, sample_clinic):
        """Test crear razón estandarizada."""
        from models import REASON_CATEGORY_MODIFICATION
        reason = StandardizedReason(
            reason='Test reason',
            category=REASON_CATEGORY_MODIFICATION,
            clinic_id=sample_clinic.id
        )
        db_session.session.add(reason)
        db_session.session.commit()

        assert reason.id is not None
        assert reason.reason == 'Test reason'


@pytest.mark.unit
class TestPatientModel:
    """Tests para el modelo Patient."""

    def test_create_patient(self, db_session, sample_clinic):
        """Test crear paciente."""
        patient = Patient(
            rut='12345678-9',
            primer_nombre='María',
            apellido_paterno='González',
            age=30,
            sex='F',
            clinic_id=sample_clinic.id
        )
        db_session.session.add(patient)
        db_session.session.commit()

        assert patient.id is not None
        assert patient.rut == '12345678-9'

    def test_patient_full_name(self, db_session, sample_patient):
        """Test property full_name."""
        expected = 'Juan Carlos Pérez González'
        assert sample_patient.full_name == expected

    def test_patient_full_name_partial(self, db_session, sample_clinic):
        """Test full_name con nombres parciales."""
        patient = Patient(
            rut='99999999-9',
            primer_nombre='Pedro',
            apellido_paterno='Soto',
            age=25,
            sex='M',
            clinic_id=sample_clinic.id
        )
        db_session.session.add(patient)
        db_session.session.commit()

        assert patient.full_name == 'Pedro Soto'


@pytest.mark.unit
class TestTicketModel:
    """Tests para el modelo Ticket."""

    def test_create_ticket(self, db_session, sample_ticket):
        """Test crear ticket."""
        assert sample_ticket.id == 'TH-TEST-2025-001'
        assert sample_ticket.status == TICKET_STATUS_VIGENTE

    def test_ticket_can_be_modified(self, db_session, sample_ticket):
        """Test método can_be_modified()."""
        assert sample_ticket.can_be_modified() is True

        from models import TICKET_STATUS_ANULADO
        sample_ticket.status = TICKET_STATUS_ANULADO
        db_session.session.commit()

        assert sample_ticket.can_be_modified() is False

    def test_ticket_modification_count(self, db_session, sample_ticket):
        """Test método get_modification_count()."""
        assert sample_ticket.get_modification_count() == 0

        # Agregar modificación
        mod = FpaModification(
            ticket_id=sample_ticket.id,
            clinic_id=sample_ticket.clinic_id,
            previous_fpa=sample_ticket.current_fpa,
            new_fpa=sample_ticket.current_fpa + timedelta(hours=2),
            reason='Test',
            modified_by='test_user'
        )
        db_session.session.add(mod)
        db_session.session.commit()

        assert sample_ticket.get_modification_count() == 1


@pytest.mark.unit
class TestFpaModificationModel:
    """Tests para el modelo FpaModification."""

    def test_create_modification(self, db_session, sample_ticket):
        """Test crear modificación de FPA."""
        old_fpa = sample_ticket.current_fpa
        new_fpa = old_fpa + timedelta(hours=3)

        mod = FpaModification(
            ticket_id=sample_ticket.id,
            clinic_id=sample_ticket.clinic_id,
            previous_fpa=old_fpa,
            new_fpa=new_fpa,
            reason='Complicación post-operatoria',
            justification='Paciente requiere observación',
            modified_by='clinical_user'
        )
        db_session.session.add(mod)
        db_session.session.commit()

        assert mod.id is not None
        assert mod.reason == 'Complicación post-operatoria'


@pytest.mark.unit
class TestLoginAuditModel:
    """Tests para el modelo LoginAudit."""

    def test_create_login_audit(self, db_session, sample_user_admin, sample_clinic):
        """Test crear registro de auditoría de login."""
        audit = LoginAudit(
            user_id=sample_user_admin.id,
            username=sample_user_admin.username,
            clinic_id=sample_clinic.id,
            ip_address='192.168.1.1'
        )
        db_session.session.add(audit)
        db_session.session.commit()

        assert audit.id is not None
        assert audit.username == sample_user_admin.username


@pytest.mark.unit
class TestActionAuditModel:
    """Tests para el modelo ActionAudit."""

    def test_create_action_audit(self, db_session, sample_user_admin, sample_clinic):
        """Test crear registro de auditoría de acción."""
        audit = ActionAudit(
            user_id=sample_user_admin.id,
            username=sample_user_admin.username,
            clinic_id=sample_clinic.id,
            action='create_ticket',
            target_id='TH-TEST-2025-001',
            target_type='Ticket'
        )
        db_session.session.add(audit)
        db_session.session.commit()

        assert audit.id is not None
        assert audit.action == 'create_ticket'
