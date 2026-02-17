# Ticket-Home: Revisión de Preparación para Producción

**Fecha:** 2026-02-16
**Revisado por:** Claude (revisión automatizada de código)
**Alcance:** Codebase completo - enfoque en riesgos para el día de salida en vivo

---

## Resumen Ejecutivo

La aplicación tiene una arquitectura sólida (Flask + SQLAlchemy, patrón service/repository, validadores, auditoría). Sin embargo, se encontraron **2 bugs que van a causar errores en runtime**, varios riesgos de concurrencia relevantes para un entorno multi-clínica, y problemas de timezone que pueden afectar la lógica de negocio en producción (Chile, UTC-3/UTC-4).

### Clasificación de hallazgos

| Severidad | Cantidad | Descripción |
|-----------|----------|-------------|
| BLOCKER | 2 | Bugs que causan crash en runtime |
| CRITICAL | 3 | Problemas que causan datos incorrectos o pérdida de datos |
| HIGH | 5 | Riesgos significativos para operación en producción |
| MEDIUM | 8 | Problemas que deberían corregirse pronto |
| LOW | 5 | Mejoras recomendadas |

---

## BLOCKER - Corregir antes de desplegar

### B1. Variables indefinidas en modificación de FPA (`NameError` en runtime)

**Archivo:** `routes/tickets.py:296`

```python
# Línea 296: reason y justification NO están definidas en este scope
TicketService.modify_fpa(ticket, new_fpa, reason, justification, current_user)
```

Las variables `reason` y `justification` nunca se extraen de `request.form` en la función `update_fpa()`. El validador (línea 267) valida el form, pero los valores no se asignan a variables locales antes del uso en línea 296.

**Impacto:** Cualquier intento de modificar un FPA producirá un `NameError` inmediato. Esta es una funcionalidad core del sistema.

**Fix:**
```python
# Agregar antes de la línea 296:
reason = request.form.get('reason', '')
justification = request.form.get('justification', '')
```

### B2. `--timeout 0` en Gunicorn (workers inmortales)

**Archivo:** `startup.sh:58`

```bash
exec gunicorn \
    --timeout 0 \        # ← Sin timeout para workers
    --workers 1 \
    --threads 8 \
```

Con `timeout 0`, un worker que se cuelgue (query lenta, deadlock, loop infinito) nunca será reciclado. Con solo **1 worker**, esto significa que toda la aplicación se congela indefinidamente.

**Impacto:** Un solo request problemático puede dejar la app inaccesible para todas las clínicas hasta que Cloud Run mate el contenedor.

**Fix:** Usar un timeout razonable:
```bash
--timeout 120 \
--graceful-timeout 30 \
```

---

## CRITICAL - Datos incorrectos o pérdida de datos

### C1. Timezone: comparaciones `datetime.now()` vs datos UTC en BD

**Archivos afectados:**
- `routes/tickets.py:378, 452, 562, 642`
- `routes/visualizador.py:41`
- `routes/dashboard.py:17`

**Problema:** La BD almacena timestamps con `datetime.utcnow()` (models.py:57), pero las comparaciones de estado usan `datetime.now()` (hora local del servidor):

```python
# models.py - se guarda en UTC
created_at = db.Column(db.DateTime, default=datetime.utcnow)

# routes/tickets.py:378 - se compara con hora local
ticket.is_scheduled = datetime.now() < ticket.pavilion_end_time

# routes/tickets.py:452 - misma inconsistencia
ticket.is_scheduled = (datetime.now() < admission_time)
```

**Impacto real:** Depende de la timezone del servidor en Cloud Run. Si el servidor usa UTC (lo más probable en Cloud Run), `datetime.now()` == `datetime.utcnow()` y no hay problema inmediato. **Pero** si alguien configura `TZ=America/Santiago` en el container, todas las transiciones de estado se desplazan 3-4 horas.

**Preguntas:**
1. Los `pavilion_end_time` que ingresan los usuarios, ¿están en hora Chile o UTC? Si los usuarios ingresan "14:00" pensando en hora Chile pero se almacena como UTC, hay 3-4 horas de desfase.
2. ¿El filtro `datetime_local` (app.py:125-131) que convierte UTC→Chile se aplica consistentemente en todos los templates?

