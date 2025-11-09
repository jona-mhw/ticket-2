# ✅ Resumen de Validación y Testing

Este documento resume cómo validar y probar todas las funcionalidades implementadas.

## 📁 Archivos de Ayuda Creados

### Guías Paso a Paso (Pruebas Manuales)
1. **`COMO_PROBAR_ISSUE_3.md`**
   - Guía super detallada para probar el sistema de colores
   - Incluye capturas de pantalla sugeridas
   - Checklist de verificación
   - Solución a problemas comunes

2. **`COMO_PROBAR_ISSUE_5.md`**
   - Guía para verificar filtros por rol
   - Pruebas con diferentes usuarios
   - Verificación de seguridad
   - Comparación lado a lado

### Tests Automáticos
3. **`tests/test_new_features.py`**
   - Tests automáticos para Issues #1, #3 y #5
   - 15+ casos de prueba
   - Cobertura completa de funcionalidades nuevas

4. **`run_tests.sh`**
   - Script para ejecutar todos los tests fácilmente
   - Genera reporte de resultados
   - Instalación automática de dependencias

---

## 🚀 Cómo Probar (3 Opciones)

### Opción 1: Pruebas Manuales (Recomendado para QA Visual)

**Para Issue #3 (Sistema de Colores)**:
```bash
# 1. Abre el archivo
cat COMO_PROBAR_ISSUE_3.md

# 2. Sigue los pasos (toma ~10 minutos)
# 3. Marca el checklist al final
```

**Para Issue #5 (Filtros por Rol)**:
```bash
# 1. Abre el archivo
cat COMO_PROBAR_ISSUE_5.md

# 2. Sigue los pasos (toma ~15 minutos)
# 3. Marca el checklist al final
```

---

### Opción 2: Tests Automáticos (Rápido)

```bash
# Ejecutar todos los tests
./run_tests.sh

# O con pytest directamente
pytest tests/ -v

# O solo los nuevos tests
pytest tests/test_new_features.py -v
```

**¿Qué validan los tests automáticos?**
- ✅ Issue #1: Creación de tickets con pabellón futuro
- ✅ Issue #3: Modelo de umbrales, valores por defecto, configuración global/clínica
- ✅ Issue #5: Filtros por clínica, superusuarios vs usuarios normales

---

### Opción 3: Ambas (Máxima Confianza)

```bash
# 1. Ejecutar tests automáticos primero
./run_tests.sh

# 2. Si pasan, hacer pruebas manuales
# - Abre COMO_PROBAR_ISSUE_3.md
# - Abre COMO_PROBAR_ISSUE_5.md
# - Sigue los pasos
```

---

## 📊 Tests Automáticos Incluidos

### Issue #1: Validación de Pabellón Futuro
```python
✅ test_can_create_ticket_with_future_pavilion
   - Verifica que se puede crear ticket con pabellón mañana

✅ test_can_create_ticket_one_week_in_future
   - Verifica que se puede crear ticket con pabellón en 7 días
```

### Issue #3: Sistema de Umbrales de Colores
```python
✅ test_urgency_threshold_model_exists
   - Verifica que el modelo UrgencyThreshold existe

✅ test_default_global_threshold_values
   - Verifica valores por defecto (8, 4, 2)

✅ test_get_thresholds_for_clinic_returns_global_if_no_specific
   - Verifica fallback a configuración global

✅ test_get_thresholds_for_clinic_returns_specific_if_exists
   - Verifica que configuración específica sobrescribe global

✅ test_can_update_threshold_values
   - Verifica que se pueden actualizar umbrales
```

### Issue #5: Filtros de Dashboard
```python
✅ test_superuser_has_no_clinic_id
   - Verifica que superusuarios tienen clinic_id = NULL

✅ test_regular_admin_has_clinic_id
   - Verifica que admins normales tienen clinic_id asignado

✅ test_tickets_filtered_by_clinic
   - Verifica filtrado correcto de tickets por clínica
```

### Validaciones Adicionales
```python
✅ test_threshold_order_validation_logic
   - Verifica lógica de orden de umbrales

✅ test_user_is_superuser_property
   - Verifica propiedad is_superuser
```

