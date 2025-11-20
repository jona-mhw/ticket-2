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
    def calculate_admission_time(surgery_time):
        """
        Calcula la hora de ingreso basada en la hora de cirugía.
        Regla General: 2 horas antes.
        Excepción: Si cirugía es a las 08:00, ingreso es a las 06:30.
        """
        # Excepción: Cirugía a las 08:00 AM (con tolerancia de +/- 5 min si es necesario, pero seremos estrictos por ahora)
        if surgery_time.hour == 8 and surgery_time.minute == 0:
            return surgery_time.replace(hour=6, minute=30)
        
        # Regla General: 2 horas antes
        return surgery_time - timedelta(hours=2)

    @staticmethod
    def calculate(surgery_time, surgery) -> Tuple[object, int]:
        """
        Calculate FPA (Fecha Probable de Alta) and overnight stays.

        Args:
            surgery_time (datetime): Scheduled time for the surgery (Start time)
            surgery (Surgery): Surgery model instance with base_stay_hours

        Returns:
            tuple: (fpa datetime, overnight_stays int)

        Business Rules (Issue #63):
            1. Admission Time = Surgery Time - 2h (Exception: 08:00 -> 06:30)
            2. Base FPA = Admission Time + Base Stay Hours
            3. Rounding: ALWAYS round UP to the next full hour if there are minutes.
               - 10:00 -> 10:00
               - 10:01 -> 11:00
        
        Business Rules (Issue #60):
            4. Overnight stays = Effective nights passed.
        """
        # 1. Calcular Hora de Ingreso
        admission_time = FPACalculator.calculate_admission_time(surgery_time)
        
        # 2. Calcular FPA Base
        base_hours = surgery.base_stay_hours
        fpa = admission_time + timedelta(hours=base_hours)

        # 3. Redondeo: SIEMPRE hacia arriba si hay minutos (Issue #63)
        if fpa.minute > 0 or fpa.second > 0:
            # Eliminar minutos/segundos y sumar 1 hora
            fpa = fpa.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            # Ya es hora cerrada
            fpa = fpa.replace(minute=0, second=0, microsecond=0)

        # 4. Calcular Estancia (Noches Efectivas) - Issue #60
        # La estancia se calcula desde el ingreso hasta la FPA redondeada
        # Usamos la diferencia de fechas calendario para contar "noches"
        
        # Opción A: Diferencia de días calendario (simple)
        # Si ingreso es hoy y salida es mañana -> 1 noche
        # Si ingreso es hoy y salida es hoy -> 0 noches
        
        # Ajuste: Si la FPA es exactamente medianoche (00:00) del día siguiente, 
        # técnicamente cuenta como noche del día anterior para efectos de cama, 
        # pero matemáticamente date() cambia.
        # Sin embargo, la lógica estándar de "noches" es date_diff.
        
        days_diff = (fpa.date() - admission_time.date()).days
        overnight_stays = max(0, days_diff)

        return fpa, overnight_stays
