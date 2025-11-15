# Ticket Home - Sistema de Gestión de FPA RedSalud

Plataforma web para la gestión y seguimiento de Fechas Probables de Alta (FPA) de pacientes quirúrgicos en las clínicas de RedSalud Chile.

**Versión**: 0.1 rs
**Ambientes**: DEV, QA

---

## 🏥 Sobre el Sistema

Ticket Home permite a los equipos médicos y administrativos de RedSalud:

- **Gestionar pacientes** post-quirúrgicos con seguimiento de FPA
- **Generar alertas** automáticas según estado del paciente
- **Visualizar dashboards** con métricas en tiempo real
- **Exportar reportes** para análisis y auditoría
- **Multi-clínica** con datos aislados por centro médico

### Clínicas Integradas
- Clínica RedSalud Santiago Centro
- Clínica RedSalud Vitacura
- Clínica RedSalud Providencia
- Clínica RedSalud Elqui
- Clínica RedSalud Rancagua
- Clínica RedSalud Iquique
- Clínica RedSalud Magallanes
- Clínica RedSalud Valdivia
- Clínica RedSalud Biobío

---

## 🔐 Acceso al Sistema

### Ambientes Disponibles

| Ambiente | URL | Propósito | Documentación |
|----------|-----|-----------|---------------|
| **LOCAL** | localhost:5000 | Desarrollo diario (80%) | `deployment/local/` |
| **MHW DEV** | https://ticket-home-beta.mhwdev.dev | Cloud personal - Testing/Demos (15%) | `deployment/mhw-dev/` |
| **Empresa DEV** | https://ticket-home.mhwdev.dev | Testing funcional RedSalud (4%) | `deployment/empresa-dev/` |
| **Empresa QA** | https://qa-ticket-home.mhwdev.dev | Pre-producción RedSalud (1%) | `deployment/empresa-qa/` |

### Requisitos de Acceso

**Para acceder necesitas**:
1. Estar agregado al Google Group correspondiente:
   - DEV: `rs-ticket-home@googlegroups.com`
   - QA: `qa-ticket-home-rs@googlegroups.com`
2. Usar tu email corporativo de RedSalud

**Si no tienes acceso**, contacta al administrador del sistema.

---

## 🚀 Tecnología

- **Backend**: Python 3.11 + Flask
- **Base de Datos**: PostgreSQL 17 en Google Cloud SQL
- **Infraestructura**: Google Cloud Run con IAP
- **Seguridad**: Autenticación SSO + Headers de seguridad HTTP
- **Frontend**: Bootstrap 5 + DataTables + Chart.js

---

## 👥 Roles de Usuario

### Superusuarios
Acceso completo a todas las clínicas y funcionalidades administrativas.

### Usuarios por Clínica
Acceso limitado a su clínica asignada con permisos de gestión de tickets.

---

## 📊 Funcionalidades Principales

### Dashboard
- Métricas de pacientes en tiempo real
- Gráficos de alertas por tipo
- Estadísticas por clínica

### Gestión de Tickets
- Crear, editar y eliminar tickets de pacientes
- Cálculo automático de FPA
- Sistema de alertas por colores (verde, amarillo, rojo)
- Filtros avanzados y búsqueda

### Administración (Solo Superusuarios)
- Gestión de usuarios
- Gestión de clínicas
- Auditoría de cambios

### Exportación
- Exportar tickets a Excel
- Impresión de reportes
- Filtros personalizables

---

## 🧪 Testing

Suite de tests con pytest para garantizar calidad del código.

### Ejecutar Tests

```bash
# Instalar dependencias de testing
pip install -r requirements.txt

# Ejecutar todos los tests
pytest

# Con coverage report
pytest --cov=. --cov-report=html
```

### Métricas Actuales
- **49 tests** implementados
- **Coverage modelos**: 94.58%
- **Coverage total**: 27.23%

Ver documentación completa en: `tests/README.md`

---

## 🚀 Deployment

**Ver guía completa**: [`deployment/README.md`](deployment/README.md)

### Quick Start por Ambiente

**LOCAL** (Desarrollo diario):
```bash
flask run
```

**MHW DEV** (Tu cloud personal):
```powershell
cd deployment/mhw-dev
.\Deploy-Interactive.ps1
```

**Empresa DEV/QA** (RedSalud):
```batch
cd deployment\empresa-dev
1-build-push-local.bat
2-deploy-normal.bat
```

---

## 📖 Documentación Técnica

- [`deployment/README.md`](deployment/README.md) - **Guía completa de deployment**
- [`deployment/mhw-dev/docs/SECRETS_GUIDE.md`](deployment/mhw-dev/docs/SECRETS_GUIDE.md) - Gestión de secretos
- [`tests/README.md`](tests/README.md) - Guía completa de testing
- [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) - Arquitectura técnica
- `DEPLOYMENT_LOG.md` - Log detallado del primer deployment

---

## 🔧 Soporte

**Reporte de issues**: https://github.com/jona-mhw/rs-ticket-home/issues

**Desarrollado para**: RedSalud Chile
**Versión actual**: 0.1 rs
**Última actualización**: Noviembre 2025
