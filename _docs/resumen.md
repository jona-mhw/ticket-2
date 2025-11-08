# Ticket Home - Resumen Ejecutivo para Retomar el Proyecto

**Versión Actual**: v1.9.0 Foundation
**Fecha**: Noviembre 2025
**Última Actualización**: Este documento

---

## 🎯 Propósito de Este Documento

Este archivo está diseñado para que puedas retomar el proyecto Ticket Home de manera eficiente en futuras conversaciones con Claude Code, **minimizando tokens** y **maximizando efectividad**.

**NO NECESITAS EXPLORAR TODO EL CODEBASE**. Lee este documento primero y explora archivos específicos solo cuando sean necesarios.

---

## 📋 ¿Qué es Ticket Home?

Sistema web para gestionar la **Fecha Probable de Alta (FPA)** de pacientes post-quirúrgicos en 9 clínicas de RedSalud Chile.

**Problema que resuelve**: Coordinar altas hospitalarias calculando automáticamente cuándo un paciente debería salir del hospital basándose en el tipo de cirugía y hora de fin de pabellón.

**Usuario objetivo**: Personal de enfermería, administradores de clínica, médicos (solo lectura)

---

## 🏗️ Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Backend** | Flask 2.3.3 (Python 3.11) |
| **ORM** | SQLAlchemy + Flask-Migrate |
| **Base de Datos** | PostgreSQL 17 (Cloud SQL) |
| **Frontend** | Jinja2 + HTML5 + CSS3 + JavaScript vanilla |
| **Autenticación** | IAP (Identity-Aware Proxy) + Login tradicional |
| **Deployment** | Docker + Cloud Run (serverless) |
| **Infraestructura** | Google Cloud Platform (GCP) |
| **CI/CD** | **Manual** (NO hay Cloud Run Jobs - restricción importante) |

---

## 🚨 RESTRICCIONES IMPORTANTES

### 1. **NO Puedes Usar Cloud Run Jobs**
- **Por qué**: El usuario no tiene acceso/permisos
- **Solución**: Scripts manuales de deployment con Docker local
- **Ubicación scripts**: `_deployment_scripts/`

### 2. **Docker Local es OBLIGATORIO**
- Debes construir imágenes localmente
- Push manual a Artifact Registry
- Deploy manual a Cloud Run

### 3. **Estrategia de Reset de DB**
- **Problema**: Sin Jobs, no puedes ejecutar comandos de Flask en Cloud Run directamente
- **Solución**: Variable de entorno `RESET_DB_ON_STARTUP=true` en el primer deploy, luego `false`
- **Scripts**: Ver `2-deploy-con-reset-db-sa-west1.txt` (2 pasos)

---

## 📁 Estructura de Archivos Clave

```
rs-ticket-home/
├── app.py                    # Factory de Flask, blueprints, configuración
├── models.py                 # 13 modelos SQLAlchemy (multi-tenant)
├── commands.py               # 10 comandos CLI de Flask (seed, reset, etc.)
├── config.py                 # Configuración (detecta local vs production)
├── startup.sh                # Script de inicio del contenedor Docker
├── auth_iap.py               # Autenticación híbrida IAP + tradicional
│
├── routes/                   # 6 Blueprints Flask
│   ├── auth.py              # Login/logout IAP
│   ├── tickets.py           # CRUD tickets + cálculo FPA
│   ├── admin.py             # Panel admin + datos maestros
│   ├── dashboard.py         # KPIs y gráficos
│   ├── visualizador.py      # Vista solo lectura
│   ├── exports.py           # PDF y Excel
│   └── utils.py             # Helpers compartidos
│
├── templates/                # 24 templates Jinja2
│   ├── base.html            # Template padre (footer con versión)
│   ├── tickets/             # 7 templates de tickets
│   └── admin/               # 9 templates de admin
│
├── migrations/               # 7 migraciones Alembic
│
├── _deployment_scripts/      # Scripts de deployment (CRÍTICOS)
│   ├── 1-build-and-push-v3.bat              # Build DEV
│   ├── 1-build-and-push-qa.bat              # Build QA
│   ├── 2-deploy-con-reset-db-sa-west1.txt   # Deploy DEV con reset (2 pasos)
│   ├── 2-deploy-qa-con-reset-db-minimal.txt # Deploy QA con reset (3 pasos)
│   ├── 3-deploy-normal-sa-west1.txt         # Deploy DEV sin reset
│   └── 3-deploy-qa-normal.txt               # Deploy QA sin reset
│
└── _docs/                    # Documentación
    ├── resumen.md           # Este archivo
    └── arquitectura-tecnica.md  # Documentación técnica detallada
```

