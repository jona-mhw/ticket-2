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

| Ambiente | URL | Acceso |
|----------|-----|--------|
| **DEV** | https://ticket-home.mhwdev.dev | Google SSO + Login tradicional |
| **QA** | https://qa-ticket-home.mhwdev.dev | Solo Google SSO |

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

## 📖 Documentación Técnica

Para información técnica sobre deployment y desarrollo:
- `_deployment_scripts/README.md` - Guía de deployment
- `RESUMEN-SEGURIDAD-v1.9.3.md` - Documentación de seguridad
- `_docs/changelog.md` - Historial de versiones

---

## 🔧 Soporte

**Reporte de issues**: https://github.com/jona-mhw/rs-ticket-home/issues

**Desarrollado para**: RedSalud Chile
**Versión actual**: 0.1 rs
**Última actualización**: Noviembre 2025
