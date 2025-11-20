import unittest
from datetime import datetime, timedelta
from services.fpa_calculator import FPACalculator

class MockSurgery:
    def __init__(self, base_stay_hours, is_ambulatory=False, ambulatory_cutoff_hour=None):
        self.base_stay_hours = base_stay_hours
        self.is_ambulatory = is_ambulatory
        self.ambulatory_cutoff_hour = ambulatory_cutoff_hour

class TestFPACalculator(unittest.TestCase):
    
    def test_issue_60_bug_estancia_24h(self):
        """
        Issue #60: Cirugía de 24h debería dar 1 día de estancia, no 2.
        Caso: 19-11-2025 09:53 -> FPA 20-11-2025 ~10:00
        """
        surgery_time = datetime(2025, 11, 19, 9, 53)
        surgery = MockSurgery(base_stay_hours=24)
        
        fpa, overnight_stays = FPACalculator.calculate(surgery_time, surgery)
        
        # Ingreso: 09:53 - 2h = 07:53
        # FPA Base: 07:53 + 24h = 20-11 07:53
        # Redondeo: 07:53 -> 08:00 (UP)
        # Estancia: 20-11 08:00 - 19-11 07:53 (Ingreso) -> 1 día calendario (19 al 20)
        
        print(f"\nTest Issue #60 (24h): Surgery {surgery_time} -> FPA {fpa}, Stays {overnight_stays}")
        
        self.assertEqual(overnight_stays, 1, "Should be 1 day stay")
        self.assertEqual(fpa, datetime(2025, 11, 20, 8, 0))

    def test_issue_63_rule_1_normal_admission(self):
        """
        Issue #63 Regla 1: Ingreso 2 horas antes.
        Caso: 19-11 10:00 AM, 48h estancia.
        Ingreso: 08:00 AM.
        FPA Base: 21-11 08:00 AM.
        Redondeo: 08:00 (No minutos) -> 08:00.
        """
        surgery_time = datetime(2025, 11, 19, 10, 0)
        surgery = MockSurgery(base_stay_hours=48)
        
        fpa, overnight_stays = FPACalculator.calculate(surgery_time, surgery)
        
        print(f"Test Issue #63 (Rule 1): Surgery {surgery_time} -> FPA {fpa}")
        
        self.assertEqual(fpa, datetime(2025, 11, 21, 8, 0))
        # Estancia: 19 al 21 -> 2 días
        self.assertEqual(overnight_stays, 2)

    def test_issue_63_rule_2_exception_0800(self):
        """
        Issue #63 Regla 2: Excepción 08:00 AM -> Ingreso 06:30 AM.
        Caso: 19-11 08:00 AM, 24h estancia.
        Ingreso: 06:30 AM.
        FPA Base: 20-11 06:30 AM.
        Redondeo: 06:30 -> 07:00 AM (UP).
        """
        surgery_time = datetime(2025, 11, 19, 8, 0)
        surgery = MockSurgery(base_stay_hours=24)
        
        fpa, overnight_stays = FPACalculator.calculate(surgery_time, surgery)
        
        print(f"Test Issue #63 (Rule 2): Surgery {surgery_time} -> FPA {fpa}")
        
        self.assertEqual(fpa, datetime(2025, 11, 20, 7, 0))
        self.assertEqual(overnight_stays, 1)

    def test_issue_63_rounding_minutes(self):
        """
        Issue #63 Redondeo: Siempre hacia arriba si hay minutos.
        Caso: 10:15 -> 11:00.
        """
        surgery_time = datetime(2025, 11, 19, 10, 15)
        surgery = MockSurgery(base_stay_hours=24)
        
        # Ingreso: 08:15
        # FPA Base: 20-11 08:15
        # Redondeo: 09:00
        
        fpa, overnight_stays = FPACalculator.calculate(surgery_time, surgery)
        
        print(f"Test Issue #63 (Rounding): Surgery {surgery_time} -> FPA {fpa}")
        
        self.assertEqual(fpa, datetime(2025, 11, 20, 9, 0))

if __name__ == '__main__':
    unittest.main()
