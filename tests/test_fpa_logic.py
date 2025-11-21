"""
Tests CRÍTICOS del cálculo de FPA (Fecha Probable de Alta).
Esta es la lógica de negocio central de Ticket Home.

ACTUALIZADO: Ahora contempla la lógica "Admission Time = Surgery Time - 2h"
y el redondeo de Issues #53 y #63.

Casos probados:
1. Cirugía ambulatoria antes del cutoff
2. Cirugía ambulatoria después del cutoff
3. Cirugía con estadía nocturna
4. Casos edge: medianoche, cambio de año
"""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time

from models import Ticket, Surgery, Specialty
from services.fpa_calculator import FPACalculator

@pytest.mark.fpa
@pytest.mark.unit
class TestFPACalculation:
    """Tests del cálculo de FPA (método calculate_fpa)."""

    def test_ambulatory_before_cutoff(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria que termina ANTES del cutoff (14:00).
        Lógica actual:
        - Admission = 11:00 - 2h = 09:00
        - Base = 6h
        - FPA = 09:00 + 6h = 15:00

        Pero si es AMBULATORIA y cutoff (???)
        El flag 'ambulatory_cutoff_hour' no parece usarse en FPACalculator.calculate().
        Revisando FPACalculator.calculate(): NO HAY LÓGICA DE CUTOFF.
        Solo usa base_stay_hours.

        Si la lógica antigua dependía de 'ambulatory_cutoff_hour', esa lógica fue ELIMINADA
        en el refactor de servicios. El código actual es:
        FPA = (Time - 2h) + BaseHours + Rounding.
        """
        # Crear cirugía ambulatoria
        surgery = Surgery(
            name='Hernia Inguinal',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=True
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-001', clinic_id=sample_clinic.id)

        # Pabellón 11:00
        pavilion_end = datetime(2025, 1, 15, 11, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Calculation:
        # Admission = 11:00 - 2h = 09:00
        # FPA Raw = 09:00 + 6h = 15:00
        # Rounding: 15:00 -> 15:00

        expected_fpa = datetime(2025, 1, 15, 15, 0)

        assert fpa == expected_fpa

    def test_ambulatory_after_cutoff(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria.
        """
        surgery = Surgery(
            name='Hernia Inguinal',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=True
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-002', clinic_id=sample_clinic.id)

        # Pabellón 16:00
        pavilion_end = datetime(2025, 1, 15, 16, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 16:00 - 2h = 14:00
        # FPA Raw = 14:00 + 6h = 20:00
        expected_fpa = datetime(2025, 1, 15, 20, 0)

        assert fpa == expected_fpa

    def test_ambulatory_at_cutoff_exactly(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria.
        """
        surgery = Surgery(
            name='Hernia Inguinal',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=True
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-003', clinic_id=sample_clinic.id)

        # Pabellón 14:00
        pavilion_end = datetime(2025, 1, 15, 14, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 14:00 - 2h = 12:00
        # FPA Raw = 12:00 + 6h = 18:00
        expected_fpa = datetime(2025, 1, 15, 18, 0)

        assert fpa == expected_fpa

    def test_normal_surgery_24_hours(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía normal con 24 horas de estadía.
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

        ticket = Ticket(id='TH-TEST-004', clinic_id=sample_clinic.id)

        # Pabellón 14:30
        pavilion_end = datetime(2025, 1, 15, 14, 30)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 14:30 - 2h = 12:30
        # FPA Raw = 12:30 + 24h = 12:30 (next day)
        # Rounding: 12:30 -> 13:00 (UP because minutes > 0)
        expected_fpa = datetime(2025, 1, 16, 13, 0)

        assert fpa == expected_fpa
        # Overnight: 15 Jan (Admission) to 16 Jan (FPA) -> 1 night
        assert overnight == 1

    def test_normal_surgery_48_hours(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía con 48 horas de estadía.
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

        ticket = Ticket(id='TH-TEST-005', clinic_id=sample_clinic.id)

        # Pabellón 10:00
        pavilion_end = datetime(2025, 1, 15, 10, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 10:00 - 2h = 08:00
        # FPA Raw = 08:00 + 48h = 08:00 (+2 days)
        expected_fpa = datetime(2025, 1, 17, 8, 0)

        assert fpa == expected_fpa
        assert overnight == 2

    def test_edge_case_midnight(self, db_session, sample_clinic, sample_specialty):
        """
        Caso edge: pabellón a medianoche (00:00).
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

        ticket = Ticket(id='TH-TEST-006', clinic_id=sample_clinic.id)

        # Pabellón 00:00
        pavilion_end = datetime(2025, 1, 15, 0, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 00:00 - 2h = 22:00 (del día anterior, 14 Jan)
        # FPA Raw = 22:00 + 12h = 10:00 (15 Jan)
        expected_fpa = datetime(2025, 1, 15, 10, 0)

        assert fpa == expected_fpa
        # Overnight: 14 Jan to 15 Jan -> 1 night
        assert overnight == 1

    def test_edge_case_end_of_year(self, db_session, sample_clinic, sample_specialty):
        """
        Caso edge: cirugía que cruza año nuevo.
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

        ticket = Ticket(id='TH-TEST-007', clinic_id=sample_clinic.id)

        # Pabellón 31 Dic 20:00
        pavilion_end = datetime(2024, 12, 31, 20, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 20:00 - 2h = 18:00
        # FPA Raw = 18:00 + 48h = 18:00 (2 Ene 2025)
        expected_fpa = datetime(2025, 1, 2, 18, 0)

        assert fpa == expected_fpa
        assert overnight == 2

    def test_overnight_calculation_same_day(self, db_session, sample_clinic, sample_specialty):
        """
        Test cálculo de overnight stays cuando FPA es el mismo día.
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

        ticket = Ticket(id='TH-TEST-008', clinic_id=sample_clinic.id)

        # Pabellón 10:00
        pavilion_end = datetime(2025, 1, 15, 10, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 10:00 - 2h = 08:00
        # FPA Raw = 08:00 + 3h = 11:00
        expected_fpa = datetime(2025, 1, 15, 11, 0)

        assert fpa == expected_fpa
        # Overnight: 15 Jan to 15 Jan -> 0 nights
        assert overnight == 0

    def test_ambulatory_early_morning(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria temprano.
        """
        surgery = Surgery(
            name='Cirugía Ambulatoria Matutina',
            base_stay_hours=4,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=True
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-009', clinic_id=sample_clinic.id)

        # Pabellón 08:00
        # Exception Rule: 08:00 -> Admission 06:30
        pavilion_end = datetime(2025, 1, 15, 8, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 06:30 (Exception Rule)
        # FPA Raw = 06:30 + 4h = 10:30
        # Rounding: 10:30 -> 11:00
        expected_fpa = datetime(2025, 1, 15, 11, 0)

        assert fpa == expected_fpa

    def test_surgery_without_ambulatory_flag(self, db_session, sample_clinic, sample_specialty):
        """
        Test que cirugía sin flag ambulatoria.
        """
        surgery = Surgery(
            name='Cirugía Estándar',
            base_stay_hours=18,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-010', clinic_id=sample_clinic.id)

        # Pabellón 14:00
        pavilion_end = datetime(2025, 1, 15, 14, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 14:00 - 2h = 12:00
        # FPA Raw = 12:00 + 18h = 06:00 (Next day)
        expected_fpa = datetime(2025, 1, 16, 6, 0)

        assert fpa == expected_fpa
        assert overnight == 1


@pytest.mark.fpa
class TestFPAEdgeCases:
    """Tests de casos edge adicionales."""

    def test_very_short_surgery(self, db_session, sample_clinic, sample_specialty):
        """Cirugía de 1 hora."""
        surgery = Surgery(
            name='Procedimiento Menor',
            base_stay_hours=1,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-011', clinic_id=sample_clinic.id)
        # Pabellón 14:30
        pavilion_end = datetime(2025, 1, 15, 14, 30)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 14:30 - 2h = 12:30
        # FPA Raw = 12:30 + 1h = 13:30
        # Rounding: 13:30 -> 14:00
        expected_fpa = datetime(2025, 1, 15, 14, 0)

        assert fpa == expected_fpa
        assert overnight == 0

    def test_very_long_surgery(self, db_session, sample_clinic, sample_specialty):
        """Cirugía de 120 horas (5 días)."""
        surgery = Surgery(
            name='Cirugía Compleja',
            base_stay_hours=120,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-012', clinic_id=sample_clinic.id)
        # Pabellón 10:00
        pavilion_end = datetime(2025, 1, 15, 10, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 10:00 - 2h = 08:00
        # FPA Raw = 08:00 + 120h = 08:00 (+5 days)
        expected_fpa = datetime(2025, 1, 20, 8, 0)

        assert fpa == expected_fpa
        assert overnight == 5


@pytest.mark.fpa
@pytest.mark.issue53
class TestFPARounding:
    """
    Tests para Issue #53: Corrección de lógica de redondeo FPA.

    Lógica implementada en FPACalculator (calculate):
    SIEMPRE se redondea hacia ARRIBA si hay minutos > 0.

    Wait, FPACalculator says:
        if fpa.minute > 0 or fpa.second > 0:
            # Eliminar minutos/segundos y sumar 1 hora
            fpa = fpa.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    Los tests anteriores (test_fpa_logic original) probaban un redondeo
    de 'Ticket.calculated_discharge_time_block' (30min split),
    no del FPA mismo.

    PERO los tests aquí están llamando a `calculate_fpa` que retorna el FPA.

    Vamos a ajustar los tests a la lógica REAL de FPACalculator.
    """

    def test_rounding_no_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 0 minutos → No redondea."""
        surgery = Surgery(
            name='Cirugía Test',
            base_stay_hours=24,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-ROUND-001', clinic_id=sample_clinic.id)
        # 22:00
        pavilion_end = datetime(2025, 11, 12, 22, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 20:00
        # FPA = 20:00 + 24h = 20:00 (Next Day)
        expected_fpa = datetime(2025, 11, 13, 20, 0)
        assert fpa == expected_fpa

    def test_rounding_with_15_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 15 minutos → Redondea ARRIBA (Regla General)."""
        surgery = Surgery(
            name='Cirugía Test',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-ROUND-002', clinic_id=sample_clinic.id)
        # 14:15
        pavilion_end = datetime(2025, 11, 15, 14, 15)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 12:15
        # FPA Raw = 12:15 + 6h = 18:15
        # Rounding: 18:15 -> 19:00
        expected_fpa = datetime(2025, 11, 15, 19, 0)
        assert fpa == expected_fpa

    def test_rounding_with_29_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 29 minutos → Redondea ARRIBA (Regla General)."""
        surgery = Surgery(
            name='Cirugía Test',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-ROUND-003', clinic_id=sample_clinic.id)
        # 08:29 (Excepción de 08:00 solo aplica si min=0, aquí es 29 -> 06:29)
        pavilion_end = datetime(2025, 11, 15, 8, 29)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 06:29
        # FPA Raw = 06:29 + 6h = 12:29
        # Rounding: 12:29 -> 13:00
        expected_fpa = datetime(2025, 11, 15, 13, 0)
        assert fpa == expected_fpa

    def test_rounding_with_30_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 30 minutos → Redondea ARRIBA."""
        surgery = Surgery(
            name='Cirugía Test',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-ROUND-004', clinic_id=sample_clinic.id)
        # 08:30
        pavilion_end = datetime(2025, 11, 15, 8, 30)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 06:30
        # FPA Raw = 06:30 + 6h = 12:30
        # Rounding: 12:30 -> 13:00
        expected_fpa = datetime(2025, 11, 15, 13, 0)
        assert fpa == expected_fpa

    def test_rounding_with_45_minutes(self, db_session, sample_clinic, sample_specialty):
        """FPA con 45 minutos → Redondea ARRIBA."""
        surgery = Surgery(
            name='Cirugía Test',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-ROUND-005', clinic_id=sample_clinic.id)
        # 08:45
        pavilion_end = datetime(2025, 11, 15, 8, 45)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 06:45
        # FPA Raw = 06:45 + 6h = 12:45
        # Rounding: 12:45 -> 13:00
        expected_fpa = datetime(2025, 11, 15, 13, 0)
        assert fpa == expected_fpa

    def test_rounding_midnight_edge_case(self, db_session, sample_clinic, sample_specialty):
        """FPA que redondea a medianoche."""
        surgery = Surgery(
            name='Cirugía Test',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-ROUND-006', clinic_id=sample_clinic.id)
        # 17:40
        pavilion_end = datetime(2025, 11, 15, 17, 40)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 15:40
        # FPA Raw = 15:40 + 6h = 21:40
        # Rounding: 21:40 -> 22:00
        expected_fpa = datetime(2025, 11, 15, 22, 0)
        assert fpa == expected_fpa

    def test_real_case_issue_53(self, db_session, sample_clinic, sample_specialty):
        """
        Caso real del Issue #53.
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

        ticket = Ticket(id='TH-ISSUE-53', clinic_id=sample_clinic.id)
        # 22:00
        pavilion_end = datetime(2025, 11, 12, 22, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Admission = 20:00
        # FPA = 20:00 + 24h = 20:00
        expected_fpa = datetime(2025, 11, 13, 20, 0)
        assert fpa == expected_fpa

