#!/bin/bash
# 🚀 Script para crear los 4 issues usando GitHub REST API
# No requiere GitHub CLI, solo curl
# Uso: GITHUB_TOKEN=tu_token ./create-issues-api.sh

set -e

# Configuración
REPO_OWNER="jona-mhw"
REPO_NAME="ticket-2"
API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Error: GITHUB_TOKEN no está configurado${NC}"
    echo ""
    echo "📝 Configúralo así:"
    echo "   export GITHUB_TOKEN=tu_token_aqui"
    echo ""
    echo "🔑 Crear token en: https://github.com/settings/tokens/new"
    echo "   Permisos necesarios: 'repo' (Full control of private repositories)"
    echo ""
    exit 1
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎯 Creando 4 issues épicos en GitHub...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Función para crear issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"

    # Convertir labels a formato JSON array
    local labels_json=$(echo "$labels" | awk -F',' '{
        printf "["
        for(i=1; i<=NF; i++) {
            gsub(/^[ \t]+|[ \t]+$/, "", $i)
            printf "\"%s\"", $i
            if(i<NF) printf ","
        }
        printf "]"
    }')

    # Crear JSON payload
    local json_payload=$(jq -n \
        --arg title "$title" \
        --arg body "$body" \
        --argjson labels "$labels_json" \
        '{title: $title, body: $body, labels: $labels}')

    # Hacer request a GitHub API
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "$API_URL" \
        -d "$json_payload")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "201" ]; then
        issue_number=$(echo "$body" | jq -r '.number')
        echo -e "${GREEN}✅ Issue #${issue_number} creado${NC}"
        return 0
    else
        echo -e "${RED}❌ Error al crear issue (HTTP $http_code)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Issue #1: Pytest
echo -e "${BLUE}📝 Creando Issue #1: Pytest${NC}"
create_issue \
    "🧪 Implementar pytest con fixtures y coverage >80%" \
    "### 📋 Descripción
Implementar suite de testing completa usando pytest para garantizar la calidad del código y prevenir regresiones.

### 🎯 Objetivos
- [ ] Setup inicial de pytest con configuración profesional
- [ ] Fixtures compartidos para DB, usuarios, clínicas
- [ ] Tests unitarios de modelos (13 modelos)
- [ ] Tests de la lógica de cálculo FPA (crítico)
- [ ] Tests de autenticación (IAP + tradicional)
- [ ] Tests de blueprints principales
- [ ] Coverage report >80%
- [ ] Documentación de cómo correr tests