**Recomendación:** Definir explícitamente si la app trabaja en "naive local" o "aware UTC". Lo más limpio: almacenar todo en UTC y convertir al mostrar (que es lo que el filtro `datetime_local` intenta hacer), pero asegurar que los inputs del usuario también se conviertan.

### C2. Race condition en `PatientRepository.get_or_create()`

**Archivo:** `repositories/patient_repository.py:25-42`

```python
patient = PatientRepository.get_by_rut(rut, clinic_id)  # Check
if patient:
    return patient, False
patient = Patient(rut=rut, clinic_id=clinic_id)          # Create
db.session.add(patient)
return patient, True
```

Existe un unique constraint `uq_patient_rut_clinic` en la BD. Dos requests concurrentes con el mismo RUT pueden ambos pasar el check y fallar con `IntegrityError` no manejado.

**Escenario probable:** Dos enfermeras ingresan tickets para el mismo paciente al mismo tiempo. Una de las dos recibe error 500.

**Fix:**
```python
try:
    db.session.add(patient)
    db.session.flush()
except IntegrityError:
    db.session.rollback()
    patient = PatientRepository.get_by_rut(rut, clinic_id)
    return patient, False
```

### C3. Inconsistencia en cálculo de estado (`is_scheduled`)

**Archivos:**
- `routes/tickets.py:378` — Usa `datetime.now() < ticket.pavilion_end_time`
- `routes/tickets.py:452` — Usa `datetime.now() < admission_time` (calculado de pavilion_end_time)
- `routes/tickets.py:562` — Usa `datetime.now() < ticket.pavilion_end_time`

Tres vistas diferentes calculan `is_scheduled` de forma distinta. La vista de nursing board (línea 452) usa `admission_time` (2h antes de pavilion_end_time), mientras que las otras usan `pavilion_end_time` directamente.

**Impacto:** Un mismo ticket puede aparecer como "Programado" en el tablero de enfermería pero como "Activo" en la lista de tickets, durante el período de 2 horas antes de cirugía.

**Recomendación:** Centralizar el cálculo de estado en el modelo `Ticket` o en un servicio, usando una sola fuente de verdad.

---

## HIGH - Riesgos significativos

### H1. `RESET_DB_ON_STARTUP` puede borrar producción

**Archivo:** `startup.sh:23-34`

```bash
if [ "$RESET_DB_ON_STARTUP" = "true" ]; then
    flask reset-db 2>&1 || echo "Advertencia: Error en reset-db"
fi
```

Si alguien configura `RESET_DB_ON_STARTUP=true` en las variables de entorno de producción (por error de copiar config de QA), toda la base de datos se borra al siguiente deploy.

**Recomendación:** Agregar validación de entorno:
```bash
if [ "$RESET_DB_ON_STARTUP" = "true" ] && [ "$ENVIRONMENT" = "production" ]; then
    echo "ERROR: RESET_DB_ON_STARTUP no permitido en producción!"
    exit 1
fi
```

### H2. Migraciones fallan silenciosamente en startup

**Archivo:** `startup.sh:39`

```bash
flask db upgrade 2>/dev/null || echo "Advertencia: No se pudieron aplicar todas las migraciones"
```

Stderr se redirige a `/dev/null` y los errores solo producen un warning. La app arranca con un schema potencialmente incompleto.

**Impacto:** Si una migración falla (ej: constraint ya existe, timeout), la app arranca pero crashea al usar las tablas/columnas que la migración debía crear.

**Fix:** No redirigir stderr, y considerar `set -e` con trap para las migraciones:
```bash
flask db upgrade 2>&1 || { echo "ERROR: Migraciones fallaron"; exit 1; }
```

### H3. Exposición de errores internos al usuario

**Archivo:** `routes/tickets.py:310`

```python
except Exception as e:
    db.session.rollback()
    flash(f'Error al modificar FPA: {str(e)}', 'error')
```

`str(e)` puede contener stack traces, nombres de tablas, queries SQL, etc. Este patrón se repite en múltiples rutas.

**Recomendación:** Loggear el error completo server-side, mostrar mensaje genérico al usuario:
```python
except Exception as e:
    db.session.rollback()
    current_app.logger.error(f'Error modificando FPA ticket {ticket_id}: {e}', exc_info=True)
    flash('Error al modificar FPA. Contacte al administrador.', 'error')
```

### H4. `check_password()` hace commit dentro del método

**Archivo:** `models.py:63-69`