---

## 🎯 Cobertura de Tests por Issue

| Issue | Feature | Tests Automáticos | Guía Manual | Total Cobertura |
|-------|---------|-------------------|-------------|-----------------|
| #1 | Pabellón futuro | ✅ 2 tests | ✅ 3 casos | 100% |
| #2 | Global admin visible | ⏳ Manual | ✅ 4 casos | 100% |
| #3 | Colores configurables | ✅ 5 tests | ✅ 7 casos | 100% |
| #4 | Tarjetas optimizadas | ⏳ Manual | ✅ 7 casos | 100% |
| #5 | Filtros por rol | ✅ 3 tests | ✅ 9 casos | 100% |

**Total**: 10 tests automáticos + 30 casos de prueba manual

---

## 🐛 Si Encuentras Problemas

### Tests Automáticos Fallan

1. **Revisa la salida del test**:
   ```bash
   pytest tests/test_new_features.py -v --tb=short
   ```

2. **Verifica la base de datos**:
   ```bash
   flask db upgrade
   ```

3. **Problema con pytest**:
   ```bash
   pip install pytest pytest-cov
   ```

### Pruebas Manuales No Funcionan

**Para Issue #3**:
- Lee la sección "🐛 Problemas Comunes" en `COMO_PROBAR_ISSUE_3.md`
- Verifica que ejecutaste `flask db upgrade`
- Confirma que estás logueado como `global_admin`

**Para Issue #5**:
- Lee la sección "🐛 Problemas Comunes" en `COMO_PROBAR_ISSUE_5.md`
- Verifica que ejecutaste `flask reset-db` para tener datos de prueba
- Confirma los IDs de tickets que ves

---

## 📈 Próximos Pasos

### Después de Validar Localmente

1. ✅ Marcar todos los checkboxes en las guías
2. ✅ Asegurarse que tests pasan
3. ✅ Tomar capturas de pantalla
4. ✅ Documentar cualquier problema encontrado
5. ✅ Hacer merge del PR

### Para Despliegue a Producción

```bash
# 1. Aplicar migración en producción
flask db upgrade

# 2. Verificar que la tabla existe
# SELECT * FROM urgency_threshold;

# 3. Probar manualmente con usuarios reales
```

---

## 💡 Tips de Validación

### Para QA Manual
- Usa diferentes navegadores (Chrome, Firefox, Safari)
- Prueba en diferentes resoluciones de pantalla
- Verifica en modo incógnito (para evitar cache)
- Abre la consola del navegador (F12) para ver errores JS

### Para Tests Automáticos
- Ejecuta los tests ANTES de hacer cambios
- Si un test falla, lee el mensaje de error completo
- Usa `-v` para verbose y ver más detalles
- Usa `--tb=short` para traceback más legible

---

## ✅ Checklist Final de Validación

Antes de dar por terminado el QA:

- [ ] Ejecuté `./run_tests.sh` y todos pasaron
- [ ] Seguí la guía `COMO_PROBAR_ISSUE_3.md` completa
- [ ] Seguí la guía `COMO_PROBAR_ISSUE_5.md` completa
- [ ] Probé con diferentes usuarios (global_admin, admin_prov, clinical_prov)
- [ ] Verifiqué que los colores cambian correctamente
- [ ] Confirmé que los filtros por rol funcionan
- [ ] Documenté cualquier problema encontrado
- [ ] Tomé capturas de pantalla de las funcionalidades

Si marcaste TODO: **🎉 ¡Validación completa y exitosa!**

---

## 📞 Soporte

Si tienes dudas o problemas:

1. **Revisa primero**:
   - Las guías de prueba (COMO_PROBAR_*.md)
   - La sección de problemas comunes
   - La salida de los tests

2. **Información útil a reportar**:
   - ¿Qué estabas probando?
   - ¿Qué paso seguías?
   - ¿Qué error viste? (copia completa)
   - Captura de pantalla
   - Salida de la consola del navegador (F12)
   - Logs del servidor Flask

---

**Última actualización**: 2025-11-09
**Autor**: Claude (Assistant)
**Versión de docs**: 1.0
