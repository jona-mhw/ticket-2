# 🤖 Instructivo: Claude Code Web - Trabajar con Ticket Home

**Propósito**: Guía para que Claude Code Web retome el proyecto Ticket Home en nuevas sesiones desde cero.

**Última actualización**: 2025-01-09
**Versión**: v0.1.4

---

## 📋 Contexto del Proyecto

**Ticket Home** es un sistema de gestión de Fechas Programadas de Alta (FPA) para RedSalud Chile, desarrollado en Flask/Python y desplegado en GCP Cloud Run.

### Stack Tecnológico

- **Backend**: Flask 2.3.3, Python 3.11 (dev) / 3.13+ (producción)
- **Base de datos**: PostgreSQL 17 (Cloud SQL en GCP)
- **ORM**: SQLAlchemy 3.0.5 con Flask-SQLAlchemy
- **Testing**: pytest 7.4.3, pytest-flask, pytest-cov
- **Autenticación**: IAP (Identity-Aware Proxy) de Google + fallback tradicional
- **Deploy**: GCP Cloud Run (serverless)
- **CI/CD**: GitHub Actions

### Características Clave

- **Multi-tenancy**: Cada clínica tiene datos aislados por `clinic_id`
- **Roles**: Superuser, Admin, Clinical, Visualizador
- **Lógica crítica**: Cálculo de FPA (ambulatoria vs normal, cutoff hours)
- **Auditoría**: LoginAudit y ActionAudit con multi-tenancy

---

## 🎯 Primer Paso: Exploración Inicial

Cuando inicies una nueva sesión de Claude Code Web, **SIEMPRE** empieza con estos pasos:

### 1. Leer la Estructura del Proyecto

```bash
# Examina los archivos clave primero
cat README.md                          # Visión general del proyecto
cat _docs/ARCHITECTURE.md              # Arquitectura técnica (si existe)
cat requirements.txt                   # Dependencias Python
```

### 2. Explorar Carpetas Especiales con `_`

El proyecto usa prefijo `_` para carpetas especiales:

```
_config/           → Backups de configuración GCP (app.yaml, etc.)
_deployment_scripts/ → Scripts de deploy manual a DEV/QA
_docs/             → Documentación técnica
_next_project/     → Framework para replicar arquitectura
```

**Comando para explorar**:
```bash
ls -la | grep "^d.*_"
```

### 3. Entender el Código Principal

**Archivos críticos a revisar**:

| Archivo | Propósito | Líneas clave |
|---------|-----------|--------------|
| `app.py` | Factory de aplicación Flask | L109-123 (app factory) |
| `models.py` | Todos los modelos ORM (13 modelos) | L1-286 (completo) |
| `routes/utils.py` | Queries optimizadas con eager loading | L31-36 (joinedload) |
| `commands.py` | CLI commands (crear tickets, seed DB) | L56-708 (commands) |
| `config.py` | Configuración por entorno | Todo el archivo |

### 4. Revisar Tests Existentes

```bash
# Ver estructura de tests
ls tests/

# Archivos esperados:
# - conftest.py           → Fixtures compartidos
# - test_models.py        → Tests de modelos (23 tests)
# - test_auth.py          → Tests de autenticación (14 tests)
# - test_fpa_logic.py     → Tests de FPA (12 tests) ⚠️ CRÍTICO
# - test_audit_logs.py    → Tests de auditoría (11 tests)
```

### 5. Ejecutar Tests para Validar Entorno

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Esperado: 60/60 tests passed
# Coverage en models.py: ~94%
```

---

## 🔍 Cómo Convertirte en Experto del Proyecto

### Paso 1: Leer Documentación de Sesiones Anteriores

El proyecto tiene documentación generada de sesiones previas:

```bash
# Leer resúmenes de implementaciones anteriores
cat RESUMEN_SESION_COMPLETA.html          # Resumen visual completo
cat REDIS_CACHE_IMPLEMENTATION.md         # Guía de Redis (pendiente)
cat PERFORMANCE_OPTIMIZATIONS.md          # Optimizaciones de queries
cat EXPLICACION_LOGS_PERFIL.html          # Explicación Issue #8
```

### Paso 2: Entender la Lógica de Negocio Crítica

**FPA (Fecha Programada de Alta)** es el corazón del sistema:

```python
# En models.py, clase Ticket
def calculate_fpa(self, pavilion_end, surgery):
    """
    Calcula FPA basada en:
    - Cirugía ambulatoria vs normal
    - Cutoff hour (hora límite para alta mismo día)
    - Base stay hours
    """
