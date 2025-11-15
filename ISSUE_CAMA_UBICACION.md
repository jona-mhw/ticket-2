# Feature: Separar campo de Cama en dos campos independientes (Cama + Ubicación)

## 📋 Descripción de la Necesidad

Como usuario de la plataforma, quiero poder registrar tanto la **cama** como la **ubicación/comentarios** del paciente de forma independiente, para tener mejor trazabilidad y organización de la información de ubicación hospitalaria.

### Contexto Actual ❌
- Actualmente existe UN solo campo llamado `room` (100 caracteres)
- Se usa para registrar información mixta (número de cama + ubicación)
- Aparece en la vista de tarjetas con ícono de casa
- Es editable in-line haciendo clic
- No está claro si deben ingresar solo el número de cama o también ubicación

### Comportamiento Esperado ✅
- **Dos campos separados e independientes:**
  1. **Cama** (bed_number): Máximo 10 caracteres, texto libre
     - Ej: "201", "A-15", "UCI-3"
  2. **Ubicación** (location): Máximo 50 caracteres, texto libre
     - Ej: "Piso 2 Ala Norte", "UCI Pediátrica", "Pabellón recuperación"

- **Ambos campos visibles en:**
  - Vista de tarjetas (nursing board)
  - Vista de lista (nursing list)
  - Detalle del ticket
  - Exportaciones (PDF, Excel)

- **Labels/placeholders claros** para evitar confusión entre ambos campos
- **Edición in-line** en vista de tarjetas (similar al comportamiento actual)
- **Ambos campos opcionales** (nullable)

---

## 🔍 Análisis Técnico

### Archivos a Modificar

#### 1. **Backend - Modelo de Datos**

**`models.py` (línea 197)**
```python
# ANTES
room = db.Column(db.String(100), nullable=True)

# DESPUÉS
bed_number = db.Column(db.String(10), nullable=True)  # Número de cama
location = db.Column(db.String(50), nullable=True)     # Ubicación/comentarios
```

**Migración Alembic requerida:**
```python
# migrations/versions/XXXX_split_room_into_bed_and_location.py
def upgrade():
    # Opción 1: Migrar datos existentes de 'room' a 'bed_number'
    op.add_column('ticket', sa.Column('bed_number', sa.String(10), nullable=True))
    op.add_column('ticket', sa.Column('location', sa.String(50), nullable=True))
    
    # Copiar datos existentes de 'room' a 'bed_number' (primeros 10 chars)
    op.execute("UPDATE ticket SET bed_number = LEFT(room, 10) WHERE room IS NOT NULL")
    
    # Eliminar columna antigua
    op.drop_column('ticket', 'room')

def downgrade():
    op.add_column('ticket', sa.Column('room', sa.String(100), nullable=True))
    op.execute("UPDATE ticket SET room = bed_number WHERE bed_number IS NOT NULL")
    op.drop_column('ticket', 'location')
    op.drop_column('ticket', 'bed_number')
```

#### 2. **Backend - API Endpoint**

**`routes/tickets.py` (líneas 503-535)**
```python
# ANTES
@tickets_bp.route('/api/update-room', methods=['POST'])
def api_update_room():
    room = data.get('room', '').strip()
    ticket.room = room if room else None

# DESPUÉS
@tickets_bp.route('/api/update-bed-location', methods=['POST'])
def api_update_bed_location():
    bed_number = data.get('bed_number', '').strip()
    location = data.get('location', '').strip()
    
    # Validaciones
    if bed_number and len(bed_number) > 10:
        return jsonify({'error': 'Número de cama no puede exceder 10 caracteres'}), 400
    if location and len(location) > 50:
        return jsonify({'error': 'Ubicación no puede exceder 50 caracteres'}), 400
    
    ticket.bed_number = bed_number if bed_number else None
    ticket.location = location if location else None
    
    AuditService.log_action(
        user=current_user,
        action=f"Actualizó cama: {bed_number or 'Sin cama'}, ubicación: {location or 'Sin ubicación'}",
        target_id=ticket_id,
        target_type='Ticket'
    )
```

#### 3. **Frontend - Vista de Tarjetas**

**`templates/tickets/nursing_board.html` (líneas 153-162)**

Rediseñar el badge actual para mostrar AMBOS campos:

