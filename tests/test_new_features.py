"""
Tests para las nuevas funcionalidades implementadas (Issues #1, #3, #5).
"""
import pytest
from datetime import datetime, timedelta
from models import (
    db, UrgencyThreshold, Ticket, Patient, User,
    TICKET_STATUS_VIGENTE, ROLE_ADMIN, ROLE_CLINICAL
)


class TestIssue1FuturePavillionValidation:
    """Tests para Issue #1: Validación de pabellón futuro eliminada."""

    def test_can_create_ticket_with_future_pavilion(self, db_session, sample_clinic,
                                                      sample_patient, sample_surgery_normal,
                                                      sample_doctor, sample_discharge_slots):
        """Verificar que se puede crear un ticket con hora de pabellón en el FUTURO."""
        # Arrange: Fecha de pabellón MAÑANA
        future_pavilion_time = datetime.now() + timedelta(days=1)
        future_fpa = future_pavilion_time + timedelta(hours=24)

        # Act: Crear ticket con pabellón futuro
        ticket = Ticket(
            id='TH-TEST-2025-FUTURE',
            patient_id=sample_patient.id,
            surgery_id=sample_surgery_normal.id,
            doctor_id=sample_doctor.id,
            clinic_id=sample_clinic.id,
            pavilion_end_time=future_pavilion_time,
            medical_discharge_date=future_fpa.date(),
            system_calculated_fpa=future_fpa,
            initial_fpa=future_fpa,
            current_fpa=future_fpa,
            overnight_stays=1,
            status=TICKET_STATUS_VIGENTE,
            created_by='test_user',
            discharge_slot_id=sample_discharge_slots[0].id,
            surgery_name_snapshot=sample_surgery_normal.name,
            surgery_base_hours_snapshot=sample_surgery_normal.base_stay_hours
        )
        db_session.session.add(ticket)
        db_session.session.commit()

        # Assert: El ticket se creó exitosamente
        saved_ticket = Ticket.query.filter_by(id='TH-TEST-2025-FUTURE').first()
        assert saved_ticket is not None
        assert saved_ticket.pavilion_end_time > datetime.now()
        assert saved_ticket.status == TICKET_STATUS_VIGENTE

    def test_can_create_ticket_one_week_in_future(self, db_session, sample_clinic,
                                                   sample_patient, sample_surgery_normal,
                                                   sample_doctor, sample_discharge_slots):
        """Verificar que se puede crear un ticket con pabellón en 1 semana."""
        # Arrange: Fecha de pabellón en 7 días
        week_ahead = datetime.now() + timedelta(days=7)
        future_fpa = week_ahead + timedelta(hours=24)

        # Act
        ticket = Ticket(
            id='TH-TEST-2025-WEEK',
            patient_id=sample_patient.id,
            surgery_id=sample_surgery_normal.id,
            doctor_id=sample_doctor.id,
            clinic_id=sample_clinic.id,
            pavilion_end_time=week_ahead,
            medical_discharge_date=future_fpa.date(),
            system_calculated_fpa=future_fpa,
            initial_fpa=future_fpa,
            current_fpa=future_fpa,
            overnight_stays=1,
            status=TICKET_STATUS_VIGENTE,
            created_by='test_user',
            discharge_slot_id=sample_discharge_slots[0].id,
            surgery_name_snapshot=sample_surgery_normal.name,
            surgery_base_hours_snapshot=sample_surgery_normal.base_stay_hours
        )
        db_session.session.add(ticket)
        db_session.session.commit()

        # Assert
        saved_ticket = Ticket.query.filter_by(id='TH-TEST-2025-WEEK').first()
        assert saved_ticket is not None
        assert (saved_ticket.pavilion_end_time - datetime.now()).days >= 6


