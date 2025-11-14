# Bug: FPA indicado por médico no se respeta - sistema usa siempre FPA calculado

## 🐛 Descripción del Problema

Cuando un médico crea un ticket e indica una **Fecha Posible de Alta (FPA) diferente** a la calculada automáticamente por el sistema, el ticket **NO respeta** la fecha indicada por el médico.

### Comportamiento Actual ❌
- El médico selecciona una fecha en el campo `medical_discharge_date`
- El sistema captura y guarda este valor en la base de datos
- **PERO** el sistema establece `initial_fpa` y `current_fpa` usando el FPA calculado automáticamente
- La fecha indicada por el médico queda registrada pero no se usa

### Comportamiento Esperado ✅
- Si el médico indica una fecha diferente a la sugerida, **esa fecha debe ser el FPA del ticket**
- El `initial_fpa` debe ser la fecha indicada por el médico (no el cálculo automático)
- El `current_fpa` debe inicializarse con el FPA del médico
- El panel de enfermería, PDF y todas las vistas deben mostrar el FPA del médico

---

## 🔍 Análisis Técnico

### Archivos Afectados

**1. `routes/tickets.py` (líneas 70-96)**
```python
# Problema: Captura medical_discharge_date pero NO lo usa
medical_discharge_date = datetime.strptime(
    request.form.get('medical_discharge_date'),
    '%Y-%m-%d'
).date()

ticket_data = {
    # ...
    'medical_discharge_date': medical_discharge_date,  # Se guarda pero no se usa
    # Falta: convertir medical_discharge_date a datetime y usarlo como initial_fpa
}

ticket = TicketService.create_ticket(ticket_data, current_user)
```

**2. `services/ticket_service.py` (líneas 47-100)**
```python
def create_ticket(ticket_data, user):
    # Problema: Siempre calcula FPA automático
    fpa, overnight_stays = FPACalculator.calculate(
        ticket_data['pavilion_end_time'],
        ticket_data['surgery']
    )

    # Problema: No usa medical_discharge_date para determinar initial_fpa
    ticket = Ticket(
        # ...
        initial_fpa=ticket_data.get('initial_fpa', fpa),  # Siempre usa 'fpa'
        current_fpa=ticket_data.get('current_fpa', fpa),   # Siempre usa 'fpa'
        # Falta lógica para comparar medical_discharge_date vs fpa
    )
```

---

## 💡 Solución Propuesta

### Paso 1: Convertir `medical_discharge_date` a datetime en `routes/tickets.py`

```python
# Convertir medical_discharge_date (date) a datetime con hora de bloque
medical_discharge_date = datetime.strptime(
    request.form.get('medical_discharge_date'),
    '%Y-%m-%d'
).date()

# Calcular FPA automático del sistema
system_fpa, _ = FPACalculator.calculate(pavilion_end_time, surgery)

# Determinar si el médico indicó una fecha diferente
if medical_discharge_date != system_fpa.date():
    # Convertir la fecha del médico a datetime
    # IMPORTANTE: Usar un bloque horario por defecto (ej: 18:00)
    # O mejor: agregar un campo para que el médico seleccione el bloque
    medical_fpa_datetime = datetime.combine(medical_discharge_date, time(18, 0))

    # Pasar el FPA del médico al ticket_data
    ticket_data['initial_fpa'] = medical_fpa_datetime
    ticket_data['current_fpa'] = medical_fpa_datetime
else:
    # Si son iguales, usar el FPA calculado (que ya tiene la hora correcta)
    ticket_data['initial_fpa'] = system_fpa
    ticket_data['current_fpa'] = system_fpa
```

### Paso 2: Actualizar `ticket_service.py`

```python
def create_ticket(ticket_data, user):
    # Calcular FPA automático (para referencia)
    system_fpa, overnight_stays = FPACalculator.calculate(
        ticket_data['pavilion_end_time'],
        ticket_data['surgery']
    )

    # Usar initial_fpa del ticket_data si fue proporcionado (FPA del médico)
    # Sino, usar el calculado automáticamente
    initial_fpa = ticket_data.get('initial_fpa', system_fpa)
    current_fpa = ticket_data.get('current_fpa', system_fpa)

    # Recalcular overnight_stays si se usó FPA del médico
    if 'initial_fpa' in ticket_data:
        time_diff = initial_fpa - ticket_data['pavilion_end_time']
        overnight_stays = max(0, time_diff.days)
        if time_diff.seconds > 0:
            overnight_stays += 1

    ticket = Ticket(
        # ...
        system_calculated_fpa=system_fpa,  # Guardar el cálculo del sistema
        initial_fpa=initial_fpa,            # Usar FPA del médico o sistema
        current_fpa=current_fpa,            # Usar FPA del médico o sistema
        overnight_stays=overnight_stays,    # Recalculado
        # ...
    )
```

---

## ✅ Criterios de Aceptación

- [ ] Si el médico indica una fecha **igual** a la calculada, el ticket usa el FPA calculado
- [ ] Si el médico indica una fecha **diferente** a la calculada, el ticket usa el FPA del médico
- [ ] El `initial_fpa` refleja la decisión del médico
- [ ] El `current_fpa` refleja la decisión del médico
- [ ] El panel de enfermería muestra el FPA indicado por el médico
- [ ] El PDF de exportación muestra el FPA indicado por el médico
- [ ] La vista de detalle muestra claramente si hubo discrepancia inicial
- [ ] Los campos `initial_reason` e `initial_justification` se asocian correctamente cuando hay discrepancia
- [ ] El campo `overnight_stays` se calcula correctamente con el FPA del médico

---

## 📊 Impacto

- **Prioridad**: 🔴 ALTA
- **Usuarios afectados**: Médicos y personal clínico
- **Módulos afectados**: Creación de tickets, panel de enfermería, exportación PDF

---

## 🏷️ Labels Sugeridos
`bug`, `priority: high`, `backend`, `business-logic`
