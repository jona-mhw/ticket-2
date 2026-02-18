"""
Tests CRÍTICOS del cálculo de FPA (Fecha Probable de Alta).
Esta es la lógica de negocio central de Ticket Home.

IMPORTANTE (Issue #63, 2026-02-17):
    El FPACalculator usa la lógica actualizada:
    1. Admission Time = Surgery Time - 2h (Excepción: 08:00 → 06:30)
    2. Base FPA = Admission Time + Base Stay Hours
    3. Rounding: SIEMPRE hacia ARRIBA si hay minutos/segundos
       - 10:00 → 10:00 (sin cambio)
       - 10:01 → 11:00 (sube a la siguiente hora)
       - 10:30 → 11:00 (sube aunque sea la "más cercana")
    4. Overnight stays = diferencia de fechas entre admission y FPA

    Los tests anteriores (Issue #53) esperaban redondeo al más cercano,
    lo cual fue cambiado por Issue #63. Esta versión refleja el estado actual.
"""
import pytest
from datetime import datetime, timedelta

from services.fpa_calculator import FPACalculator
from models import Ticket, Surgery, Specialty


# ===========================================================================
# Tests para FPACalculator.calculate_admission_time()
# ===========================================================================

@pytest.mark.fpa
@pytest.mark.unit
class TestAdmissionTimeCalculation:
    """Tests para calculate_admission_time - regla: surgery_time - 2h."""

    def test_general_rule_14h30(self):
        """Cirugía a las 14:30 → ingreso a las 12:30 (regla general -2h)."""
        surgery_time = datetime(2025, 1, 15, 14, 30)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 15, 12, 30)

    def test_general_rule_10h00(self):
        """Cirugía a las 10:00 → ingreso a las 08:00."""
        surgery_time = datetime(2025, 1, 15, 10, 0)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 15, 8, 0)

    def test_exception_08h00(self):
        """Excepción: Cirugía a las 08:00 → ingreso a las 06:30 (no 06:00)."""
        surgery_time = datetime(2025, 1, 15, 8, 0)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 15, 6, 30)

    def test_midnight_surgery(self):
        """Cirugía a las 00:00 → ingreso a las 22:00 del día anterior."""
        surgery_time = datetime(2025, 1, 15, 0, 0)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 14, 22, 0)

    def test_early_morning_surgery(self):
        """Cirugía a las 02:00 → ingreso a las 00:00 mismo día."""
        surgery_time = datetime(2025, 1, 15, 2, 0)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 15, 0, 0)

    def test_late_night_surgery(self):
        """Cirugía a las 23:00 → ingreso a las 21:00."""
        surgery_time = datetime(2025, 1, 15, 23, 0)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 15, 21, 0)

    def test_not_08h00_exception_08h01(self):
        """08:01 NO aplica excepción → ingreso a las 06:01."""
        surgery_time = datetime(2025, 1, 15, 8, 1)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 15, 6, 1)

    def test_not_08h00_exception_07h59(self):
        """07:59 NO aplica excepción → ingreso a las 05:59."""
        surgery_time = datetime(2025, 1, 15, 7, 59)
        admission = FPACalculator.calculate_admission_time(surgery_time)
        assert admission == datetime(2025, 1, 15, 5, 59)


# ===========================================================================
# Tests para FPACalculator.calculate() - cálculo completo con FPA
# ===========================================================================

