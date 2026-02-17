# Últimos Cambios - Sesión 2026-02-16

## 1. Fix "Calculando..." en Detalle de Ticket

**Archivo:** `routes/tickets.py` (línea ~243, función `detail()`)

**Problema:** Al abrir el detalle de un ticket, el campo de hora de admisión mostraba "Calculando..." porque `ticket.admission_time` era `None` — la ruta nunca calculaba ese valor antes de renderizar el template.

**Solución:** Se agregó una llamada a `FPACalculator.calculate_admission_time(ticket.pavilion_end_time)` justo antes del `render_template`, asignando el resultado a `ticket.admission_time` si no existía previamente. El template (`templates/tickets/detail.html:287`) ya tenía la lógica condicional `ticket.admission_time.strftime('%H:%M') if ticket.admission_time else 'Calculando...'`, así que al poblar el atributo, el valor real se muestra automáticamente.

---

## 2. Columnas Ordenables en Tablas de Datos Maestros (Admin)

**Archivo:** `templates/admin/master_data.html`

**Problema:** Las 4 tablas de datos maestros (Especialidades, Cirugías, Razones Estandarizadas, Médicos) eran HTML estático sin capacidad de ordenar columnas.

**Solución:**
- Se agregó atributo `id` a cada `<table>`: `specialtiesTable`, `surgeriesTable`, `reasonsTable`, `doctorsTable`.
- Se inicializó DataTables (ya cargado globalmente en `base.html`) en el bloque `<script>` existente con configuración mínima:
  - `paging: false`, `searching: false`, `info: false` (tablas pequeñas)
  - `ordering: true`
  - Columna "Acciones" excluida del ordenamiento (`columnDefs: [{ orderable: false, targets: -1 }]`)
  - Idioma español via plugin i18n

---

## 3. Reemplazo de Tendencia Semanal por Tabla de Médicos con Más Modificaciones FPA

**Archivos:** `routes/dashboard.py`, `templates/dashboard.html`

**Problema:** El gráfico de líneas "Tendencia Semanal" (tickets creados por día en los últimos 7 días) debía reemplazarse por una tabla mostrando los médicos tratantes cuyos tickets tienen más modificaciones FPA.

**Solución en el backend (`routes/dashboard.py`):**
- Se agregó `Doctor` al import de modelos.
- Se reemplazó el loop de 7 días (`weekly_trend`) por un query:
  ```python
  db.session.query(Doctor.name, func.count(FpaModification.id))
      .join(Ticket, FpaModification.ticket_id == Ticket.id)
      .join(Doctor, Ticket.doctor_id == Doctor.id)
      .group_by(Doctor.id, Doctor.name)
      .order_by(func.count(FpaModification.id).desc())
      .limit(10)
  ```
- Se eliminó `weekly_trend` de `chart_data` y se agregó `doctor_modifications` al contexto del template.

**Solución en el frontend (`templates/dashboard.html`):**
- Se reemplazó el `<canvas id="weeklyTrendChart">` por una tabla HTML con columnas: #, Médico, Modificaciones.
- Se eliminó todo el bloque de JavaScript de Chart.js que inicializaba `weeklyChart`.
- Se incluyó un `{% else %}` para mostrar "Sin datos de modificaciones" si la lista está vacía.

---

## Archivos Modificados (resumen)

| Archivo | Cambio |
|---|---|
| `routes/tickets.py` | Cálculo de `admission_time` en `detail()` |
| `templates/admin/master_data.html` | IDs en tablas + init DataTables |
| `routes/dashboard.py` | Query `doctor_modifications` reemplaza `weekly_trend` |
| `templates/dashboard.html` | Tabla de médicos reemplaza gráfico de tendencia semanal |

## Verificación

- `py_compile` exitoso en ambos archivos Python modificados.
- Para verificar visualmente: revisar detalle de ticket (admisión), `/admin/master-data` (ordenar columnas), `/dashboard` (tabla de médicos).
