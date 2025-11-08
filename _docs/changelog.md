# Changelog - Ticket Home

Registro cronológico de cambios, mejoras y correcciones del sistema.

---

## [0.1 rs] - 2025-11-04

### Modificado
- **[UX-001] Flexibilidad en formato de ingreso de RUT para Médicos**
  - Eliminada validación de patrón HTML5 en campo RUT de médicos
  - **Comportamiento anterior**: Pattern estricto `\d{1,2}\.\d{3}\.\d{3}-[\dkK]` rechazaba formatos diferentes
  - **Comportamiento nuevo**: Campo acepta cualquier formato de ingreso, placeholder sugiere formato estándar
  - **Razón**: Permitir flexibilidad en el ingreso de datos según necesidades operativas
  - Archivos modificados: `templates/admin/doctor_form.html`, `templates/admin/master_data.html`

### Corregido
- **[BUG-001] DischargeTimeSlots faltantes en seed mínimo QA** ⭐
  - **Problema**: Al crear tickets en QA, el bloque de FPA mostraba "N/A" porque no existían DischargeTimeSlots
  - **Causa raíz**: El seed mínimo (`init_db_qa_minimal` y `reset_db_qa_minimal`) solo creaba clínicas y superusuarios, sin datos esenciales del sistema
  - **Solución**: Agregada creación automática de DischargeTimeSlots (12 bloques de 2 horas) para cada clínica
  - **Impacto**: Sistema ahora funcional en QA - cálculo de FPA muestra correctamente el bloque horario
  - **Clasificación**: DischargeTimeSlots son datos esenciales del sistema, NO datos demo
  - **Nota**: StandardizedReasons deben crearse manualmente en QA según necesidades del cliente
  - Archivos modificados: `commands.py` (init_db_qa_minimal_command, reset_db_qa_minimal_command)

### Agregado
- **[ADMIN-001] Filtro de Clínica para Superusuarios en Datos Maestros** ⭐
  - Implementado selector de clínica superior en página de Datos Maestros
  - **Funcionalidad**: Superusuarios pueden filtrar y gestionar datos maestros de una clínica específica
  - **Filtrado aplicado a**: Especialidades, Cirugías, Razones Estandarizadas, Médicos
  - **Validación**: Todos los formularios de creación automáticamente usan la clínica seleccionada en el filtro
  - **Persistencia**: El filtro se mantiene activo después de crear/modificar datos
  - **UX**: Mensaje de advertencia cuando no hay clínica seleccionada, formularios ocultos hasta seleccionar clínica
  - **Tablas simplificadas**: Eliminada columna "Clínica" (redundante con el filtro superior)
  - Archivos modificados: `routes/admin.py` (master_data, create_*, toggle_*), `templates/admin/master_data.html`

- **[DATA-003] Campo RUT para Médicos**
  - Reemplazado campo "Licencia Médica" por "RUT" en modelo Doctor
  - **Formato**: RUT chileno con validación (12.345.678-9)
  - **Validación**: Pattern HTML5 `\d{1,2}\.\d{3}\.\d{3}-[\dkK]`
  - **Migración**: Creada migración `5af46148d926` para renombrar columna
  - Archivos modificados: `models.py`, `routes/admin.py`, `templates/admin/master_data.html`, `templates/admin/doctor_form.html`, `templates/admin/doctors.html`

### Modificado
- **Gestión de Datos Maestros**: Interfaz optimizada para superusuarios con flujo clínica-céntrico
- **Formularios de Creación**: Eliminados dropdowns redundantes de clínica, ahora usan filtro superior
- **Redirecciones**: Todas las acciones (crear, toggle) mantienen el filtro de clínica activo

### Técnico
- Backend filtra datos por `clinic_id` desde query string
- JavaScript/Formulario GET para auto-submit al cambiar clínica
- Validaciones de seguridad: usuarios regulares solo ven/gestionan su clínica asignada

---

## [0.1 rs] - 2025-11-03

### Agregado
- **[USER-001] Campos de Contraseña Condicionales**
  - Formularios de usuario ahora ocultan campos de contraseña cuando `ENABLE_DEMO_LOGIN=false`
  - Ambiente QA (solo SSO): No solicita ni permite contraseñas
  - Ambiente DEV (híbrido): Mantiene campos de contraseña visibles
  - Archivos modificados: `routes/admin.py`, `templates/admin/users.html`