```python
def check_password(self, password):
    if not self.password.startswith('scrypt:') and not self.password.startswith('pbkdf2:'):
        if self.password == password:
            self.set_password(password)
            db.session.commit()  # ← Commit durante autenticación
            return True
```

Un commit dentro de un método que parece ser de solo lectura puede causar side-effects inesperados si hay cambios pendientes en la sesión de SQLAlchemy.

**Pregunta:** ¿Todavía existen usuarios con contraseñas en texto plano en la BD? Si ya se migraron todos, este código se puede simplificar.

### H5. Overnight stays se calcula con dos fórmulas diferentes

**Ubicaciones:**
1. `services/fpa_calculator.py:78-79`: `(fpa.date() - admission_time.date()).days`
2. `routes/tickets.py:299-303`: `time_diff.days + (1 if time_diff.seconds > 0)`
3. `services/ticket_service.py:72-75`: Misma fórmula que tickets.py

Las fórmulas 1 y 2 pueden dar resultados distintos para el mismo caso. Ejemplo:
- Pavilion end: 16 Feb 22:00, FPA: 17 Feb 06:00
- Fórmula 1 (dates): `17 Feb - 16 Feb = 1 día`
- Fórmula 2 (timedelta): `timedelta = 8h → days=0, seconds=28800 → 0 + 1 = 1` ← coincide
- Pero con: Pavilion end: 16 Feb 10:00, FPA: 18 Feb 10:00
- Fórmula 2: `timedelta = 2 days, seconds=0 → 2 + 0 = 2`
- Fórmula 1 (con admission): depende de admission_time

**Recomendación:** Centralizar el cálculo en un solo lugar (FPACalculator) y usarlo siempre.

---

## MEDIUM - Deberían corregirse pronto

### M1. Nursing board carga TODOS los tickets sin paginación

**Archivo:** `routes/tickets.py:436`

```python
tickets = query.all()  # Sin límite
```

A diferencia de la vista de lista (que sí pagina, línea 373), el nursing board carga todos los tickets. Con varias clínicas operando durante meses, esto degradará el rendimiento progresivamente.

### M2. `console.log` en código de producción

**Archivos:**
- `templates/admin/export_confirmation.html:29` — Loguea email del usuario
- `templates/tickets/create.html:422`
- `templates/tickets/nursing_board.html` — 3 ocurrencias
- `static/js/tickets.js:383`

El de `export_confirmation.html` es el más preocupante porque expone el email del usuario actual en la consola del browser.

### M3. Credenciales demo visibles en login.html

**Archivo:** `templates/login.html:106-150`

La sección de credenciales demo está condicionada a `config.ENVIRONMENT == 'local'`, lo cual es correcto. Sin embargo, verificar que la variable `ENVIRONMENT` esté correctamente configurada en producción es crítico — si falta, el default es `'local'` (config.py:7).

**Pregunta:** ¿`ENVIRONMENT` está configurado como variable de entorno en Cloud Run? Si no, el default `'local'` habilitaría el demo login y mostraría las credenciales.

### M4. Sin custom error handler para errores 500

No hay `@app.errorhandler(500)` definido. Si ocurre un error no manejado, Flask mostrará su página de error por defecto (que en modo debug incluye el debugger interactivo).

### M5. `is_superuser` property cachea falsos negativos

**Archivo:** `models.py:82-99`

Si la query a la tabla `Superuser` falla (timeout, conexión caída), el resultado `False` se cachea en `_is_superuser` y no se reintenta en la misma request. Un superusuario podría perder acceso temporalmente sin ningún log de error visible.

### M6. Urgency thresholds hardcodeados en nursing board

**Archivo:** `routes/tickets.py:460-466`

```python
if total_hours <= 1:
    ticket.urgency_level = 'critical'
elif total_hours <= 6:
    ticket.urgency_level = 'warning'
```

Los valores 1 y 6 horas están hardcodeados, a pesar de que existe un modelo `UrgencyThreshold` configurable en la BD. La configuración de umbrales solo se carga en el frontend (JavaScript) pero el backend usa valores fijos.

### M7. Restaurar ticket borra datos de anulación

**Archivo:** `services/ticket_service.py:205-208`

```python
ticket.annulled_at = None
ticket.annulled_by = None
ticket.annulled_reason = None
```

Al restaurar un ticket, se pierden los datos de quién lo anuló y por qué. Solo queda en el audit log. Sería mejor mantener estos campos y usar un flag `is_restored`.

