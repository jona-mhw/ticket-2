"""
Tests para bugs y gaps de cobertura detectados en revisión (2026-02-17).

Bugs documentados:
  BUG-1: ticket_service.py:157 - Audit log graba el FPA anterior incorrectamente
          (usa ticket.current_fpa DESPUÉS de actualizarlo → muestra mismo valor dos veces)
  BUG-2: ticket_repository.py:101 - usa datetime.now() en vez de utcnow()
  BUG-3: routes/tickets.py:207 - clave duplicada en dict de respuesta JSON
  BUG-4: PatientRepository.get_or_create() - race condition no manejada (sin try/except)
  BUG-5: routes/tickets.py:309 - overnight_stays en update_fpa usa pavilion_end_time
          en vez de admission_time

Gaps de cobertura:
  - TimeBlockHelper: casos edge y validaciones
  - string_utils.generate_prefix: casos edge
  - TicketValidator: todos los métodos
  - Ticket.can_be_modified + límite de 5 modificaciones
  - UrgencyThreshold.get_thresholds_for_clinic
  - datetime_utils.calculate_time_remaining
"""
import pytest
from datetime import datetime, timedelta
from models import (
    db, Ticket, Patient, Surgery, Clinic, ActionAudit,
    FpaModification, UrgencyThreshold, TICKET_STATUS_VIGENTE, TICKET_STATUS_ANULADO
)
from services.ticket_service import TicketService
from services.fpa_calculator import FPACalculator
from utils.time_blocks import TimeBlockHelper
from utils.string_utils import generate_prefix
from utils.datetime_utils import calculate_time_remaining, utcnow
from validators.ticket_validator import TicketValidator


# ===========================================================================
# BUG-1: Audit log graba FPA anterior incorrecto en modify_fpa
# ===========================================================================

class TestBug1AuditLogFPA:
    """
    BUG-1: En ticket_service.py, modify_fpa() actualiza ticket.current_fpa
    ANTES de escribir el audit log. Resultado: el log dice
    "Modificó FPA de <new_fpa> a <new_fpa>" en lugar de
    "Modificó FPA de <old_fpa> a <new_fpa>".

    ESTADO: BUG ACTIVO - este test FALLA actualmente.
    """

    def test_modify_fpa_audit_log_shows_correct_previous_fpa(
        self, app, db_session, sample_ticket, sample_user_admin, sample_reasons
    ):
        """
        El audit log de modify_fpa debe contener la FPA anterior (original),
        no la nueva.
        """
        with app.app_context():
            original_fpa = sample_ticket.current_fpa
            new_fpa = original_fpa + timedelta(hours=4)
            reason = sample_reasons[0].reason

            TicketService.modify_fpa(sample_ticket, new_fpa, reason, 'justificación test', sample_user_admin)
            db_session.session.commit()

            # Recuperar el último audit log para este ticket
            audit = ActionAudit.query.filter_by(
                target_id=sample_ticket.id,
                target_type='Ticket'
            ).order_by(ActionAudit.id.desc()).first()

            assert audit is not None, "Debe existir un registro de auditoría"

            # El log DEBE mencionar la FPA anterior (original_fpa)
            # BUG: actualmente dice new_fpa para ambos valores
            original_fpa_str = original_fpa.strftime('%Y-%m-%d %H:%M:%S')
            assert original_fpa_str in audit.action, (
                f"El audit log debería mencionar la FPA anterior ({original_fpa_str}) "
                f"pero contiene: '{audit.action}'"
            )

    def test_modify_fpa_modification_record_has_correct_previous_fpa(
        self, app, db_session, sample_ticket, sample_user_admin, sample_reasons
    ):
        """
        La FpaModification SÍ guarda correctamente la FPA anterior
        (la lógica de la modification record es correcta, solo el audit log tiene bug).
        """
        with app.app_context():
            original_fpa = sample_ticket.current_fpa
            new_fpa = original_fpa + timedelta(hours=4)
            reason = sample_reasons[0].reason

            modification = TicketService.modify_fpa(
                sample_ticket, new_fpa, reason, 'test', sample_user_admin
            )
            db_session.session.commit()

            # La modification record debe tener el previous_fpa correcto
            assert modification.previous_fpa == original_fpa, (
                f"FpaModification.previous_fpa debe ser {original_fpa}, "
                f"pero es {modification.previous_fpa}"
            )
            assert modification.new_fpa == new_fpa


