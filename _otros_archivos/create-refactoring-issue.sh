#!/bin/bash
# 🚀 Script para crear issue de Refactorización Completa
# Uso: GITHUB_TOKEN=tu_token ./create-refactoring-issue.sh

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
echo -e "${BLUE}♻️  Creando Issue de Refactorización Completa...${NC}"
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
    body_response=$(echo "$response" | sed '$d')

    if [ "$http_code" = "201" ]; then
        issue_number=$(echo "$body_response" | jq -r '.number')
        issue_url=$(echo "$body_response" | jq -r '.html_url')
        echo -e "${GREEN}✅ Issue #${issue_number} creado exitosamente!${NC}"
        echo -e "${BLUE}🔗 URL: ${issue_url}${NC}"
        return 0
    else
        echo -e "${RED}❌ Error al crear issue (HTTP $http_code)${NC}"
        echo "$body_response" | jq '.' 2>/dev/null || echo "$body_response"
        return 1
    fi
}

# Issue de Refactorización
echo -e "${BLUE}📝 Creando Issue: Refactorización Completa${NC}"
create_issue \
    "♻️ Refactorización Completa: Arquitectura Limpia y Separación de Responsabilidades" \
    "## 📋 Descripción

Refactorizar la aplicación Ticket Home para mejorar la mantenibilidad, escalabilidad y calidad del código mediante la aplicación de principios SOLID, arquitectura limpia y mejores prácticas de desarrollo.

## 🎯 Motivación

