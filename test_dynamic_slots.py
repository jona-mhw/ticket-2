"""
Script de prueba para validar los bloques horarios dinámicos.
"""
from datetime import datetime, timedelta

class MockTicket:
    """Mock de ticket para pruebas."""
    def __init__(self, current_fpa):
        self.current_fpa = current_fpa

    def get_dynamic_discharge_slot(self):
        """Calcula el bloque horario dinámico."""
        if not self.current_fpa:
            return "Sin horario"

        end_time = self.current_fpa
        start_time = end_time - timedelta(hours=2)
        return f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

# Casos de prueba
test_cases = [
    {
        'desc': 'Cirugía a las 10:15',
        'fpa': datetime(2025, 1, 2, 10, 15),
        'expected': '08:15 - 10:15'
    },
    {
        'desc': 'Cirugía a las 10:45',
        'fpa': datetime(2025, 1, 2, 10, 45),
        'expected': '08:45 - 10:45'
    },
    {
        'desc': 'Cirugía 01/01/2025 10:00 + 24 horas',
        'fpa': datetime(2025, 1, 2, 10, 0),
        'expected': '08:00 - 10:00'
    },
    {
        'desc': 'FPA a las 14:30',
        'fpa': datetime(2025, 1, 2, 14, 30),
        'expected': '12:30 - 14:30'
    },
    {
        'desc': 'FPA a las 23:45',
        'fpa': datetime(2025, 1, 2, 23, 45),
        'expected': '21:45 - 23:45'
    },
    {
        'desc': 'FPA a las 01:30 (madrugada)',
        'fpa': datetime(2025, 1, 2, 1, 30),
        'expected': '23:30 - 01:30'
    }
]

print("="*70)
print("PRUEBAS DE BLOQUES HORARIOS DINÁMICOS")
print("="*70)
print("\nLógica: Bloque de 2 horas TERMINANDO en la hora exacta del FPA\n")

all_pass = True
for i, test in enumerate(test_cases, 1):
    ticket = MockTicket(test['fpa'])
    result = ticket.get_dynamic_discharge_slot()

    print(f"{i}. {test['desc']}")
    print(f"   FPA: {test['fpa'].strftime('%d/%m/%Y %H:%M')}")
    print(f"   Bloque calculado: {result}")
    print(f"   Bloque esperado:  {test['expected']}")

    if result == test['expected']:
        print(f"   ✓ CORRECTO")
    else:
        print(f"   ✗ ERROR")
        all_pass = False
    print()

print("="*70)
if all_pass:
    print("✓ TODAS LAS PRUEBAS PASARON")
else:
    print("✗ ALGUNAS PRUEBAS FALLARON")
print("="*70)
