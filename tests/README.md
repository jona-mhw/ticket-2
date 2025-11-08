# 🧪 Tests de Ticket Home

Suite de tests completa con pytest para garantizar calidad y prevenir regresiones.

## 📁 Estructura

```
tests/
├── conftest.py              # Fixtures compartidos (DB, usuarios, clínicas)
├── test_models.py           # Tests de los 13 modelos
├── test_fpa_logic.py        # Tests del cálculo FPA (CRÍTICO)
├── test_auth.py             # Tests de autenticación
└── README.md                # Esta documentación
```

## 🚀 Ejecutar Tests

### Instalar dependencias

```bash
pip install -r requirements.txt
```

### Correr todos los tests

```bash
pytest
```

### Correr tests con coverage

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

Luego abre `htmlcov/index.html` para ver el reporte visual.

### Correr tests específicos

```bash
# Solo tests de modelos
pytest tests/test_models.py

# Solo tests del cálculo FPA
pytest tests/test_fpa_logic.py

# Solo tests de autenticación
pytest tests/test_auth.py

# Tests con un marker específico
pytest -m fpa
pytest -m auth
pytest -m unit
```

### Correr un test específico

```bash
pytest tests/test_fpa_logic.py::TestFPACalculation::test_ambulatory_before_cutoff
```

### Modo verbose

```bash
pytest -v
```

### Ver print statements

```bash
pytest -s
```

## 📊 Coverage Objetivo

**Meta: >80% de coverage**

Áreas críticas con 100% coverage:
- ✅ Cálculo de FPA (`models.py:Ticket.calculate_fpa`)
- ✅ Modelos principales (User, Ticket, Patient, etc.)
- ✅ Autenticación híbrida

## 🏷️ Markers Disponibles

Los tests están organizados con markers:

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.fpa` - Tests del cálculo FPA (crítico)
- `@pytest.mark.auth` - Tests de autenticación
- `@pytest.mark.slow` - Tests que tardan más

### Usar markers

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests FPA
pytest -m fpa

# Excluir tests lentos
pytest -m "not slow"
```

## 🔧 Fixtures Disponibles

Definidos en `conftest.py`:

### Básicos
- `app` - Aplicación Flask configurada para testing
- `client` - Cliente de test HTTP
- `db_session` - Sesión de base de datos limpia

### Usuarios
- `sample_user_admin` - Usuario administrador
- `sample_user_clinical` - Usuario clínico
- `sample_user_visualizador` - Usuario solo lectura
- `sample_user_super` - Superusuario global

### Datos
- `sample_clinic` - Clínica de prueba
- `sample_specialty` - Especialidad médica
- `sample_surgery_normal` - Cirugía con estadía nocturna
- `sample_surgery_ambulatory` - Cirugía ambulatoria con cutoff
- `sample_doctor` - Doctor de prueba
- `sample_patient` - Paciente de prueba
- `sample_ticket` - Ticket completo de prueba
- `sample_discharge_slots` - 12 bloques horarios de alta
- `sample_reasons` - Razones estandarizadas

### Autenticación
- `authenticated_client` - Cliente con usuario autenticado

## 🎯 Casos de Prueba Críticos

### FPA Calculation (test_fpa_logic.py)

1. **Cirugía ambulatoria antes del cutoff**
   - Pabellón termina antes de 14:00 → alta día siguiente 8:00 AM

2. **Cirugía ambulatoria después del cutoff**
   - Pabellón termina después de 14:00 → cálculo normal

3. **Cirugía con estadía nocturna**
   - 24h, 48h, etc. → cálculo correcto de días

4. **Casos edge**
   - Medianoche
   - Cambio de año
   - Cirugías muy cortas (1h)
   - Cirugías muy largas (120h)

### Multi-tenancy (test_auth.py)

1. Usuario solo ve datos de su clínica
2. Superuser ve todas las clínicas
3. Isolation entre clínicas

### Autenticación (test_auth.py)

1. Login tradicional (DEV)
2. IAP authentication (QA/PROD)
3. Auto-creación de superusers desde IAP headers

## 📝 Escribir Nuevos Tests

### Template básico

```python
import pytest

@pytest.mark.unit
def test_mi_funcionalidad(db_session, sample_clinic):
    # Arrange
    dato = crear_dato()

    # Act
    resultado = hacer_algo(dato)

    # Assert
    assert resultado == esperado
```

### Usar fixtures

```python
def test_con_fixtures(db_session, sample_user_admin, sample_ticket):
    # Los fixtures están disponibles automáticamente
    assert sample_ticket.created_by == 'test_user'
```

### Parametrize tests

```python
@pytest.mark.parametrize('input,expected', [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiple_cases(input, expected):
    assert input * 2 == expected
```

## 🐛 Debugging Tests

### Usar pdb (debugger)

```python
def test_con_debug(db_session):
    import pdb; pdb.set_trace()
    # El test se pausará aquí
```

### Ver output SQL

Modificar `conftest.py` temporalmente:

```python
app.config['SQLALCHEMY_ECHO'] = True
```

## ✅ Checklist antes de Commit

- [ ] Todos los tests pasan: `pytest`
- [ ] Coverage >80%: `pytest --cov`
- [ ] Sin warnings: `pytest --strict-warnings`
- [ ] Tests nuevos para funcionalidad nueva
- [ ] Tests actualizados si cambiaste código existente

## 📚 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [Testing Flask Apps](https://flask.palletsprojects.com/en/latest/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
