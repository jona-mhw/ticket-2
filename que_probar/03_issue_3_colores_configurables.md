# QA Issue #3: Sistema de Configuración de Colores de Tickets

## 📝 Descripción del Cambio
Se implementó un sistema completo para configurar los umbrales de colores de las tarjetas de tickets. Los superusuarios pueden configurar umbrales globales y por clínica.

## 🎯 Objetivo de la Prueba
Verificar que los umbrales de colores se pueden configurar correctamente y que los cambios se reflejan inmediatamente en el tablero de tickets.

## ✅ Pre-requisitos
- Migración de base de datos aplicada (`e7f8g9h0i1j2`)
- Al menos un ticket activo en el sistema
- Usuario con rol admin o superuser

## 📋 Casos de Prueba

### Caso 1: Acceso a Configuración como Superusuario
**Pasos:**
1. Iniciar sesión como `global_admin` / `password123`
2. En el menú de navegación, buscar opción de configuración de colores
   (Puede estar en Admin → Configuración → Umbrales de Colores)
3. Navegar a `/admin/configuracion/umbrales-colores`

**Resultado Esperado:**
- ✅ Página carga correctamente
- ✅ Muestra sección "Configuración Global (Por Defecto)"
- ✅ Muestra sección "Configuraciones Específicas por Clínica"
- ✅ Valores por defecto: Verde=8h, Amarillo=4h, Rojo=2h

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Captura de pantalla:**
```
[Adjuntar captura de la página de configuración]
```

---

### Caso 2: Modificar Configuración Global
**Pasos:**
1. Como `global_admin`, ir a configuración de umbrales
2. En la sección "Configuración Global", modificar valores:
   - Verde: `10` horas
   - Amarillo: `5` horas
   - Rojo: `1` hora
3. Hacer clic en "Guardar Configuración Global"

**Resultado Esperado:**
- ✅ Mensaje de éxito: "Configuración de umbrales guardada exitosamente"
- ✅ Valores se actualizan en la página
- ✅ Muestra fecha/hora de última actualización
- ✅ Muestra nombre del usuario que actualizó

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 3: Verificar Cambios en Tablero de Tickets
**Pasos:**
1. Con la configuración del Caso 2 aplicada (Verde=10h, Amarillo=5h, Rojo=1h)
2. Ir a "Tablero de Enfermería" (`/tickets/nursing`)
3. Observar los colores de las tarjetas de tickets

**Resultado Esperado:**
- ✅ Tickets con más de 10 horas restantes: COLOR VERDE
- ✅ Tickets con 5-10 horas restantes: COLOR AMARILLO
- ✅ Tickets con menos de 1 hora restante: COLOR ROJO
- ✅ Los colores se actualizan automáticamente (refrescar página si es necesario)

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Anotar ejemplos específicos de tickets y sus colores]
```

---

### Caso 4: Configuración Específica por Clínica
**Pasos:**
1. Como `global_admin`, ir a configuración de umbrales
2. En la sección "Configuraciones Específicas por Clínica"
3. Para "Clínica RedSalud Providencia", configurar:
   - Verde: `12` horas
   - Amarillo: `6` horas
   - Rojo: `3` horas
4. Guardar cambios

**Resultado Esperado:**
- ✅ Configuración se guarda exitosamente
- ✅ Los tickets de Providencia usan los nuevos umbrales (12h/6h/3h)
- ✅ Los tickets de OTRAS clínicas siguen usando configuración global (10h/5h/1h)

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 5: Acceso como Administrador de Clínica
**Pasos:**
1. Cerrar sesión
2. Iniciar sesión como `admin_prov` / `password123`
3. Ir a `/admin/configuracion/umbrales-colores`

**Resultado Esperado:**
- ✅ Puede acceder a la página
- ✅ SOLO ve configuración de SU clínica (Providencia)
- ✅ NO ve configuración global
- ✅ NO ve otras clínicas

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 6: Validación de Umbrales Incorrectos
**Pasos:**
1. Como `global_admin`, ir a configuración
2. Intentar guardar con valores INCORRECTOS:
   - Verde: `2` horas
   - Amarillo: `5` horas
   - Rojo: `10` horas
   (Orden incorrecto: Rojo > Amarillo > Verde)
3. Hacer clic en guardar

**Resultado Esperado:**
- ✅ Muestra mensaje de error: "Los umbrales deben estar en orden: Rojo < Amarillo < Verde"
- ✅ NO se guardan los cambios
- ✅ Mantiene valores anteriores

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 7: Verificar API de Umbrales
**Pasos:**
1. Con el navegador o herramienta como Postman
2. Hacer request GET a: `/admin/api/umbrales-colores`
3. Verificar respuesta JSON

**Resultado Esperado:**
```json
{
  "green_threshold_hours": 10,
  "yellow_threshold_hours": 5,
  "red_threshold_hours": 1
}
```
(O los valores configurados)

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Respuesta obtenida:**
```json
[Pegar respuesta JSON aquí]
```

---

## 🔍 Verificaciones Adicionales

### Verificar en Base de Datos
```sql
-- Ver configuración global
SELECT * FROM urgency_threshold WHERE clinic_id IS NULL;

-- Ver configuraciones por clínica
SELECT ut.*, c.name as clinic_name
FROM urgency_threshold ut
JOIN clinic c ON ut.clinic_id = c.id
ORDER BY c.name;
```

### Verificar Auditoría
```sql
-- Ver logs de cambios de configuración
SELECT * FROM action_audit
WHERE action LIKE '%umbrales de colores%'
ORDER BY timestamp DESC;
```

### Pruebas de Actualización Dinámica
- [ ] Los colores se actualizan al refrescar la página
- [ ] Los colores se actualizan en tiempo real (countdown)
- [ ] El JavaScript carga correctamente los umbrales

### Pruebas de Permisos
- [ ] Usuario `clinical` NO puede acceder a la configuración
- [ ] Usuario `visualizador` NO puede acceder a la configuración
- [ ] Solo admin y superuser tienen acceso

## 📊 Resumen de Resultados

**Total de casos:** 7
**Aprobados:** ___
**Fallidos:** ___
**Observaciones generales:**
```
[Espacio para resumen del QA]
```

## 🎨 Colores Esperados según Umbrales

| Umbral | Color | Descripción |
|--------|-------|-------------|
| > Verde (8h) | 🟢 Verde | Tiempo suficiente |
| Entre Amarillo y Verde (4-8h) | 🟡 Amarillo | Advertencia |
| < Amarillo (4h) | 🟡 Amarillo | Advertencia |
| < Rojo (2h) | 🔴 Rojo | Urgente/Crítico |

## 🐛 Bugs Encontrados
```
[Si se encontraron bugs, listarlos aquí con detalles]
```