---

## 🌍 Ambientes y Proyectos GCP

| Ambiente | Proyecto GCP | Región | Artifact Registry | DB Seed |
|----------|--------------|---------|-------------------|---------|
| **DEV** | `dev-ticket-home-redsalud` | `southamerica-west1` | `us-central1` | Datos demo completos |
| **QA** | `qa-ticket-home-redsalud` | `southamerica-west1` | `southamerica-west1` | Mínimo (9 clínicas + superusuarios) |
| **PROD** | `prod-ticket-home-redsalud` | TBD | TBD | Por definir |

**Nota**: Artifact Registry de DEV está en `us-central1` por razones históricas. Cloud Run de DEV está en `southamerica-west1`.

---

## 🔑 Comandos Flask Más Usados

```bash
# Seed completo con datos demo (DEV)
flask init-db

# Reset completo + seed demo (DEV)
flask reset-db

# Seed mínimo solo clínicas + superusuarios (QA)
flask init-db-qa-minimal

# Reset + seed mínimo (QA)
flask reset-db-qa-minimal

# Ejecutar migraciones
flask db upgrade

# Sincronizar superusuarios desde variable de entorno
flask sync-superusers

# Exportar DB local a SQL (backup)
flask export-local-db --upload-to-gcs --bucket=ticket-home-db-exports
```

---

## 🚀 Flujo de Deployment Típico

### Deployment a DEV (sin reset)

```bash
# 1. Build imagen
docker build -t us-central1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:latest .

# 2. Push a Artifact Registry
docker push us-central1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:latest

# 3. Deploy a Cloud Run (copiar comando de 3-deploy-normal-sa-west1.txt)
gcloud run deploy ticket-home --image=... --region=southamerica-west1 ...

# 4. CRÍTICO: Agregar permiso IAM (si no, error 403)
gcloud run services add-iam-policy-binding ticket-home \
  --region=southamerica-west1 \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project=dev-ticket-home-redsalud
```

### Deployment a QA (sin reset)

```bash
# Igual que DEV pero con:
# - Imagen: southamerica-west1-docker.pkg.dev/qa-ticket-home-redsalud/...
# - Proyecto: qa-ticket-home-redsalud
# - Service Account: qa-ticket-home@qa-ticket-home-redsalud.iam.gserviceaccount.com
# - VPC Connector: tckthome-conn-qa-sa-west1
```

**Ver scripts en `_deployment_scripts/` para comandos completos.**

---

## 🔐 Variables de Entorno Importantes

### Comunes a Todos los Ambientes

```bash
ENVIRONMENT=production|qa        # Nombre del ambiente
FLASK_ENV=production             # Modo Flask
FLASK_DEBUG=false                # Debug desactivado en producción
ENABLE_IAP=true                  # Habilita autenticación IAP
ENABLE_DEMO_LOGIN=true           # Permite login tradicional (emergencias)
SUPERUSER_EMAILS="email1@x.com;email2@y.com"  # Superusuarios separados por ;
```

### Específicas de Deployment

```bash
# Para resetear DB en primer deploy
RESET_DB_ON_STARTUP=true         # true = resetea, false = no toca DB

# Para usar seed mínimo en QA
USE_QA_MINIMAL_SEED=true         # Solo con RESET_DB_ON_STARTUP=true
```

### Secrets (en Secret Manager)

```bash
DATABASE_URL                     # postgresql://...
SECRET_KEY                       # Clave secreta Flask
```

---

## 🗄️ Modelo de Datos Esencial

**Multi-tenant**: Todo está segregado por `clinic_id` (excepto `Superuser`)

**13 Modelos principales**:

1. **Clinic** - 9 clínicas RedSalud
2. **Superuser** - Emails autorizados como superusuarios (sin clinic_id)
3. **User** - Usuarios con 4 roles: `superuser`, `admin`, `clinical`, `visualizador`
   - `superuser`: Acceso global a todas las clínicas, puede crear otros superusuarios
   - `admin`: Administrador de una clínica específica
   - `clinical`: Usuario operativo de una clínica
   - `visualizador`: Solo lectura en una clínica