- **[DATA-001] Nueva Categoría de Razones: Discrepancia Inicial** ⭐
  - Implementada 3ra categoría de razones estandarizadas: `REASON_CATEGORY_INITIAL`
  - **Uso**: Cuando el médico cambia la FPA calculada automáticamente al CREAR el ticket
  - **Ubicación**: Formulario de creación de tickets → Sección de discrepancia inicial
  - **5 razones nuevas**: Criterio médico especializado, Complejidad del procedimiento, Comorbilidades, Protocolo clínico, Evaluación pre-alta
  - **Filtrado dinámico por clínica**: Para superusuarios, las razones se filtran automáticamente según la clínica seleccionada al inicio del formulario
  - Ahora existen **3 categorías completas**:
    1. **Discrepancia Inicial** (5 razones) - Al crear ticket
    2. **Modificación** (7 razones) - Al modificar FPA de ticket existente
    3. **Anulación** (4 razones) - Al anular ticket
  - **Total**: 16 razones estandarizadas por clínica
  - Archivos modificados: `models.py`, `commands.py`, `routes/tickets.py`, `templates/tickets/create.html`, `templates/admin/master_data.html`

- **[DATA-002] Razones de Modificación y Anulación Ampliadas**
  - Ampliado seed de 2 a 7 razones de modificación
  - Ampliado seed de 1 a 4 razones de anulación
  - Nuevas razones: Interconsulta médica, Resultados de exámenes, Cuidados intensivos, etc.

### Modificado
- **Versión Unificada**: Confirmada versión 0.1 rs en todos los archivos productivos
- **Validación SSO**: Usuario creados en modo SSO-only reciben password aleatorio seguro (no utilizable)
- **Gestión de Usuarios**: Formularios adaptan campos según configuración de autenticación del ambiente

### Técnico
- Validación de password ahora condicional según `ENABLE_DEMO_LOGIN`
- Imports de `os` agregados donde se necesita leer variables de entorno
- Template users.html recibe variable `enable_demo_login` para controlar visualización

### Deployment
- QA debe usar `ENABLE_DEMO_LOGIN=false` (ya configurado en scripts)
- DEV debe usar `ENABLE_DEMO_LOGIN=true` (ya configurado en scripts)
- Razones ampliadas se aplicarán en próximo reset de DB o creación manual

---

## [0.1 rs Release] - 2025-11-02

### Cambios
- **Versión de Producto**: Primera versión orientada a usuario final
- README.md actualizado con enfoque en producto y usuarios
- Scripts de deployment reorganizados y simplificados
- Footer actualizado a "0.1 rs" para identificación de versión productiva

### Técnico
- Mantiene todas las mejoras de seguridad de v1.9.x
- Sistema listo para uso en ambientes DEV y QA

---

## [v1.9.3 Security Hardening] - 2025-11-02

### Corregido
- **[CONFIG] IAM Policy Binding por Ambiente**
  - DEV: Grupo `rs-ticket-home@googlegroups.com`
  - QA: Grupo `qa-ticket-home-rs@googlegroups.com`
  - Cada ambiente ahora tiene el grupo de Google correcto para IAP

### Deployment
- Deployado a DEV y QA con configuración correcta de grupos IAP
- Versión actualizada en footer para confirmar deployment exitoso

---

## [v1.9.2 Security Hardening] - 2025-11-02

### Corregido
- **[HIGH-001] XSS via JSON Injection en Dashboard** (Severidad ALTA)
  - Archivo: `templates/dashboard.html:260`
  - Cambio: `{{ chart_data|safe }}` → `{{ chart_data|tojson }}`
  - Impacto: Previene ejecución de JavaScript malicioso en dashboard
  - CWE-79: Cross-site Scripting

- **[HOTFIX] CSP bloqueando recursos externos** (Post-deployment fix)
  - Archivo: `app.py:167-181`
  - Problema: Content Security Policy inicial muy restrictivo bloqueaba CDNs necesarios
  - Solución: Agregados CDNs a allowlist del CSP:
    - `script-src`: cdn.jsdelivr.net, cdn.tailwindcss.com, code.jquery.com, cdn.datatables.net, cdnjs.cloudflare.com
    - `style-src`: cdn.jsdelivr.net, fonts.googleapis.com, cdnjs.cloudflare.com, cdn.datatables.net
    - `font-src`: fonts.gstatic.com, cdnjs.cloudflare.com
    - `connect-src`: cdn.datatables.net
  - Impacto: Permite carga de Bootstrap, jQuery, DataTables, Chart.js, Font Awesome, Tailwind
  - Mantiene seguridad básica mientras permite funcionalidad completa