### 📁 Archivos a Crear
\`\`\`
tests/
├── conftest.py              # Fixtures compartidos
├── test_models.py           # Tests de User, Clinic, Patient, etc.
├── test_fpa_logic.py        # Tests del cálculo FPA (GOLD)
├── test_auth.py             # Tests de autenticación
├── test_routes_tickets.py   # Tests de CRUD tickets
├── test_routes_admin.py     # Tests de panel admin
├── test_routes_dashboard.py # Tests de métricas
└── pytest.ini               # Configuración pytest
\`\`\`

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
\`\`\`txt
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0
faker==20.1.0
freezegun==1.4.0
\`\`\`

### ✅ Definition of Done
- [ ] Tests pasan en local
- [ ] Coverage >80% (verificar con \`pytest --cov\`)
- [ ] Documentación en README sobre cómo correr tests
- [ ] Fixtures reutilizables para futuras pruebas
- [ ] Sin warnings en pytest

### 🔗 Referencias
- [Documentación pytest](https://docs.pytest.org/)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [Testing Flask Apps](https://flask.palletsprojects.com/en/latest/testing/)" \
    "testing,enhancement,priority: high"

echo ""

# Issue #2: CI/CD
echo -e "${BLUE}📝 Creando Issue #2: CI/CD Pipeline${NC}"
create_issue \
    "🚀 Implementar CI/CD Pipeline con GitHub Actions" \
    "### 📋 Descripción
Automatizar testing, linting, build y deploy usando GitHub Actions para reducir errores humanos y acelerar entregas.

### 🎯 Objetivos
- [ ] Workflow de CI (tests + linting en cada PR)
- [ ] Workflow de deploy automático a QA
- [ ] Workflow de deploy manual a PROD
- [ ] Notifications en caso de fallo
- [ ] Quality gates (no merge si tests fallan)
- [ ] Cache de dependencies para velocidad

### 📁 Archivos a Crear
\`\`\`
.github/workflows/
├── ci.yml              # Tests + linting en cada PR
├── deploy-qa.yml       # Auto-deploy a QA en merge a main
├── deploy-prod.yml     # Manual deploy a PROD
└── nightly-tests.yml   # Tests completos cada noche
\`\`\`

### 🎯 Quality Gates
- ✅ Todos los tests deben pasar
- ✅ Coverage mínimo: 80%
- ✅ No errores de flake8 críticos
- ✅ Black formatting correcto
- ✅ No vulnerabilidades críticas (safety)

### 🚀 Deploy Workflows
- **QA:** Auto-deploy en merge a \`main\`
- **PROD:** Manual trigger con aprobación requerida

### ✅ Definition of Done
- [ ] CI workflow funciona en PRs
- [ ] Tests se corren automáticamente
- [ ] No se puede hacer merge si tests fallan
- [ ] Deploy a QA automático
- [ ] Deploy a PROD manual con botón
- [ ] Notificaciones configuradas

### 🔗 Referencias
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Flask CI/CD Examples](https://github.com/actions/starter-workflows/tree/main/ci)" \
    "ci/cd,automation,priority: high"

echo ""

# Issue #3: Redis Cache
echo -e "${BLUE}📝 Creando Issue #3: Redis Cache${NC}"
create_issue \
    "⚡ Implementar Redis Cache Layer para Performance" \
    "### 📋 Descripción
Agregar capa de caché con Redis para mejorar performance del dashboard y reducir carga en PostgreSQL.

### 🎯 Objetivos
- [ ] Setup Redis en GCP Memorystore
- [ ] Cache de queries frecuentes (dashboard stats)
- [ ] Session store en Redis (no en cookies)
- [ ] Invalidación inteligente de cache
- [ ] Métricas de hit rate
- [ ] Fallback automático si Redis falla

### 📊 Métricas Esperadas
- Dashboard load time: 3s → <500ms (6x más rápido)
- DB queries en dashboard: 15 → 2
- Cache hit rate objetivo: >70%

### 🛠️ Stack Técnico
\`\`\`txt
redis==5.0.1
flask-caching==2.1.0
\`\`\`

### 🏗️ Infraestructura GCP
- Crear Redis instance en Memorystore
- VPC peering con Cloud Run
- Configurar en Terraform/Cloud Console

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

### 🔗 Referencias
- [Flask-Caching Docs](https://flask-caching.readthedocs.io/)
- [GCP Memorystore](https://cloud.google.com/memorystore/docs/redis)" \
    "performance,enhancement,infrastructure"

echo ""

# Issue #4: Query Optimization
echo -e "${BLUE}📝 Creando Issue #4: Query Optimization${NC}"
create_issue \
    "🔍 Optimizar Queries y Resolver N+1 Problems" \
    "### 📋 Descripción
Identificar y resolver problemas de performance en queries de base de datos, especialmente N+1 queries que causan carga excesiva.

### 🎯 Objetivos
- [ ] Auditoría completa de queries
- [ ] Implementar eager loading donde corresponda
- [ ] Agregar indexes en columnas clave
- [ ] Query profiling en endpoints lentos
- [ ] Documentar slow queries

### 🔍 N+1 Problems Identificados

**Problema 1: Nursing Board**
\`\`\`python
# ❌ ANTES (N+1 query)
tickets = Ticket.query.filter_by(clinic_id=clinic_id).all()
for ticket in tickets:
    print(ticket.patient.nombre)  # Query por cada ticket!
    print(ticket.specialty.name)  # Otra query!
    print(ticket.doctor.nombre)   # Otra query!
# Total: 1 + (N * 3) queries

# ✅ DESPUÉS (eager loading)
tickets = Ticket.query\\
    .filter_by(clinic_id=clinic_id)\\
    .options(
        joinedload(Ticket.patient),
        joinedload(Ticket.specialty),
        joinedload(Ticket.doctor)
    ).all()
# Total: 1 query con JOINs
\`\`\`

### 📊 Indexes a Crear
\`\`\`sql
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
\`\`\`

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

### 🔗 Referencias
- [SQLAlchemy Loading Techniques](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html)
- [PostgreSQL Index Performance](https://www.postgresql.org/docs/current/indexes.html)" \
    "performance,database,tech-debt"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ¡TODOS LOS ISSUES CREADOS EXITOSAMENTE!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📋 Ve tus issues en:"
echo "   https://github.com/${REPO_OWNER}/${REPO_NAME}/issues"
echo ""
echo "🚀 Siguiente paso: Asignar issues y empezar con #1 (pytest)"
echo ""
