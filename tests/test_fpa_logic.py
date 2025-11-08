"""
Tests CRÍTICOS del cálculo de FPA (Fecha Probable de Alta).
Esta es la lógica de negocio central de Ticket Home.

Casos probados:
1. Cirugía ambulatoria antes del cutoff → alta día siguiente 8am
2. Cirugía ambulatoria después del cutoff → alta según base hours
3. Cirugía con estadía nocturna → cálculo correcto de días
4. Casos edge: medianoche, cambio de año
"""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time

from models import Ticket, Surgery, Specialty


@pytest.mark.fpa
@pytest.mark.unit
class TestFPACalculation:
    """Tests del cálculo de FPA (método calculate_fpa)."""

    def test_ambulatory_before_cutoff(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria que termina ANTES del cutoff (14:00).
        Debería dar alta al día siguiente a las 8:00 AM.
        """
        # Crear cirugía ambulatoria con cutoff 14:00
        surgery = Surgery(
            name='Hernia Inguinal',
            base_stay_hours=6,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=True,
            ambulatory_cutoff_hour=14  # 2:00 PM
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-001', clinic_id=sample_clinic.id)

        # Pabellón termina a las 11:00 (ANTES del cutoff 14:00)
        pavilion_end = datetime(2025, 1, 15, 11, 0)  # 11:00 AM

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # Con 6 horas base: 11:00 + 6h = 17:00 (5:00 PM)
        # Como es ambulatoria y terminó antes de 14:00, debería ser 8:00 AM del día siguiente
        expected_fpa = datetime(2025, 1, 16, 8, 0)  # Día siguiente, 8:00 AM

        assert fpa == expected_fpa
        assert overnight == 1  # 1 noche de pernocte

    def test_ambulatory_after_cutoff(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria que termina DESPUÉS del cutoff (14:00).
        Debería calcular FPA normal (pavilion_end + base_hours).
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

        ticket = Ticket(id='TH-TEST-002', clinic_id=sample_clinic.id)

        # Pabellón termina a las 16:00 (DESPUÉS del cutoff 14:00)
        pavilion_end = datetime(2025, 1, 15, 16, 0)  # 4:00 PM

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 16:00 + 6h = 22:00 (10:00 PM del mismo día)
        expected_fpa = datetime(2025, 1, 15, 22, 0)

        assert fpa == expected_fpa
        assert overnight == 1  # Mismo día pero cuenta 1 noche

    def test_ambulatory_at_cutoff_exactly(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria que termina EXACTAMENTE a la hora del cutoff.
        pavilion_hour < cutoff_hour → False (14 < 14 es False)
        Debería calcular normal.
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

        ticket = Ticket(id='TH-TEST-003', clinic_id=sample_clinic.id)

        # Pabellón termina EXACTAMENTE a las 14:00
        pavilion_end = datetime(2025, 1, 15, 14, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 14:00 + 6h = 20:00
        expected_fpa = datetime(2025, 1, 15, 20, 0)

        assert fpa == expected_fpa

    def test_normal_surgery_24_hours(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía normal con 24 horas de estadía.
        Debería calcular: pavilion_end + 24h.
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

        # Pabellón termina a las 14:30
        pavilion_end = datetime(2025, 1, 15, 14, 30)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 14:30 + 24h = 14:30 del día siguiente
        expected_fpa = datetime(2025, 1, 16, 14, 30)

        assert fpa == expected_fpa
        assert overnight == 1

    def test_normal_surgery_48_hours(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía con 48 horas de estadía (2 noches).
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

        pavilion_end = datetime(2025, 1, 15, 10, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 10:00 + 48h = 10:00 dos días después
        expected_fpa = datetime(2025, 1, 17, 10, 0)

        assert fpa == expected_fpa
        assert overnight == 2

    def test_edge_case_midnight(self, db_session, sample_clinic, sample_specialty):
        """
        Caso edge: pabellón termina a medianoche.
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

        # Pabellón termina a las 00:00 (medianoche)
        pavilion_end = datetime(2025, 1, 15, 0, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 00:00 + 12h = 12:00 (mediodía del mismo día)
        expected_fpa = datetime(2025, 1, 15, 12, 0)

        assert fpa == expected_fpa
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

        # Pabellón termina el 31 de diciembre a las 20:00
        pavilion_end = datetime(2024, 12, 31, 20, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 20:00 + 48h = 20:00 del 2 de enero
        expected_fpa = datetime(2025, 1, 2, 20, 0)

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

        pavilion_end = datetime(2025, 1, 15, 10, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 10:00 + 3h = 13:00 (mismo día)
        expected_fpa = datetime(2025, 1, 15, 13, 0)

        assert fpa == expected_fpa
        # Mismo día pero con segundos > 0 → cuenta 1 noche
        assert overnight == 1

    def test_ambulatory_early_morning(self, db_session, sample_clinic, sample_specialty):
        """
        Cirugía ambulatoria temprano en la mañana (antes del cutoff).
        """
        surgery = Surgery(
            name='Cirugía Ambulatoria Matutina',
            base_stay_hours=4,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=True,
            ambulatory_cutoff_hour=12
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-009', clinic_id=sample_clinic.id)

        # Pabellón termina a las 8:00 AM
        pavilion_end = datetime(2025, 1, 15, 8, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 8:00 + 4h = 12:00
        # Como es ambulatoria y terminó antes de 12:00, debería ser 8:00 AM del día siguiente
        expected_fpa = datetime(2025, 1, 16, 8, 0)

        assert fpa == expected_fpa
        assert overnight == 1

    def test_surgery_without_ambulatory_flag(self, db_session, sample_clinic, sample_specialty):
        """
        Test que cirugía sin flag ambulatoria funciona correctamente.
        """
        surgery = Surgery(
            name='Cirugía Estándar',
            base_stay_hours=18,
            specialty_id=sample_specialty.id,
            clinic_id=sample_clinic.id,
            is_ambulatory=False,
            ambulatory_cutoff_hour=None
        )
        db_session.session.add(surgery)
        db_session.session.commit()

        ticket = Ticket(id='TH-TEST-010', clinic_id=sample_clinic.id)

        pavilion_end = datetime(2025, 1, 15, 14, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 14:00 + 18h = 8:00 AM del día siguiente
        expected_fpa = datetime(2025, 1, 16, 8, 0)

        assert fpa == expected_fpa
        assert overnight == 1


@pytest.mark.fpa
class TestFPAEdgeCases:
    """Tests de casos edge adicionales."""

    def test_very_short_surgery(self, db_session, sample_clinic, sample_specialty):
        """Cirugía de 1 hora (muy corta)."""
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
        pavilion_end = datetime(2025, 1, 15, 14, 30)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        expected_fpa = datetime(2025, 1, 15, 15, 30)
        assert fpa == expected_fpa
        assert overnight == 1

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
        pavilion_end = datetime(2025, 1, 15, 10, 0)

        fpa, overnight = ticket.calculate_fpa(pavilion_end, surgery)

        # 10:00 + 120h = 10:00 cinco días después
        expected_fpa = datetime(2025, 1, 20, 10, 0)
        assert fpa == expected_fpa
        assert overnight == 5