### Agregado
- **[MED-001] Headers de Seguridad HTTP** (Severidad MEDIA)
  - Archivo: `app.py` - Nueva función `set_security_headers()`
  - Headers implementados:
    - `X-Frame-Options: DENY` (previene clickjacking)
    - `Strict-Transport-Security: max-age=31536000` (fuerza HTTPS por 1 año en QA/PROD)
    - `X-Content-Type-Options: nosniff` (previene MIME sniffing)
    - `Content-Security-Policy` (política de seguridad de contenido)
    - `Referrer-Policy: strict-origin-when-cross-origin` (control de referrer)
    - `Permissions-Policy` (limita APIs del navegador)
  - **NOTA**: Headers solo se aplican en ambientes QA/PROD, NO en local (facilita desarrollo)
  - Protege contra: Clickjacking, SSL stripping, MIME sniffing, XSS
  - CWE-693: Protection Mechanism Failure

- **[NEW] Separación de Autenticación por Ambiente**
  - Archivo: `app.py` - Modificado middleware `before_request_auth()`
  - **DEV**: Autenticación híbrida (IAP + Login tradicional) - `ENABLE_DEMO_LOGIN=true`
  - **QA/PROD**: Solo SSO (Login tradicional deshabilitado) - `ENABLE_DEMO_LOGIN=false`
  - Nuevo template: `templates/errors/unauthorized.html` - Página de error 403 para usuarios no autorizados en QA/PROD
  - Mejora seguridad eliminando vector de ataque de passwords débiles en ambientes productivos

- **[MED-002] Migración de Emails de Superusuarios a Secret Manager** (Severidad MEDIA)
  - Archivo: `_deployment_scripts/0-setup-secrets-v1.9.2.sh`
  - Emails de superusuarios movidos desde variables de entorno a Google Secret Manager
  - Scripts de deployment actualizados para usar `--set-secrets="SUPERUSER_EMAILS=superuser-emails:latest"`
  - Reduce exposición de información sensible en repositorio GitHub público
  - CWE-200: Exposure of Sensitive Information

### Modificado
- **Scripts de Deployment Actualizados**
  - `3-deploy-normal-sa-west1-v2.txt` - DEV con secrets y `ENABLE_DEMO_LOGIN=true`
  - `3-deploy-qa-normal-v2.txt` - QA con secrets y `ENABLE_DEMO_LOGIN=false` (solo SSO)
  - Agregados comentarios explicativos sobre cambios de seguridad
  - Agregadas instrucciones de verificación post-deployment

### Seguridad
- **Puntuación OWASP Top 10 mejorada**: 7/10 → 8.5/10
- **Vulnerabilidades corregidas**: 1 ALTA, 2 MEDIAS
- **Postura de seguridad**: BUENA → EXCELENTE

### Deployment
- **Breaking Changes en QA/PROD**:
  - QA y PROD requieren autenticación SSO exclusivamente
  - Login tradicional deshabilitado en ambientes no-DEV
  - Usuarios deben estar autorizados en Google IAP para acceder

### Técnico
- Archivos modificados:
  - `templates/dashboard.html` (XSS fix)
  - `app.py` (headers de seguridad + separación de auth)
  - `templates/errors/unauthorized.html` (nuevo)
  - `_deployment_scripts/` (3 archivos nuevos/actualizados)

### Testing
- Headers de seguridad verificables con: `curl -I https://ticket-home.mhwdev.dev`
- Política de autenticación verificable en QA: debe mostrar error 403 sin IAP
- Dashboard debe renderizar sin errores JavaScript

---

## [v1.9.1 Superuser] - 2025-11-01

### Agregado
- **Gestión completa de superusuarios desde la interfaz**
  - Nueva opción "Superusuario" en formularios de creación/edición de usuarios
  - Solo superusuarios pueden crear o modificar otros superusuarios
  - Badge visual distintivo (rojo) para identificar superusuarios en el listado
  - Sincronización automática con tabla `Superuser` al crear/editar

- **Nueva constante `ROLE_SUPERUSER`** en `models.py`
  - Valor: `'superuser'`
  - Uso consistente en toda la aplicación