4. **Specialty** - Especialidades médicas por clínica
5. **Surgery** - Cirugías con `base_stay_hours` (base del cálculo FPA)
6. **Doctor** - Médicos tratantes
7. **DischargeTimeSlot** - 12 bloques horarios de alta (2h cada uno)
8. **StandardizedReason** - Razones predefinidas para modificar/anular
9. **Patient** - Pacientes (RUT, nombres, edad, sexo)
10. **Ticket** - Registro principal (ID: `TH-{PREFIX}-{YEAR}-{XXX}`)
11. **FpaModification** - Historial de cambios de FPA (máx 5 por ticket)
12. **LoginAudit** - Auditoría de logins
13. **ActionAudit** - Auditoría de acciones críticas

**Cálculo de FPA**:
```python
fpa = pavilion_end_time + timedelta(hours=surgery.base_stay_hours)
# Si es ambulatoria y termina antes del cutoff → ajustar a 08:00 del día siguiente
```

---

## 🎨 Frontend

- **Templates**: Jinja2 con herencia (base.html)
- **CSS**: Tailwind-like utility classes + custom CSS
- **JavaScript**: Vanilla JS para interactividad
- **Diseño**: Responsive, optimizado para desktop
- **Logo**: RedSalud (`static/images/logo-redsalud.svg`)

**Footer con versión**: `templates/base.html:646`

---

## 👥 Contexto Laboral

- **Cliente**: RedSalud (red de clínicas en Chile)
- **Desarrollador**: Único (tú)
- **Usuario del sistema**: jonathan.segura@redsalud.cl
- **Deployment**: Manual por restricciones de permisos GCP
- **Testing**: NO hay tests automatizados (considerar agregar en futuro)
- **Ambientes**: DEV → QA → PROD (PROD pendiente)

---

## 🔍 Cómo Retomar Trabajo Eficientemente

### ✅ SÍ Debes Hacer

1. **Leer este archivo primero** antes de explorar código
2. **Revisar `_deployment_scripts/`** para entender deployment
3. **Consultar arquitectura-tecnica.md** para detalles de infraestructura
4. **Explorar archivos específicos** solo cuando la tarea lo requiera
5. **Usar `Grep` o `Glob`** para búsquedas rápidas en lugar de leer todo

### ❌ NO Debes Hacer

1. **NO leas todos los archivos** del proyecto innecesariamente
2. **NO explores templates HTML** a menos que sea necesario
3. **NO revises migraciones** a menos que haya un problema de DB
4. **NO intentes usar Cloud Run Jobs** (no disponibles)
5. **NO asumas que hay CI/CD automático** (todo es manual)

---

## 👑 Gestión de Superusuarios

### ¿Qué es un Superusuario?

Un superusuario es un usuario con acceso global a todas las clínicas del sistema. Características:
- **clinic_id = None** (no pertenece a ninguna clínica específica)
- **Email en tabla Superuser** (registro adicional para verificación)
- **Permisos de administrador** en todas las clínicas
- **Puede crear otros superusuarios** (privilegio exclusivo)

### Crear Superusuario desde la Interfaz

1. Accede a `/admin/users` como superusuario
2. En el formulario "Crear Nuevo Usuario":
   - Usuario: nombre de usuario
   - Email: email del nuevo superusuario
   - Contraseña: contraseña inicial
   - **Rol: Superusuario** (opción visible solo para superusuarios)
   - Campo "Clínica" se oculta automáticamente
3. Haz clic en "Crear Usuario"
4. El sistema automáticamente:
   - Crea usuario con `role='superuser'` y `clinic_id=None`
   - Agrega email a tabla `Superuser`

### Editar o Convertir a Superusuario

1. En listado de usuarios, haz clic en "Editar"
2. Cambia el rol a "Superusuario"
3. Campo "Clínica" se oculta automáticamente
4. El sistema automáticamente:
   - Actualiza `role='superuser'` y `clinic_id=None`
   - Agrega/actualiza entrada en tabla `Superuser`
   - Si había una clínica asignada, la elimina

### Identificación Visual

En el listado de usuarios, los superusuarios muestran:
- **Badge rojo** con texto "Superusuario"
- **Clínica**: "Global" (en vez de nombre de clínica)