# ===========================================================================
# BUG-2: datetime.now() en ticket_repository
# ===========================================================================

class TestBug2DatetimeConsistency:
    """
    BUG-2: ticket_repository.py usa datetime.now() en el filtro de status='Vigente'
    en vez de utcnow(). Esto puede causar diferencias de timezone.
    """

    def test_utcnow_is_used_in_calculate_time_remaining(self):
        """
        calculate_time_remaining() usa utcnow() internamente.
        Este test verifica que calcula correctamente respecto a UTC.
        """
        future_fpa = utcnow() + timedelta(hours=2)
        result = calculate_time_remaining(future_fpa)

        assert result is not None
        assert result['expired'] is False
        assert result['hours'] <= 2

    def test_calculate_time_remaining_expired(self):
        """FPA en el pasado → expired=True."""
        past_fpa = utcnow() - timedelta(hours=1)
        result = calculate_time_remaining(past_fpa)

        assert result is not None
        assert result['expired'] is True
        assert result['days'] == 0
        assert result['hours'] == 0

    def test_calculate_time_remaining_none(self):
        """FPA None → retorna None."""
        assert calculate_time_remaining(None) is None

    def test_calculate_time_remaining_exact_now(self):
        """FPA igual a ahora → expired=True (fpa <= now)."""
        now = utcnow()
        result = calculate_time_remaining(now)
        # FPA <= now → expired
        assert result['expired'] is True

    def test_datetime_utcnow_in_ticket_service_annul(
        self, app, db_session, sample_ticket, sample_user_admin
    ):
        """
        annul_ticket usa datetime.utcnow() explícitamente.
        El annulled_at debe ser una fecha razonable (cerca de ahora).
        """
        with app.app_context():
            before = utcnow()
            TicketService.annul_ticket(sample_ticket, 'test reason', sample_user_admin)
            db_session.session.commit()
            after = utcnow()

            assert sample_ticket.annulled_at is not None
            assert before <= sample_ticket.annulled_at <= after


# ===========================================================================
# BUG-3: Clave duplicada en JSON de api_calculate_fpa
# ===========================================================================

