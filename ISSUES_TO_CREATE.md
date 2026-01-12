# Issues para Mejoras Dashboard - Plataforma Ticket Home

> Crear estos 5 issues en GitHub: https://github.com/jona-mhw/ticket-2/issues

---

## Issue #1: Dashboard - Redefinir KPIs (Vigentes, Creados Hoy, Vencidos, Anulados)

**Labels:** `enhancement`, `dashboard`, `KPI`

### Descripción
Redefinición de los 4 indicadores principales del dashboard con criterios específicos de filtrado y ordenamiento.

### Objetivo
Actualizar los KPIs con las siguientes definiciones:

#### 1. **Vigentes**
- **Definición**: Tickets que tienen tiempo restante (no han llegado a la fecha de alta)
- **Criterio**: Tickets con estado activo y `discharge_date` > fecha/hora actual
- **Ordenamiento**: Los tickets programados para cirugía HOY deben mostrarse al final de la lista
- **Orden por defecto**: Descendente (más reciente → más antiguo)

#### 2. **Creados Hoy**
- **Definición**: Total de tickets generados en la fecha actual
- **Criterio**: `created_at` entre 00:01 y 23:59 del día actual
- **Orden por defecto**: Descendente (más reciente → más antiguo)

#### 3. **Vencidos**
- **Definición**: Tickets que llegaron a su fecha de alta
- **Criterio**: `discharge_date` <= fecha/hora actual
- **Orden por defecto**: Descendente (más reciente → más antiguo)

#### 4. **Anulados**
- **Definición**: Tickets con estado de anulación
- **Criterio**: `status` = 'Anulado'
- **Orden por defecto**: Descendente (más reciente → más antiguo)

### Criterios de Aceptación
- [ ] Los 4 KPIs muestran contadores correctos según las definiciones
- [ ] Todos los tickets se ordenan por defecto de forma descendente
- [ ] En 'Vigentes', los tickets programados para cirugía HOY aparecen al final
- [ ] Los cálculos consideran la zona horaria correcta (00:01-23:59)
- [ ] Los KPIs se actualizan en tiempo real al cambiar estados

### Archivos Relevantes
- `routes/dashboard.py`
- `templates/dashboard.html`
- `services/ticket_service.py`
- `repositories/ticket_repository.py`

---

## Issue #2: Tickets - Eliminar opción de fecha de alta manual

**Labels:** `enhancement`, `tickets`, `UX`

### Problema Actual
El sistema actualmente permite al usuario seleccionar entre:
1. Fecha y hora calculada automáticamente para la cirugía
2. Indicar manualmente una fecha de alta distinta (indicación médica)

### Cambio Solicitado
**Eliminar la opción #2** - El sistema debe usar ÚNICAMENTE la fecha calculada automáticamente.

### Impacto

**Formulario de Creación de Tickets:**
- ❌ Remover campo de entrada manual para 'Fecha Posible de Alta (Indicación Médica)'
- ✅ Mantener solo la fecha calculada por el sistema
- ✅ Mostrar la fecha calculada como información (no editable)

**Lógica de Backend:**
- Eliminar validaciones relacionadas con fecha de alta manual
- Asegurar que `discharge_date` siempre se calcule automáticamente

### Criterios de Aceptación
- [ ] El formulario de creación de tickets NO muestra campo para fecha de alta manual
- [ ] La fecha de alta se calcula automáticamente según lógica existente
- [ ] No es posible crear tickets con fecha de alta customizada
- [ ] Los tickets existentes con fecha manual no se ven afectados (considerar migración)
- [ ] Las pruebas unitarias se actualizan para reflejar el cambio

### Archivos Relevantes
- `templates/tickets/create.html`
- `routes/tickets.py` (endpoint de creación)
- `services/ticket_service.py`
- `models.py` (validaciones)
- `forms/` (si existen forms WTF para tickets)

---

## Issue #3: Dashboard y Tablero - Filtro de Clínica para Superusuario

**Labels:** `enhancement`, `dashboard`, `filter`, `superuser`

### Objetivo
Agregar un filtro de selección de clínica que permita al Superusuario:
- Ver datos de **todas las clínicas** (opción por defecto)
- Filtrar por una **clínica específica**

### Ubicaciones
Este filtro debe aparecer en:
1. **Dashboard Principal** (`dashboard.html`)
2. **Tablero de Enfermería** (`nursing_board.html`)

### Comportamiento

**Visibilidad:**
- ✅ Visible SOLO para usuarios con rol `Superusuario`
- ❌ Oculto para usuarios `admin`, `clinical`, `visualizador`

**Opciones del Filtro:**
```
[ Dropdown ]
- Todas las clínicas (default)
- Clínica A
- Clínica B
- Clínica C
...
```

**Funcionalidad:**
- Al seleccionar 'Todas las clínicas': mostrar datos sin restricción
- Al seleccionar una clínica específica: filtrar todos los KPIs y tablas por `clinic_id`
- El filtro es acumulativo con otros filtros (fechas, cirugía, etc.)

### Criterios de Aceptación
- [ ] El filtro aparece en Dashboard y Tablero de Enfermería
- [ ] Solo visible para rol Superusuario
- [ ] Muestra 'Todas las clínicas' como opción por defecto
- [ ] Lista todas las clínicas activas del sistema
- [ ] Al cambiar selección, actualiza todos los KPIs y tablas
- [ ] Se puede combinar con otros filtros (fechas, cirugía)
- [ ] Mantiene selección al navegar entre pestañas/secciones

