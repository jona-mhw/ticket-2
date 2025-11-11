"""
Script de prueba para validar la lógica de cálculo de FPA y asignación de bloques horarios.
"""
from datetime import datetime, time

# Simular bloques horarios
class DischargeSlot:
    def __init__(self, name, start_hour, start_min, end_hour, end_min):
        self.name = name
        self.start_time = time(start_hour, start_min)
        self.end_time = time(end_hour, end_min)

# Crear bloques horarios estándar
slots = [
    DischargeSlot('08:00-10:00', 8, 0, 10, 0),
    DischargeSlot('10:00-12:00', 10, 0, 12, 0),
    DischargeSlot('12:00-14:00', 12, 0, 14, 0),
    DischargeSlot('14:00-16:00', 14, 0, 16, 0),
    DischargeSlot('16:00-18:00', 16, 0, 18, 0),
    DischargeSlot('18:00-20:00', 18, 0, 20, 0),
    DischargeSlot('20:00-22:00', 20, 0, 22, 0),
    DischargeSlot('22:00-00:00', 22, 0, 0, 0),
    DischargeSlot('00:00-02:00', 0, 0, 2, 0),
    DischargeSlot('02:00-04:00', 2, 0, 4, 0),
    DischargeSlot('04:00-06:00', 4, 0, 6, 0),
    DischargeSlot('06:00-08:00', 6, 0, 8, 0),
]

def find_slot(fpa_time):
    """Encuentra el slot que corresponde a un FPA dado."""
    matching_slots = []
    for slot in slots:
        # Manejar el caso especial de 22:00-00:00
        if slot.end_time == time(0, 0):
            end_compare = time(23, 59, 59)
        else:
            end_compare = slot.end_time

        if slot.start_time <= fpa_time <= end_compare:
            matching_slots.append(slot)

    # Si hay múltiples coincidencias, tomar el que termina más temprano
    if matching_slots:
        matching_slots.sort(key=lambda s: s.end_time)
        return matching_slots[0]
    return None

# Casos de prueba
test_cases = [
    {
        'desc': 'Cirugía 01/01/2025 10:00, duración 24 horas',
        'pavilion_end': datetime(2025, 1, 1, 10, 0),
        'duration_hours': 24,
        'expected_slot': '08:00-10:00'
    },
    {
        'desc': 'Cirugía termina a las 10:15',
        'pavilion_end': datetime(2025, 1, 1, 10, 15),
        'duration_hours': 0,  # Sin duración adicional
        'expected_slot': '10:00-12:00'
    },
    {
        'desc': 'Cirugía termina a las 10:45',
        'pavilion_end': datetime(2025, 1, 1, 10, 45),
        'duration_hours': 0,  # Sin duración adicional
        'expected_slot': '10:00-12:00'
    },
    {
        'desc': 'FPA exactamente a las 12:00',
        'pavilion_end': datetime(2025, 1, 1, 12, 0),
        'duration_hours': 0,
        'expected_slot': '10:00-12:00'  # Debería ser el que termina a las 12:00
    },
    {
        'desc': 'FPA a las 12:01',
        'pavilion_end': datetime(2025, 1, 1, 12, 1),
        'duration_hours': 0,
        'expected_slot': '12:00-14:00'
    }
]

print("="*70)
print("PRUEBAS DE LÓGICA DE ASIGNACIÓN DE BLOQUES HORARIOS FPA")
print("="*70)

for i, test in enumerate(test_cases, 1):
    from datetime import timedelta

    # Calcular FPA
    fpa = test['pavilion_end'] + timedelta(hours=test['duration_hours'])
    fpa_time = fpa.time()

    # Encontrar slot
    slot = find_slot(fpa_time)

    print(f"\n{i}. {test['desc']}")
    print(f"   Pabellón termina: {test['pavilion_end'].strftime('%d/%m/%Y %H:%M')}")
    print(f"   Duración: {test['duration_hours']} horas")
    print(f"   FPA calculado: {fpa.strftime('%d/%m/%Y %H:%M')}")
    print(f"   Slot encontrado: {slot.name if slot else 'NO ENCONTRADO'}")
    print(f"   Slot esperado: {test['expected_slot']}")

    if slot and slot.name == test['expected_slot']:
        print(f"   ✓ CORRECTO")
    else:
        print(f"   ✗ ERROR - No coincide con el esperado")

print("\n" + "="*70)
print("EXPLICACIÓN DE BLOQUES HORARIOS")
print("="*70)
print("\nBloques disponibles en el sistema (cada 2 horas):")
for slot in slots:
    print(f"  - {slot.name}")

print("\n" + "="*70)
print("NOTA IMPORTANTE:")
print("="*70)
print("Los bloques son fijos de 2 horas. NO existe bloque 09:00-11:00.")
print("Si el requerimiento menciona bloques variables, se necesita")
print("modificar la estructura de DischargeTimeSlot en la base de datos.")
print("="*70)