```html
<!-- ANTES: Un solo badge con ícono de casa -->
<div class="room-badge editable-room" data-ticket-id="{{ ticket.id }}">
    <svg class="w-5 h-5 room-icon">...</svg>
    <span class="room-display">{{ ticket.room or 'Sin cama' }}</span>
    <input type="text" class="room-input" maxlength="10">
</div>

<!-- DESPUÉS: Dos campos compactos en la parte superior -->
<div class="bed-location-header">
    <!-- Campo Cama (compacto) -->
    <div class="bed-field editable-field" 
         data-ticket-id="{{ ticket.id }}" 
         data-field="bed_number"
         title="Clic para editar cama">
        <svg class="w-3 h-3 field-icon">🛏️</svg>
        <span class="field-label">Cama:</span>
        <span class="field-value">{{ ticket.bed_number or '-' }}</span>
        <input type="text" class="field-input" placeholder="201" maxlength="10" style="display: none;">
    </div>
    
    <!-- Campo Ubicación (compacto) -->
    <div class="location-field editable-field" 
         data-ticket-id="{{ ticket.id }}" 
         data-field="location"
         title="Clic para editar ubicación">
        <svg class="w-3 h-3 field-icon">📍</svg>
        <span class="field-label">Ubic:</span>
        <span class="field-value">{{ ticket.location or '-' }}</span>
        <input type="text" class="field-input" placeholder="Piso 2" maxlength="50" style="display: none;">
    </div>
</div>
```

**CSS sugerido:**
```css
.bed-location-header {
    display: flex;
    gap: 0.5rem;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    color: #6b7280;
    border-bottom: 1px solid #e5e7eb;
}

.bed-field, .location-field {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    cursor: pointer;
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    transition: background 0.2s;
}

.bed-field:hover, .location-field:hover {
    background: #f3f4f6;
}

.field-icon {
    width: 0.75rem;
    height: 0.75rem;
}

.field-label {
    font-weight: 500;
    color: #6b7280;
}

.field-value {
    font-weight: 600;
    color: #111827;
}
```

**JavaScript:**
- Adaptar lógica de edición in-line para ambos campos
- Cambiar endpoint de `/api/update-room` → `/api/update-bed-location`
- Enviar `bed_number` y `location` en el payload

#### 4. **Otras Vistas a Actualizar**

**`templates/tickets/nursing_list.html`**
- Mostrar columna de "Cama" y "Ubicación" separadas
- O combinar visualmente con formato: "Cama 201 - Piso 2 Ala Norte"

**`templates/tickets/detail.html`**
- Mostrar ambos campos en la información del ticket
- Permitir edición si es necesario

**`templates/admin/edit_ticket.html`**
- Agregar ambos campos en formulario de edición

#### 5. **Exportaciones**

**`routes/exports.py`**
- PDF: Agregar ambos campos (bed_number y location)
- Excel: Agregar columnas separadas para cada campo

#### 6. **Búsqueda**

**`repositories/ticket_repository.py`**
```python
# Actualizar búsqueda para incluir ambos campos
if search:
    query = query.filter(
        or_(
            Patient.rut.ilike(f'%{search}%'),
            Patient.nombre.ilike(f'%{search}%'),
            Ticket.bed_number.ilike(f'%{search}%'),  # NUEVO
            Ticket.location.ilike(f'%{search}%')      # NUEVO
        )
    )
```

---

## ✅ Criterios de Aceptación

### Modelo de Datos
- [ ] Campo `room` eliminado de la tabla `ticket`
- [ ] Campo `bed_number` agregado (String 10 chars, nullable)
- [ ] Campo `location` agregado (String 50 chars, nullable)
- [ ] Migración Alembic creada y probada
- [ ] Datos existentes migrados correctamente (room → bed_number)

### API Backend
- [ ] Endpoint `/api/update-bed-location` implementado
- [ ] Validación de longitud máxima (10 chars para cama, 50 para ubicación)
- [ ] Auditoría registra cambios en ambos campos
- [ ] Endpoint antiguo `/api/update-room` eliminado o deprecated

### Vista de Tarjetas (Nursing Board)
- [ ] Dos campos compactos en la parte superior de cada tarjeta
- [ ] Menor protagonismo visual (tamaño pequeño, colores sutiles)
- [ ] Labels claros: "Cama:" y "Ubic:"
- [ ] Edición in-line funciona para ambos campos
- [ ] Placeholders claros ("201" y "Piso 2")
- [ ] Validación en frontend: máx 10 chars (cama) y 50 chars (ubicación)
- [ ] Ambos campos opcionales (pueden quedar vacíos, mostrar "-")
- [ ] No afecta la visualización de la información principal (paciente, RUT, cirugía, FPA, etc.)