```

**Casos críticos a entender**:
1. Cirugía ambulatoria ANTES de cutoff → Alta al día siguiente a las 8 AM
2. Cirugía ambulatoria DESPUÉS de cutoff → Cálculo normal (pavilion_end + stay_hours)
3. Cirugía normal → Siempre pavilion_end + stay_hours

**Tests de FPA**: `tests/test_fpa_logic.py` documenta todos los escenarios.

### Paso 3: Entender Multi-Tenancy

**Reglas de isolation**:

| Perfil | clinic_id | Qué puede ver |
|--------|-----------|---------------|
| Superuser | `NULL` | TODO (todas las clínicas) |
| Admin | `1` (ej: Providencia) | Solo clínica 1 |
| Clinical | `2` (ej: Vitacura) | Solo clínica 2 |
| Visualizador | `3` (ej: Elqui) | Solo clínica 3, read-only |

**Código de referencia**:
```python
# Filtrado automático por clínica (routes/utils.py)
if current_user.clinic_id:
    query = query.filter(Ticket.clinic_id == current_user.clinic_id)
```

### Paso 4: Conocer las Optimizaciones Existentes

**N+1 Prevention** (routes/utils.py L31-36):
```python
query = Ticket.query.options(
    joinedload(Ticket.patient),
    joinedload(Ticket.surgery).joinedload(Surgery.specialty),
    joinedload(Ticket.attending_doctor),
    joinedload(Ticket.discharge_time_slot)
)
```

**Resultado**: 152 queries → 1 query (96% reducción)

---

## 🛠️ Trabajar en Nuevas Issues

### Flujo de Trabajo Estándar

1. **Crear branch desde rama actual**:
   ```bash
   # Verifica branch actual
   git status

   # El branch siempre debe empezar con 'claude/' y terminar con session ID
   # Ejemplo: claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F
   ```

2. **Leer la Issue en GitHub** (o archivo `.github/ISSUES_TO_CREATE.md`):
   ```bash
   # Si la issue está documentada localmente
   cat .github/ISSUES_TO_CREATE.md
   ```

3. **Planificar con TodoWrite**:
   ```
   Siempre usa la herramienta TodoWrite para:
   - Desglosar la tarea en pasos
   - Trackear progreso
   - Marcar completed INMEDIATAMENTE después de cada paso
   ```

4. **Implementar cambios**:
   - Prefiere **editar** archivos existentes sobre crear nuevos
   - Mantén consistencia con estilo del proyecto
   - Agrega tests SIEMPRE que agregues funcionalidad

5. **Ejecutar tests**:
   ```bash
   # Tests específicos
   pytest tests/test_nombre.py -v

   # Todos los tests
   pytest tests/ -v

   # Con coverage
   pytest tests/ --cov=. --cov-report=term-missing
   ```

6. **Commit con mensaje descriptivo**:
   ```bash
   git add <archivos>
   git commit -m "$(cat <<'EOF'
   tipo: título breve del cambio

   Descripción detallada:
   - Qué cambió
   - Por qué cambió
   - Resultados (tests, coverage)

   Cierra #<issue-number>
   EOF
   )"
   ```

7. **Push al branch**:
   ```bash
   # IMPORTANTE: El branch debe empezar con 'claude/' y terminar con session ID
   git push -u origin <branch-name>
   ```

### Tipos de Commits

- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Solo documentación
- `test:` - Agregar o modificar tests
- `refactor:` - Refactorización sin cambio funcional
- `perf:` - Mejora de performance
- `chore:` - Cambios en build, CI/CD, etc.

---

## 📚 Comandos Útiles del Proyecto

### Flask CLI Commands

```bash
# Crear tablas en DB
flask db upgrade

# Seed data de prueba
flask seed

# Crear ticket manualmente
flask create-ticket

# Ver logs de auditoría
flask audit-report
```

### Testing

```bash
# Tests con markers
pytest -m fpa          # Solo tests de FPA (críticos)
pytest -m auth         # Solo tests de autenticación
pytest -m unit         # Tests unitarios
pytest -m integration  # Tests de integración