### M8. Sin validación de formato RUT en backend

**Archivo:** `validators/ticket_validator.py`

El RUT se formatea en el frontend (JavaScript) pero no se valida su formato/dígito verificador en el backend. Un request directo al API podría insertar RUTs inválidos.

---

## LOW - Mejoras recomendadas

### L1. `.env` en el repositorio

El archivo `.env` está committed en git con `SECRET_KEY=local-dev-key`. Aunque es un valor de desarrollo, la buena práctica es solo tener `.env.example` y que cada entorno tenga su propio `.env`.

### L2. `print()` en config.py

Las líneas 14, 20, 22 de `config.py` usan `print()` en vez del logger de Flask. En producción estos prints van a stdout de Gunicorn pero sin formato de log estructurado.

### L3. Import dentro de loop

**Archivo:** `routes/tickets.py:446`

```python
for ticket in tickets:
    from services.fpa_calculator import FPACalculator  # Import en cada iteración
```

Python cachea imports, así que no hay impacto funcional, pero es un code smell que indica acoplamiento que se intentó evitar.

### L4. Single worker en Gunicorn

**Archivo:** `startup.sh:56`

```bash
--workers 1 \
--threads 8 \
```

Con 1 worker y 8 threads, el GIL de Python limita el paralelismo real para operaciones CPU-bound. Para Cloud Run con múltiples clínicas concurrentes, considerar 2-4 workers (dependiendo de la RAM del container).

### L5. CSP permite `unsafe-inline` y `unsafe-eval`

**Archivo:** `app.py:176`

Necesario para Chart.js y scripts inline en templates, pero debilita la protección CSP. A futuro, migrar scripts inline a archivos separados y usar nonces.

---

## Preguntas para el equipo

Antes de ir a producción, sería bueno clarificar:

1. **Timezone de los datos:** Cuando un usuario ingresa "14:00" como hora de fin de pabellón, ¿eso es hora Chile (CLT/CLST) o se asume UTC? Esto determina si C1 es un problema real o no.

2. **Contraseñas legacy:** ¿Existen todavía usuarios con contraseñas en texto plano? (relevante para H4). Si todos usan IAP en producción, el login con contraseña quizás no se usa.

3. **Variable ENVIRONMENT en Cloud Run:** ¿Está configurada como `production`? Si no, el default `local` habilitaría demo login y deshabilitaría security headers.

4. **Volumen esperado:** ¿Cuántos tickets por clínica por día? ¿Cuántas clínicas? Esto determina la urgencia de M1 (paginación) y L4 (workers).

5. **Flujo de deploy:** ¿Hay un pipeline CI/CD que corra los tests antes de desplegar? ¿Se probó que `flask db upgrade` funcione correctamente contra la BD de producción?

6. **Backup de BD:** ¿Hay backups automáticos configurados en Cloud SQL? Especialmente relevante por H1 (RESET_DB_ON_STARTUP).

7. **Monitoreo:** ¿Hay alertas configuradas para errores 500, latencia alta, o uso de memoria? Con 1 worker, un memory leak sería fatal.

---

## Checklist pre-producción

- [ ] **B1:** Agregar extracción de `reason` y `justification` en `update_fpa()`
- [ ] **B2:** Cambiar `--timeout 0` a `--timeout 120` en startup.sh
- [ ] **C1:** Verificar comportamiento de timezone en Cloud Run y documentar decisión
- [ ] **C2:** Agregar manejo de `IntegrityError` en `get_or_create()`
- [ ] **C3:** Centralizar cálculo de `is_scheduled` en un solo lugar
- [ ] **H1:** Bloquear `RESET_DB_ON_STARTUP` en producción
- [ ] **H2:** No silenciar errores de migración en startup
- [ ] **H3:** Sanitizar mensajes de error (no exponer `str(e)`)
- [ ] **M3:** Verificar que `ENVIRONMENT=production` esté en Cloud Run
- [ ] **M4:** Agregar error handler para 500
- [ ] Confirmar que backup automático está activo en Cloud SQL
- [ ] Correr suite de tests completa (`pytest`) contra la BD de producción (schema)
- [ ] Revisar que las 17 migraciones aplican limpiamente sobre una BD vacía
- [ ] Probar el flujo completo: crear ticket → modificar FPA → anular → restaurar