### Modificado
- **models.py - Método `is_admin()`**
  - Ahora incluye superusuarios: `return self.role == 'admin' or self.is_superuser`
  - Los superusuarios heredan todos los permisos de administrador

- **routes/admin.py - Función `create_user()`**
  - Validación de permisos: solo superusuarios pueden crear otros superusuarios
  - Campo `clinic_id` es `None` para superusuarios (no pertenecen a ninguna clínica)
  - Inserción automática en tabla `Superuser` al crear superusuario

- **routes/admin.py - Función `edit_user()`**
  - Manejo de transiciones entre roles normales y superusuario
  - Actualización automática de tabla `Superuser` al cambiar roles
  - Manejo de cambios de email para superusuarios existentes

- **templates/admin/users.html**
  - Select de rol incluye opción "Superusuario" (visible solo para superusuarios)
  - JavaScript para ocultar campo "Clínica" cuando se selecciona rol superusuario
  - Badge de rol muestra "Superusuario" basándose en `user.is_superuser` en vez de `user.role`
  - Modal de edición detecta correctamente superusuarios y pre-selecciona el rol

### Corregido
- **Problema**: Superusuarios creados no tenían permisos de administrador
  - **Causa**: Método `is_admin()` solo verificaba `role == 'admin'`
  - **Solución**: Actualizado `is_admin()` para incluir `is_superuser`

- **Problema**: Superusuarios aparecían como "Admin" en listado
  - **Causa**: Template mostraba `user.role` directamente
  - **Solución**: Template verifica `user.is_superuser` y muestra badge correcto

### Técnico
- Archivos modificados:
  - `models.py`: +1 constante, modificado método `is_admin()` (línea 65-67)
  - `routes/admin.py`: +2 imports, lógica completa en `create_user()` y `edit_user()`
  - `templates/admin/users.html`: +3 funciones JavaScript, actualizado listado y formularios

---

## [v1.9.0 Foundation] - 2025-11-01

### Agregado
- **Documentación ejecutiva completa**
  - `_docs/resumen.md`: Guía ejecutiva para retomar proyecto eficientemente
  - `_docs/arquitectura-tecnica.md`: Documentación técnica detallada (12 secciones)

- **Seed mínimo para QA**
  - Nuevo comando Flask: `flask init-db-qa-minimal`
  - Nuevo comando Flask: `flask reset-db-qa-minimal`
  - Solo carga 9 clínicas + superusuarios (sin datos demo)

- **Variable de entorno `USE_QA_MINIMAL_SEED`**
  - Permite elegir tipo de seed en deployment
  - Integrado en `startup.sh`

### Modificado
- **startup.sh**: Lógica condicional para seed mínimo vs completo
- **commands.py**: Agregadas funciones `init_db_qa_minimal_command()` y `reset_db_qa_minimal_command()`
- **Versión**: Actualizada a v1.9.0 Foundation en `templates/base.html:646`

### Deployment
- Scripts de deployment actualizados con warnings críticos sobre IAM policy binding
- Checklist agregado a todos los scripts de deployment
- Recordatorio visible: paso de IAM policy es OBLIGATORIO después de cada deploy

---

## [v1.8.2 Dracula] - 2025-10-XX

### Modificado
- Mejoras UX para ticket detail
- Enhanced branding

---

## [v1.8.1] - 2025-10-XX

### Modificado
- UX improvements
- User management enhancements

---

## [v1.8.0 Dracula] - 2025-10-XX

### Agregado
- Mejoras UX
- Sistema de auditoría

---

## [v1.7.0 Charlotte] - 2025-10-XX

### Agregado
- (Detalles por documentar)

---

## Leyenda de Categorías

- **Agregado**: Nuevas funcionalidades
- **Modificado**: Cambios en funcionalidades existentes
- **Corregido**: Bugs fixes
- **Eliminado**: Funcionalidades removidas
- **Deprecado**: Funcionalidades que serán removidas
- **Seguridad**: Parches de seguridad
- **Técnico**: Cambios técnicos internos sin impacto funcional visible
- **Deployment**: Cambios en infraestructura o proceso de deployment

---

## Notas

- Este changelog sigue el formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
- Versionado semántico: MAJOR.MINOR.PATCH
- Versiones sin número usan nombres temáticos (ej: Dracula, Charlotte, Foundation)