### Métodos Técnicos

```python
# models.py - User model

# Verificar si es superusuario
user.is_superuser  # Propiedad que verifica clinic_id=None + email en tabla Superuser

# Verificar permisos de admin (incluye superusuarios)
user.is_admin()    # Retorna True si role='admin' OR is_superuser=True
```

### Comandos Flask

```bash
# Sincronizar superusuarios desde variable de entorno
flask sync-superusers

# Variable de entorno que define emails de superusuarios
SUPERUSER_EMAILS="email1@example.com;email2@example.com;email3@example.com"
```

### Archivos Relacionados

- `models.py:11` - Constante `ROLE_SUPERUSER = 'superuser'`
- `models.py:65-67` - Método `is_admin()` incluye superusuarios
- `models.py:69-82` - Propiedad `is_superuser`
- `routes/admin.py:195-256` - Función `create_user()` con lógica de superusuario
- `routes/admin.py:284-385` - Función `edit_user()` con gestión de tabla Superuser
- `templates/admin/users.html` - UI completa de gestión

---

## 🆘 Problemas Comunes y Soluciones

### Error 403 después de deploy
**Causa**: Falta permiso IAM
**Solución**: Ejecutar `gcloud run services add-iam-policy-binding...` (ver scripts)

### DB no se resetea en deployment
**Causa**: `RESET_DB_ON_STARTUP=false`
**Solución**: Usar script de deploy con reset (2 o 3 pasos)

### Cambios en models.py no se reflejan
**Causa**: Falta migración o DB no se actualizó
**Solución**: `flask db migrate -m "descripción"` + `flask db upgrade` + redeploy con reset

### Superusuarios no pueden acceder (método antiguo)
**Causa**: No están en tabla `Superuser`
**Solución**: Actualizar `SUPERUSER_EMAILS` env var + `flask sync-superusers`

### Superusuario creado no tiene permisos de admin
**Causa**: Método `is_admin()` no incluía superusuarios (ya corregido en v1.9.1)
**Solución**: Actualizar a v1.9.1 o posterior. El método `is_admin()` ahora retorna True para superusuarios

### Error al subir imagen a Artifact Registry
**Causa**: No estás autenticado o proyecto incorrecto
**Solución**: `gcloud config set project [PROJECT_ID]` + `gcloud auth login`

---

## 📝 Notas de Versiones

### v1.9.1 Superuser (2025-11-01)
- **Gestión completa de superusuarios desde la interfaz**
  - Creación de superusuarios desde UI (antes solo por comandos Flask)
  - Edición y conversión de usuarios a superusuario
  - Badge visual distintivo para identificar superusuarios
  - Sincronización automática con tabla Superuser
- **Corrección**: Superusuarios ahora tienen permisos de administrador correctamente
  - Actualizado método `is_admin()` para incluir superusuarios
- **Documentación**: Agregado `_docs/changelog.md` para registro de cambios

### v1.9.0 Foundation
- Primera versión concluida y estable
- Seed mínimo para QA implementado
- Deployment manual a DEV y QA funcionando
- Documentación completa creada (`resumen.md` + `arquitectura-tecnica.md`)

### v1.8.2 Dracula
- UX improvements para ticket detail
- Enhanced branding

### v1.8.1
- UX improvements y user management enhancements

### v1.8.0 Dracula
- Mejoras UX y auditoría

---

## 🔗 Enlaces Importantes

- **Repositorio Git**: https://github.com/jona-mhw/rs-ticket-home
- **DEV URL**: https://ticket-home.mhwdev.dev (via Load Balancer)
- **QA URL**: https://qa-ticket-home.mhwdev.dev (via Load Balancer)
- **Cloud SQL Proxy** (desarrollo local): Ejecutar antes de `flask run`

---

## 💡 Tips para Trabajar con Claude Code

1. **Cita este archivo** al inicio de nuevas conversaciones
2. **Especifica el ambiente** (DEV/QA) al pedir deployments
3. **Pregunta por archivos específicos** en lugar de exploraciones generales
4. **Usa Grep/Glob** para búsquedas rápidas de código
5. **Consulta arquitectura-tecnica.md** para detalles de infraestructura GCP

---

**Fin del Resumen Ejecutivo**
Para detalles técnicos completos, consulta: `arquitectura-tecnica.md`