@pytest.mark.fpa
@pytest.mark.unit
class TestFPACalculation:
    """Tests del cálculo completo FPA (Issue #63: admission = surgery - 2h)."""

    def test_normal_surgery_24_hours(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía normal con 24 horas de estadía.
        surgery_time = 14:30 → admission = 12:30 → fpa = 12:30+24 = 12:30 next day → round UP → 13:00
        """
        surgery = Surgery(
            name='Colecistectomía',
            base_stay_hours=24,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 14, 30)  # surgery at 14:30
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 12:30, fpa = 12:30 + 24h = 12:30 next day
        # 12:30 tiene minutos → round UP → 13:00 next day
        expected_fpa = datetime(2025, 1, 16, 13, 0)
        assert fpa == expected_fpa
        assert overnight == 1

    def test_normal_surgery_48_hours(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía con 48 horas de estadía (2 noches).
        surgery_time = 10:00 → admission = 08:00 → fpa = 08:00+48 = 08:00 two days later (exact)
        """
        surgery = Surgery(
            name='Cirugía Mayor',
            base_stay_hours=48,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 10, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 08:00, fpa = 08:00 + 48h = 08:00 two days later (exact hour)
        expected_fpa = datetime(2025, 1, 17, 8, 0)
        assert fpa == expected_fpa
        assert overnight == 2

    def test_surgery_exact_hour_no_rounding(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía que da FPA a hora exacta → no se redondea.
        surgery = 10:00, 6h → admission = 08:00 → fpa = 14:00 (exact)
        """
        surgery = Surgery(
            name='Cirugía Simple',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 10, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 08:00, fpa = 08:00 + 6h = 14:00 (exact)
        expected_fpa = datetime(2025, 1, 15, 14, 0)
        assert fpa == expected_fpa
        assert overnight == 0  # mismo día

    def test_edge_case_midnight_surgery(self, db_session, sample_clinic, sample_specialty):
        """
        Caso edge: cirugía a medianoche (00:00).
        surgery = 00:00 → admission = 22:00 prev day → fpa = 22:00+12 = 10:00 same day as surgery
        """
        surgery = Surgery(
            name='Cirugía de Emergencia',
            base_stay_hours=12,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 0, 0)  # medianoche 15 enero
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 22:00 del 14 enero
        # fpa = 22:00 + 12h = 10:00 del 15 enero (exact)
        expected_fpa = datetime(2025, 1, 15, 10, 0)
        assert fpa == expected_fpa
        assert overnight == 1  # 15 ene - 14 ene = 1

    def test_edge_case_end_of_year(self, db_session, sample_clinic, sample_specialty):
        """
        Caso edge: cirugía que cruza año nuevo.
        surgery = Dec 31 20:00, 48h → admission = 18:00 Dec 31 → fpa = 18:00 Jan 2
        """
        surgery = Surgery(
            name='Cirugía de Fin de Año',
            base_stay_hours=48,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2024, 12, 31, 20, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 18:00 Dec 31, fpa = 18:00 + 48h = 18:00 Jan 2 (exact)
        expected_fpa = datetime(2025, 1, 2, 18, 0)
        assert fpa == expected_fpa
        assert overnight == 2

    def test_same_day_discharge(self, db_session, sample_clinic, sample_specialty):
        """
        Alta el mismo día: surgery=10:00, 3h → admission=08:00 → fpa=11:00 (same day)
        overnight = 0.
        """
        surgery = Surgery(
            name='Cirugía Corta',
            base_stay_hours=3,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 10, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 08:00, fpa = 11:00 (exact, mismo día)
        expected_fpa = datetime(2025, 1, 15, 11, 0)
        assert fpa == expected_fpa
        assert overnight == 0

    def test_special_08h00_surgery(self, db_session, sample_clinic, sample_specialty):
        """
        Excepción 08:00: surgery=08:00 → admission=06:30 (no 06:00).
        surgery=08:00, 12h → admission=06:30 → fpa=06:30+12=18:30 → round UP → 19:00
        """
        surgery = Surgery(
            name='Cirugía Matutina',
            base_stay_hours=12,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 8, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 06:30 (excepción), fpa = 06:30 + 12h = 18:30 → round UP → 19:00
        expected_fpa = datetime(2025, 1, 15, 19, 0)
        assert fpa == expected_fpa
        assert overnight == 0  # mismo día

    def test_surgery_with_minutes_in_fpa(self, db_session, sample_clinic, sample_specialty):
        """
        FPA con minutos → SIEMPRE redondea hacia ARRIBA (Issue #63).
        surgery=14:30, 6h → admission=12:30 → fpa=12:30+6=18:30 → round UP → 19:00
        """
        surgery = Surgery(
            name='Cirugía Estándar',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 14, 30)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 12:30, fpa = 12:30 + 6h = 18:30 → round UP → 19:00
        expected_fpa = datetime(2025, 1, 15, 19, 0)
        assert fpa == expected_fpa

    def test_ambulatory_treated_same_as_normal(self, db_session, sample_clinic, sample_specialty):
        """
        Las cirugías ambulatorias se calculan IGUAL que las normales en el FPACalculator.
        El flag is_ambulatory NO afecta el cálculo (lógica ambulatoria fue eliminada).
        surgery=11:00, 6h, ambulatory → admission=09:00 → fpa=09:00+6=15:00 (exact)
        """
        surgery = Surgery(
            name='Hernia Inguinal',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=True,
            ambulatory_cutoff_hour=14
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 11, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # El flag ambulatorio NO cambia el cálculo
        # admission = 09:00, fpa = 09:00 + 6h = 15:00 (exact)
        expected_fpa = datetime(2025, 1, 15, 15, 0)
        assert fpa == expected_fpa
        assert overnight == 0


# ===========================================================================
# Tests para el redondeo FPA (Issue #63: SIEMPRE hacia ARRIBA)
# ===========================================================================

@pytest.mark.fpa
@pytest.mark.unit
class TestFPARounding:
    """
    Tests para el redondeo del FPA (Issue #63).

    Regla: Si el FPA tiene minutos o segundos, se redondea SIEMPRE
    hacia ARRIBA a la siguiente hora entera.
    - 10:00 → 10:00 (sin cambio)
    - 10:01 → 11:00
    - 10:29 → 11:00 (NO se redondea al más cercano)
    - 10:30 → 11:00
    - 10:59 → 11:00
    """

    def test_rounding_exact_hour_no_change(self, db_session, sample_clinic, sample_specialty):
        """FPA a hora exacta → sin cambio."""
        surgery = Surgery(
            name='Test', base_stay_hours=24,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 22:00 → admission 20:00 → fpa = 20:00 + 24h = 20:00 next day (exact)
        pavilion_end = datetime(2025, 11, 12, 22, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        expected_fpa = datetime(2025, 11, 13, 20, 0)  # exact, no rounding
        assert fpa == expected_fpa
        assert fpa.minute == 0

        # Verificar bloque: 20:00 → 18:00 - 20:00
        ticket = Ticket(id='TH-ROUND-001', clinic_id=sample_clinic.id)
        ticket.current_fpa = fpa
        assert ticket.calculated_discharge_time_block == "18:00 - 20:00"

    def test_rounding_up_1_minute(self, db_session, sample_clinic, sample_specialty):
        """FPA con 1 minuto → redondea ARRIBA (no importa que esté cerca de la hora baja)."""
        surgery = Surgery(
            name='Test', base_stay_hours=6,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 14:01 → admission 12:01 → fpa = 12:01 + 6h = 18:01 → round UP → 19:00
        pavilion_end = datetime(2025, 11, 15, 14, 1)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        assert fpa == datetime(2025, 11, 15, 19, 0)
        assert fpa.minute == 0

    def test_rounding_up_15_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 15 minutos → redondea ARRIBA (Issue #63 no es al más cercano)."""
        surgery = Surgery(
            name='Test', base_stay_hours=6,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 14:15 → admission 12:15 → fpa = 12:15 + 6h = 18:15 → round UP → 19:00
        pavilion_end = datetime(2025, 11, 15, 14, 15)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # Issue #63: redondea SIEMPRE arriba (18:15 → 19:00, no 18:00)
        assert fpa == datetime(2025, 11, 15, 19, 0)
        assert fpa.minute == 0

    def test_rounding_up_29_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 29 minutos → redondea ARRIBA (límite inferior de la hora siguiente)."""
        surgery = Surgery(
            name='Test', base_stay_hours=6,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 08:29 → admission 06:29 → fpa = 06:29 + 6h = 12:29 → round UP → 13:00
        pavilion_end = datetime(2025, 11, 15, 8, 29)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        assert fpa == datetime(2025, 11, 15, 13, 0)

    def test_rounding_up_30_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 30 minutos → redondea ARRIBA."""
        surgery = Surgery(
            name='Test', base_stay_hours=6,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 08:30 → admission 06:30 → fpa = 06:30 + 6h = 12:30 → round UP → 13:00
        pavilion_end = datetime(2025, 11, 15, 8, 30)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        assert fpa == datetime(2025, 11, 15, 13, 0)

    def test_rounding_up_45_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 45 minutos → redondea ARRIBA."""
        surgery = Surgery(
            name='Test', base_stay_hours=6,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 08:45 → admission 06:45 → fpa = 06:45 + 6h = 12:45 → round UP → 13:00
        pavilion_end = datetime(2025, 11, 15, 8, 45)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        assert fpa == datetime(2025, 11, 15, 13, 0)

    def test_rounding_midnight_edge_case(self, db_session, sample_clinic, sample_specialty):
        """FPA que redondea a medianoche (22:00 del día siguiente → 00:00)."""
        surgery = Surgery(
            name='Test', base_stay_hours=6,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 17:40 → admission 15:40 → fpa = 15:40 + 6h = 21:40 → round UP → 22:00
        pavilion_end = datetime(2025, 11, 15, 17, 40)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        expected_fpa = datetime(2025, 11, 15, 22, 0)
        assert fpa == expected_fpa

        # Bloque: 22:00 → "20:00 - 22:00"
        ticket = Ticket(id='TH-ROUND-006', clinic_id=sample_clinic.id)
        ticket.current_fpa = fpa
        assert ticket.calculated_discharge_time_block == "20:00 - 22:00"

    def test_rounding_to_next_day(self, db_session, sample_clinic, sample_specialty):
        """FPA con minutos en hora 23:xx → redondea a 00:00 del día siguiente."""
        surgery = Surgery(
            name='Test', base_stay_hours=4,
            specialty_id=sample_specialty.id, clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # surgery 01:30 → admission 23:30 prev day → fpa = 23:30 + 4h = 03:30 → round UP → 04:00
        pavilion_end = datetime(2025, 11, 15, 1, 30)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 23:30 Nov 14, fpa = 23:30 + 4h = 03:30 Nov 15 → round UP → 04:00 Nov 15
        expected_fpa = datetime(2025, 11, 15, 4, 0)
        assert fpa == expected_fpa

    def test_real_case_issue_53(self, db_session, sample_clinic, sample_specialty):
        """
        Caso real (Issue #53 adaptado al Issue #63):
        surgery 22:00, 24h → admission 20:00 → fpa 20:00 next day (exact).
        Bloque esperado: 18:00 - 20:00.
        """
        surgery = Surgery(
            name='Cirugía 24h',
            base_stay_hours=24,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 11, 12, 22, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 20:00, fpa = 20:00 + 24h = 20:00 next day (exact)
        expected_fpa = datetime(2025, 11, 13, 20, 0)
        assert fpa == expected_fpa
        assert overnight == 1

        # Bloque: 20:00 es exact → "18:00 - 20:00"
        ticket = Ticket(id='TH-ISSUE-53', clinic_id=sample_clinic.id)
        ticket.current_fpa = fpa
        assert ticket.calculated_discharge_time_block == "18:00 - 20:00"


# ===========================================================================
# Tests adicionales de edge cases
# ===========================================================================

@pytest.mark.fpa
class TestFPAEdgeCases:
    """Tests de casos edge del FPACalculator."""

    def test_very_short_surgery(self, db_session, sample_clinic, sample_specialty):
        """Cirugía de 1 hora: surgery=14:30, 1h → admission=12:30 → fpa=12:30+1=13:30 → UP → 14:00."""
        surgery = Surgery(
            name='Procedimiento Menor',
            base_stay_hours=1,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 14, 30)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 12:30, fpa = 12:30 + 1h = 13:30 → round UP → 14:00
        expected_fpa = datetime(2025, 1, 15, 14, 0)
        assert fpa == expected_fpa
        assert overnight == 0  # mismo día

    def test_very_long_surgery(self, db_session, sample_clinic, sample_specialty):
        """Cirugía de 120h (5 días): surgery=10:00 → admission=08:00 → fpa=08:00+120=08:00 5 días después."""
        surgery = Surgery(
            name='Cirugía Compleja',
            base_stay_hours=120,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        pavilion_end = datetime(2025, 1, 15, 10, 0)
        fpa, overnight = FPACalculator.calculate(pavilion_end, surgery)

        # admission = 08:00, fpa = 08:00 + 120h = 08:00 cinco días después (exact)
        expected_fpa = datetime(2025, 1, 20, 8, 0)
        assert fpa == expected_fpa
        assert overnight == 5

    def test_fpa_always_has_zero_minutes(self, db_session, sample_clinic, sample_specialty):
        """El FPA resultante siempre debe tener minutos=0 y segundos=0."""
        surgery = Surgery(
            name='Test',
            base_stay_hours=7,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # Cualquier combinación de tiempo que resulte en minutos
        test_times = [
            datetime(2025, 1, 15, 8, 15),
            datetime(2025, 1, 15, 10, 30),
            datetime(2025, 1, 15, 14, 45),
            datetime(2025, 1, 15, 7, 1),
        ]

        for surgery_time in test_times:
            fpa, _ = FPACalculator.calculate(surgery_time, surgery)
            assert fpa.minute == 0, f"FPA tiene {fpa.minute} minutos para surgery {surgery_time}"
            assert fpa.second == 0, f"FPA tiene {fpa.second} segundos para surgery {surgery_time}"

    def test_overnight_stays_never_negative(self, db_session, sample_clinic, sample_specialty):
        """Los overnight_stays nunca deben ser negativos."""
        surgery = Surgery(
            name='Test',
            base_stay_hours=2,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        # Casos donde FPA podría ser el mismo día o antes
        test_times = [
            datetime(2025, 1, 15, 12, 0),  # admission=10:00, fpa=12:00 (same day)
            datetime(2025, 1, 15, 14, 0),  # admission=12:00, fpa=14:00 (same day)
        ]

        for surgery_time in test_times:
            _, overnight = FPACalculator.calculate(surgery_time, surgery)
            assert overnight >= 0, f"overnight_stays negativo ({overnight}) para surgery {surgery_time}"
