# 🏗️ Arquitectura de Ticket Home

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Arquitectura General](#arquitectura-general)
- [Capas de la Aplicación](#capas-de-la-aplicación)
- [Patrones de Diseño](#patrones-de-diseño)
- [Multi-Tenancy](#multi-tenancy)
- [Autenticación y Autorización](#autenticación-y-autorización)
- [Flujo de Datos](#flujo-de-datos)
- [Diagramas](#diagramas)
- [Tecnologías](#tecnologías)

---

## 📝 Introducción

Ticket Home es una aplicación web Flask para gestionar tickets de alta médica en clínicas. La arquitectura sigue principios de **Clean Architecture** combinados con el patrón **MVC** (Model-View-Controller), pero con capas adicionales para separación de responsabilidades.

### ¿Qué es Clean Architecture?

Si conoces **MVC** (Model-View-Controller), Clean Architecture es una evolución que agrega más capas:

**MVC Tradicional:**
```
View ← Controller ← Model
```

**Clean Architecture (Ticket Home):**
```
Templates (View) ← Routes (Controller) ← Services (Business Logic) ← Repositories (Data Access) ← Models (Entities)
                                        ↑
                                   Validators
                                   DTOs/Utils
```

### Beneficios

✅ **Separación de responsabilidades**: Cada capa tiene una función clara
✅ **Testeable**: Puedes testear cada capa independientemente
✅ **Mantenible**: Cambios en una capa no afectan otras
✅ **Escalable**: Fácil agregar nuevas funcionalidades
✅ **SOLID**: Sigue principios de diseño orientado a objetos

---

## 🏗️ Arquitectura General

### Vista de Alto Nivel

```
┌─────────────────────────────────────────────────────────────┐
│                         USUARIO                             │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE PRESENTACIÓN                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Templates (Jinja2)                                   │  │
│  │  - dashboard.html, tickets.html, etc.                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE CONTROLADORES                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Routes (Blueprint)                                   │  │
│  │  - tickets.py, auth.py, admin.py, dashboard.py       │  │
│  │  Responsabilidad: Manejar HTTP requests/responses    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│               CAPA DE VALIDACIÓN (Opcional)                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Validators                                           │  │
│  │  - ticket_validator.py, user_validator.py            │  │
│  │  Responsabilidad: Validar datos de entrada           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE LÓGICA DE NEGOCIO                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Services                                             │  │
│  │  - ticket_service.py, user_service.py                │  │
│  │  - fpa_calculator.py, audit_service.py               │  │
│  │  Responsabilidad: Reglas de negocio y cálculos       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE ACCESO A DATOS                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Repositories                                         │  │
│  │  - ticket_repository.py, user_repository.py          │  │
│  │  Responsabilidad: Consultas a la base de datos       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                     CAPA DE ENTIDADES                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Models (SQLAlchemy ORM)                              │  │
│  │  - User, Ticket, Clinic, Patient, Surgery, etc.      │  │
│  │  Responsabilidad: Definir estructura de datos        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                      BASE DE DATOS                          │
│                  PostgreSQL (Cloud SQL)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Capas de la Aplicación

### 1. Templates (Vista / View)

**Ubicación**: `/templates/`

**Tecnología**: Jinja2

**Responsabilidad**: Presentar datos al usuario

**Archivos principales:**
- `dashboard.html` - Dashboard principal
- `tickets.html` - Lista de tickets
- `ticket_create.html` - Formulario de creación
- `login.html` - Pantalla de login

**Ejemplo:**
```jinja2
{% extends "base.html" %}
{% block content %}
  <h1>Tickets de Alta</h1>
  {% for ticket in tickets %}
    <div class="ticket-card">
      <p>{{ ticket.id }} - {{ ticket.patient.full_name }}</p>
    </div>
  {% endfor %}
{% endblock %}
```

**Características:**
- ✅ No contiene lógica de negocio
- ✅ Solo renderiza datos que recibe del controlador
- ✅ Usa plantillas heredables con `extends`

---

### 2. Routes (Controlador / Controller)

**Ubicación**: `/routes/`

**Responsabilidad**: Manejar peticiones HTTP y coordinar flujo

**Archivos principales:**
- `tickets.py` - Endpoints de tickets (CRUD)
- `auth.py` - Login, logout, autenticación
- `admin.py` - Administración de clínicas y usuarios
- `dashboard.py` - Dashboard y métricas
- `exports.py` - Exportación de datos

**Ejemplo** (`routes/tickets.py`):
```python
@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'clinical'])
def create_ticket():
    if request.method == 'POST':
        # 1. Recibir datos del formulario
        form_data = request.form.to_dict()

        # 2. Validar datos
        errors = TicketValidator.validate_creation(form_data)
        if errors:
            return render_template('ticket_create.html', errors=errors)

        # 3. Preparar datos para el servicio
        ticket_data = {
            'patient': Patient.query.get(form_data['patient_id']),
            'surgery': Surgery.query.get(form_data['surgery_id']),
            'clinic': current_user.clinic,
            # ... más datos
        }

        # 4. Llamar al servicio (lógica de negocio)
        ticket = TicketService.create_ticket(ticket_data, current_user)

        # 5. Guardar en base de datos
        db.session.commit()

        # 6. Responder al usuario
        flash('Ticket creado exitosamente', 'success')
        return redirect(url_for('tickets.list_tickets'))

    # GET: Mostrar formulario
    return render_template('ticket_create.html')
```

**Responsabilidades:**
- ✅ Recibir datos HTTP (request.form, request.args)
- ✅ Validar entrada (llamando a Validators)
- ✅ Coordinar servicios y repositorios
- ✅ Manejar transacciones de base de datos
- ✅ Devolver respuestas HTTP (render_template, redirect, jsonify)
- ❌ NO debe contener lógica de negocio compleja
- ❌ NO debe hacer queries directas complejas

---

### 3. Validators (Validación)

**Ubicación**: `/validators/`

**Responsabilidad**: Validar datos de entrada

**Archivos principales:**
- `ticket_validator.py`
- `user_validator.py`

**Ejemplo** (`validators/ticket_validator.py`):
```python
class TicketValidator:
    """Validates ticket data before processing."""

    @staticmethod
    def validate_creation(form_data):
        """
        Validate ticket creation form data.

        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []

        # Required fields
        if not form_data.get('patient_id'):
            errors.append("Debe seleccionar un paciente")

        if not form_data.get('surgery_id'):
            errors.append("Debe seleccionar una cirugía")

        # Date validation
        try:
            pavilion_end = datetime.fromisoformat(form_data['pavilion_end_time'])
            discharge_date = datetime.fromisoformat(form_data['medical_discharge_date'])

            if discharge_date < pavilion_end:
                errors.append("Fecha de alta no puede ser anterior a salida de pabellón")
        except (ValueError, KeyError):
            errors.append("Fechas inválidas")

        return errors
```

**Beneficios:**
- ✅ Validación reutilizable
- ✅ Separada de controladores
- ✅ Fácil de testear

---

### 4. Services (Lógica de Negocio)

**Ubicación**: `/services/`

**Responsabilidad**: Implementar reglas de negocio

**Archivos principales:**
- `ticket_service.py` - Lógica de tickets
- `fpa_calculator.py` - Cálculo de FPA (Fecha Probable de Alta)
- `user_service.py` - Gestión de usuarios
- `patient_service.py` - Gestión de pacientes
- `audit_service.py` - Logs de auditoría

**Ejemplo** (`services/ticket_service.py`):
```python
class TicketService:
    """Business logic for ticket management."""

    @staticmethod
    def create_ticket(ticket_data, user):
        """
        Create a new ticket with all business logic applied.
        """
        # 1. Calcular FPA (lógica de negocio compleja)
        fpa, overnight_stays = FPACalculator.calculate(
            ticket_data['pavilion_end_time'],
            ticket_data['surgery']
        )

        # 2. Generar ID único con formato específico
        ticket_id = TicketService.generate_ticket_id(ticket_data['clinic'])

        # 3. Crear ticket con datos calculados
        ticket = Ticket(
            id=ticket_id,
            patient_id=ticket_data['patient'].id,
            surgery_id=ticket_data['surgery'].id,
            clinic_id=ticket_data['clinic'].id,
            pavilion_end_time=ticket_data['pavilion_end_time'],
            system_calculated_fpa=fpa,
            current_fpa=fpa,
            overnight_stays=overnight_stays,
            created_by=user.username
        )

        # 4. Guardar en base de datos
        db.session.add(ticket)

        # 5. Log de auditoría
        AuditService.log_action(
            user=user,
            action=f"Creó ticket para paciente {ticket_data['patient'].full_name}",
            target_id=ticket_id,
            target_type='Ticket'
        )

        return ticket

    @staticmethod
    def generate_ticket_id(clinic):
        """Generate unique ticket ID: TH-PREFIX-YYYY-XXX"""
        current_year = datetime.now().year
        clinic_prefix = generate_prefix(clinic.name).upper()

        # Find last ticket number
        year_prefix = f"TH-{clinic_prefix}-{current_year}-"
        last_ticket = Ticket.query.filter(
            Ticket.id.like(f"{year_prefix}%"),
            Ticket.clinic_id == clinic.id
        ).order_by(Ticket.id.desc()).first()

        new_number = 1 if not last_ticket else int(last_ticket.id.split('-')[-1]) + 1

        return f"{year_prefix}{new_number:03d}"
```

**Características:**
- ✅ Contiene toda la lógica de negocio
- ✅ Métodos estáticos para operaciones sin estado
- ✅ Puede llamar a repositorios para datos
- ✅ Independiente de HTTP/frameworks
- ✅ Testeable sin necesidad de web server

**Otro ejemplo** (`services/fpa_calculator.py`):
```python
class FPACalculator:
    """Calculate FPA (Fecha Probable de Alta) based on surgery rules."""

    @staticmethod
    def calculate(pavilion_end_time, surgery):
        """
        Calculate when patient should be discharged.

        Args:
            pavilion_end_time: When surgery ended
            surgery: Surgery model with base_stay_hours

        Returns:
            tuple: (fpa_datetime, overnight_stays_count)
        """
        base_hours = surgery.base_stay_hours

        # Add base hours
        fpa = pavilion_end_time + timedelta(hours=base_hours)

        # Count overnight stays (business rule)
        overnight_stays = FPACalculator._count_overnight_stays(
            pavilion_end_time,
            fpa
        )

        return fpa, overnight_stays

    @staticmethod
    def _count_overnight_stays(start, end):
        """Count how many nights patient stayed."""
        # Complex business logic here...
        pass
```

---

### 5. Repositories (Acceso a Datos)

**Ubicación**: `/repositories/`

**Responsabilidad**: Abstraer acceso a la base de datos

**Archivos principales:**
- `ticket_repository.py`
- `user_repository.py`
- `patient_repository.py`
- `audit_repository.py`

**Ejemplo** (`repositories/ticket_repository.py`):
```python
class TicketRepository:
    """Data access layer for Tickets."""

    @staticmethod
    def get_by_id(ticket_id, clinic_id=None):
        """
        Get ticket by ID with optional clinic filtering.
        """
        query = Ticket.query.filter_by(id=ticket_id)
        if clinic_id:
            query = query.filter_by(clinic_id=clinic_id)
        return query.first()

    @staticmethod
    def get_with_relations(ticket_id, clinic_id=None):
        """
        Get ticket with all related entities (eager loading).
        """
        query = Ticket.query.options(
            joinedload(Ticket.patient),
            joinedload(Ticket.surgery).joinedload(Surgery.specialty),
            joinedload(Ticket.attending_doctor),
            joinedload(Ticket.discharge_time_slot)
        ).filter_by(id=ticket_id)

        if clinic_id:
            query = query.filter_by(clinic_id=clinic_id)

        return query.first()

    @staticmethod
    def build_filtered_query(filters, current_user):
        """
        Build complex filtered query with joins.
        """
        query = Ticket.query.options(
            joinedload(Ticket.patient),
            joinedload(Ticket.surgery)
        ).join(Patient).join(Surgery)

        # Multi-tenancy: Filter by clinic
        if not current_user.is_superuser:
            query = query.filter(Ticket.clinic_id == current_user.clinic_id)

        # Status filter
        if filters.get('status'):
            query = query.filter(Ticket.status == filters['status'])

        # Search by ticket ID, patient name or RUT
        if filters.get('search'):
            search = filters['search']
            query = query.filter(
                db.or_(
                    Ticket.id.ilike(f"%{search}%"),
                    Patient.full_name.ilike(f"%{search}%"),
                    Patient.rut.ilike(f"%{search}%")
                )
            )

        return query

    @staticmethod
    def save(ticket):
        """Persist ticket to database."""
        db.session.add(ticket)
        return ticket
```

**Beneficios:**
- ✅ Queries complejas centralizadas
- ✅ Reutilización de queries
- ✅ Fácil cambiar ORM en el futuro
- ✅ Testeable con mocks

---

### 6. Models (Entidades / Modelos)

**Ubicación**: `/models.py` (archivo único)

**Tecnología**: SQLAlchemy ORM

**Responsabilidad**: Definir estructura de datos

**Modelos principales:**
- `User` - Usuarios del sistema
- `Clinic` - Clínicas (multi-tenancy)
- `Patient` - Pacientes
- `Ticket` - Ticket de alta médica
- `Surgery` - Cirugías
- `Doctor` - Médicos
- `LoginAudit` - Auditoría de logins
- `ActionAudit` - Auditoría de acciones

**Ejemplo** (`models.py`):
```python
class Ticket(db.Model):
    """Ticket de alta médica."""

    # Primary Key
    id = db.Column(db.String(50), primary_key=True)  # TH-PROV-2025-001

    # Foreign Keys
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    surgery_id = db.Column(db.Integer, db.ForeignKey('surgery.id'), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)

    # Dates
    pavilion_end_time = db.Column(db.DateTime, nullable=False)
    medical_discharge_date = db.Column(db.DateTime, nullable=False)

    # FPA (Fecha Probable de Alta)
    system_calculated_fpa = db.Column(db.DateTime, nullable=False)
    initial_fpa = db.Column(db.DateTime, nullable=False)
    current_fpa = db.Column(db.DateTime, nullable=False)

    # Status
    status = db.Column(db.String(50), default='Vigente')
    overnight_stays = db.Column(db.Integer, default=0)

    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80))

    # Relationships
    patient = db.relationship('Patient', backref='tickets')
    surgery = db.relationship('Surgery', backref='tickets')
    attending_doctor = db.relationship('Doctor', backref='tickets')

    def can_be_modified(self):
        """Business rule: only active tickets can be modified."""
        return self.status == 'Vigente'

    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'patient_name': self.patient.full_name,
            'surgery_name': self.surgery.name,
            'current_fpa': self.current_fpa.isoformat(),
            'status': self.status
        }
```

**Características:**
- ✅ Define estructura de tablas
- ✅ Relaciones entre entidades (ForeignKey, relationships)
- ✅ Métodos helper simples (can_be_modified, to_dict)
- ❌ NO contiene lógica de negocio compleja

---

### 7. DTOs y Utilidades

**Ubicación**: `/dto/`, `/utils/`

**Responsabilidad**: Objetos de transferencia de datos y funciones auxiliares

**Ejemplos:**
- `dto/ticket_dto.py` - Data Transfer Objects
- `utils/string_utils.py` - Funciones de strings
- `utils/date_utils.py` - Funciones de fechas

---

## 🎯 Patrones de Diseño

### 1. Repository Pattern

**Problema**: Acceso directo a ORM en controladores es difícil de mantener y testear.

**Solución**: Capa intermedia (Repository) que abstrae el acceso a datos.

**Antes** (antipatrón):
```python
# En routes/tickets.py
@tickets_bp.route('/list')
def list_tickets():
    # Query compleja directamente en el controlador ❌
    tickets = Ticket.query.join(Patient).join(Surgery)\
        .filter(Ticket.clinic_id == current_user.clinic_id)\
        .filter(Ticket.status == 'Vigente')\
        .order_by(Ticket.created_at.desc())\
        .all()
    return render_template('tickets.html', tickets=tickets)
```

**Después** (con Repository):
```python
# En routes/tickets.py
@tickets_bp.route('/list')
def list_tickets():
    # Llamada simple al repository ✅
    tickets = TicketRepository.build_filtered_query(
        filters={'status': 'Vigente'},
        current_user=current_user
    ).all()
    return render_template('tickets.html', tickets=tickets)
```

---

### 2. Service Layer Pattern

**Problema**: Lógica de negocio esparcida en controladores.

**Solución**: Centralizar reglas de negocio en Services.

**Ejemplo**:
```python
# ❌ Antes: Lógica en el controlador
@tickets_bp.route('/create', methods=['POST'])
def create_ticket():
    # Calcular FPA manualmente
    base_hours = surgery.base_stay_hours
    fpa = pavilion_end + timedelta(hours=base_hours)

    # Generar ID manualmente
    last_ticket = Ticket.query.filter(...).first()
    new_number = int(last_ticket.id.split('-')[-1]) + 1
    ticket_id = f"TH-{prefix}-{year}-{new_number:03d}"

    # Crear ticket
    ticket = Ticket(id=ticket_id, ...)
    db.session.add(ticket)

    # Log
    log = ActionAudit(...)
    db.session.add(log)

    db.session.commit()

# ✅ Después: Lógica en el servicio
@tickets_bp.route('/create', methods=['POST'])
def create_ticket():
    ticket = TicketService.create_ticket(ticket_data, current_user)
    db.session.commit()
```

---

### 3. Dependency Injection (Manual)

No usamos frameworks de DI, pero seguimos el principio:

```python
# Service recibe dependencias como parámetros
class TicketService:
    @staticmethod
    def create_ticket(ticket_data, user):
        # Puede ser testeado pasando mocks
        audit_service = AuditService()
        fpa_calculator = FPACalculator()
        # ...
```

---

### 4. Principios SOLID

#### Single Responsibility Principle (SRP)
Cada clase tiene una única responsabilidad:
- `TicketRepository` → Solo acceso a datos de tickets
- `TicketService` → Solo lógica de negocio de tickets
- `TicketValidator` → Solo validación de tickets

#### Open/Closed Principle (OCP)
Puedes extender funcionalidad sin modificar código existente:
```python
# Agregar nuevo tipo de export sin modificar ExportService
class PDFExporter(BaseExporter):
    def export(self, data):
        # Implementación específica de PDF
        pass
```

#### Liskov Substitution Principle (LSP)
Subclases pueden reemplazar a su clase base sin romper funcionalidad.

#### Interface Segregation Principle (ISP)
No hay interfaces gigantes, cada repositorio/servicio tiene métodos específicos.

#### Dependency Inversion Principle (DIP)
Capas altas dependen de abstracciones, no de implementaciones concretas.

---

## 🏢 Multi-Tenancy

### ¿Qué es Multi-Tenancy?

**Multi-tenancy** significa que múltiples clínicas usan la misma aplicación, pero cada una ve solo sus propios datos.

### Implementación

Cada tabla principal tiene `clinic_id`:

```python
class Ticket(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    # ...

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    # ...
```

### Isolation (Aislamiento)

**Regla de oro**: Un usuario de la Clínica A no puede ver datos de la Clínica B.

Implementado en Repositories:

```python
class TicketRepository:
    @staticmethod
    def build_filtered_query(filters, current_user):
        query = Ticket.query.join(Patient).join(Surgery)

        # 🔒 Multi-tenancy filter
        if not current_user.is_superuser:
            query = query.filter(
                Ticket.clinic_id == current_user.clinic_id,
                Patient.clinic_id == current_user.clinic_id,
                Surgery.clinic_id == current_user.clinic_id
            )

        return query
```

### Superusuarios

**Superusuarios** tienen `clinic_id = NULL` y pueden ver datos de todas las clínicas:

```python
class User(db.Model):
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)

    @property
    def is_superuser(self):
        if self.clinic_id is not None:
            return False
        return Superuser.query.filter_by(email=self.email).first() is not None
```

---

## 🔐 Autenticación y Autorización

### Autenticación

Dos métodos:

1. **SSO con Google (IAP - Identity-Aware Proxy)**
   - Producción y QA: Solo SSO
   - Usuario autenticado automáticamente por Google

2. **Login tradicional** (usuario/contraseña)
   - Solo en DEV con `ENABLE_DEMO_LOGIN=true`
   - Para testing local

**Implementación** (`auth_iap.py`):
```python
def iap_authenticate():
    """Extract user from IAP header."""
    iap_email = request.headers.get('X-Goog-Authenticated-User-Email')

    if iap_email:
        # Remove prefix: "accounts.google.com:user@example.com"
        email = iap_email.split(':', 1)[1] if ':' in iap_email else iap_email

        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            login_user(user)
            return True

    return False
```

### Autorización (Roles)

**Roles definidos**:
- `superuser` - Acceso total, todas las clínicas
- `admin` - Administrador de una clínica
- `clinical` - Personal clínico (puede crear/modificar tickets)
- `visualizador` - Solo lectura

**Decorator para proteger endpoints**:
```python
def requires_role(allowed_roles):
    """Decorator to restrict access by role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if current_user.role not in allowed_roles and not current_user.is_superuser:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Uso
@tickets_bp.route('/create')
@requires_role(['admin', 'clinical'])
def create_ticket():
    # Solo admins y clinical pueden crear tickets
    pass
```

### Auditoría

Todos los logins y acciones se registran:

```python
class LoginAudit(db.Model):
    """Log de intentos de login."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(80))
    clinic_id = db.Column(db.Integer, nullable=True)  # NULL para superusers
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ActionAudit(db.Model):
    """Log de acciones en el sistema."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(80))
    clinic_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(500))
    target_id = db.Column(db.String(50))
    target_type = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 🔄 Flujo de Datos

### Ejemplo: Crear un Ticket

```
1. Usuario completa formulario en ticket_create.html
   ↓
2. POST a /tickets/create (routes/tickets.py)
   ↓
3. Controlador valida datos con TicketValidator
   ↓
4. Si válido, llama a TicketService.create_ticket()
   ↓
5. Service:
   - Calcula FPA con FPACalculator
   - Genera ID único
   - Crea objeto Ticket (Model)
   - Registra auditoría con AuditService
   ↓
6. Service retorna ticket al controlador
   ↓
7. Controlador hace db.session.commit()
   ↓
8. Controlador redirige a lista de tickets con flash message
   ↓
9. Usuario ve ticket creado en tickets.html
```

### Diagrama de Secuencia

```
Usuario → Navegador → Routes → Validators → Services → Repositories → Models → DB
                        ↓                        ↓
                      Templates ←── Services ←── Models
```

---

## 📊 Diagramas

### Diagrama de Capas (Detallado)

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENTE WEB                             │
│                      (Chrome, Firefox, etc.)                     │
└──────────────────────────────────────────────────────────────────┘
                               ↕ HTTPS
┌──────────────────────────────────────────────────────────────────┐
│                        LOAD BALANCER (GCP)                       │
│                     SSL Termination + IAP                        │
└──────────────────────────────────────────────────────────────────┘
                               ↕ HTTP
┌──────────────────────────────────────────────────────────────────┐
│                        CLOUD RUN (GCP)                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Flask Application                        │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Presentation Layer                                  │  │  │
│  │  │  - templates/ (Jinja2)                              │  │  │
│  │  │  - static/ (CSS, JS)                                │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Controller Layer                                    │  │  │
│  │  │  - routes/ (Flask Blueprints)                       │  │  │
│  │  │    • tickets.py                                     │  │  │
│  │  │    • auth.py                                        │  │  │
│  │  │    • admin.py                                       │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Validation Layer                                    │  │  │
│  │  │  - validators/                                       │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Business Logic Layer                                │  │  │
│  │  │  - services/                                         │  │  │
│  │  │    • ticket_service.py                              │  │  │
│  │  │    • fpa_calculator.py                              │  │  │
│  │  │    • audit_service.py                               │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Data Access Layer                                   │  │  │
│  │  │  - repositories/                                     │  │  │
│  │  │    • ticket_repository.py                           │  │  │
│  │  │    • user_repository.py                             │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Domain Layer                                        │  │  │
│  │  │  - models.py (SQLAlchemy ORM)                       │  │  │
│  │  │    • User, Ticket, Clinic, Patient, etc.           │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                               ↕ SQL
┌──────────────────────────────────────────────────────────────────┐
│                    CLOUD SQL (PostgreSQL)                        │
│                     Multi-tenant database                        │
└──────────────────────────────────────────────────────────────────┘
```

### Diagrama Entidad-Relación (Simplificado)

```
┌─────────────┐          ┌─────────────┐
│   Clinic    │◄─────────│    User     │
│             │ 1      * │             │
│ - id        │          │ - id        │
│ - name      │          │ - username  │
└─────────────┘          │ - email     │
      ▲                  │ - role      │
      │ 1                │ - clinic_id │
      │                  └─────────────┘
      │                        │
      │ *                      │ *
┌─────────────┐          ┌─────────────┐
│   Patient   │          │ LoginAudit  │
│             │          │ ActionAudit │
│ - id        │          └─────────────┘
│ - rut       │
│ - name      │
│ - clinic_id │
└─────────────┘
      ▲
      │ 1
      │
      │ *
┌─────────────┐
│   Ticket    │
│             │
│ - id        │
│ - patient_id│
│ - surgery_id│
│ - clinic_id │
│ - fpa       │
│ - status    │
└─────────────┘
      │
      │ *
      ▼ 1
┌─────────────┐
│   Surgery   │
│             │
│ - id        │
│ - name      │
│ - base_hours│
│ - clinic_id │
└─────────────┘
```

---

## 🛠️ Tecnologías

### Backend

- **Flask** (3.0.0) - Framework web
- **SQLAlchemy** (2.0.23) - ORM
- **Flask-Login** (0.6.3) - Gestión de sesiones
- **Flask-Migrate** (4.0.5) - Migraciones de DB
- **PostgreSQL** - Base de datos

### Frontend

- **Jinja2** - Templating engine
- **Bootstrap 5** - CSS framework
- **JavaScript** - Interactividad

### Testing

- **pytest** (7.4.3) - Framework de testing
- **pytest-cov** - Cobertura de tests

### Deployment

- **Docker** - Containerización
- **Google Cloud Run** - Serverless platform
- **Cloud SQL** - Managed PostgreSQL
- **IAP** - Identity-Aware Proxy
- **Secret Manager** - Secrets storage
- **Artifact Registry** - Docker images

---

## 📈 Métricas de Arquitectura

### Cobertura de Tests

```bash
pytest --cov=. --cov-report=term-missing
```

**Objetivo**: > 80% cobertura

### Capas y Archivos

- **Templates**: 15+ archivos HTML
- **Routes**: 6 blueprints
- **Services**: 5 servicios
- **Repositories**: 4 repositorios
- **Models**: 15+ modelos
- **Validators**: 2 validadores
- **Tests**: 25+ tests

### Métricas de Código

- **Separación de responsabilidades**: Alta ✅
- **Acoplamiento**: Bajo ✅
- **Cohesión**: Alta ✅
- **Testabilidad**: Alta ✅
- **Mantenibilidad**: Alta ✅

---

## 🚀 Cómo Navegar el Código

### 1. Entender el Dominio

Comienza leyendo `models.py` para entender las entidades del negocio:
```bash
# Ver modelos principales
grep "^class " models.py
```

### 2. Ver Endpoints Disponibles

Revisa los blueprints en `routes/`:
```bash
ls routes/
# Output: tickets.py, auth.py, admin.py, dashboard.py, exports.py
```

### 3. Seguir el Flujo

Para entender una funcionalidad (ej: crear ticket):
1. `routes/tickets.py` → Endpoint `/create`
2. `validators/ticket_validator.py` → Validación
3. `services/ticket_service.py` → Lógica de negocio
4. `repositories/ticket_repository.py` → Acceso a datos (si aplica)
5. `models.py` → Modelo Ticket

### 4. Ver Tests

Los tests documentan el comportamiento esperado:
```bash
cat tests/test_tickets.py
cat tests/test_auth.py
cat tests/test_audit_logs.py
```

---

## 🎓 Conceptos Clave - Glosario

### MVC vs Clean Architecture

| MVC Tradicional | Clean Architecture (Ticket Home) |
|----------------|----------------------------------|
| Model | Models + Repositories |
| View | Templates (Jinja2) |
| Controller | Routes + Services + Validators |

### FPA
**Fecha Probable de Alta**: Fecha calculada en que el paciente debería ser dado de alta, basado en:
- Hora de salida de pabellón
- Tipo de cirugía (horas base)
- Pernoctas

### Multi-Tenancy
Múltiples clínicas usando la misma aplicación con datos aislados.

### IAP (Identity-Aware Proxy)
Capa de autenticación de Google que verifica identidad antes de permitir acceso a la aplicación.

### ORM (Object-Relational Mapping)
Abstracción que permite trabajar con base de datos usando objetos Python (SQLAlchemy).

### Repository Pattern
Patrón que abstrae acceso a datos, facilitando testing y mantenibilidad.

### Service Layer
Capa que contiene toda la lógica de negocio, independiente de frameworks.

---

## 📚 Referencias y Lectura Adicional

### Arquitectura

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)

### Flask

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask Blueprints](https://flask.palletsprojects.com/en/3.0.x/blueprints/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

### Testing

- [pytest Documentation](https://docs.pytest.org/)
- [Testing Flask Applications](https://flask.palletsprojects.com/en/3.0.x/testing/)

### Google Cloud

- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [IAP Documentation](https://cloud.google.com/iap/docs)

---

## 🎯 Resumen Ejecutivo

### Lo Más Importante

1. **Clean Architecture**: Separación en capas con responsabilidades claras
2. **Multi-Tenancy**: Cada clínica ve solo sus datos (isolation por `clinic_id`)
3. **Repository Pattern**: Abstrae acceso a datos
4. **Service Layer**: Centraliza lógica de negocio
5. **SOLID Principles**: Código mantenible y escalable

### Flujo Típico

```
Usuario → Template → Route → Validator → Service → Repository → Model → DB
```

### Ventajas de Esta Arquitectura

✅ **Testeable**: Cada capa se testea independientemente
✅ **Mantenible**: Cambios en una capa no afectan otras
✅ **Escalable**: Fácil agregar nuevas funcionalidades
✅ **Segura**: Multi-tenancy garantiza isolation de datos
✅ **Profesional**: Sigue best practices de la industria

---

**Creado por**: Claude Code
**Fecha**: Noviembre 2025
**Versión**: 1.0
**Proyecto**: Ticket Home - RedSalud