**Problemas Actuales:**
- ✗ \`routes/admin.py\` tiene **746 líneas** (debería tener <200)
- ✗ \`commands.py\` tiene **720 líneas** (debería tener <200)
- ✗ \`routes/tickets.py\` tiene **634 líneas** (debería tener <200)
- ✗ Lógica de negocio mezclada con controladores
- ✗ Código duplicado (\`calculate_time_remaining\` aparece 2 veces)
- ✗ Sin capa de servicios (toda la lógica está en routes)
- ✗ Modelos con responsabilidades mixtas
- ✗ Sin validadores centralizados
- ✗ Dificulta testing unitario efectivo

## 🏗️ Objetivos de Refactorización

### 1. Separación de Responsabilidades (SOLID)
- [ ] Crear capa de **Services** para lógica de negocio
- [ ] Crear capa de **Repositories** para acceso a datos
- [ ] Crear capa de **Validators** para validación de datos
- [ ] Crear capa de **DTOs** para transferencia de datos
- [ ] Mantener **Routes** solo como controllers (orquestación)

### 2. Estructura de Carpetas Propuesta

\`\`\`
ticket-home/
├── app/
│   ├── __init__.py              # Factory de app Flask
│   ├── models/                  # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── clinic.py
│   │   ├── patient.py
│   │   ├── ticket.py
│   │   └── audit.py
│   ├── services/                # Lógica de negocio (NUEVO)
│   │   ├── __init__.py
│   │   ├── ticket_service.py    # Crear, modificar, anular tickets
│   │   ├── fpa_calculator.py    # Cálculo FPA (extraído de models)
│   │   ├── user_service.py      # Gestión de usuarios
│   │   └── audit_service.py     # Logging de acciones
│   ├── repositories/            # Acceso a datos (NUEVO)
│   │   ├── __init__.py
│   │   ├── ticket_repository.py
│   │   ├── user_repository.py
│   │   └── patient_repository.py
│   ├── validators/              # Validación de datos (NUEVO)
│   │   ├── __init__.py
│   │   ├── ticket_validator.py
│   │   └── user_validator.py
│   ├── dto/                     # Data Transfer Objects (NUEVO)
│   │   ├── __init__.py
│   │   ├── ticket_dto.py
│   │   └── user_dto.py
│   ├── routes/                  # Controllers (REFACTORIZAR)
│   │   ├── __init__.py
│   │   ├── tickets.py          # Reducir de 634 a ~150 líneas
│   │   ├── admin.py            # Reducir de 746 a ~200 líneas
│   │   ├── dashboard.py
│   │   └── auth.py
│   ├── utils/                   # Utilidades compartidas
│   │   ├── __init__.py
│   │   ├── datetime_utils.py   # Funciones de fechas
│   │   ├── string_utils.py     # generate_prefix, etc.
│   │   └── decorators.py       # admin_required, etc.
│   └── config/                  # Configuración
│       ├── __init__.py
│       ├── development.py
│       └── production.py
├── tests/                       # Tests organizados por capa
│   ├── unit/
│   │   ├── test_services/
│   │   ├── test_repositories/
│   │   └── test_validators/
│   └── integration/
│       └── test_routes/
├── migrations/                  # Migraciones Alembic
├── app.py                       # Entry point
└── requirements.txt
\`\`\`

### 3. Ejemplos de Refactorización

#### ❌ ANTES (routes/tickets.py - 634 líneas)
\`\`\`python
@tickets_bp.route('/create', methods=['POST'])
def create():
    # Validación inline (20 líneas)
    if not request.form.get('rut'):
        flash('RUT es requerido', 'error')
        return redirect(...)

    # Lógica de negocio inline (50 líneas)
    patient = Patient.query.filter_by(rut=rut).first()
    if not patient:
        patient = Patient(...)
        db.session.add(patient)

    # Cálculo FPA inline (30 líneas)
    base_hours = surgery.base_stay_hours
    fpa = pavilion_end_time + timedelta(hours=base_hours)
    # ... más lógica compleja ...

    # Persistencia inline (15 líneas)
    db.session.commit()
    flash('Ticket creado', 'success')
\`\`\`

#### ✅ DESPUÉS (routes/tickets.py - ~150 líneas)
\`\`\`python
@tickets_bp.route('/create', methods=['POST'])
def create():
    # 1. Validar entrada
    validation_errors = TicketValidator.validate_create(request.form)
    if validation_errors:
        return jsonify({'errors': validation_errors}), 400

    # 2. Convertir a DTO
    ticket_data = TicketDTO.from_form(request.form)

    # 3. Ejecutar lógica de negocio (service)
    try:
        ticket = TicketService.create_ticket(ticket_data, current_user)
        flash('Ticket creado exitosamente', 'success')
        return redirect(url_for('tickets.nursing_board'))
    except BusinessException as e:
        flash(str(e), 'error')
        return redirect(url_for('tickets.create'))
\`\`\`

#### 🧩 Service Layer (NUEVO)
\`\`\`python
# app/services/ticket_service.py
class TicketService:
    @staticmethod
    def create_ticket(ticket_data: TicketDTO, user: User) -> Ticket:
        \"\"\"Crea un ticket con toda la lógica de negocio centralizada.\"\"\"

        # 1. Obtener/crear paciente
        patient = PatientRepository.get_or_create(
            rut=ticket_data.patient_rut,
            clinic_id=user.clinic_id
        )

        # 2. Calcular FPA
        fpa_info = FPACalculator.calculate(
            pavilion_end_time=ticket_data.pavilion_end_time,
            surgery=ticket_data.surgery
        )

        # 3. Generar ID
        ticket_id = TicketIDGenerator.generate(user.clinic_id)

        # 4. Crear ticket
        ticket = Ticket(
            id=ticket_id,
            patient=patient,
            system_calculated_fpa=fpa_info.fpa,
            # ... más campos ...
        )

        # 5. Auditar acción
        AuditService.log_action(
            user=user,
            action='create_ticket',
            target=ticket
        )

        # 6. Persistir
        TicketRepository.save(ticket)

        return ticket
\`\`\`

### 4. Tareas Específicas

#### 4.1. Crear Capa de Servicios
- [ ] \`TicketService\` - Crear, modificar, anular tickets
- [ ] \`FPACalculator\` - Extraer lógica de cálculo FPA de \`models.py\`
- [ ] \`UserService\` - Gestión de usuarios y permisos
- [ ] \`AuditService\` - Centralizar logging de acciones
- [ ] \`PatientService\` - Lógica de pacientes
- [ ] \`DashboardService\` - Lógica de métricas y estadísticas

#### 4.2. Crear Capa de Repositories
- [ ] \`TicketRepository\` - Queries complejas de tickets
- [ ] \`UserRepository\` - Queries de usuarios
- [ ] \`PatientRepository\` - Queries de pacientes
- [ ] \`AuditRepository\` - Queries de auditoría

#### 4.3. Crear Validadores
- [ ] \`TicketValidator\` - Validar datos de tickets
- [ ] \`UserValidator\` - Validar datos de usuarios
- [ ] \`DateValidator\` - Validar fechas y FPA

#### 4.4. Refactorizar Routes (Controllers)
- [ ] \`routes/tickets.py\` - Reducir de 634 a ~150 líneas
- [ ] \`routes/admin.py\` - Reducir de 746 a ~200 líneas
- [ ] \`routes/dashboard.py\` - Simplificar queries

#### 4.5. Refactorizar Models
- [ ] Separar modelos en archivos individuales
- [ ] Mover lógica de negocio a Services
- [ ] Mantener solo propiedades y relaciones

#### 4.6. Eliminar Código Duplicado
- [ ] Unificar \`calculate_time_remaining\` (aparece en tickets.py y utils.py)
- [ ] Centralizar decoradores (\`admin_required\`, \`superuser_required\`)
- [ ] Extraer funciones comunes de \`commands.py\`

#### 4.7. Mejorar Utilidades
- [ ] \`datetime_utils.py\` - Funciones de fechas
- [ ] \`string_utils.py\` - \`generate_prefix\`, formateo
- [ ] \`decorators.py\` - Centralizar decoradores

### 5. Principios a Aplicar

#### SOLID
- **S**ingle Responsibility: Cada clase/función hace una sola cosa
- **O**pen/Closed: Abierto a extensión, cerrado a modificación
- **L**iskov Substitution: Interfaces consistentes
- **I**nterface Segregation: Interfaces pequeñas y específicas
- **D**ependency Inversion: Depender de abstracciones

#### DRY (Don't Repeat Yourself)
- Eliminar código duplicado
- Centralizar lógica común
- Reutilizar componentes

#### KISS (Keep It Simple, Stupid)
- Código claro y simple
- Evitar complejidad innecesaria
- Funciones pequeñas (<50 líneas)

### 6. Métricas de Éxito

**Antes de Refactorización:**
\`\`\`
routes/admin.py:     746 líneas
routes/tickets.py:   634 líneas
commands.py:         720 líneas
Total:              2100 líneas en 3 archivos
\`\`\`

**Después de Refactorización:**
\`\`\`
routes/admin.py:     ~200 líneas (controllers puros)
routes/tickets.py:   ~150 líneas (controllers puros)
commands.py:         ~200 líneas (comandos CLI)
services/:           ~600 líneas (lógica de negocio)
repositories/:       ~300 líneas (queries)
validators/:         ~200 líneas (validación)
Total:              1650 líneas bien organizadas
\`\`\`

**Beneficios Medibles:**
- ✅ Reducción de ~21% en total de líneas
- ✅ Archivos individuales <250 líneas (estándar: <200)
- ✅ Separación clara de responsabilidades
- ✅ Testing más fácil (unit tests de services)
- ✅ Menos código duplicado
- ✅ Mayor cohesión, menor acoplamiento

### 7. Plan de Ejecución

1. **Fase 1: Setup (2 días)**
   - Crear estructura de carpetas
   - Configurar imports y namespaces

2. **Fase 2: Services (3 días)**
   - Crear FPACalculator
   - Crear TicketService
   - Crear AuditService

3. **Fase 3: Repositories (2 días)**
   - Crear repositories básicos
   - Migrar queries complejas

4. **Fase 4: Refactorizar Routes (3 días)**
   - Refactorizar tickets.py
   - Refactorizar admin.py

5. **Fase 5: Testing (2 días)**
   - Tests unitarios de services
   - Tests de integración

6. **Fase 6: Limpieza (1 día)**
   - Eliminar código muerto
   - Actualizar documentación

**Total: ~13 días de desarrollo**

## ✅ Definition of Done

- [ ] Todos los archivos <250 líneas
- [ ] Capa de services implementada
- [ ] Capa de repositories implementada
- [ ] Sin código duplicado
- [ ] Todos los tests pasan
- [ ] Coverage >80%
- [ ] Documentación actualizada
- [ ] Code review aprobado
- [ ] Sin regresiones funcionales

## 🔗 Referencias

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Flask Best Practices](https://flask.palletsprojects.com/en/latest/patterns/)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

## 📝 Notas

Esta refactorización NO cambia funcionalidad, solo reorganiza el código. Todas las features existentes seguirán funcionando exactamente igual." \
    "refactoring,enhancement,priority: high,tech-debt"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ¡ISSUE DE REFACTORIZACIÓN CREADO!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📋 Ve el issue en:"
echo "   https://github.com/${REPO_OWNER}/${REPO_NAME}/issues"
echo ""
echo "🚀 Siguiente paso: Implementar las fases de refactorización"
echo ""
