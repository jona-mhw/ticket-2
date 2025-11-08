# Ticket Home - Arquitectura Técnica y de Infraestructura

**Versión**: v1.9.0 Foundation
**Fecha**: Noviembre 2025
**Autor**: Documentación Técnica Completa

---

## 📚 Tabla de Contenidos

1. [Visión General de la Arquitectura](#visión-general-de-la-arquitectura)
2. [Stack Tecnológico Detallado](#stack-tecnológico-detallado)
3. [Arquitectura de Software](#arquitectura-de-software)
4. [Infraestructura Google Cloud Platform](#infraestructura-google-cloud-platform)
5. [Seguridad e Identidad](#seguridad-e-identidad)
6. [Flujo de Datos del Usuario](#flujo-de-datos-del-usuario)
7. [Modelo de Datos](#modelo-de-datos)
8. [Deployment y CI/CD](#deployment-y-cicd)
9. [Mejores Prácticas Implementadas](#mejores-prácticas-implementadas)
10. [Monitoreo y Observabilidad](#monitoreo-y-observabilidad)
11. [Rendimiento y Escalabilidad](#rendimiento-y-escalabilidad)
12. [Disaster Recovery y Backups](#disaster-recovery-y-backups)

---

## 1. Visión General de la Arquitectura

### 1.1 Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUARIO FINAL                            │
│           (Personal Médico RedSalud - 9 Clínicas)              │
└──────────────────┬──────────────────────────────────────────────┘
                   │ HTTPS (TLS 1.2+)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              GOOGLE CLOUD LOAD BALANCER                         │
│  - SSL Termination (Certificado Google-managed)                │
│  - Path-based routing (/static/* vs /*) │
│  - Health checks                                                │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│         IDENTITY-AWARE PROXY (IAP)                              │
│  - OAuth 2.0 Authentication                                     │
│  - JWT Token Validation                                         │
│  - User Email Extraction                                        │
│  - Authorization (IAM-based)                                    │
└──────────────────┬──────────────────────────────────────────────┘
                   │ X-Goog-IAP-JWT-Assertion + X-Goog-Authenticated-User-Email
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD RUN (Serverless)                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  CONTENEDOR DOCKER                                        │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ Gunicorn (1 worker, 8 threads)                      │ │ │
│  │  │  └─ Flask App (Python 3.11)                         │ │ │
│  │  │      ├─ auth_bp (IAP + Tradicional)                 │ │ │
│  │  │      ├─ tickets_bp (CRUD + FPA Calc)                │ │ │
│  │  │      ├─ admin_bp (Gestión)                          │ │ │
│  │  │      ├─ dashboard_bp (KPIs)                         │ │ │
│  │  │      ├─ visualizador_bp (Read-only)                 │ │ │
│  │  │      └─ exports_bp (PDF/Excel)                      │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│  Recursos:                                                      │
│  - CPU: 2 vCPUs                                                 │
│  - Memory: 1 GiB                                                │
│  - Min Instances: 1 (always warm)                              │
│  - Max Instances: 3 (autoscaling)                              │
│  - Concurrency: 80 requests/instance                           │
│  - Timeout: 900s (15 min)                                       │
└──────────────────┬──────────────────────────────────────────────┘
                   │ Private IP (VPC Connector)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   VPC CONNECTOR                                 │
│  - tckthome-conn-sa-west1 (DEV)                                │
│  - tckthome-conn-qa-sa-west1 (QA)                              │
│  - IP Range: 10.9.0.0/28 (DEV), 10.10.0.0/28 (QA)             │
│  - Egress: private-ranges-only                                 │
└──────────────────┬──────────────────────────────────────────────┘
                   │ Private Connection
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              CLOUD SQL (PostgreSQL 17)                          │
│  - Instance: dev-ticket-home / qa-ticket-home                  │
│  - Tier: db-custom-1-3840 (1 vCPU, 3.75 GB RAM)               │
│  - Private IP: 10.103.160.3 (DEV), 10.168.160.3 (QA)          │
│  - Backups: Automated daily                                    │
│  - High Availability: Single zone (cost optimization)          │
└─────────────────────────────────────────────────────────────────┘

ALMACENAMIENTO LATERAL:

┌─────────────────────────────────────────────────────────────────┐
│                   SECRET MANAGER                                │
│  - tickethome-db-url:latest → DATABASE_URL                     │
│  - tickethome-secret-key:latest → SECRET_KEY                   │
│  - Encryption: Google-managed keys                             │
│  - Access: Service Account only                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                ARTIFACT REGISTRY                                │
│  - DEV: us-central1-docker.pkg.dev/.../ticket-home:latest      │
│  - QA: southamerica-west1-docker.pkg.dev/.../ticket-home:latest│
│  - Images: ~300-400 MB comprimidas                             │
│  - Retention: Últimas 10 imágenes                              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Principios Arquitectónicos

1. **Serverless First**: Cloud Run elimina gestión de infraestructura
2. **Security by Design**: IAP + VPC privada + Secret Manager
3. **Multi-tenancy**: Segregación por `clinic_id` a nivel de datos
4. **Stateless**: Cada request es independiente (excepto sesiones Flask)
5. **Immutable Infrastructure**: Docker images versionadas
6. **Cost Optimization**: Autoscaling, min instances = 1, recursos ajustados

---

## 2. Stack Tecnológico Detallado

### 2.1 Backend

| Componente | Versión | Propósito | Por Qué Se Eligió |
|------------|---------|-----------|-------------------|
| **Python** | 3.11 | Lenguaje base | Moderno, rápido, soporte de tipo hints |
| **Flask** | 2.3.3 | Web framework | Ligero, flexible, amplio ecosistema |
| **Werkzeug** | 2.3.7 | WSGI toolkit | Incluido con Flask, seguro |
| **Gunicorn** | 22.0.0 | WSGI server | Producción-ready, multithreading |
| **SQLAlchemy** | (via Flask-SQLAlchemy 3.0.5) | ORM | Maduro, potente, pythonic |
| **Flask-Migrate** | 4.0.5 | Migraciones DB | Alembic wrapper, estándar de Flask |
| **Flask-Login** | 0.6.3 | Gestión sesiones | Integración nativa con Flask |
| **psycopg2-binary** | latest | PostgreSQL driver | Driver oficial, performance |
| **python-dateutil** | 2.8.2 | Manipulación fechas | Cálculos FPA complejos |
| **pytz** | latest | Timezones | Zona horaria Chile (America/Santiago) |
| **PyJWT** | 2.10.1 | JWT validation | Validar tokens IAP |
| **cryptography** | 41.0.7 | Crypto operations | Dependency de PyJWT |

**Total dependencias**: 19 (mantener mínimo reduce superficie de ataque)

### 2.2 Frontend

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Templates** | Jinja2 | Server-side rendering |
| **CSS** | Custom CSS + Tailwind-like | Estilos responsive |
| **JavaScript** | Vanilla JS (ES6+) | Interactividad sin dependencias |
| **Iconos** | Unicode + SVG | Logo RedSalud vectorial |

**Ventajas**:
- Sin frameworks pesados (React/Vue)
- Carga rápida (< 100KB total)
- SEO-friendly (server-side rendering)
- Funciona sin JavaScript (progressive enhancement)

### 2.3 Reportes y Exportación

| Librería | Versión | Uso |
|----------|---------|-----|
| **ReportLab** | 4.0.8 | Generación PDF profesionales |
| **openpyxl** | 3.1.2 | Lectura Excel |
| **xlsxwriter** | 3.1.9 | Escritura Excel optimizada |

### 2.4 Desarrollo Local

| Herramienta | Propósito |
|-------------|-----------|
| **Cloud SQL Proxy** | Conectar a DB de producción localmente |
| **python-dotenv** | Cargar variables `.env.local` |
| **Docker Desktop** | Build y test local de contenedores |

---

## 3. Arquitectura de Software

### 3.1 Patrón MVC con Blueprints

```
┌─────────────────────────────────────────────────────────────┐
│                      VIEW LAYER                             │
│  templates/                                                 │
│  ├── base.html (herencia)                                   │
│  ├── tickets/*.html (7 templates)                           │
│  ├── admin/*.html (9 templates)                             │
│  └── *.html (dashboard, login, etc.)                        │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ render_template()
                            │
┌─────────────────────────────────────────────────────────────┐
│                   CONTROLLER LAYER                          │
│  routes/ (6 Blueprints Flask)                              │
│  ├── auth.py         → /auth/*                             │
│  ├── tickets.py      → /tickets/*                          │
│  ├── admin.py        → /admin/*                            │
│  ├── dashboard.py    → /dashboard/*                        │
│  ├── visualizador.py → /visualizador/*                     │
│  ├── exports.py      → /export/*                           │
│  └── utils.py        → helpers compartidos                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ ORM queries
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     MODEL LAYER                             │
│  models.py (13 modelos SQLAlchemy)                         │
│  ├── Clinic, User, Patient, Ticket                         │
│  ├── Surgery, Specialty, Doctor                            │
│  ├── FpaModification, LoginAudit, ActionAudit              │
│  └── DischargeTimeSlot, StandardizedReason, Superuser      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ SQL queries
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
│  PostgreSQL 17 (Cloud SQL)                                  │
│  - ACID compliance                                          │
│  - Transacciones                                            │
│  - Foreign keys + constraints                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Factory Pattern (app.py)

```python
def create_app():
    """Application Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)  # Configuración centralizada

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    # ... 4 más

    # Register CLI commands
    register_commands(app)

    # Middleware
    @app.before_request
    def check_authentication():
        # IAP o login tradicional
        ...

    return app
```

**Ventajas**:
- Testeable (múltiples instancias de app)
- Configuración flexible (local vs production)
- Extensiones desacopladas

### 3.3 Modelos de Datos - Diseño Multi-tenant

```python
# Patrón base para multi-tenancy
class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Todos los modelos heredan clinic_id
class Ticket(BaseModel):
    # ...datos específicos de ticket

    # Query automático por clínica
    @classmethod
    def for_clinic(cls, clinic_id):
        return cls.query.filter_by(clinic_id=clinic_id)
```

**Segregación de datos**:
- A nivel de aplicación (no DB separadas)
- Filtrado automático por `clinic_id` en queries
- Superusuarios (`clinic_id=NULL`) ven todo
- Mejor para <100 clínicas, costo-efectivo

### 3.4 Cálculo de FPA - Lógica de Negocio Central

```python
def calculate_fpa(surgery, pavilion_end_time, discharge_time_slot):
    """
    FPA = Hora fin pabellón + Horas base de cirugía

    Consideraciones:
    1. Cirugías ambulatorias con cutoff hour (ej: 14:00)
    2. Si termina antes del cutoff → FPA = 08:00 del día siguiente
    3. Si termina después → FPA = normal
    4. Bloque horario de alta (12 opciones de 2h)
    """

    # Paso 1: Cálculo base
    fpa = pavilion_end_time + timedelta(hours=surgery.base_stay_hours)

    # Paso 2: Ajuste ambulatorio
    if surgery.is_ambulatory:
        if pavilion_end_time.hour < surgery.ambulatory_cutoff_hour:
            fpa = fpa.replace(hour=8, minute=0)  # 08:00 AM

    # Paso 3: Ajuste a bloque horario
    fpa = ajustar_a_bloque(fpa, discharge_time_slot)

    return fpa
```

**Por qué es importante**:
- Core business logic de la aplicación
- Ahorra horas de coordinación manual
- Reduce errores humanos en cálculo de altas

---

## 4. Infraestructura Google Cloud Platform

### 4.1 Servicios GCP Utilizados

| Servicio | Propósito | Costo Mensual Estimado | Ventajas |
|----------|-----------|------------------------|----------|
| **Cloud Run** | Hosting aplicación | $10-30 | Serverless, autoscaling, pago por uso |
| **Cloud SQL** | Base de datos PostgreSQL | $50-80 | Managed, backups automáticos, HA opcional |
| **VPC Connector** | Red privada Cloud Run ↔ Cloud SQL | $10-15 | Seguridad (no internet público) |
| **Secret Manager** | Almacenar credenciales | $1-2 | Cifrado, versionado, rotación |
| **Artifact Registry** | Registro de imágenes Docker | $5-10 | Privado, versionado, regional |
| **Load Balancer** | Balanceo HTTPS + SSL | $20-30 | Global, CDN, health checks |
| **Cloud Logging** | Logs centralizados | $5-10 | Búsqueda, alertas, retención |
| **IAP** | Autenticación SSO | Gratis | OAuth 2.0, no código extra |

**Total estimado**: $100-180/mes por ambiente

### 4.2 Regiones y Disponibilidad

| Ambiente | Región Primary | Región Artifact | Justificación |
|----------|----------------|-----------------|---------------|
| **DEV** | `southamerica-west1` (Santiago) | `us-central1` (Iowa) | Latencia baja para usuarios chilenos |
| **QA** | `southamerica-west1` (Santiago) | `southamerica-west1` | Todo en misma región (óptimo) |
| **PROD** | `southamerica-west1` (Santiago) | `southamerica-west1` | TBD |

**Por qué Santiago**:
- Usuarios finales están en Chile
- Latencia <50ms vs >200ms con US regions
- Compliance (datos de salud en territorio nacional)

### 4.3 Networking - Flujo de Red Completo

```
INTERNET
    │
    │ Port 443 (HTTPS)
    │
    ▼
[Cloud Load Balancer - Global]
    │
    │ Backend: Cloud Run NEG (Network Endpoint Group)
    │
    ▼
[Identity-Aware Proxy]
    │
    │ Inject headers: X-Goog-IAP-JWT-Assertion, X-Goog-Authenticated-User-Email
    │
    ▼
[Cloud Run Service]
    │ Region: southamerica-west1
    │ Internal traffic only (--ingress=internal-and-cloud-load-balancing)
    │
    │ VPC Connector: tckthome-conn-sa-west1
    │ IP Range: 10.9.0.0/28 (16 IPs)
    │ Egress: private-ranges-only (no internet directo)
    │
    ▼
[VPC Private Network]
    │
    │ Private IP Communication
    │
    ▼
[Cloud SQL Private IP]
    │ IP: 10.103.160.3 (DEV)
    │ Port: 5432 (PostgreSQL)
    │ Auth: IAM + Password
```

**Capas de seguridad**:
1. TLS 1.2+ hasta Load Balancer
2. IAP valida identidad (OAuth 2.0)
3. Cloud Run solo acepta tráfico de Load Balancer
4. VPC privada (sin IPs públicas)
5. Cloud SQL solo accesible desde VPC
6. Secret Manager para credenciales

### 4.4 Cloud SQL - Configuración Detallada

**Instancia DEV**:
```yaml
Name: dev-ticket-home
Version: PostgreSQL 17
Tier: db-custom-1-3840 (1 vCPU, 3.75 GB RAM)
Storage: 10 GB SSD (auto-resize habilitado)
Backups:
  - Automated: Daily at 03:00 AM Chile Time
  - Retention: 7 days
  - Point-in-time recovery: Enabled (7 days)
High Availability: Disabled (single zone, cost optimization)
Encryption: Google-managed keys
Private IP: 10.103.160.3
Public IP: Disabled (security)
Connection: Via VPC Connector only
```

**Conexión desde Cloud Run**:
```python
# En startup.sh, Cloud Run ya está en VPC
DATABASE_URL = "postgresql://user:pass@10.103.160.3:5432/tickethome_db"

# NO se usa Unix socket porque no es Cloud SQL Proxy
# Se usa IP privada directa
```

**Conexión desde local** (desarrollo):
```bash
# Usar Cloud SQL Proxy
./cloud-sql-proxy dev-ticket-home-redsalud:southamerica-west1:dev-ticket-home --port 5432

# Luego conectar a localhost:5432
DATABASE_URL = "postgresql://user:pass@localhost:5432/tickethome_db"
```

### 4.5 Service Accounts e IAM

**Service Account de Cloud Run**:
```
dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com
```

**Roles asignados**:
- `roles/cloudsql.client` → Conectar a Cloud SQL
- `roles/secretmanager.secretAccessor` → Leer secrets
- `roles/artifactregistry.reader` → Pull imágenes Docker

**Principio de mínimos privilegios**: Solo permisos esenciales

**IAM Policy en Cloud Run**:
```bash
# Permite acceso desde Load Balancer (con IAP)
member: allUsers
role: roles/run.invoker

# IAP protege a nivel superior, pero Cloud Run permite "allUsers"
# porque el tráfico ya pasó por IAP
```

### 4.6 Secret Manager - Gestión de Credenciales

```
Secret: tickethome-db-url
├── Version: latest (always points to newest)
├── Version: 1 (original)
├── Version: 2 (rotated)
└── Access: dev-ticket-home@...iam.gserviceaccount.com

Secret: tickethome-secret-key
├── Version: latest
└── Version: 1

Encryption: Google-managed keys (automatic)
Replication: Automatic
Access Audit: Cloud Logging
```

**Uso en Cloud Run**:
```bash
gcloud run deploy ... \
  --set-secrets="DATABASE_URL=tickethome-db-url:latest,SECRET_KEY=tickethome-secret-key:latest"
```

**Ventajas**:
- NO hay credenciales en código ni variables de entorno visibles
- Rotación sin redeploy (cambiar version)
- Auditoría de accesos

---

## 5. Seguridad e Identidad

### 5.1 Identity-Aware Proxy (IAP) - Detallado

**¿Qué es IAP?**
- Proxy de Google que valida identidad ANTES de llegar a la app
- OAuth 2.0 + JWT
- SSO corporativo (Google Workspace o Cloud Identity)

**Flujo de autenticación**:

```
1. Usuario accede a https://ticket-home.mhwdev.dev/
   │
2. Load Balancer redirige a IAP
   │
3. IAP verifica si hay sesión OAuth
   │
   ├─ NO hay sesión → Redirige a Google OAuth
   │  │
   │  ├─ Usuario inicia sesión con Google
   │  │
   │  └─ IAP valida email contra lista autorizada
   │     │
   │     ├─ Email autorizado → Crear JWT + Cookie
   │     └─ Email NO autorizado → Error 403
   │
   └─ SÍ hay sesión → Validar JWT
      │
      ├─ JWT válido → Inyectar headers
      │  │ X-Goog-IAP-JWT-Assertion: eyJhbG...
      │  └─ X-Goog-Authenticated-User-Email: accounts.google.com:user@domain.com
      │
      └─ JWT expirado/inválido → Redirigir a OAuth

4. Request llega a Cloud Run con headers IAP
   │
5. Flask valida JWT (PyJWT) y extrae email
   │
6. Flask busca/crea usuario en DB
   │
   ├─ Usuario existe → Login automático (Flask-Login)
   │
   └─ Usuario NO existe pero es superusuario → Crear y login

7. Response al usuario
```

**Código de validación IAP** (auth_iap.py):

```python
class IAPAuthenticator:
    def validate_iap_jwt(self, iap_jwt):
        """Valida JWT de IAP con PyJWT"""
        try:
            # Obtener public keys de Google
            keys = requests.get(
                'https://www.gstatic.com/iap/verify/public_key'
            ).json()

            # Decodificar y validar JWT
            claims = jwt.decode(
                iap_jwt,
                keys,
                algorithms=['ES256'],
                audience='/projects/PROJECT_NUMBER/apps/BACKEND_SERVICE_ID'
            )

            return claims['email']
        except:
            return None

    def get_authenticated_email(self):
        """Extrae email desde headers IAP"""
        iap_jwt = request.headers.get('X-Goog-IAP-JWT-Assertion')
        email_header = request.headers.get('X-Goog-Authenticated-User-Email')

        if iap_jwt:
            email = self.validate_iap_jwt(iap_jwt)
            if email:
                return email

        # Fallback a header (solo en development)
        if email_header:
            return email_header.split(':')[1]  # "accounts.google.com:user@x.com"

        return None
```

**Configuración IAP en GCP Console**:
```
1. Ir a Security > Identity-Aware Proxy
2. Habilitar IAP en Load Balancer backend
3. Configurar OAuth Consent Screen:
   - Tipo: Interno (solo usuarios de la org)
   - Scopes: email, profile, openid
4. Agregar usuarios autorizados:
   - Por email individual
   - Por grupo de Google Workspace
   - Por dominio (@redsalud.cl)
```

### 5.2 Autenticación Híbrida (IAP + Tradicional)

**¿Por qué híbrida?**
- IAP es ideal para producción (SSO corporativo)
- Login tradicional es backup en caso de problemas IAP
- Development local sin IAP complejo

**Variables de entorno**:
```python
ENABLE_IAP = true          # Valida JWT de IAP
ENABLE_DEMO_LOGIN = true   # Permite login tradicional como fallback
```

**Flujo híbrido** (app.py):

```python
@app.before_request
def check_authentication():
    # Rutas públicas (login, logout, static)
    if is_public_route():
        return None

    # Intento 1: Autenticación IAP
    if os.getenv('ENABLE_IAP') == 'true':
        email = hybrid_auth.get_iap_email()
        if email:
            user = login_or_create_user(email)
            if user:
                login_user(user)
                return None

    # Intento 2: Sesión Flask-Login existente
    if current_user.is_authenticated:
        return None

    # Intento 3: Login tradicional habilitado?
    if os.getenv('ENABLE_DEMO_LOGIN') == 'true':
        return redirect(url_for('auth.demo_login'))

    # Sin autenticación → 403
    return render_template('unauthorized.html'), 403
```

**Creación automática de usuarios** (para superusuarios):

```python
def login_or_create_user(email):
    user = User.query.filter_by(email=email).first()

    if user:
        return user if user.is_active else None

    # Usuario no existe, es superusuario?
    if Superuser.query.filter_by(email=email).first():
        # Crear usuario global (sin clinic_id)
        user = User(
            username=email.split('@')[0],
            email=email,
            role='admin',
            clinic_id=None,  # Superusuario global
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return user

    return None
```

### 5.3 Autorización - Roles y Permisos

**3 Roles principales**:

| Rol | Permisos | Acceso | Típico Usuario |
|-----|----------|--------|----------------|
| **admin** | CRUD completo, gestión usuarios, datos maestros, dashboard | Una clínica o global (superusuario) | Jefe de enfermería, administrador clínica |
| **clinical** | CRUD tickets, modificar FPA (max 5), anular tickets propios | Una clínica | Enfermero/a de piso |
| **visualizador** | Solo lectura tickets | Una clínica | Médico tratante, auditor |

**Decoradores de autorización**:

```python
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin']:
            flash('Acceso denegado. Solo administradores.', 'error')
            return redirect(url_for('tickets.nursing_board'))
        return f(*args, **kwargs)
    return decorated_function

def superuser_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.clinic_id is not None:  # Superuser has clinic_id=NULL
            flash('Acceso denegado. Solo superusuarios.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
```

**Uso**:
```python
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    # Solo admins pueden acceder
    ...

@admin_bp.route('/clinics')
@login_required
@superuser_required
def list_clinics():
    # Solo superusers ven todas las clínicas
    ...
```

### 5.4 Seguridad de Datos - Cifrado y Privacidad

**En tránsito**:
- HTTPS/TLS 1.2+ (Load Balancer → Usuarios)
- HTTPS (Cloud Run → Cloud SQL via VPC privada)
- Secrets en tránsito cifrados (Secret Manager)

**En reposo**:
- Cloud SQL: Cifrado automático con Google-managed keys
- Secret Manager: Cifrado automático
- Artifact Registry: Cifrado automático

**Datos sensibles en la aplicación**:
- **RUT de pacientes**: Almacenado en texto plano (necesario para búsqueda)
  - Riesgo mitigado: Solo personal autorizado con IAP accede
- **Nombres de pacientes**: Texto plano (mismo argumento)
- **Passwords de usuarios**: Hashed con Werkzeug (bcrypt-like)
  - Nunca se almacenan en texto plano

**GDPR/Compliance**:
- Datos de salud en Chile (cumplo con ley 20.584)
- Auditoría completa de accesos (LoginAudit, ActionAudit)
- Retención de logs: 30 días

### 5.5 Prevención de Vulnerabilidades OWASP Top 10

| Vulnerabilidad | Mitigación Implementada |
|----------------|-------------------------|
| **A01 - Broken Access Control** | Decoradores `@admin_required`, filtrado por `clinic_id` |
| **A02 - Cryptographic Failures** | TLS, secrets cifrados, passwords hasheadas |
| **A03 - Injection** | SQLAlchemy ORM (queries parametrizadas), validación inputs |
| **A04 - Insecure Design** | IAP como barrera, VPC privada, principio mínimos privilegios |
| **A05 - Security Misconfiguration** | Secrets en Secret Manager, `DEBUG=False` en prod |
| **A06 - Vulnerable Components** | Dependencias actualizadas (requirements.txt con versiones fijas) |
| **A07 - Auth Failures** | IAP + JWT, sesiones Flask seguras, logout completo |
| **A08 - Data Integrity Failures** | Constraints DB, validaciones backend |
| **A09 - Logging Failures** | Cloud Logging, LoginAudit, ActionAudit |
| **A10 - SSRF** | VPC privada egress-only, no acceso internet desde Cloud Run |

---

## 6. Flujo de Datos del Usuario

### 6.1 Flujo Completo - Usuario Crea un Ticket

```
PASO 1: AUTENTICACIÓN
User Browser
    │ GET https://ticket-home.mhwdev.dev/tickets/create
    ▼
Load Balancer (HTTPS)
    │ TLS Termination
    ▼
IAP (Identity-Aware Proxy)
    │ ¿Sesión OAuth válida?
    ├─ NO → Redirige a Google OAuth
    └─ SÍ → Valida JWT + Inyecta headers
    │
    ▼
Cloud Run (ticket-home service)
    │ Flask recibe request con headers:
    │ - X-Goog-IAP-JWT-Assertion: eyJhbG...
    │ - X-Goog-Authenticated-User-Email: accounts.google.com:user@redsalud.cl
    │
    │ @app.before_request check_authentication()
    │   └─ Valida JWT → Extrae email
    │   └─ Busca User en DB por email
    │   └─ login_user() con Flask-Login
    │
    ▼
Route: tickets.create (GET)
    │ @login_required
    │ @check_user_clinic (valida clinic_id)
    │
    │ Renderiza template con:
    │ - Lista de especialidades (filtradas por clinic_id)
    │ - Lista de cirugías (filtradas por clinic_id)
    │ - Lista de médicos (filtrados por clinic_id)
    │ - 12 bloques horarios
    │
    ▼
Response (HTML + CSS + JS)
    │
    ▼
User Browser
    │ Muestra formulario de creación de ticket
    │ JavaScript habilita:
    │ - Filtrado de cirugías por especialidad
    │ - Cálculo FPA en tiempo real (AJAX)


PASO 2: USUARIO LLENA FORMULARIO

User Browser
    │ Usuario completa datos:
    │ - RUT paciente: 12345678-9
    │ - Nombres: Juan Pérez
    │ - Especialidad: Cirugía General
    │ - Cirugía: Apendicectomía (base_stay_hours=24)
    │ - Hora fin pabellón: 2025-11-01 14:30
    │ - Médico tratante: Dr. García
    │ - Bloque horario: 08:00 - 10:00
    │ - Sala: 301
    │ - Cama: 3
    │
    │ POST /tickets/create
    ▼
Cloud Run
    │ Flask recibe form data
    │
    │ Validaciones backend:
    │ - RUT válido (formato chileno)
    │ - Datos requeridos presentes
    │ - Usuario pertenece a clinic_id
    │ - Cirugía pertenece a clinic_id
    │
    │ Crear/Buscar Patient:
    │   patient = Patient.query.filter_by(rut=rut).first()
    │   if not patient:
    │       patient = Patient(rut=rut, ...)
    │       db.session.add(patient)
    │
    │ Generar ID de Ticket:
    │   prefix = generate_prefix(clinic.name)  # "PROV" para Providencia
    │   year = datetime.now().year  # 2025
    │   last_ticket = Ticket.query.filter_by(clinic_id=..., prefix=prefix).order_by(Ticket.sequential_number.desc()).first()
    │   sequential = (last_ticket.sequential_number + 1) if last_ticket else 1
    │   ticket_id = f"TH-{prefix}-{year}-{sequential:03d}"  # TH-PROV-2025-042
    │
    │ Calcular FPA:
    │   fpa = pavilion_end_time + timedelta(hours=surgery.base_stay_hours)
    │   # 2025-11-01 14:30 + 24h = 2025-11-02 14:30
    │
    │   if surgery.is_ambulatory:
    │       if pavilion_end_time.hour < surgery.ambulatory_cutoff_hour:
    │           fpa = fpa.replace(hour=8, minute=0)  # Ajustar a 08:00 AM
    │
    │   # Ajustar a bloque horario seleccionado (08:00-10:00)
    │   fpa = fpa.replace(hour=8, minute=0)
    │
    │ Crear Ticket:
    │   ticket = Ticket(
    │       ticket_id=ticket_id,
    │       clinic_id=current_user.clinic_id,
    │       patient_id=patient.id,
    │       surgery_id=surgery.id,
    │       doctor_id=doctor.id,
    │       pavilion_end_time=pavilion_end_time,
    │       fpa_date=fpa,
    │       original_fpa=fpa,
    │       discharge_time_slot_id=time_slot.id,
    │       room=301,
    │       bed=3,
    │       status='Vigente',
    │       created_by_id=current_user.id
    │   )
    │   db.session.add(ticket)
    │
    │ Registrar acción en auditoría:
    │   log_action(
    │       user=current_user,
    │       action_type='create_ticket',
    │       entity='Ticket',
    │       entity_id=ticket.id,
    │       description=f'Creó ticket {ticket_id}'
    │   )
    │
    │ Commit transacción:
    │   db.session.commit()
    │
    ▼
VPC Connector
    │ Private IP traffic
    ▼
Cloud SQL (PostgreSQL)
    │ BEGIN TRANSACTION
    │ INSERT INTO patient (rut, first_name, ...) VALUES (...) ON CONFLICT DO UPDATE
    │ INSERT INTO ticket (ticket_id, clinic_id, patient_id, ...) VALUES (...)
    │ INSERT INTO action_audit (user_id, action_type, ...) VALUES (...)
    │ COMMIT TRANSACTION
    │
    │ Response: Row IDs
    ▼
Cloud Run
    │ Flash message: "Ticket TH-PROV-2025-042 creado exitosamente"
    │ Redirect: /tickets/TH-PROV-2025-042 (detalle)
    ▼
User Browser
    │ Muestra página de detalle del ticket:
    │ - Información del paciente
    │ - FPA calculada: 2025-11-02 08:00
    │ - Tiempo restante hasta FPA: 17 horas 30 minutos (countdown en JS)
    │ - Botones: Modificar FPA, Anular Ticket, Generar PDF
```

**Datos que viajan**:
1. Request HTTP (form data)
2. Query SQL (parametrizada, segura)
3. Response HTML (server-side rendering)
4. JavaScript hace polling cada 60s para actualizar countdown

### 6.2 Flujo de Modificación de FPA

```
User Browser
    │ POST /tickets/TH-PROV-2025-042/update_fpa
    │ Body:
    │   - new_fpa_date: 2025-11-03 10:00
    │   - reason_id: 2 (Complicación postoperatoria)
    │   - justification: "Fiebre persistente, requiere 24h adicionales de observación"
    ▼
Cloud Run
    │ Validaciones:
    │ - Usuario autenticado y autorizado
    │ - Ticket existe y es de su clínica (o es superusuario)
    │ - Máximo 5 modificaciones no alcanzado
    │ - Nueva FPA > FPA actual (no puede retroceder tiempo)
    │ - Razón válida y pertenece a clínica
    │
    │ Calcular noches de pernocte:
    │   overnight_stays = ceil((new_fpa - original_fpa).total_seconds() / 86400)
    │   # Si original_fpa = 2025-11-02 08:00 y new_fpa = 2025-11-03 10:00
    │   # Diferencia = 26 horas → 2 noches
    │
    │ Crear registro de modificación:
    │   modification = FpaModification(
    │       ticket_id=ticket.id,
    │       previous_fpa=ticket.fpa_date,
    │       new_fpa=new_fpa_date,
    │       reason_id=reason_id,
    │       justification=justification,
    │       overnight_stays=overnight_stays,
    │       modified_by_id=current_user.id,
    │       modified_at=datetime.now()
    │   )
    │   db.session.add(modification)
    │
    │ Actualizar ticket:
    │   ticket.fpa_date = new_fpa_date
    │   ticket.modification_count += 1
    │   ticket.last_modification_reason = justification
    │
    │ Auditoría:
    │   log_action(
    │       user=current_user,
    │       action_type='modify_fpa',
    │       entity='Ticket',
    │       entity_id=ticket.id,
    │       description=f'Modificó FPA de {previous_fpa} a {new_fpa_date}'
    │   )
    │
    │ Commit:
    │   db.session.commit()
    │
    ▼
Cloud SQL
    │ BEGIN
    │ INSERT INTO fpa_modification (...) VALUES (...)
    │ UPDATE ticket SET fpa_date=..., modification_count=..., last_modification_reason=...
    │ INSERT INTO action_audit (...) VALUES (...)
    │ COMMIT
    ▼
Cloud Run
    │ Flash: "FPA modificada exitosamente"
    │ Redirect: /tickets/TH-PROV-2025-042
    ▼
User Browser
    │ Ticket detail page con:
    │ - Nueva FPA: 2025-11-03 10:00
    │ - Historial de modificaciones (tabla con 1 fila)
    │ - Noches de pernocte: 2
    │ - Contador de modificaciones: 1/5
```

**Seguridad en este flujo**:
- Solo `admin` y `clinical` pueden modificar FPA
- No se puede modificar FPA de tickets anulados
- Auditoría completa con usuario, timestamp, justificación
- Límite de 5 modificaciones previene abuso

### 6.3 Flujo de Exportación PDF

```
User Browser
    │ GET /export/ticket/TH-PROV-2025-042/pdf
    ▼
Cloud Run
    │ Validar permisos (usuario puede ver este ticket)
    │
    │ Cargar datos completos:
    │   ticket = Ticket.query.get_or_404(ticket_id)
    │   patient = ticket.patient
    │   surgery = ticket.surgery
    │   doctor = ticket.doctor
    │   modifications = FpaModification.query.filter_by(ticket_id=ticket.id).order_by(FpaModification.modified_at).all()
    │
    │ Generar PDF con ReportLab:
    │   buffer = BytesIO()
    │   pdf = canvas.Canvas(buffer, pagesize=letter)
    │
    │   # Header con logo RedSalud
    │   pdf.drawImage('static/images/logo-redsalud.svg', x=50, y=750, width=100, height=30)
    │
    │   # Título
    │   pdf.setFont("Helvetica-Bold", 16)
    │   pdf.drawString(50, 700, f"Reporte de Alta - Ticket {ticket.ticket_id}")
    │
    │   # Información del paciente
    │   pdf.setFont("Helvetica", 10)
    │   pdf.drawString(50, 650, f"Paciente: {patient.first_name} {patient.last_name}")
    │   pdf.drawString(50, 635, f"RUT: {patient.rut}")
    │   pdf.drawString(50, 620, f"Edad: {patient.age} años")
    │
    │   # FPA y modificaciones
    │   pdf.drawString(50, 590, f"FPA Original: {ticket.original_fpa.strftime('%d/%m/%Y %H:%M')}")
    │   pdf.drawString(50, 575, f"FPA Actual: {ticket.fpa_date.strftime('%d/%m/%Y %H:%M')}")
    │
    │   # Tabla de modificaciones (si hay)
    │   if modifications:
    │       y = 540
    │       pdf.setFont("Helvetica-Bold", 9)
    │       pdf.drawString(50, y, "Historial de Modificaciones:")
    │       y -= 15
    │       pdf.setFont("Helvetica", 8)
    │       for mod in modifications:
    │           pdf.drawString(60, y, f"{mod.modified_at.strftime('%d/%m/%Y %H:%M')} - Nueva FPA: {mod.new_fpa.strftime('%d/%m/%Y %H:%M')}")
    │           pdf.drawString(60, y-10, f"Razón: {mod.reason.name} - {mod.justification}")
    │           y -= 30
    │
    │   # Firma (espacio para firma del médico)
    │   pdf.line(50, 150, 250, 150)
    │   pdf.drawString(50, 135, f"Dr. {doctor.first_name} {doctor.last_name}")
    │   pdf.drawString(50, 120, "Médico Tratante")
    │
    │   # Footer
    │   pdf.setFont("Helvetica", 8)
    │   pdf.drawString(50, 50, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    │   pdf.drawString(50, 40, f"Sistema Ticket Home v1.9.0 - {ticket.clinic.name}")
    │
    │   pdf.save()
    │   buffer.seek(0)
    │
    │ Response:
    │   return send_file(
    │       buffer,
    │       mimetype='application/pdf',
    │       as_attachment=True,
    │       download_name=f'Ticket_{ticket.ticket_id}.pdf'
    │   )
    ▼
User Browser
    │ Descarga archivo: Ticket_TH-PROV-2025-042.pdf (tamaño ~50-100 KB)
```

**Por qué PDF y no HTML**:
- Formato estándar para documentos médicos
- No modificable (integridad)
- Imprimible con formato consistente
- Compatible con sistemas externos

---

## 7. Modelo de Datos

### 7.1 Esquema Relacional Completo

```sql
-- Tabla central: Clínicas RedSalud
CREATE TABLE clinic (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,  -- "Clínica RedSalud Providencia"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Superusuarios globales (NO tienen clinic_id)
CREATE TABLE superuser (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usuarios del sistema (multi-tenant)
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER REFERENCES clinic(id),  -- NULL para superusuarios
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'admin', 'clinical', 'visualizador'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Especialidades médicas por clínica
CREATE TABLE specialty (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,  -- "Cirugía General"
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(clinic_id, name)  -- Mismo nombre en diferentes clínicas OK
);

-- Cirugías con horas base de estancia
CREATE TABLE surgery (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
    specialty_id INTEGER REFERENCES specialty(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,  -- "Apendicectomía"
    base_stay_hours DECIMAL(5,2) NOT NULL,  -- 24.00 horas
    is_ambulatory BOOLEAN DEFAULT FALSE,
    ambulatory_cutoff_hour INTEGER,  -- 14 (2:00 PM)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Médicos tratantes
CREATE TABLE doctor (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),
    rut VARCHAR(12) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bloques horarios de alta (12 bloques de 2 horas)
CREATE TABLE discharge_time_slot (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
    start_time TIME NOT NULL,  -- 08:00
    end_time TIME NOT NULL,    -- 10:00
    name VARCHAR(50),          -- "08:00 - 10:00"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Razones predefinidas para modificar/anular
CREATE TABLE standardized_reason (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
    category VARCHAR(20) NOT NULL,  -- 'modification' o 'annulment'
    name VARCHAR(200) NOT NULL,  -- "Complicación postoperatoria"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pacientes (puede tener múltiples tickets en el tiempo)
CREATE TABLE patient (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
    rut VARCHAR(12) NOT NULL,  -- RUT chileno: 12345678-9
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    age INTEGER,
    sex VARCHAR(10),  -- 'M', 'F', 'Otro'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(clinic_id, rut)  -- RUT único por clínica (puede duplicarse entre clínicas)
);

-- TICKET - Registro principal
CREATE TABLE ticket (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(30) NOT NULL UNIQUE,  -- TH-PROV-2025-042
    clinic_id INTEGER NOT NULL REFERENCES clinic(id) ON DELETE CASCADE,
    patient_id INTEGER NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
    surgery_id INTEGER REFERENCES surgery(id) ON DELETE SET NULL,
    doctor_id INTEGER REFERENCES doctor(id) ON DELETE SET NULL,
    discharge_time_slot_id INTEGER REFERENCES discharge_time_slot(id) ON DELETE SET NULL,

    -- Datos de pabellón
    pavilion_end_time TIMESTAMP NOT NULL,  -- Fin de cirugía

    -- Ubicación del paciente
    room VARCHAR(20),  -- Sala: "301"
    bed VARCHAR(20),   -- Cama: "3"

    -- FPA (Fecha Probable de Alta)
    original_fpa TIMESTAMP NOT NULL,  -- FPA calculada inicialmente
    fpa_date TIMESTAMP NOT NULL,      -- FPA actual (puede cambiar)
    overnight_stays INTEGER DEFAULT 0, -- Noches de pernocte

    -- Modificaciones
    modification_count INTEGER DEFAULT 0,  -- Máximo 5
    last_modification_reason TEXT,

    -- Estado
    status VARCHAR(20) DEFAULT 'Vigente',  -- 'Vigente' o 'Anulado'
    initial_reason TEXT,  -- Razón de creación (opcional)

    -- Auditoría
    created_by_id INTEGER REFERENCES user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    modified_by_id INTEGER REFERENCES user(id),
    modified_at TIMESTAMP,
    annulled_by_id INTEGER REFERENCES user(id),
    annulled_at TIMESTAMP,
    annulment_reason TEXT,

    -- Índices para búsqueda rápida
    INDEX idx_ticket_clinic (clinic_id),
    INDEX idx_ticket_patient (patient_id),
    INDEX idx_ticket_status (status),
    INDEX idx_ticket_fpa (fpa_date),
    INDEX idx_ticket_created (created_at DESC)
);

-- Historial de modificaciones de FPA
CREATE TABLE fpa_modification (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES ticket(id) ON DELETE CASCADE,
    previous_fpa TIMESTAMP NOT NULL,
    new_fpa TIMESTAMP NOT NULL,
    reason_id INTEGER REFERENCES standardized_reason(id) ON DELETE SET NULL,
    justification TEXT NOT NULL,
    overnight_stays INTEGER,
    modified_by_id INTEGER NOT NULL REFERENCES user(id),
    modified_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_modification_ticket (ticket_id),
    INDEX idx_modification_date (modified_at DESC)
);

-- Auditoría de logins
CREATE TABLE login_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id) ON DELETE SET NULL,
    clinic_id INTEGER REFERENCES clinic(id) ON DELETE SET NULL,
    email VARCHAR(255),
    login_method VARCHAR(20),  -- 'iap', 'traditional'
    success BOOLEAN NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),

    INDEX idx_login_timestamp (timestamp DESC),
    INDEX idx_login_user (user_id)
);

-- Auditoría de acciones críticas
CREATE TABLE action_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id) ON DELETE SET NULL,
    clinic_id INTEGER REFERENCES clinic(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'create_ticket', 'modify_fpa', 'annul_ticket', etc.
    entity_type VARCHAR(50),  -- 'Ticket', 'User', 'Surgery', etc.
    entity_id INTEGER,
    description TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),

    INDEX idx_action_timestamp (timestamp DESC),
    INDEX idx_action_user (user_id),
    INDEX idx_action_type (action_type)
);
```

### 7.2 Cardinalidades y Relaciones

```
Clinic (1) ──────< (N) User
             │
             ├───< (N) Specialty
             │          │
             │          └───< (N) Surgery
             │
             ├───< (N) Doctor
             ├───< (N) DischargeTimeSlot
             ├───< (N) StandardizedReason
             ├───< (N) Patient
             └───< (N) Ticket

Patient (1) ──────< (N) Ticket

Ticket (1) ──────< (N) FpaModification

User (1) ──────< (N) LoginAudit
         └──────< (N) ActionAudit
```

### 7.3 Constraints e Integridad Referencial

**Foreign Keys con acciones**:
- `ON DELETE CASCADE`: Si se borra clínica → borrar todos los datos relacionados
- `ON DELETE SET NULL`: Si se borra cirugía → mantener ticket pero sin referencia
- `ON DELETE RESTRICT`: (no usado) Evitar borrado si hay dependencias

**Unique Constraints**:
- `(clinic_id, rut)` en Patient: Mismo paciente puede estar en múltiples clínicas
- `(clinic_id, name)` en Specialty: Misma especialidad en diferentes clínicas
- `ticket_id` global: Identificador único de ticket

**Check Constraints** (a implementar):
```sql
ALTER TABLE ticket ADD CONSTRAINT check_modification_limit
    CHECK (modification_count <= 5);

ALTER TABLE ticket ADD CONSTRAINT check_fpa_future
    CHECK (fpa_date >= pavilion_end_time);

ALTER TABLE fpa_modification ADD CONSTRAINT check_fpa_increase
    CHECK (new_fpa > previous_fpa);
```

---

## 8. Deployment y CI/CD

### 8.1 Flujo de Deployment Manual (sin Cloud Run Jobs)

**Restricción**: Sin acceso a Cloud Run Jobs, todo es manual con Docker local

**Workflow completo**:

```
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: DESARROLLO LOCAL                                    │
└─────────────────────────────────────────────────────────────┘
1. Escribir código en local
2. Probar con Flask local + Cloud SQL Proxy:
   ./cloud-sql-proxy dev-ticket-home-redsalud:southamerica-west1:dev-ticket-home --port 5432
   flask run
3. Commit a Git:
   git add .
   git commit -m "feat: nueva funcionalidad"
   git push origin main

┌─────────────────────────────────────────────────────────────┐
│ PASO 2: BUILD DE IMAGEN DOCKER                              │
└─────────────────────────────────────────────────────────────┘
4. Ejecutar script de build (Windows):
   _deployment_scripts/1-build-and-push-v3.bat (DEV)
   _deployment_scripts/1-build-and-push-qa.bat (QA)

   Internamente ejecuta:
   docker build -t REGISTRY/PROJECT/REPO/IMAGE:latest .
   docker push REGISTRY/PROJECT/REPO/IMAGE:latest

┌─────────────────────────────────────────────────────────────┐
│ PASO 3: DEPLOYMENT A CLOUD RUN                              │
└─────────────────────────────────────────────────────────────┘
5. Decidir tipo de deploy:

   A) Deploy CON reset de DB (primera vez o cambios en models.py):
      - Copiar comando de: 2-deploy-con-reset-db-sa-west1.txt
      - PASO 1: Deploy con RESET_DB_ON_STARTUP=true
      - PASO 2: IAM policy binding (allUsers → run.invoker)
      - PASO 3: Deploy con RESET_DB_ON_STARTUP=false (persistencia)

   B) Deploy SIN reset (solo cambios de código):
      - Copiar comando de: 3-deploy-normal-sa-west1.txt
      - PASO 1: Deploy con RESET_DB_ON_STARTUP=false
      - PASO 2: IAM policy binding (allUsers → run.invoker)

┌─────────────────────────────────────────────────────────────┐
│ PASO 4: VERIFICACIÓN                                        │
└─────────────────────────────────────────────────────────────┘
6. Verificar deployment:
   - Acceder a URL: https://ticket-home.mhwdev.dev (DEV)
   - Verificar versión en footer
   - Revisar logs: gcloud logging read ...
   - Verificar DB (si hubo reset): gcloud sql connect ...

┌─────────────────────────────────────────────────────────────┐
│ PASO 5: DEPLOYMENT A QA (repetir 2-4 pero para QA)         │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Scripts de Deployment Detallados

**1-build-and-push-v3.bat** (DEV):
```batch
@echo off
set PROJECT_ID=dev-ticket-home-redsalud
set REGION=us-central1
set REPO_NAME=tickethome-repo
set IMAGE_NAME=ticket-home
set FULL_IMAGE=%REGION%-docker.pkg.dev/%PROJECT_ID%/%REPO_NAME%/%IMAGE_NAME%:latest

echo Building Docker image...
docker build -t %FULL_IMAGE% .

echo Pushing to Artifact Registry...
docker push %FULL_IMAGE%

echo Done!
pause
```

**2-deploy-con-reset-db-sa-west1.txt** (DEV con reset):
```bash
# PASO 1: Deploy con reset
gcloud run deploy ticket-home \
  --image=us-central1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:latest \
  --region=southamerica-west1 \
  --service-account=dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com \
  --vpc-connector=tckthome-conn-sa-west1 \
  --vpc-egress=private-ranges-only \
  --no-allow-unauthenticated \
  --ingress=internal-and-cloud-load-balancing \
  --add-cloudsql-instances=dev-ticket-home-redsalud:southamerica-west1:dev-ticket-home \
  --port=8080 \
  --timeout=900 \
  --memory=1Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=3 \
  --concurrency=80 \
  --set-env-vars="ENVIRONMENT=production,FLASK_ENV=production,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=true,SUPERUSER_EMAILS=global_admin@tickethome.com;jonathan.segura@redsalud.cl;admin@tickethome.com" \
  --set-secrets="DATABASE_URL=tickethome-db-url:latest,SECRET_KEY=tickethome-secret-key:latest"

# PASO 2: IAM Policy
gcloud run services add-iam-policy-binding ticket-home \
  --region=southamerica-west1 \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project=dev-ticket-home-redsalud

# PASO 3: Deploy sin reset (persistencia)
gcloud run deploy ticket-home \
  --image=us-central1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:latest \
  --region=southamerica-west1 \
  --service-account=dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com \
  --vpc-connector=tckthome-conn-sa-west1 \
  --vpc-egress=private-ranges-only \
  --no-allow-unauthenticated \
  --ingress=internal-and-cloud-load-balancing \
  --add-cloudsql-instances=dev-ticket-home-redsalud:southamerica-west1:dev-ticket-home \
  --port=8080 \
  --timeout=900 \
  --memory=1Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=3 \
  --concurrency=80 \
  --set-env-vars="ENVIRONMENT=production,FLASK_ENV=production,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false,SUPERUSER_EMAILS=global_admin@tickethome.com;jonathan.segura@redsalud.cl;admin@tickethome.com" \
  --set-secrets="DATABASE_URL=tickethome-db-url:latest,SECRET_KEY=tickethome-secret-key:latest"
```

**Dockerfile optimizado**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias primero (aprovechar cache de Docker)
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY app.py config.py models.py commands.py auth_iap.py .
COPY routes ./routes
COPY templates ./templates
COPY static ./static
COPY migrations ./migrations
COPY .env.production .env

# Preparar startup script
COPY startup.sh .
RUN apt-get update && \
    apt-get install -y dos2unix && \
    dos2unix startup.sh && \
    chmod +x startup.sh && \
    apt-get remove -y dos2unix && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8080

ENTRYPOINT ["/bin/bash", "/app/startup.sh"]
```

**startup.sh** (punto de entrada del contenedor):
```bash
#!/bin/bash
set -e

echo "=========================================="
echo "🚀 TICKET-HOME - INICIO"
echo "=========================================="

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no configurada"
    exit 1
fi

echo "✅ DATABASE_URL configurada"

# Resetear DB si está activado
if [ "$RESET_DB_ON_STARTUP" = "true" ]; then
    echo "🔥 RESET_DB_ON_STARTUP=true detectado"
    echo "🔥 BORRANDO Y RECREANDO BASE DE DATOS COMPLETA"

    # Detectar si debe usar seed mínimo para QA
    if [ "$USE_QA_MINIMAL_SEED" = "true" ]; then
        echo "🔹 USE_QA_MINIMAL_SEED=true detectado"
        echo "🔹 Usando seed mínimo (solo clínicas + superusuarios)"
        flask reset-db-qa-minimal
    else
        echo "🔹 Usando seed completo con datos demo"
        flask reset-db
    fi
fi

# Verificar datos
echo "🔍 Verificando base de datos..."
python3 << 'PYEOF'
from app import app, db
from models import User, Clinic

try:
    with app.app_context():
        user_count = User.query.count()
        clinic_count = Clinic.query.count()
        print(f"✅ Clínicas: {clinic_count}, Usuarios: {user_count}")
except Exception as e:
    print(f"⚠️  Error verificando DB: {e}")
PYEOF

# Iniciar Gunicorn
PORT=${PORT:-8080}
echo "🌐 Iniciando servidor en puerto: $PORT"

exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 8 \
    --timeout 0 \
    --graceful-timeout 300 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app
```

### 8.3 Estrategia de Reset de DB sin Cloud Run Jobs

**Problema**: Cloud Run Jobs no disponible, no se pueden ejecutar comandos Flask directamente en producción

**Solución ingeniosa**: Variable de entorno `RESET_DB_ON_STARTUP`

**Flujo**:

```
1. Desarrollador modifica models.py (agrega columna, nueva tabla, etc.)

2. Crear migración localmente:
   flask db migrate -m "add new column to ticket"
   flask db upgrade  # Aplicar localmente

3. Commit y push cambios (incluyendo archivo de migración)

4. Build imagen Docker con nueva migración

5. Deploy PASO 1 con RESET_DB_ON_STARTUP=true:
   - Cloud Run inicia contenedor
   - startup.sh detecta RESET_DB_ON_STARTUP=true
   - Ejecuta: flask reset-db
     - DROP SCHEMA public CASCADE
     - CREATE SCHEMA public
     - flask db upgrade (aplica TODAS las migraciones)
     - Seed de datos demo (9 clínicas, usuarios, etc.)
   - Gunicorn inicia con DB limpia

6. Deploy PASO 2 (inmediato) con RESET_DB_ON_STARTUP=false:
   - Cloud Run inicia nuevo contenedor
   - startup.sh NO resetea DB
   - DB persiste entre reinicios
   - Gunicorn inicia normalmente

7. Ahora cada reinicio de Cloud Run NO toca la DB
```

**Por qué 2 deploys**:
- Si dejas `RESET_DB_ON_STARTUP=true`, cada autoscale/reinicio borrará DB
- 2 deploys asegura que solo el primero resetea, luego persiste

**Alternativa (si tuvieras Cloud Run Jobs)**:
```bash
# Esto NO funciona actualmente
gcloud run jobs create db-reset \
  --image=... \
  --execute-now \
  --task-timeout=10m \
  --command="flask reset-db"
```

### 8.4 Versionado y Tags

**Estrategia actual**: `latest` tag solamente

**Mejora futura**: Versionado semántico

```bash
# Build con versión específica
docker build -t REGISTRY/PROJECT/REPO/ticket-home:v1.9.0 .
docker build -t REGISTRY/PROJECT/REPO/ticket-home:latest .

# Push ambas
docker push REGISTRY/PROJECT/REPO/ticket-home:v1.9.0
docker push REGISTRY/PROJECT/REPO/ticket-home:latest

# Deploy con versión específica (rollback fácil)
gcloud run deploy ticket-home \
  --image=REGISTRY/PROJECT/REPO/ticket-home:v1.9.0 \
  ...
```

**Ventajas versionado**:
- Rollback instantáneo a versión anterior
- Historial de deployments claro
- Pruebas A/B (traffic splitting)

---

## 9. Mejores Prácticas Implementadas

### 9.1 Desarrollo

- [x] **Virtual environments**: `.venv` para dependencias aisladas
- [x] **Requirements pinneados**: Versiones exactas en `requirements.txt`
- [x] **Gitignore completo**: `.env`, `__pycache__`, `.venv` excluidos
- [x] **Secrets en variables de entorno**: NO en código
- [x] **Factory pattern**: `create_app()` testeable
- [x] **Blueprints modulares**: 6 blueprints bien separados
- [x] **ORM en lugar de SQL raw**: SQLAlchemy previene injection
- [x] **Migraciones versionadas**: Alembic con historial completo
- [x] **Type hints** (parcial): Algunos archivos usan type annotations

### 9.2 Seguridad

- [x] **IAP para autenticación**: OAuth 2.0 + JWT
- [x] **HTTPS everywhere**: TLS 1.2+
- [x] **VPC privada**: Sin IPs públicas en Cloud Run/SQL
- [x] **Secret Manager**: Credenciales cifradas
- [x] **Passwords hasheadas**: Werkzeug security
- [x] **CSRF protection** (parcial): Flask forms tienen CSRF tokens
- [x] **SQL Injection prevention**: ORM parametrizado
- [x] **XSS prevention**: Jinja2 auto-escaping
- [x] **Auditoría completa**: LoginAudit + ActionAudit
- [x] **Roles y permisos**: Decoradores `@admin_required`, etc.
- [ ] **Rate limiting**: Falta implementar (Cloudflare o Flask-Limiter)
- [ ] **Content Security Policy**: Falta implementar

### 9.3 Performance

- [x] **Serverless autoscaling**: Cloud Run ajusta instancias
- [x] **Min instances = 1**: Siempre una instancia caliente (no cold starts)
- [x] **Connection pooling**: SQLAlchemy pool para PostgreSQL
- [x] **Eager loading**: `.options(joinedload())` en queries complejas
- [x] **Índices en DB**: Columnas de búsqueda frecuente (clinic_id, status, fpa_date)
- [ ] **Caching**: Falta implementar (Redis o Memcached para sesiones)
- [ ] **CDN**: Falta configurar (Cloud CDN para static files)
- [ ] **Lazy loading de imágenes**: Falta implementar

### 9.4 Observabilidad

- [x] **Cloud Logging**: Logs centralizados automáticos
- [x] **Gunicorn access logs**: Cada request loggeado
- [x] **Auditoría de negocio**: LoginAudit, ActionAudit en DB
- [ ] **Métricas personalizadas**: Falta implementar (Cloud Monitoring)
- [ ] **Alertas**: Falta configurar (uptime checks, error rate alerts)
- [ ] **Tracing distribuido**: Falta implementar (Cloud Trace)
- [ ] **Health checks personalizados**: Falta implementar (endpoint /health)

### 9.5 Costo

- [x] **Serverless pay-per-use**: Solo pagas por requests
- [x] **Autoscaling down to 1**: No pagas por instancias ociosas (solo 1 min)
- [x] **Single-zone DB**: No paga HA innecesariamente
- [x] **Storage SSD optimizado**: 10 GB auto-resize
- [ ] **Cloud CDN**: Falta implementar (reduciría egress costs)
- [ ] **Scheduled scaling**: Falta implementar (min=0 en horarios nocturnos)

---

## 10. Monitoreo y Observabilidad

### 10.1 Cloud Logging - Logs Disponibles

**Tipos de logs**:

1. **Request logs** (automáticos):
```json
{
  "httpRequest": {
    "requestMethod": "GET",
    "requestUrl": "https://ticket-home.mhwdev.dev/tickets/create",
    "status": 200,
    "latency": "0.234s",
    "userAgent": "Mozilla/5.0...",
    "remoteIp": "186.189.100.106"
  },
  "resource": {
    "type": "cloud_run_revision",
    "labels": {
      "service_name": "ticket-home",
      "revision_name": "ticket-home-00015-d5c"
    }
  },
  "timestamp": "2025-11-01T14:30:00.123Z"
}
```

2. **Application logs** (Gunicorn + Flask):
```
[2025-11-01 14:30:00] INFO in app: Usuario jonathan.segura@redsalud.cl autenticado vía IAP
[2025-11-01 14:30:05] INFO in tickets: Ticket TH-PROV-2025-042 creado exitosamente
```

3. **Startup logs** (startup.sh):
```
==========================================
🚀 TICKET-HOME - INICIO
==========================================
✅ DATABASE_URL configurada
ℹ️  RESET_DB_ON_STARTUP no está activo
🔍 Verificando base de datos...
✅ Clínicas: 9, Usuarios: 30
🌐 Iniciando servidor en puerto: 8080
```

**Consultas útiles**:

```bash
# Errors en últimas 24h
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --project=dev-ticket-home-redsalud \
  --limit=50 \
  --freshness=24h

# Requests lentos (>2s)
gcloud logging read "resource.type=cloud_run_revision AND httpRequest.latency>2s" \
  --project=dev-ticket-home-redsalud \
  --limit=20

# Logins de un usuario específico
gcloud logging read 'textPayload=~"jonathan.segura@redsalud.cl"' \
  --project=dev-ticket-home-redsalud \
  --limit=10
```

### 10.2 Auditoría de Aplicación (DB)

**LoginAudit**:
```sql
SELECT
    email,
    login_method,
    success,
    timestamp
FROM login_audit
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 100;
```

**ActionAudit** (acciones críticas):
```sql
SELECT
    u.email,
    a.action_type,
    a.entity_type,
    a.description,
    a.timestamp
FROM action_audit a
LEFT JOIN user u ON a.user_id = u.id
WHERE a.timestamp > NOW() - INTERVAL '30 days'
  AND a.action_type IN ('create_ticket', 'modify_fpa', 'annul_ticket')
ORDER BY a.timestamp DESC;
```

### 10.3 Métricas de Cloud Run (automáticas)

**Disponibles en Cloud Console**:
- Request count
- Request latencies (p50, p95, p99)
- Container instance count (autoscaling)
- CPU utilization
- Memory utilization
- Billable container time
- Startup latency

**Exportables a Grafana/DataStudio** para dashboards personalizados

---

## 11. Rendimiento y Escalabilidad

### 11.1 Configuración de Recursos

**Cloud Run**:
- **CPU**: 2 vCPUs por instancia
  - Justificación: Gunicorn 1 worker + 8 threads = maneja hasta 8 requests concurrentes
- **Memory**: 1 GiB por instancia
  - Uso típico: ~400-600 MB (SQLAlchemy + Flask + templates)
  - Margen: Evita OOM en picos
- **Concurrency**: 80 requests/instance
  - Configurado conservadoramente (gunicorn puede manejar más)
- **Min instances**: 1 (siempre warm, evita cold starts)
- **Max instances**: 3
  - Para 9 clínicas con ~50 usuarios cada una = 450 usuarios máx
  - Estimado: 80 req/inst * 3 inst = 240 requests concurrentes
  - Suficiente para uso típico (picos de ~50-100 requests/min)

**Cloud SQL**:
- **Tier**: db-custom-1-3840 (1 vCPU, 3.75 GB RAM)
  - Connection limit: ~100 conexiones concurrentes
  - SQLAlchemy pool: 5 connections/instance * 3 instancias = 15 conexiones máx
  - Mucho margen disponible

### 11.2 Puntos de Escalabilidad

**Escenario 1: Crecimiento a 20 clínicas**
- Cambios necesarios: Ninguno (multi-tenancy ya soporta N clínicas)
- Impacto: Aumento de datos, queries siguen siendo eficientes con índices

**Escenario 2: 1000+ usuarios concurrentes**
- Cloud Run: Aumentar `max-instances` a 10-20
- Cloud SQL: Upgrade a db-custom-2-7680 (2 vCPUs, 7.5 GB RAM)
- Agregar Redis para caché de sesiones

**Escenario 3: Expansión internacional (otros países)**
- Crear regiones adicionales (europe-west1, asia-southeast1)
- Multi-region Cloud SQL (lectura local, escritura global)
- Cloud CDN para static assets

### 11.3 Bottlenecks Actuales

1. **Queries N+1**: Algunos templates cargan relaciones en loop
   - Solución: Eager loading con `joinedload()`
2. **Sin caché**: Cada request regenera templates
   - Solución: Flask-Caching para templates estáticos
3. **PDF generation**: Bloquea thread mientras genera PDF
   - Solución: Background task con Cloud Tasks

---

## 12. Disaster Recovery y Backups

### 12.1 Backups de Cloud SQL

**Automáticos**:
- **Frecuencia**: Diario a las 03:00 AM Chile (America/Santiago)
- **Retención**: 7 días
- **Point-in-time recovery**: Últimos 7 días (cualquier momento)
- **Ubicación**: Misma región (southamerica-west1)

**On-demand**:
```bash
gcloud sql backups create \
  --instance=dev-ticket-home \
  --project=dev-ticket-home-redsalud \
  --description="Pre-deployment backup v1.9.0"
```

**Restauración**:
```bash
# Opción 1: Crear nueva instancia desde backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=dev-ticket-home \
  --backup-project=dev-ticket-home-redsalud \
  --instance=dev-ticket-home-restored

# Opción 2: Point-in-time recovery
gcloud sql instances clone dev-ticket-home dev-ticket-home-clone \
  --point-in-time="2025-11-01T14:30:00Z"
```

### 12.2 Backups de Aplicación

**Código fuente**: Git (GitHub)
- Remoto: https://github.com/jona-mhw/rs-ticket-home
- Commits: Historial completo

**Docker images**: Artifact Registry
- Retención: Últimas 10 imágenes (manual cleanup de viejas)
- Versionado: `latest` tag (mejorar con semantic versioning)

**Configuración**: Google Secret Manager
- Versionado automático de secrets
- Rollback a versión anterior sin redeploy

### 12.3 Plan de Disaster Recovery

**RTO** (Recovery Time Objective): 1 hora
**RPO** (Recovery Point Objective): 24 horas (backup diario)

**Escenario 1: Cloud Run caído**
1. Verificar Cloud Run status (GCP status page)
2. Rollback a revisión anterior:
   ```bash
   gcloud run services update-traffic ticket-home \
     --to-revisions=ticket-home-00014-4zc=100
   ```
3. Si persiste, redeploy desde imagen previa

**Escenario 2: Cloud SQL corrupto**
1. Crear instancia nueva desde backup más reciente
2. Actualizar `DATABASE_URL` secret
3. Redeploy Cloud Run con nuevo secret
4. Downtime: ~30 min

**Escenario 3: Región southamerica-west1 caída**
1. (No implementado) Failover a us-central1
2. Requiere: Multi-region SQL + Load Balancer multi-region
3. Inversión futura si se requiere 99.9% SLA

---

## Conclusión

Ticket Home es una aplicación **production-ready** con arquitectura moderna, seguridad robusta y diseño escalable. Utiliza las mejores prácticas de GCP, serverless, y seguridad por diseño.

**Fortalezas**:
- Autenticación SSO con IAP
- Multi-tenancy eficiente
- Deployment reproducible
- Auditoría completa
- Costos optimizados

**Próximas mejoras recomendadas**:
1. Implementar tests automatizados (pytest)
2. Agregar CI/CD con Cloud Build triggers
3. Configurar alertas y SLOs
4. Implementar caché con Redis
5. Versionado semántico de images

---

**Versión**: v1.9.0 Foundation
**Última Actualización**: Noviembre 2025
**Mantenedor**: jonathan.segura@redsalud.cl
