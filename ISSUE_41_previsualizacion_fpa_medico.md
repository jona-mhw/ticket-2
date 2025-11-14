# Bug: Previsualización de FPA muestra solo cálculo automático, no el FPA indicado por médico

## 🐛 Descripción del Problema

En el formulario de creación de tickets, la **previsualización de FPA** (panel inferior pegajoso) muestra **solo el FPA calculado automáticamente** por el sistema, ignorando la fecha que indicó el médico en el campo "Fecha Posible de Alta (Indicación Médica)".

### Comportamiento Actual ❌
- El médico selecciona una cirugía → Sistema calcula FPA automático
- Sistema muestra FPA calculado en el panel de previsualización
- El médico cambia la fecha en el campo `medical_discharge_date` a una fecha diferente
- **PROBLEMA**: La previsualización NO se actualiza, sigue mostrando el FPA calculado
- El médico no puede ver claramente cuál será el FPA final del ticket

### Comportamiento Esperado ✅
- La previsualización debe mostrar **el FPA que indicó el médico**, no solo el calculado
- Si el médico cambia `medical_discharge_date`, la previsualización debe actualizarse
- Debe quedar claro cuál es el FPA que se usará (el del médico, no el del sistema)
- Idealmente, mostrar ambos: "FPA Calculado" vs "FPA Indicado por Médico"

---

## 🔍 Análisis Técnico

### Archivos Afectados

**1. `templates/tickets/create.html` (líneas 358-450)**

El JavaScript solo muestra el `data.fpa_display_str` del cálculo automático:

```javascript
async function updateFpaPreview() {
    // ...
    const response = await fetch('{{ url_for("tickets.api_calculate_fpa") }}', {
        // ... llama al endpoint que solo calcula FPA automático
    });

    const data = await response.json();

    // Problema: Solo muestra el FPA calculado
    systemFpaHelper.innerHTML = `Sugerencia del sistema: <span class="font-semibold text-gray-700">${data.fpa_display_str}</span>`;

    // Problema: La previsualización solo muestra el FPA calculado
    fpaPreview.innerHTML = `
        <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <p class="text-xs font-medium text-gray-600 mb-1">FPA Calculada</p>
                    <p class="text-lg font-bold text-primary">${data.fpa_display_str}</p>
                    // ...
                </div>
            </div>
        </div>
    `;

    // Falta: Leer el valor de medical_discharge_date y mostrarlo en la previsualización
}
```

**2. `templates/tickets/create.html` (líneas 484-487)**

El evento `change` de `medical_discharge_date` solo marca una bandera, pero no actualiza la previsualización:

```javascript
medicalDischargeDateInput.addEventListener('change', () => {
    medicalDateManuallySet = true;  // Solo marca que fue cambiado manualmente
    updateFpaPreview();              // Pero updateFpaPreview() no usa esta fecha
});
```

---

## 💡 Solución Propuesta

### Paso 1: Actualizar la función `updateFpaPreview()` para mostrar el FPA del médico

```javascript
async function updateFpaPreview() {
    const surgeryId = surgerySelect.value;
    const pavilionEndValue = pavilionEndTimeInput.value;
    const medicalDischargeDate = medicalDischargeDateInput.value;  // NUEVO: Leer fecha del médico
    const clinicId = currentClinicId || (isSuperuser && clinicSelect ? parseInt(clinicSelect.value) : null);

    if (!surgeryId || !pavilionEndValue) {
        // ...
        return;
    }

    try {
        // Calcular FPA del sistema (para referencia)
        const response = await fetch('{{ url_for("tickets.api_calculate_fpa") }}', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                surgery_id: surgeryId,
                pavilion_end_time: pavilionEndValue,
                clinic_id: clinicId
            }),
        });

        const data = await response.json();

        // Actualizar helper text
        systemFpaHelper.innerHTML = `Sugerencia del sistema: <span class="font-semibold text-gray-700">${data.fpa_display_str}</span>`;

        // NUEVO: Autocompletar medical_discharge_date si no fue cambiado manualmente
        if (!medicalDateManuallySet) {
            medicalDischargeDateInput.value = data.fpa_date_iso;
        }

        // NUEVO: Determinar qué FPA mostrar (del médico o del sistema)
        const medicalDate = new Date(medicalDischargeDateInput.value + 'T00:00:00');
        const systemDate = new Date(data.fpa_date_iso + 'T00:00:00');
        const usingMedicalDate = medicalDate.getTime() !== systemDate.getTime();

        // NUEVO: Mostrar ambos FPAs si son diferentes
        if (usingMedicalDate) {
            fpaPreview.innerHTML = `
                <div class="bg-yellow-50 rounded-lg p-4 border border-yellow-300">
                    <div class="flex items-center gap-2 mb-3">
                        <svg class="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>
                        <h4 class="text-sm font-semibold text-yellow-900">FPA Indicado por Médico (Diferente al Calculado)</h4>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-white rounded p-3 border border-gray-300">
                            <p class="text-xs font-medium text-gray-600 mb-1">FPA Calculada (Sistema)</p>
                            <p class="text-lg font-bold text-gray-700">${data.fpa_display_str}</p>
                        </div>
                        <div class="bg-yellow-100 rounded p-3 border-2 border-yellow-500">
                            <p class="text-xs font-medium text-yellow-800 mb-1">FPA Indicada (Médico)</p>
                            <p class="text-lg font-bold text-yellow-900">${formatDateDMY(medicalDate)}</p>
                            <p class="text-xs text-yellow-700 mt-1">⚠️ Esta fecha será la FPA del ticket</p>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Si son iguales, mostrar solo el FPA calculado (como antes)
            fpaPreview.innerHTML = `
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <p class="text-xs font-medium text-gray-600 mb-1">FPA Calculada</p>
                            <p class="text-lg font-bold text-primary">${data.fpa_display_str}</p>
                            <p class="text-xs text-gray-500 mt-1">${data.fpa_date_iso} a las ${data.fpa_time}</p>
                        </div>
                        <div>
                            <p class="text-xs font-medium text-gray-600 mb-1">Estancia Calculada</p>
                            <p class="text-lg font-bold text-blue-700">${daysDiff} día${daysDiff !== 1 ? 's' : ''}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // Mostrar/ocultar sección de justificación
        if (usingMedicalDate) {
            justificationSection.style.display = 'block';
            initialReasonSelect.required = true;
        } else {
            justificationSection.style.display = 'none';
            initialReasonSelect.required = false;
        }

    } catch (error) {
        console.error('Error fetching FPA:', error);
        // ...
    }
}

// Helper para formatear fecha como DD/MM/YYYY
function formatDateDMY(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}
```

---

## ✅ Criterios de Aceptación

- [ ] Si el médico NO cambia `medical_discharge_date`, la previsualización muestra solo el FPA calculado
- [ ] Si el médico cambia `medical_discharge_date` a una fecha diferente, la previsualización muestra:
  - FPA Calculada (Sistema)
  - FPA Indicada (Médico) - destacada visualmente
  - Mensaje claro de que se usará el FPA del médico
- [ ] La previsualización se actualiza en tiempo real al cambiar `medical_discharge_date`
- [ ] Se muestra un ícono de advertencia cuando hay discrepancia
- [ ] La sección de justificación aparece automáticamente cuando hay discrepancia

---

## 📊 Impacto

- **Prioridad**: 🟡 MEDIA-ALTA
- **Usuarios afectados**: Médicos creando tickets
- **Módulos afectados**: Formulario de creación de tickets

---

## 🏷️ Labels Sugeridos
`bug`, `ux`, `frontend`, `priority: medium-high`
