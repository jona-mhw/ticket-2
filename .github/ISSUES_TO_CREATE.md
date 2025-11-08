# 📝 Issues para Crear en GitHub

Copia y pega estos issues en GitHub:
https://github.com/jona-mhw/ticket-2/issues/new

---

## Issue #1: 🧪 Implementar pytest con fixtures y coverage >80%

### 📋 Descripción
Implementar suite de testing completa usando pytest para garantizar la calidad del código y prevenir regresiones.

### 🎯 Objetivos
- [x] Setup inicial de pytest con configuración profesional
- [x] Fixtures compartidos para DB, usuarios, clínicas
- [x] Tests unitarios de modelos (13 modelos)
- [x] Tests de la lógica de cálculo FPA (crítico)
- [x] Tests de autenticación (IAP + tradicional)
- [x] Tests de blueprints principales
- [x] Coverage report >80%
- [x] Documentación de cómo correr tests

### 📁 Archivos a Crear
```
tests/
├── conftest.py              # Fixtures compartidos
├── test_models.py           # Tests de User, Clinic, Patient, etc.
├── test_fpa_logic.py        # Tests del cálculo FPA (GOLD)
├── test_auth.py             # Tests de autenticación
├── test_routes_tickets.py   # Tests de CRUD tickets
├── test_routes_admin.py     # Tests de panel admin
├── test_routes_dashboard.py # Tests de métricas
└── pytest.ini               # Configuración pytest
```

### 🎯 Casos de Prueba Críticos
1. **FPA Calculation:**
   - Cirugía ambulatoria antes de las 12pm → alta mismo día
   - Cirugía ambulatoria después de las 12pm → alta día siguiente 8am
   - Cirugía con estadía nocturna → cálculo correcto de días
   - Casos edge: medianoche, cambio de año, horario de verano

2. **Multi-tenancy:**
   - Usuario solo ve datos de su clínica
   - Superuser ve todas las clínicas
   - Isolation entre clínicas

3. **Autenticación:**
   - Login tradicional (DEV)
   - IAP authentication (QA/PROD)
   - Auto-creación de superusers desde IAP headers

### 🛠️ Dependencias
```txt
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0
faker==20.1.0  # Para generar datos de prueba
freezegun==1.4.0  # Para mockear fechas
```

### ✅ Definition of Done
- [ ] Tests pasan en local
- [ ] Coverage >80% (verificar con `pytest --cov`)
- [ ] Documentación en README sobre cómo correr tests
- [ ] Fixtures reutilizables para futuras pruebas
- [ ] Sin warnings en pytest

### 🏷️ Labels
`testing`, `enhancement`, `priority: high`, `good first issue`

