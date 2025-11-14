# 📝 Instrucciones para Crear los Issues en GitHub

He creado 3 archivos markdown con issues detallados para que los revises y luego los crees manualmente en GitHub.

## 📋 Issues Preparados

### Issue #40: Bug - FPA indicado por médico no se respeta
- **Archivo**: `ISSUE_40_fpa_medico_no_respetado.md`
- **Prioridad**: 🔴 ALTA
- **Tipo**: Bug crítico en lógica de negocio
- **Descripción**: El sistema captura el campo `medical_discharge_date` pero no lo usa para establecer el FPA del ticket

### Issue #41: Bug - Previsualización muestra solo FPA calculado
- **Archivo**: `ISSUE_41_previsualizacion_fpa_medico.md`
- **Prioridad**: 🟡 MEDIA-ALTA
- **Tipo**: Bug de UX en formulario de creación
- **Descripción**: El panel de previsualización no muestra el FPA que indicó el médico, solo el calculado

### Issue #42: Bug - Fecha incorrecta en modificación de FPA
- **Archivo**: `ISSUE_42_fecha_defecto_modificacion_fpa.md`
- **Prioridad**: 🟡 MEDIA
- **Tipo**: Bug de UX en formulario de modificación
- **Descripción**: El campo de fecha aparece con fecha de cirugía en vez del FPA actual

---

## 🔧 Cómo Crear los Issues en GitHub

### Método 1: Copiar y Pegar (Recomendado)

1. **Abre cada archivo markdown** en tu editor
2. **Copia todo el contenido** del archivo
3. **Ve a GitHub**: https://github.com/jona-mhw/ticket-2/issues/new
4. **Pega el contenido** en el campo de descripción
5. **Ajusta el título** si es necesario (primera línea del markdown sin el `#`)
6. **Agrega labels manualmente**:
   - Issue #40: `bug`, `priority: high`, `backend`, `business-logic`
   - Issue #41: `bug`, `ux`, `frontend`, `priority: medium-high`
   - Issue #42: `bug`, `ux`, `frontend`, `priority: medium`
7. **Haz clic en "Submit new issue"**

### Método 2: Usando GitHub CLI (si tienes `gh` instalado)

```bash
# Issue #40
gh issue create --title "Bug: FPA indicado por médico no se respeta - sistema usa siempre FPA calculado" \
  --body-file ISSUE_40_fpa_medico_no_respetado.md \
  --label "bug,priority: high,backend,business-logic"

# Issue #41
gh issue create --title "Bug: Previsualización de FPA muestra solo cálculo automático, no el FPA indicado por médico" \
  --body-file ISSUE_41_previsualizacion_fpa_medico.md \
  --label "bug,ux,frontend,priority: medium-high"

# Issue #42
gh issue create --title "Bug: Formulario de modificación FPA muestra fecha incorrecta por defecto" \
  --body-file ISSUE_42_fecha_defecto_modificacion_fpa.md \
  --label "bug,ux,frontend,priority: medium"
```

---

## ✅ Validación Antes de Crear

Por favor revisa cada archivo y valida:

- [ ] La descripción del problema es precisa
- [ ] El análisis técnico identifica correctamente los archivos afectados
- [ ] La solución propuesta tiene sentido
- [ ] Los criterios de aceptación son claros y medibles
- [ ] La prioridad asignada es correcta

---

## 📊 Próximos Pasos

Una vez que crees los issues en GitHub:

1. **Avísame los números de los issues** que se crearon (ej: #40, #41, #42)
2. **Indícame cuál quieres resolver primero**
3. **Yo procederé a implementar la solución**
4. **Al finalizar, te indicaré que crees el PR desde el menú de Claude Code Web**

---

## 🎯 Orden de Implementación Sugerido

1. **Issue #40** (ALTA prioridad) - Es el más crítico, afecta la funcionalidad core
2. **Issue #41** (MEDIA-ALTA) - Mejora la UX y se relaciona con #40
3. **Issue #42** (MEDIA) - Mejora incremental de UX

Alternativamente, podríamos resolverlos todos juntos en un solo PR si prefieres.