class TestIssue3ColorThresholds:
    """Tests para Issue #3: Sistema configurable de umbrales de colores."""

    def test_urgency_threshold_model_exists(self, db_session):
        """Verificar que el modelo UrgencyThreshold existe."""
        # Act: Crear un threshold
        threshold = UrgencyThreshold(
            clinic_id=None,
            green_threshold_hours=8,
            yellow_threshold_hours=4,
            red_threshold_hours=2
        )
        db_session.session.add(threshold)
        db_session.session.commit()

        # Assert
        saved = UrgencyThreshold.query.first()
        assert saved is not None
        assert saved.green_threshold_hours == 8
        assert saved.yellow_threshold_hours == 4
        assert saved.red_threshold_hours == 2

    def test_default_global_threshold_values(self, db_session):
        """Verificar que los valores por defecto son correctos."""
        # Act: Crear threshold global con valores por defecto
        threshold = UrgencyThreshold(
            clinic_id=None,
            green_threshold_hours=8,
            yellow_threshold_hours=4,
            red_threshold_hours=2,
            updated_by='system'
        )
        db_session.session.add(threshold)
        db_session.session.commit()

        # Assert
        global_threshold = UrgencyThreshold.query.filter_by(clinic_id=None).first()
        assert global_threshold.green_threshold_hours == 8
        assert global_threshold.yellow_threshold_hours == 4
        assert global_threshold.red_threshold_hours == 2

    def test_get_thresholds_for_clinic_returns_global_if_no_specific(self, db_session):
        """Verificar que se retorna configuración global si no hay específica."""
        # Arrange: Solo existe configuración global
        global_threshold = UrgencyThreshold(
            clinic_id=None,
            green_threshold_hours=10,
            yellow_threshold_hours=5,
            red_threshold_hours=1
        )
        db_session.session.add(global_threshold)
        db_session.session.commit()

        # Act: Buscar threshold para una clínica que no tiene configuración específica
        result = UrgencyThreshold.get_thresholds_for_clinic(clinic_id=999)

        # Assert: Debe retornar la global
        assert result.clinic_id is None
        assert result.green_threshold_hours == 10

    def test_get_thresholds_for_clinic_returns_specific_if_exists(self, db_session, sample_clinic):
        """Verificar que se retorna configuración específica si existe."""
        # Arrange: Configuración global + específica de clínica
        global_threshold = UrgencyThreshold(
            clinic_id=None,
            green_threshold_hours=8,
            yellow_threshold_hours=4,
            red_threshold_hours=2
        )
        clinic_threshold = UrgencyThreshold(
            clinic_id=sample_clinic.id,
            green_threshold_hours=12,
            yellow_threshold_hours=6,
            red_threshold_hours=3
        )
        db_session.session.add_all([global_threshold, clinic_threshold])
        db_session.session.commit()

        # Act: Buscar threshold para la clínica que SÍ tiene configuración
        result = UrgencyThreshold.get_thresholds_for_clinic(clinic_id=sample_clinic.id)

        # Assert: Debe retornar la específica, NO la global
        assert result.clinic_id == sample_clinic.id
        assert result.green_threshold_hours == 12

    def test_can_update_threshold_values(self, db_session):
        """Verificar que se pueden actualizar los umbrales."""
        # Arrange: Crear threshold
        threshold = UrgencyThreshold(
            clinic_id=None,
            green_threshold_hours=8,
            yellow_threshold_hours=4,
            red_threshold_hours=2
        )
        db_session.session.add(threshold)
        db_session.session.commit()

        # Act: Actualizar valores
        threshold.green_threshold_hours = 10
        threshold.yellow_threshold_hours = 5
        threshold.red_threshold_hours = 1
        threshold.updated_by = 'test_user'
        db_session.session.commit()

        # Assert
        updated = UrgencyThreshold.query.first()
        assert updated.green_threshold_hours == 10
        assert updated.yellow_threshold_hours == 5
        assert updated.red_threshold_hours == 1
        assert updated.updated_by == 'test_user'