# Tests con coverage específico
pytest tests/test_models.py --cov=models --cov-report=html
```

### Git

```bash
# Ver estado actual
git status

# Ver commits recientes con formato legible
git log --oneline --graph -10

# Ver diferencias antes de commit
git diff

# Crear tag (después de merge a main)
git tag -a v0.1.x -m "Descripción del release"
```

---

## ⚠️ Reglas Importantes

### ❌ NO HAGAS

1. **No uses git commands interactivos**: `-i` no funciona (ej: `git rebase -i`, `git add -i`)
2. **No crees archivos innecesarios**: Prefiere editar existentes
3. **No uses emojis** a menos que el usuario lo pida explícitamente
4. **No hagas push a main** directamente (solo a branches `claude/*`)
5. **No modifies .gitignore** sin razón clara
6. **No agregues dependencias** sin verificar compatibilidad (Python 3.13+)

### ✅ SIEMPRE HAGAS

1. **Lee archivos antes de editar**: Usa `Read` tool primero
2. **Ejecuta tests** después de cada cambio
3. **Usa TodoWrite** para tareas complejas (3+ pasos)
4. **Mantén coverage alto**: Objetivo >90% en models.py
5. **Documenta cambios**: Commits descriptivos, código comentado si es complejo
6. **Valida multi-tenancy**: En cualquier query nueva, considera `clinic_id`

---

## 🔧 Troubleshooting Común

### Error: "freezegun compatibility"

```bash
# Solución: Ya está en requirements.txt v1.5.5
pip install freezegun==1.5.5
```

### Error: "403 forbidden" en git push

```bash
# Verifica que el branch empiece con 'claude/' y termine con session ID
git branch
# Debe ser: claude/<nombre>-<session-id>
```

### Tests fallan por DB

```bash
# Verificar que DATABASE_URL esté en sqlite para testing
export DATABASE_URL='sqlite:///:memory:'
pytest tests/
```

### Import errors en tests

```bash
# Asegúrate de estar en el directorio raíz del proyecto
cd /home/user/ticket-2
python -m pytest tests/
```

---

## 📊 Métricas de Calidad Objetivo

| Métrica | Objetivo | Actual (v0.1.4) |
|---------|----------|-----------------|
| Tests passed | 100% | ✅ 60/60 (100%) |
| Coverage models.py | >90% | ✅ 94.58% |
| Coverage total | >40% | ⚠️ 26.93% |
| Tiempo de tests | <15s | ✅ 10.20s |
| N+1 queries | 0 | ✅ Resuelto |

---

## 🎓 Recursos de Referencia

### Documentación Interna

- `_docs/ARCHITECTURE.md` - Arquitectura técnica
- `PERFORMANCE_OPTIMIZATIONS.md` - Guía de optimizaciones
- `REDIS_CACHE_IMPLEMENTATION.md` - Guía de Redis (pendiente implementar)
- `tests/README.md` - Guía de testing

### Documentación Externa

- [Flask Docs](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [pytest Docs](https://docs.pytest.org/)
- [GCP Cloud Run](https://cloud.google.com/run/docs)

---

## 🚀 Checklist de Inicio de Sesión

Cuando empieces una nueva sesión, verifica:

- [ ] He leído este instructivo completo
- [ ] He explorado la estructura del proyecto (`ls -la`)
- [ ] He leído README.md y requirements.txt
- [ ] He revisado carpetas `_*` (config, docs, deployment_scripts)
- [ ] He leído models.py para entender los 13 modelos
- [ ] He ejecutado `pytest tests/` y validado que todo pasa
- [ ] He revisado git status y git log para entender el estado actual
- [ ] He leído la documentación de sesiones anteriores (RESUMEN_SESION_COMPLETA.html, etc.)
- [ ] Entiendo la lógica crítica de FPA
- [ ] Entiendo las reglas de multi-tenancy
- [ ] Estoy listo para trabajar en la nueva issue

---

## 📞 Contacto y Ayuda

- **Desarrollador principal**: Jona (jona-mhw)
- **Repositorio**: https://github.com/jona-mhw/ticket-2
- **Cliente**: RedSalud Chile
- **Propósito**: Gestión de FPA para optimizar altas hospitalarias

---

**Nota final**: Este instructivo se actualiza con cada versión. Verifica siempre la fecha de "Última actualización" al inicio del documento.