### Vista de Lista (Nursing List)
- [ ] Columnas separadas o combinadas visualmente
- [ ] Información visible y clara

### Detalle de Ticket
- [ ] Ambos campos visibles en información del ticket
- [ ] Formato claro: "Cama: 201" y "Ubicación: Piso 2 Ala Norte"

### Exportaciones
- [ ] PDF incluye ambos campos
- [ ] Excel tiene columnas separadas para cama y ubicación

### Búsqueda
- [ ] Búsqueda encuentra tickets por número de cama
- [ ] Búsqueda encuentra tickets por ubicación
- [ ] Placeholder del buscador actualizado (ej: "Buscar paciente, RUT, cama, ubicación...")

### Testing
- [ ] Migración funciona correctamente en DB de prueba
- [ ] Edición in-line guarda correctamente en ambos campos
- [ ] Validaciones de longitud funcionan
- [ ] Búsqueda encuentra por ambos campos
- [ ] Exportaciones incluyen la información correcta

---

## 📊 Impacto

- **Prioridad**: 🟡 MEDIA-ALTA
- **Usuarios afectados**: Todo el personal clínico (médicos, enfermería, administración)
- **Módulos afectados**: 
  - Modelo de datos (migración requerida)
  - Vista de tarjetas (nursing board)
  - Vista de lista
  - Detalle de ticket
  - Exportaciones (PDF, Excel)
  - Búsqueda
  - API backend

---

## 🎨 Mockup/Wireframe Sugerido

```
┌─────────────────────────────────────────────────────┐
│ 🛏️ Cama: 201    📍 Ubic: Piso 2 Norte             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Paciente: Juan Pérez Rodríguez                     │
│  RUT: 12.345.678-9                                  │
│                                                     │
│  Cirugía: Apendicectomía Laparoscópica              │
│  Fecha cirugía: 15/11/2025 14:30                    │
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │ FPA: 16/11/2025 10:00                      │    │
│  │ Bloque: 08:00 - 10:00                      │    │
│  │ Estancia: 1 día                            │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  Dr. García - Cirugía General                       │
│  Estado: [Vigente]                                  │
│                                                     │
└─────────────────────────────────────────────────────┘

Nota: Los campos Cama y Ubicación en la parte superior
      son editables con clic (menor tamaño, color gris)
```

**Características del diseño:**
- ✅ Campos Cama y Ubicación en la **parte superior** de la tarjeta
- ✅ Tamaño de texto **pequeño** (0.75rem vs 1rem del contenido principal)
- ✅ Color **gris suave** (#6b7280) para menor protagonismo
- ✅ Separador visual sutil (border-bottom)
- ✅ Íconos pequeños (12px) en lugar de grandes
- ✅ **No interfiere** con la información principal (paciente, cirugía, FPA)
- ✅ Editable con hover/clic discreto

---

## 🔗 Referencias

- **Archivos principales afectados:**
  - `models.py` (línea 197)
  - `routes/tickets.py` (líneas 503-535)
  - `templates/tickets/nursing_board.html` (líneas 153-162)
  - `repositories/ticket_repository.py` (búsqueda)
  - `routes/exports.py` (exportaciones)

- **Endpoint actual:**
  - POST `/api/update-room`
  - Nuevo: POST `/api/update-bed-location`

---

## 💡 Consideraciones Adicionales

### Migración de Datos
- Los datos actuales del campo `room` deben migrarse a `bed_number`
- Si el valor actual excede 10 caracteres, truncar con advertencia en logs
- El campo `location` iniciará vacío para todos los tickets existentes

### UX/UI
- Usar íconos pequeños y discretos:
  - Cama: 🛏️ (12px)
  - Ubicación: 📍 (12px)
- Labels abreviados: "Cama:" y "Ubic:" (para ahorrar espacio)
- Colores sutiles (gris) para no competir con información principal
- Disposición horizontal en una sola línea

### Performance
- La búsqueda ahora incluirá 2 campos adicionales (puede afectar performance)
- Considerar agregar índices si es necesario:
  ```sql
  CREATE INDEX idx_ticket_bed_number ON ticket(bed_number);
  CREATE INDEX idx_ticket_location ON ticket(location);
  ```

### Auditoría
- Los cambios en ambos campos deben quedar registrados en `ActionAudit`
- Formato sugerido: "Actualizó cama de '201' a '202' y ubicación de 'Piso 2' a 'UCI'"
