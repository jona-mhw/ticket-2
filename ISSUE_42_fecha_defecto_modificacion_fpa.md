# Bug: Formulario de modificación FPA muestra fecha incorrecta por defecto

## 🐛 Descripción del Problema

Al ingresar al formulario de modificación de FPA de un ticket existente, el campo de fecha muestra la **fecha de cirugía** en lugar de la **FPA actual del ticket**, causando que la diferencia se muestre como negativa ("-X días").

### Comportamiento Actual ❌
- Usuario abre el detalle de un ticket
- Hace clic en "Modificar FPA"
- El campo `new_fpa_date` aparece con la fecha de cirugía (`pavilion_end_time.date()`)
- La vista previa muestra: "Diferencia: **-2 días**" (o el valor negativo correspondiente)
- El usuario debe cambiar manualmente la fecha a la FPA actual para empezar

### Comportamiento Esperado ✅
- Al abrir el formulario de modificación, el campo `new_fpa_date` debe tener **la FPA actual del ticket**
- La vista previa debe mostrar: "Diferencia: **0 días** (sin cambio)"
- El usuario parte desde la FPA actual y la modifica hacia adelante o atrás según necesidad

---

## 🔍 Análisis Técnico

### Archivos Afectados

**`templates/tickets/detail.html` (líneas 550-615)**

El código JavaScript **parece estar correcto**, pero puede haber un problema de inicialización:

```javascript
// Línea 554: Define currentFpa correctamente
const currentFpa = new Date('{{ ticket.current_fpa.strftime("%Y-%m-%d") }}');

// Líneas 607-613: Inicializa el campo correctamente
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('new_fpa_date');
    if (dateInput) {
        dateInput.value = formatDateYMD(currentFpa);  // ✅ ESTO PARECE CORRECTO
        updatePreview();
    }
});
```

### Posibles Causas del Problema

1. **Problema de timezone**: La conversión de fecha puede estar afectada por la zona horaria
2. **Caché del navegador**: El JavaScript puede no estar ejecutándose correctamente
3. **Otro script sobrescribiendo**: Puede haber otro script que cambie el valor después
4. **Valor HTML inicial**: El campo puede tener un valor `value=""` en el HTML que causa problemas

---

## 💡 Solución Propuesta

### Opción 1: Agregar valor inicial en el HTML (más confiable)

**`templates/tickets/detail.html` (línea 322)**

```html
<input type="date" id="new_fpa_date" name="new_fpa_date" required
       value="{{ ticket.current_fpa.strftime('%Y-%m-%d') }}"
       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
       onchange="updatePreview()">
```

**Ventaja**: El navegador carga el campo ya con el valor correcto, sin depender de JavaScript.

### Opción 2: Mejorar el JavaScript para debugging

**`templates/tickets/detail.html`**

```javascript
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Initializing FPA modification form');

    const dateInput = document.getElementById('new_fpa_date');
    if (!dateInput) {
        console.error('[ERROR] new_fpa_date input not found');
        return;
    }

    // Verificar que currentFpa se parseó correctamente
    console.log('[DEBUG] currentFpa:', currentFpa);
    console.log('[DEBUG] currentFpa formatted:', formatDateYMD(currentFpa));

    // Asignar valor
    dateInput.value = formatDateYMD(currentFpa);
    console.log('[DEBUG] dateInput.value set to:', dateInput.value);

    // Actualizar preview
    updatePreview();
});
```

### Opción 3: Verificar función `formatDateYMD()`

```javascript
function formatDateYMD(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const formatted = `${year}-${month}-${day}`;

    console.log('[DEBUG] formatDateYMD input:', date, 'output:', formatted);
    return formatted;
}
```

---

## 🔬 Pasos para Investigar

Si el problema persiste después de implementar la solución:

1. **Verificar valor en HTML**: Inspeccionar elemento y ver qué valor tiene `<input id="new_fpa_date">`
2. **Verificar consola del navegador**: Buscar errores de JavaScript
3. **Verificar `ticket.current_fpa`**: Asegurar que el ticket tiene una FPA válida
4. **Verificar timezone**: Confirmar que no hay problemas de conversión UTC vs local

```python
# En Python (debugging):
print(f"Current FPA: {ticket.current_fpa}")
print(f"Current FPA ISO: {ticket.current_fpa.strftime('%Y-%m-%d')}")
print(f"Pavilion end time: {ticket.pavilion_end_time}")
```

---

## ✅ Criterios de Aceptación

- [ ] Al abrir el formulario de modificación, el campo `new_fpa_date` tiene la **FPA actual del ticket**
- [ ] La vista previa inicial muestra "Diferencia: **0 días** (sin cambio)"
- [ ] Si el usuario cambia la fecha a futuro, muestra "+X días (extensión)"
- [ ] Si el usuario cambia la fecha a pasado, muestra "-X días (reducción)"
- [ ] El valor por defecto funciona correctamente en todos los navegadores (Chrome, Firefox, Safari, Edge)
- [ ] El campo se inicializa correctamente incluso si hay modificaciones previas al ticket

---

## 🧪 Casos de Prueba

| Escenario | FPA Inicial | FPA Actual | Valor Esperado en Campo | Diferencia Esperada |
|-----------|-------------|------------|-------------------------|---------------------|
| Ticket sin modificaciones | 15/11/2025 | 15/11/2025 | 2025-11-15 | 0 días |
| Ticket con 1 modificación | 15/11/2025 | 17/11/2025 | 2025-11-17 | 0 días |
| Ticket con múltiples mods | 15/11/2025 | 20/11/2025 | 2025-11-20 | 0 días |
| Ticket creado hace meses | 01/08/2025 | 01/08/2025 | 2025-08-01 | 0 días |

En todos los casos, el campo debe inicializarse con `current_fpa`, no con `pavilion_end_time` ni `initial_fpa`.

---

## 📊 Impacto

- **Prioridad**: 🟡 MEDIA
- **Usuarios afectados**: Personal médico y administrativo que modifica FPAs
- **Módulos afectados**: Formulario de modificación de FPA en vista de detalle de ticket

---

## 🏷️ Labels Sugeridos
`bug`, `ux`, `frontend`, `priority: medium`
