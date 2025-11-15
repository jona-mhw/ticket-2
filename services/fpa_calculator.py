"""
FPA Calculator Service - Business logic for calculating FPA (Fecha Probable de Alta)

This service encapsulates all the complex logic for calculating when a patient
should be discharged based on surgery type, pavilion end time, and other factors.
"""
from datetime import timedelta
from typing import Tuple


class FPACalculator:
    """Service for calculating FPA and overnight stays for patients."""

    @staticmethod
    def calculate(pavilion_end_time, surgery) -> Tuple[object, int]:
        """
        Calculate FPA (Fecha Probable de Alta) and overnight stays.

        Args:
            pavilion_end_time (datetime): When the patient left the pavilion/surgery room
            surgery (Surgery): Surgery model instance with base_stay_hours and ambulatory settings

        Returns:
            tuple: (fpa datetime, overnight_stays int)

        Business Rules:
            1. FPA = pavilion_end_time + base_stay_hours
            2. For ambulatory surgeries before cutoff hour:
               - If calculated FPA is before 8am next day, set FPA to 8am next day
            3. CORRECCIÓN Issue #53: Redondear a hora entera más cercana:
               - 0-29 minutos → Redondear ABAJO
               - 30-59 minutos → Redondear ARRIBA
            4. Overnight stays = number of nights patient stays (ceil of days)
        """
        base_hours = surgery.base_stay_hours
        total_hours = base_hours
        fpa = pavilion_end_time + timedelta(hours=total_hours)

        # Special handling for ambulatory surgeries
        if surgery and surgery.is_ambulatory and surgery.ambulatory_cutoff_hour:
            pavilion_hour = pavilion_end_time.hour
            cutoff_hour = surgery.ambulatory_cutoff_hour

            # If surgery ends before cutoff hour, adjust FPA to next morning
            if pavilion_hour < cutoff_hour:
                next_morning = pavilion_end_time.replace(
                    hour=8, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                if fpa < next_morning:
                    fpa = next_morning

        # CORRECCIÓN Issue #53: Redondear FPA a la hora entera más cercana
        # 0-29 minutos → Redondear ABAJO
        # 30-59 minutos → Redondear ARRIBA
        if fpa.minute >= 30:
            # Redondear ARRIBA: eliminar minutos/segundos y sumar 1 hora
            fpa = fpa.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            # Redondear ABAJO: eliminar minutos/segundos
            fpa = fpa.replace(minute=0, second=0, microsecond=0)

        # Calculate overnight stays
        time_diff = fpa - pavilion_end_time
        overnight_stays = max(0, time_diff.days)
        if time_diff.seconds > 0:
            overnight_stays += 1

        return fpa, overnight_stays