### Archivos Relevantes
- `templates/dashboard.html`
- `templates/tickets/nursing_board.html`
- `routes/dashboard.py`
- `routes/tickets.py`
- `models.py` (User.is_superuser)
- `static/js/tickets.js` (lógica de filtrado)

---

## Issue #4: Tablero de Enfermería - Controles de ordenamiento por fecha

**Labels:** `enhancement`, `nursing-board`, `UX`

### Objetivo
Permitir al usuario alternar el ordenamiento de tickets en el **Tablero de Enfermería** según:
- **Fecha de Creación** (Ascendente ⬆️ / Descendente ⬇️)
- **Fecha de Alta** (Ascendente ⬆️ / Descendente ⬇️)

### Alcance
**Ubicación:** SOLO en el Tablero de Enfermería (`nursing_board.html`)

**NO aplica para:**
- Dashboard principal
- Vista de lista de tickets
- Otras vistas

### Diseño Propuesto

**UI Sugerida:**
```
┌────────────────────────────────────────┐
│  Ordenar por:                          │
│  ( ) Fecha Creación  ⬆️ ⬇️              │
│  ( ) Fecha Alta      ⬆️ ⬇️              │
└────────────────────────────────────────┘
```

**Comportamiento:**
- Click en ⬆️: Ordena ascendente (más antiguo → más reciente)
- Click en ⬇️: Ordena descendente (más reciente → más antiguo)
- Por defecto: Descendente (⬇️)
- Solo un criterio activo a la vez (radio buttons o toggle)

### Criterios de Aceptación
- [ ] Controles visibles SOLO en Tablero de Enfermería
- [ ] Toggle para Fecha de Creación (ASC/DESC)
- [ ] Toggle para Fecha de Alta (ASC/DESC)
- [ ] Orden por defecto: Descendente
- [ ] Al cambiar orden, la tabla se actualiza inmediatamente
- [ ] El ordenamiento se mantiene al aplicar filtros
- [ ] Visual feedback del orden activo (iconos, colores)
- [ ] Responsive (funciona en mobile)

### Archivos Relevantes
- `templates/tickets/nursing_board.html`
- `static/js/tickets.js`
- `static/css/enhanced-tickets.css`
- `routes/tickets.py` (endpoint de tablero)

---

## Issue #5: Dashboard - Filtros de Rango de Fechas y Cirugía

**Labels:** `enhancement`, `dashboard`, `filter`

### Objetivo
Integrar dos nuevos filtros en el dashboard principal:
1. **Filtro por Rango de Fechas** (para consulta histórica)
2. **Filtro por Tipo de Cirugía** (segmentación por procedimiento)

### 1. Filtro por Rango de Fechas

**Diseño:**
```
Fecha Inicio: [📅 dd/mm/yyyy]  -  Fecha Fin: [📅 dd/mm/yyyy]  [Aplicar]
```

**Funcionalidad:**
- Date picker para seleccionar fecha inicio y fin
- Validación: Fecha inicio <= Fecha fin
- Por defecto: vacío (muestra todos los tickets)
- Al aplicar: filtra tickets por `created_at` en el rango
- Permite consultas históricas más allá del día actual

### 2. Filtro por Cirugía

**Diseño:**
```
Cirugía: [ Dropdown: Todas | Cirugía A | Cirugía B | ... ]
```

**Funcionalidad:**
- Dropdown con todas las cirugías registradas en el sistema
- Opción 'Todas' por defecto
- Al seleccionar: filtra tickets por `surgery_id`
- Lista ordenada alfabéticamente

### Características Generales

**Filtros Acumulativos:**
- ✅ Se pueden combinar: Fecha + Cirugía + Clínica (superuser)
- ✅ Los KPIs reflejan los filtros aplicados
- ✅ Las tablas muestran solo registros que cumplen TODOS los filtros activos

**Disponibilidad:**
- ✅ Todos los usuarios (admin, clinical, visualizador, superuser)
- ✅ Ubicación: Dashboard principal

**Reseteo:**
- Botón 'Limpiar Filtros' para volver a vista completa

### Criterios de Aceptación
- [ ] Filtro de rango de fechas con date pickers funcionales
- [ ] Validación: fecha inicio no puede ser mayor que fecha fin
- [ ] Filtro de cirugía con dropdown de todas las cirugías activas
- [ ] Los filtros son acumulativos (se combinan con AND)
- [ ] Los KPIs se actualizan según filtros aplicados
- [ ] Las tablas muestran solo datos filtrados
- [ ] Botón para limpiar/resetear todos los filtros
- [ ] Indicador visual de filtros activos
- [ ] Performance: filtrado eficiente en backend (no solo frontend)

### Archivos Relevantes
- `templates/dashboard.html`
- `routes/dashboard.py`
- `services/ticket_service.py`
- `repositories/ticket_repository.py`
- `static/js/tickets.js`
- `models.py` (Surgery, Ticket)

---

## Resumen de Cambios

| # | Issue | Prioridad | Complejidad |
|---|-------|-----------|-------------|
| 1 | Redefinir KPIs | Alta | Media |
| 2 | Eliminar fecha alta manual | Alta | Baja |
| 3 | Filtro clínica Superusuario | Media | Media |
| 4 | Controles ordenamiento enfermería | Baja | Baja |
| 5 | Filtros fecha y cirugía | Media | Media |

### Notas Importantes
- Los filtros deben ser **acumulativos** (se pueden combinar)
- El orden por defecto para todos los tickets es **descendente**
- El filtro de clínica es **exclusivo para Superusuario**
- La opción de descarga se implementará en una fase posterior