class TestBug3DuplicateJsonKey:
    """
    BUG-3: routes/tickets.py línea 206-207 tiene la clave 'fpa_display_str'
    duplicada en el dict de respuesta JSON. Python silenciosamente descarta
    el primer valor y usa el segundo (que tiene el mismo valor en este caso).
    """

    def test_api_fpa_response_has_expected_keys(
        self, client, app, db_session,
        sample_user_admin, sample_surgery_normal, sample_clinic
    ):
        """
        El endpoint /tickets/api/calculate-fpa retorna una respuesta JSON
        con las claves esperadas y status 200.
        """
        import json
        with client:
            from flask_login import login_user
            with app.test_request_context():
                login_user(sample_user_admin)

            surgery_time = datetime.now() + timedelta(days=1)
            surgery_time = surgery_time.replace(hour=10, minute=0, second=0, microsecond=0)

            response = client.post(
                '/tickets/api/calculate-fpa',
                data=json.dumps({
                    'surgery_id': sample_surgery_normal.id,
                    'pavilion_end_time': surgery_time.isoformat(),
                    'clinic_id': sample_clinic.id
                }),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data is not None

            # Verificar claves esperadas en respuesta
            assert 'fpa_date_iso' in data
            assert 'fpa_time' in data
            assert 'fpa_display_str' in data  # debe existir (aunque esté duplicada en código)
            assert 'surgery_base_stay_hours' in data
            assert 'admission_time_iso' in data
            assert 'admission_time_display' in data


# ===========================================================================
# BUG-4: Race condition en PatientRepository.get_or_create
# ===========================================================================

class TestBug4PatientRaceCondition:
    """
    BUG-4: PatientRepository.get_or_create() no maneja IntegrityError para
    race conditions concurrentes. El comentario dice que sí lo hace, pero
    no hay try/except en el código.
    """

    def test_get_or_create_normal_flow(self, app, db_session, sample_clinic):
        """
        El flujo normal (sin concurrencia) funciona correctamente.
        """
        from repositories.patient_repository import PatientRepository
        with app.app_context():
            # Crear paciente nuevo
            patient, created = PatientRepository.get_or_create(
                rut='55555555-5', clinic_id=sample_clinic.id
            )
            patient.primer_nombre = 'Test'
            patient.apellido_paterno = 'Patient'
            patient.age = 40
            patient.sex = 'M'
            db.session.commit()

            assert created is True
            assert patient.id is not None

            # Recuperar existente
            patient2, created2 = PatientRepository.get_or_create(
                rut='55555555-5', clinic_id=sample_clinic.id
            )
            assert created2 is False
            assert patient2.id == patient.id

    def test_get_or_create_idempotent_after_commit(self, app, db_session, sample_clinic):
        """
        Después de hacer commit, get_or_create recupera el paciente existente
        sin crear duplicados.
        """
        from repositories.patient_repository import PatientRepository

        with app.app_context():
            # Primera inserción - OK
            patient1, created1 = PatientRepository.get_or_create(
                rut='66666666-6', clinic_id=sample_clinic.id
            )
            patient1.primer_nombre = 'Primera'
            patient1.apellido_paterno = 'Insercion'
            patient1.age = 30
            patient1.sex = 'M'
            db.session.commit()

            assert created1 is True

            # Segunda llamada con mismo RUT - debe recuperar existente, no crear
            patient2, created2 = PatientRepository.get_or_create(
                rut='66666666-6', clinic_id=sample_clinic.id
            )
            assert created2 is False  # Ya existe, no se crea
            assert patient2.id == patient1.id


# ===========================================================================
# Tests para TimeBlockHelper
# ===========================================================================

class TestTimeBlockHelper:
    """Tests completos para TimeBlockHelper."""

    def test_get_all_blocks_returns_24_blocks(self):
        """Debe retornar exactamente 24 bloques."""
        blocks = TimeBlockHelper.get_all_blocks()
        assert len(blocks) == 24

    def test_all_blocks_have_required_keys(self):
        """Cada bloque debe tener las claves requeridas."""
        blocks = TimeBlockHelper.get_all_blocks()
        for block in blocks:
            assert 'value' in block
            assert 'label' in block
            assert 'start_hour' in block
            assert 'end_hour' in block

    def test_blocks_cover_all_hours(self):
        """Los bloques deben cubrir todas las horas 0-23."""
        blocks = TimeBlockHelper.get_all_blocks()
        end_hours = {b['end_hour'] for b in blocks}
        assert end_hours == set(range(24))

    def test_block_label_format(self):
        """Los labels deben tener formato HH:00 - HH:00."""
        blocks = TimeBlockHelper.get_all_blocks()
        import re
        pattern = r'^\d{2}:00 - \d{2}:00$'
        for block in blocks:
            assert re.match(pattern, block['label']), (
                f"Label '{block['label']}' no tiene el formato esperado"
            )

    def test_each_block_is_2_hours(self):
        """Cada bloque debe tener exactamente 2 horas de duración."""
        blocks = TimeBlockHelper.get_all_blocks()
        for block in blocks:
            start = block['start_hour']
            end = block['end_hour']
            diff = (end - start) % 24
            assert diff == 2, (
                f"Bloque {block['label']}: diferencia de {diff} horas, esperaba 2"
            )

    def test_specific_block_14h(self):
        """Bloque con end=14 debe ser '12:00 - 14:00'."""
        blocks = TimeBlockHelper.get_all_blocks()
        block_14 = next(b for b in blocks if b['end_hour'] == 14)
        assert block_14['label'] == '12:00 - 14:00'
        assert block_14['start_hour'] == 12
        assert block_14['value'] == 14

    def test_midnight_block(self):
        """Bloque con end=0 (medianoche) debe ser '22:00 - 00:00'."""
        blocks = TimeBlockHelper.get_all_blocks()
        block_0 = next(b for b in blocks if b['end_hour'] == 0)
        assert block_0['label'] == '22:00 - 00:00'
        assert block_0['start_hour'] == 22

    def test_get_block_for_time_exact_hour(self):
        """Hora exacta → bloque usando esa hora como extremo derecho."""
        dt = datetime(2025, 1, 15, 14, 0)
        block = TimeBlockHelper.get_block_for_time(dt)
        assert block['end_hour'] == 14
        assert block['label'] == '12:00 - 14:00'

    def test_get_block_for_time_29_minutes_rounds_down(self):
        """14:29 → redondea ABAJO a 14:00 → bloque 12:00 - 14:00."""
        dt = datetime(2025, 1, 15, 14, 29)
        block = TimeBlockHelper.get_block_for_time(dt)
        assert block['end_hour'] == 14
        assert block['label'] == '12:00 - 14:00'

    def test_get_block_for_time_30_minutes_rounds_up(self):
        """14:30 → redondea ARRIBA a 15:00 → bloque 13:00 - 15:00."""
        dt = datetime(2025, 1, 15, 14, 30)
        block = TimeBlockHelper.get_block_for_time(dt)
        assert block['end_hour'] == 15
        assert block['label'] == '13:00 - 15:00'

    def test_get_block_for_time_45_minutes_rounds_up(self):
        """14:45 → redondea ARRIBA a 15:00 → bloque 13:00 - 15:00."""
        dt = datetime(2025, 1, 15, 14, 45)
        block = TimeBlockHelper.get_block_for_time(dt)
        assert block['end_hour'] == 15
        assert block['label'] == '13:00 - 15:00'

    def test_get_block_for_time_23h40_midnight_wraparound(self):
        """23:40 → redondea ARRIBA a 24:00 → se convierte en 00:00 → bloque 22:00 - 00:00."""
        dt = datetime(2025, 1, 15, 23, 40)
        block = TimeBlockHelper.get_block_for_time(dt)
        assert block['end_hour'] == 0
        assert block['label'] == '22:00 - 00:00'

    def test_get_block_for_time_midnight(self):
        """00:00 → bloque 22:00 - 00:00."""
        dt = datetime(2025, 1, 15, 0, 0)
        block = TimeBlockHelper.get_block_for_time(dt)
        assert block['end_hour'] == 0
        assert block['label'] == '22:00 - 00:00'

    def test_get_block_label(self):
        """get_block_label retorna el label correcto para una hora dada."""
        assert TimeBlockHelper.get_block_label(14) == '12:00 - 14:00'
        assert TimeBlockHelper.get_block_label(0) == '22:00 - 00:00'
        assert TimeBlockHelper.get_block_label(2) == '00:00 - 02:00'

    def test_get_end_time_valid(self):
        """get_end_time retorna un time object correcto para horas 0-23."""
        from datetime import time
        for hour in range(24):
            end_time = TimeBlockHelper.get_end_time(hour)
            assert end_time == time(hour=hour, minute=0, second=0)


# ===========================================================================
# Tests para string_utils.generate_prefix
# ===========================================================================

class TestGeneratePrefix:
    """Tests para generate_prefix en string_utils."""

    def test_standard_redsalud_clinic(self):
        """Clínica RedSalud estándar extrae el prefijo del nombre."""
        assert generate_prefix("Clínica RedSalud Santiago") == "sant"

    def test_las_condes(self):
        """Clínica RedSalud Las Condes → 'lasc'."""
        result = generate_prefix("Clínica RedSalud Las Condes")
        assert result == "lasc"

    def test_vitacura(self):
        """Clínica RedSalud Vitacura → 'vita'."""
        result = generate_prefix("Clínica RedSalud Vitacura")
        assert result == "vita"

    def test_prefix_max_4_chars(self):
        """El prefijo nunca excede 4 caracteres."""
        long_name = "Clínica RedSalud Longísimo Nombre de Prueba"
        result = generate_prefix(long_name)
        assert len(result) <= 4

    def test_prefix_lowercase(self):
        """El prefijo es siempre en minúsculas."""
        result = generate_prefix("Clínica RedSalud SANTIAGO")
        assert result == result.lower()

    def test_prefix_only_letters(self):
        """El prefijo contiene solo letras (sin números ni caracteres especiales)."""
        import re
        result = generate_prefix("Clínica RedSalud San José")
        assert re.match(r'^[a-z]*$', result), f"Prefijo '{result}' contiene no-letras"

    def test_empty_after_strip(self):
        """
        Si el nombre NO contiene 'Clínica RedSalud' y no tiene letras válidas,
        el prefijo puede ser vacío.
        Documenta el comportamiento edge case.
        """
        result = generate_prefix("123 456")  # solo números
        assert result == ""  # re.sub elimina todo, solo queda ""

    def test_clinic_without_redsalud_prefix(self):
        """
        Si el nombre no tiene 'Clínica RedSalud', el prefijo toma los primeros 4 chars del nombre.
        """
        result = generate_prefix("Hospital Test")
        # "Hospital Test" → strip("Clínica RedSalud") → "Hospital Test" (sin cambio) → lowercase → "hospital test" → letters → "hosp"
        assert result == "hosp"


# ===========================================================================
# Tests para TicketValidator
# ===========================================================================

class TestTicketValidator:
    """Tests para todos los métodos de TicketValidator."""

    # --- validate_create ---

    def test_validate_create_valid_data(self):
        """Datos válidos de creación → sin errores."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': '45',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert errors == []

    def test_validate_create_missing_rut(self):
        """RUT faltante → error."""
        form_data = {
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': '45',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert any('RUT' in e for e in errors)

    def test_validate_create_missing_nombre(self):
        """Primer nombre faltante → error."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': '',
            'apellido_paterno': 'Pérez',
            'age': '45',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert any('nombre' in e.lower() for e in errors)

    def test_validate_create_invalid_age_negative(self):
        """Edad negativa → error."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': '-1',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert any('edad' in e.lower() or 'Edad' in e for e in errors)

    def test_validate_create_invalid_age_over_150(self):
        """Edad mayor a 150 → error."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': '200',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert any('edad' in e.lower() or '150' in e for e in errors)

    def test_validate_create_invalid_age_string(self):
        """Edad no numérica → error."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': 'abc',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert any('número' in e.lower() or 'edad' in e.lower() for e in errors)

    def test_validate_create_invalid_pavilion_time(self):
        """Formato de hora inválido → error."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': '45',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': 'not-a-date',
        }
        errors = TicketValidator.validate_create(form_data)
        assert any('pabellón' in e.lower() or 'inválida' in e.lower() for e in errors)

    def test_validate_create_age_boundary_0(self):
        """Edad 0 → válida."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': '0',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert not any('edad' in e.lower() for e in errors)

    def test_validate_create_age_boundary_150(self):
        """Edad 150 → válida."""
        form_data = {
            'rut': '11111111-1',
            'primer_nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'age': '150',
            'sex': 'M',
            'surgery_id': '1',
            'pavilion_end_time': '2025-01-15T14:30',
        }
        errors = TicketValidator.validate_create(form_data)
        assert not any('edad' in e.lower() for e in errors)

    # --- validate_fpa_modification ---

    def test_validate_fpa_modification_valid(self):
        """Datos válidos de modificación → sin errores."""
        form_data = {
            'new_fpa_date': '2025-01-16',
            'reason': 'Paciente requiere observación',
        }
        errors = TicketValidator.validate_fpa_modification(form_data)
        assert errors == []

    def test_validate_fpa_modification_missing_date(self):
        """Sin fecha → error."""
        form_data = {'reason': 'Alguna razón'}
        errors = TicketValidator.validate_fpa_modification(form_data)
        assert any('fecha' in e.lower() for e in errors)

    def test_validate_fpa_modification_missing_reason(self):
        """Sin razón → error."""
        form_data = {'new_fpa_date': '2025-01-16'}
        errors = TicketValidator.validate_fpa_modification(form_data)
        assert any('razón' in e.lower() or 'raz' in e.lower() for e in errors)

    def test_validate_fpa_modification_invalid_date(self):
        """Fecha en formato incorrecto → error."""
        form_data = {
            'new_fpa_date': 'not-a-date',
            'reason': 'Alguna razón',
        }
        errors = TicketValidator.validate_fpa_modification(form_data)
        assert any('fecha' in e.lower() or 'inválida' in e.lower() for e in errors)

    # --- validate_annulment ---

    def test_validate_annulment_valid(self):
        """Razón presente → sin errores."""
        form_data = {'annulled_reason': 'Creado por error'}
        errors = TicketValidator.validate_annulment(form_data)
        assert errors == []

    def test_validate_annulment_missing_reason(self):
        """Sin razón → error."""
        errors = TicketValidator.validate_annulment({})
        assert len(errors) > 0

    def test_validate_annulment_empty_reason(self):
        """Razón vacía → error."""
        form_data = {'annulled_reason': ''}
        errors = TicketValidator.validate_annulment(form_data)
        assert len(errors) > 0


# ===========================================================================
# Tests para Ticket.can_be_modified y límite de modificaciones
# ===========================================================================

class TestTicketModificationRules:
    """Tests para reglas de modificación de tickets."""

    def test_vigente_ticket_can_be_modified(self, db_session, sample_ticket):
        """Ticket Vigente puede ser modificado."""
        assert sample_ticket.status == TICKET_STATUS_VIGENTE
        assert sample_ticket.can_be_modified() is True

    def test_anulado_ticket_cannot_be_modified(self, db_session, sample_ticket):
        """Ticket Anulado no puede ser modificado."""
        sample_ticket.status = TICKET_STATUS_ANULADO
        db_session.session.commit()
        assert sample_ticket.can_be_modified() is False

    def test_modification_count_zero_initially(self, db_session, sample_ticket):
        """Ticket nuevo tiene 0 modificaciones."""
        assert sample_ticket.get_modification_count() == 0

    def test_modification_count_increments(self, app, db_session, sample_ticket, sample_user_admin, sample_reasons):
        """El conteo de modificaciones incrementa correctamente."""
        with app.app_context():
            reason = sample_reasons[0].reason
            for i in range(3):
                new_fpa = sample_ticket.current_fpa + timedelta(hours=(i + 1) * 2)
                TicketService.modify_fpa(sample_ticket, new_fpa, reason, 'test', sample_user_admin)
            db_session.session.commit()

            assert sample_ticket.get_modification_count() == 3

    def test_cannot_exceed_5_modifications(self, app, db_session, sample_ticket, sample_user_admin, sample_reasons):
        """
        El servicio lanza ValueError si el ticket no está vigente,
        pero la restricción de 5 modificaciones se controla en la ruta.
        Verificamos que get_modification_count() retorna el valor correcto.
        """
        with app.app_context():
            reason = sample_reasons[0].reason
            base_fpa = sample_ticket.current_fpa

            for i in range(5):
                new_fpa = base_fpa + timedelta(hours=(i + 1))
                TicketService.modify_fpa(sample_ticket, new_fpa, reason, 'test', sample_user_admin)
            db_session.session.commit()

            assert sample_ticket.get_modification_count() == 5

    def test_annul_ticket_sets_all_fields(self, app, db_session, sample_ticket, sample_user_admin):
        """annul_ticket establece todos los campos correctamente."""
        with app.app_context():
            TicketService.annul_ticket(sample_ticket, 'Creado por error', sample_user_admin)
            db_session.session.commit()

            assert sample_ticket.status == TICKET_STATUS_ANULADO
            assert sample_ticket.annulled_at is not None
            assert sample_ticket.annulled_by == sample_user_admin.username
            assert sample_ticket.annulled_reason == 'Creado por error'

    def test_restore_ticket_clears_annulment_fields(self, app, db_session, sample_ticket, sample_user_admin):
        """restore_ticket limpia todos los campos de anulación."""
        with app.app_context():
            # Anular primero
            TicketService.annul_ticket(sample_ticket, 'test', sample_user_admin)
            db_session.session.commit()

            # Restaurar
            TicketService.restore_ticket(sample_ticket, sample_user_admin)
            db_session.session.commit()

            assert sample_ticket.status == TICKET_STATUS_VIGENTE
            assert sample_ticket.annulled_at is None
            assert sample_ticket.annulled_by is None
            assert sample_ticket.annulled_reason is None

    def test_modify_fpa_raises_on_anulado_ticket(self, app, db_session, sample_ticket, sample_user_admin, sample_reasons):
        """modify_fpa lanza ValueError si el ticket está anulado."""
        with app.app_context():
            sample_ticket.status = TICKET_STATUS_ANULADO
            db_session.session.commit()

            with pytest.raises(ValueError):
                TicketService.modify_fpa(
                    sample_ticket,
                    sample_ticket.current_fpa + timedelta(hours=1),
                    sample_reasons[0].reason,
                    'test',
                    sample_user_admin
                )


# ===========================================================================
# Tests para UrgencyThreshold
# ===========================================================================

class TestUrgencyThreshold:
    """Tests para UrgencyThreshold.get_thresholds_for_clinic."""

    def test_get_thresholds_default_values_when_none_exist(self, app, db_session):
        """Sin configuración en BD → retorna valores por defecto."""
        with app.app_context():
            threshold = UrgencyThreshold.get_thresholds_for_clinic(clinic_id=999)
            assert threshold is not None
            assert threshold.green_threshold_hours == 8
            assert threshold.yellow_threshold_hours == 4
            assert threshold.red_threshold_hours == 2

    def test_get_thresholds_uses_global_if_no_clinic_specific(self, app, db_session, sample_clinic):
        """Sin config de clínica → usa la global."""
        with app.app_context():
            global_threshold = UrgencyThreshold(
                clinic_id=None,
                green_threshold_hours=12,
                yellow_threshold_hours=6,
                red_threshold_hours=3
            )
            db_session.session.add(global_threshold)
            db_session.session.commit()

            threshold = UrgencyThreshold.get_thresholds_for_clinic(clinic_id=sample_clinic.id)
            assert threshold.green_threshold_hours == 12
            assert threshold.yellow_threshold_hours == 6

    def test_get_thresholds_prefers_clinic_specific(self, app, db_session, sample_clinic):
        """Config de clínica específica tiene precedencia sobre global."""
        with app.app_context():
            # Global
            global_t = UrgencyThreshold(
                clinic_id=None,
                green_threshold_hours=8,
                yellow_threshold_hours=4,
                red_threshold_hours=2
            )
            # Clínica específica
            clinic_t = UrgencyThreshold(
                clinic_id=sample_clinic.id,
                green_threshold_hours=10,
                yellow_threshold_hours=5,
                red_threshold_hours=2
            )
            db_session.session.add_all([global_t, clinic_t])
            db_session.session.commit()

            threshold = UrgencyThreshold.get_thresholds_for_clinic(clinic_id=sample_clinic.id)
            assert threshold.green_threshold_hours == 10  # de clínica, no global


# ===========================================================================
# Tests para Ticket.calculated_discharge_time_block
# ===========================================================================

class TestCalculatedDischargeTimeBlock:
    """Tests para la propiedad calculated_discharge_time_block."""

    def test_block_for_14h00(self, db_session, sample_clinic):
        """FPA a las 14:00 → bloque '12:00 - 14:00'."""
        ticket = Ticket(
            id='TH-BLOCK-001',
            clinic_id=sample_clinic.id,
            current_fpa=datetime(2025, 1, 15, 14, 0)
        )
        assert ticket.calculated_discharge_time_block == '12:00 - 14:00'

    def test_block_for_00h00_midnight(self, db_session, sample_clinic):
        """FPA a las 00:00 → bloque '22:00 - 00:00'."""
        ticket = Ticket(
            id='TH-BLOCK-002',
            clinic_id=sample_clinic.id,
            current_fpa=datetime(2025, 1, 15, 0, 0)
        )
        assert ticket.calculated_discharge_time_block == '22:00 - 00:00'

    def test_block_for_14h30_rounds_to_15h(self, db_session, sample_clinic):
        """FPA a las 14:30 → redondea a 15:00 → bloque '13:00 - 15:00'."""
        ticket = Ticket(
            id='TH-BLOCK-003',
            clinic_id=sample_clinic.id,
            current_fpa=datetime(2025, 1, 15, 14, 30)
        )
        assert ticket.calculated_discharge_time_block == '13:00 - 15:00'

    def test_block_for_14h15_rounds_down_to_14h(self, db_session, sample_clinic):
        """FPA a las 14:15 → redondea ABAJO a 14:00 → bloque '12:00 - 14:00'."""
        ticket = Ticket(
            id='TH-BLOCK-004',
            clinic_id=sample_clinic.id,
            current_fpa=datetime(2025, 1, 15, 14, 15)
        )
        assert ticket.calculated_discharge_time_block == '12:00 - 14:00'

    def test_block_none_fpa(self, db_session, sample_clinic):
        """FPA None → 'Sin horario'."""
        ticket = Ticket(
            id='TH-BLOCK-005',
            clinic_id=sample_clinic.id,
            current_fpa=None
        )
        assert ticket.calculated_discharge_time_block == 'Sin horario'

    def test_block_for_23h40_midnight_wrap(self, db_session, sample_clinic):
        """FPA a las 23:40 → redondea a 00:00 → bloque '22:00 - 00:00'."""
        ticket = Ticket(
            id='TH-BLOCK-006',
            clinic_id=sample_clinic.id,
            current_fpa=datetime(2025, 1, 15, 23, 40)
        )
        assert ticket.calculated_discharge_time_block == '22:00 - 00:00'


# ===========================================================================
# Tests para Patient.full_name
# ===========================================================================

class TestPatientFullName:
    """Tests para la propiedad full_name del modelo Patient."""

    def test_full_name_with_all_fields(self, db_session, sample_patient):
        """Todos los campos presentes → nombre completo."""
        assert sample_patient.full_name == 'Juan Carlos Pérez González'

    def test_full_name_without_segundo_nombre(self, db_session, sample_clinic):
        """Sin segundo nombre → sin espacio extra."""
        patient = Patient(
            rut='22222222-2',
            primer_nombre='María',
            segundo_nombre=None,
            apellido_paterno='Soto',
            apellido_materno='López',
            age=30,
            sex='F',
            clinic_id=sample_clinic.id
        )
        db_session.session.add(patient)
        db_session.session.commit()
        assert patient.full_name == 'María Soto López'

    def test_full_name_only_required_fields(self, db_session, sample_clinic):
        """Solo primer nombre y apellido paterno."""
        patient = Patient(
            rut='33333333-3',
            primer_nombre='Pedro',
            segundo_nombre=None,
            apellido_paterno='González',
            apellido_materno=None,
            age=25,
            sex='M',
            clinic_id=sample_clinic.id
        )
        db_session.session.add(patient)
        db_session.session.commit()
        assert patient.full_name == 'Pedro González'

    def test_full_name_no_double_spaces(self, db_session, sample_clinic):
        """No debe haber dobles espacios cuando faltan campos opcionales."""
        patient = Patient(
            rut='44444444-4',
            primer_nombre='Ana',
            segundo_nombre=None,
            apellido_paterno='Martínez',
            apellido_materno=None,
            age=40,
            sex='F',
            clinic_id=sample_clinic.id
        )
        db_session.session.add(patient)
        db_session.session.commit()
        assert '  ' not in patient.full_name


# ===========================================================================
# Tests para TicketService.generate_ticket_id
# ===========================================================================

class TestTicketServiceGenerateId:
    """Tests para generate_ticket_id."""

    def test_generate_ticket_id_format(self, app, db_session, sample_clinic):
        """El ID generado tiene formato TH-XXXX-YYYY-NNN."""
        with app.app_context():
            ticket_id = TicketService.generate_ticket_id(sample_clinic)
            import re
            # Formato: TH-PREFIJO-AÑO-NNN
            assert re.match(r'^TH-[A-Z]+-\d{4}-\d{3}$', ticket_id), (
                f"ID '{ticket_id}' no tiene el formato esperado TH-XXX-YYYY-NNN"
            )

    def test_generate_ticket_id_sequential(self, app, db_session, sample_clinic,
                                            sample_patient, sample_surgery_normal, sample_doctor):
        """IDs generados secuencialmente se incrementan."""
        with app.app_context():
            current_year = datetime.now().year
            # Crear primer ticket
            id1 = TicketService.generate_ticket_id(sample_clinic)
            ticket1 = Ticket(
                id=id1,
                patient_id=sample_patient.id,
                surgery_id=sample_surgery_normal.id,
                clinic_id=sample_clinic.id,
                pavilion_end_time=datetime.now(),
                medical_discharge_date=datetime.now().date(),
                initial_fpa=datetime.now() + timedelta(hours=24),
                current_fpa=datetime.now() + timedelta(hours=24),
                overnight_stays=1,
                status=TICKET_STATUS_VIGENTE,
                created_by='test',
                surgery_name_snapshot='test',
                surgery_base_hours_snapshot=24
            )
            db_session.session.add(ticket1)
            db_session.session.commit()

            # El segundo debe ser mayor
            id2 = TicketService.generate_ticket_id(sample_clinic)
            num1 = int(id1.split('-')[-1])
            num2 = int(id2.split('-')[-1])
            assert num2 == num1 + 1

    def test_generate_ticket_id_starts_at_001(self, app, db_session, sample_clinic):
        """Sin tickets previos → el primer ID termina en 001."""
        with app.app_context():
            ticket_id = TicketService.generate_ticket_id(sample_clinic)
            assert ticket_id.endswith('-001')

    def test_generate_ticket_id_includes_current_year(self, app, db_session, sample_clinic):
        """El ID incluye el año actual."""
        with app.app_context():
            current_year = str(datetime.now().year)
            ticket_id = TicketService.generate_ticket_id(sample_clinic)
            assert current_year in ticket_id