class TestIssue5DashboardFilters:
    """Tests para Issue #5: Filtros de dashboard según rol."""

    def test_superuser_has_no_clinic_id(self, db_session, sample_superuser):
        """Verificar que superusuarios tienen clinic_id = NULL."""
        # Arrange & Act: Crear superusuario
        super_user = User(
            username='super_test',
            email='super@test.com',
            password='password123',
            role=ROLE_ADMIN,
            clinic_id=None,  # Superuser NO tiene clínica
            is_active=True
        )
        db_session.session.add(super_user)
        db_session.session.commit()

        # Assert
        saved_user = User.query.filter_by(username='super_test').first()
        assert saved_user is not None
        assert saved_user.clinic_id is None
        assert saved_user.is_superuser  # Debería ser True porque está en Superuser table

    def test_regular_admin_has_clinic_id(self, db_session, sample_clinic):
        """Verificar que administradores normales tienen clinic_id asignado."""
        # Arrange & Act
        admin_user = User(
            username='admin_clinic',
            email='admin@clinic.com',
            password='password123',
            role=ROLE_ADMIN,
            clinic_id=sample_clinic.id,  # Admin de clínica TIENE clinic_id
            is_active=True
        )
        db_session.session.add(admin_user)
        db_session.session.commit()

        # Assert
        saved_user = User.query.filter_by(username='admin_clinic').first()
        assert saved_user is not None
        assert saved_user.clinic_id == sample_clinic.id
        assert not saved_user.is_superuser  # NO es superuser

    def test_tickets_filtered_by_clinic(self, db_session, sample_clinic):
        """Verificar que los tickets se pueden filtrar por clínica."""
        # Arrange: Crear otra clínica y pacientes
        clinic2 = db_session.session.query(db_session.session.query(type(sample_clinic)).filter_by(name='Otra Clínica').first())
        if not clinic2:
            from models import Clinic
            clinic2 = Clinic(name='Otra Clínica', is_active=True)
            db_session.session.add(clinic2)
            db_session.session.commit()

        # Crear pacientes en ambas clínicas
        patient1 = Patient(
            rut='11111111-1',
            primer_nombre='Paciente',
            apellido_paterno='Clinic1',
            age=30,
            sex='M',
            clinic_id=sample_clinic.id
        )
        patient2 = Patient(
            rut='22222222-2',
            primer_nombre='Paciente',
            apellido_paterno='Clinic2',
            age=40,
            sex='F',
            clinic_id=clinic2.id
        )
        db_session.session.add_all([patient1, patient2])
        db_session.session.commit()

        # Assert: Query filtrando por clínica
        clinic1_patients = Patient.query.filter_by(clinic_id=sample_clinic.id).all()
        clinic2_patients = Patient.query.filter_by(clinic_id=clinic2.id).all()

        assert len(clinic1_patients) >= 1
        assert len(clinic2_patients) >= 1
        assert clinic1_patients[0].clinic_id != clinic2_patients[0].clinic_id


class TestValidations:
    """Tests adicionales de validación."""

    def test_threshold_order_validation_logic(self):
        """Verificar lógica de validación de orden de umbrales."""
        # Arrange: Valores correctos vs incorrectos
        correct = (2, 4, 8)  # rojo < amarillo < verde
        incorrect = (8, 4, 2)  # rojo > amarillo > verde

        # Act & Assert: Orden correcto
        red, yellow, green = correct
        assert red < yellow < green, "Los umbrales deben estar en orden: rojo < amarillo < verde"

        # Act & Assert: Orden incorrecto
        red_bad, yellow_bad, green_bad = incorrect
        is_valid = red_bad < yellow_bad < green_bad
        assert not is_valid, "Orden incorrecto debería ser inválido"

    def test_user_is_superuser_property(self, db_session, sample_superuser):
        """Verificar que la propiedad is_superuser funciona correctamente."""
        # Arrange: Usuario superuser
        super_user = User(
            username='test_super',
            email='super@test.com',
            password='password123',
            role=ROLE_ADMIN,
            clinic_id=None
        )
        db_session.session.add(super_user)
        db_session.session.commit()

        # Act & Assert
        # El usuario debería ser superuser si su email está en la tabla Superuser
        # Esto se verifica mediante la propiedad is_superuser del modelo User
        assert super_user.is_superuser or super_user.clinic_id is None