### 🔗 Referencias
- [Documentación pytest](https://docs.pytest.org/)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [Testing Flask Apps](https://flask.palletsprojects.com/en/latest/testing/)

---

## Issue #2: 🚀 Implementar CI/CD Pipeline con GitHub Actions

### 📋 Descripción
Automatizar testing, linting, build y deploy usando GitHub Actions para reducir errores humanos y acelerar entregas.

### 🎯 Objetivos
- [x] Workflow de CI (tests + linting en cada PR)
- [x] Workflow de deploy automático a QA
- [x] Workflow de deploy manual a PROD
- [x] Notifications en caso de fallo
- [x] Quality gates (no merge si tests fallan)
- [x] Cache de dependencies para velocidad

### 📁 Archivos a Crear
```
.github/workflows/
├── ci.yml              # Tests + linting en cada PR
├── deploy-qa.yml       # Auto-deploy a QA en merge a main
├── deploy-prod.yml     # Manual deploy a PROD
└── nightly-tests.yml   # Tests completos cada noche
```

### 🔧 Configuración CI Workflow

```yaml
# .github/workflows/ci.yml
name: 🧪 CI - Tests & Linting

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8 black

      - name: Run linting
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          black --check .

      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=term
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost/test_db

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Comment PR with coverage
        uses: py-cov-action/python-coverage-comment-action@v3
        with:
          GITHUB_TOKEN: ${{ github.token }}

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        run: |
          pip install safety bandit
          safety check
          bandit -r . -f json -o bandit-report.json
```

### 🎯 Quality Gates
- ✅ Todos los tests deben pasar
- ✅ Coverage mínimo: 80%
- ✅ No errores de flake8 críticos
- ✅ Black formatting correcto
- ✅ No vulnerabilidades críticas (safety)

### 🚀 Deploy Workflows
- **QA:** Auto-deploy en merge a `main`
- **PROD:** Manual trigger con aprobación requerida

### ✅ Definition of Done
- [ ] CI workflow funciona en PRs
- [ ] Tests se corren automáticamente
- [ ] No se puede hacer merge si tests fallan
- [ ] Deploy a QA automático
- [ ] Deploy a PROD manual con botón
- [ ] Notificaciones configuradas

### 🏷️ Labels
`ci/cd`, `automation`, `enhancement`, `priority: high`

---

## Issue #3: ⚡ Implementar Redis Cache Layer para Performance

### 📋 Descripción
Agregar capa de caché con Redis para mejorar performance del dashboard y reducir carga en PostgreSQL.

### 🎯 Objetivos
- [x] Setup Redis en GCP Memorystore
- [x] Cache de queries frecuentes (dashboard stats)
- [x] Session store en Redis (no en cookies)
- [x] Invalidación inteligente de cache
- [x] Métricas de hit rate
- [x] Fallback automático si Redis falla

### 📊 Métricas Esperadas
- Dashboard load time: 3s → <500ms (6x más rápido)
- DB queries en dashboard: 15 → 2
- Cache hit rate objetivo: >70%

### 🛠️ Stack Técnico
```txt
redis==5.0.1
flask-caching==2.1.0
```

### 🔧 Implementación

**1. Cache de Dashboard Stats:**
```python
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL')
})

@cache.memoize(timeout=300)  # 5 minutos
def get_dashboard_stats(clinic_id):
    # Queries pesadas aquí
    return stats
```

**2. Invalidación Inteligente:**
```python
# Al crear/modificar ticket:
@tickets_bp.route('/create', methods=['POST'])
def create_ticket():
    # ... crear ticket ...
    cache.delete(f'dashboard_stats_{clinic_id}')
    cache.delete(f'nursing_board_{clinic_id}')
    return redirect('/')
```

**3. Session Store:**
```python
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url(REDIS_URL)
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
```

### 🏗️ Infraestructura GCP
- Crear Redis instance en Memorystore
- VPC peering con Cloud Run
- Configurar in Terraform/Cloud Console

### ⚠️ Consideraciones
- Fallback a DB si Redis falla (no romper la app)
- TTL apropiados (no cache infinito)
- Monitoreo de hit rate
- Evitar cache stampede

### ✅ Definition of Done
- [ ] Redis configurado en GCP
- [ ] Cache implementado en dashboard
- [ ] Sessions en Redis
- [ ] Métricas de hit rate visibles
- [ ] Tests de invalidación
- [ ] Documentación de TTLs y estrategia

### 🏷️ Labels
`performance`, `enhancement`, `priority: medium`, `infrastructure`

---

## Issue #4: 🔍 Optimizar Queries y Resolver N+1 Problems

### 📋 Descripción
Identificar y resolver problemas de performance en queries de base de datos, especialmente N+1 queries que causan carga excesiva.

### 🎯 Objetivos
- [x] Auditoría completa de queries
- [x] Implementar eager loading donde corresponda
- [x] Agregar indexes en columnas clave
- [x] Query profiling en endpoints lentos
- [x] Documentar slow queries

### 🔍 N+1 Problems Identificados

**Problema 1: Nursing Board**
```python
# ❌ ANTES (N+1 query)
tickets = Ticket.query.filter_by(clinic_id=clinic_id).all()
for ticket in tickets:
    print(ticket.patient.nombre)  # Query por cada ticket!
    print(ticket.specialty.name)  # Otra query!
    print(ticket.doctor.nombre)   # Otra query!
# Total: 1 + (N * 3) queries

# ✅ DESPUÉS (eager loading)
tickets = Ticket.query\
    .filter_by(clinic_id=clinic_id)\
    .options(
        joinedload(Ticket.patient),
        joinedload(Ticket.specialty),
        joinedload(Ticket.doctor)
    ).all()
# Total: 1 query con JOINs
```

**Problema 2: Dashboard Stats**
```python
# ❌ ANTES
for clinic in clinics:
    count = Ticket.query.filter_by(clinic_id=clinic.id).count()
# N queries

# ✅ DESPUÉS
from sqlalchemy import func
stats = db.session.query(
    Ticket.clinic_id,
    func.count(Ticket.id)
).group_by(Ticket.clinic_id).all()
# 1 query
```

### 📊 Indexes a Crear

```sql
-- Tickets más buscados por clinic + status
CREATE INDEX idx_tickets_clinic_status
ON tickets(clinic_id, status);

-- Búsqueda por RUT de paciente
CREATE INDEX idx_patients_rut
ON patients(rut);

-- Auditoría por usuario
CREATE INDEX idx_action_audit_user_date
ON action_audit(user_id, timestamp DESC);

-- Tickets por fecha creación
CREATE INDEX idx_tickets_created_at
ON tickets(created_at DESC);
```

### 🛠️ Herramientas
- Flask-DebugToolbar (ver queries en desarrollo)
- SQLAlchemy query profiling
- PostgreSQL EXPLAIN ANALYZE
- New Relic / Datadog (producción)

### 📈 Métricas de Éxito
- Nursing board: <100ms (actualmente ~500ms)
- Dashboard: <200ms (actualmente ~3s con 15 queries)
- Reducir queries promedio por request: 15 → <5

### ✅ Definition of Done
- [ ] Audit de todos los endpoints principales
- [ ] N+1 problems resueltos
- [ ] Indexes creados y probados
- [ ] Query count reducido >50%
- [ ] Documentación de patterns de queries eficientes
- [ ] Before/after benchmarks

### 🏷️ Labels
`performance`, `database`, `tech-debt`, `priority: medium`

---

## 📝 Notas para Crear Issues

1. **Ve a:** https://github.com/jona-mhw/ticket-2/issues/new
2. **Copia** cada issue completo (título + descripción)
3. **Asigna labels** manualmente (o créalos si no existen)
4. **Asígnate** a ti mismo como assignee
5. **(Opcional)** Agrega a un Project/Milestone

### 🏷️ Labels a Crear en el Repo
- `testing` (verde)
- `ci/cd` (azul)
- `performance` (naranja)
- `database` (morado)
- `enhancement` (celeste)
- `tech-debt` (gris)
- `priority: high` (rojo)
- `priority: medium` (amarillo)
- `good first issue` (verde claro)

