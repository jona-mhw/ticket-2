# 🎨 GUÍA SIMPLE: Cómo Probar el Sistema de Colores (Issue #3)

## 🚀 PASO 1: Preparar la Base de Datos

Abre tu terminal y ejecuta:

```bash
# Aplicar la migración para crear la tabla de umbrales
flask db upgrade

# O si prefieres empezar desde cero:
flask reset-db
```

**Resultado esperado**: Deberías ver mensajes indicando que la base de datos se actualizó correctamente.

---

## 🔓 PASO 2: Iniciar Sesión como Superusuario

1. **Inicia la aplicación** (si no está corriendo):
   ```bash
   flask run
   # O python app.py
   ```

2. **Abre el navegador** en: `http://localhost:5000` (o el puerto que uses)

3. **Inicia sesión** con:
   - Usuario: `global_admin`
   - Contraseña: `password123`

4. **Verifica que iniciaste sesión correctamente**:
   - Deberías ver un mensaje de bienvenida
   - Tu nombre de usuario debería aparecer en la esquina superior

---

## ⚙️ PASO 3: Ir al Panel de Configuración

**Opción A - Desde el menú:**
1. En la barra de navegación superior, busca el menú de **"Admin"** o **"Administración"**
2. Haz clic en **"Configuración"** o similar
3. Busca **"Umbrales de Colores"** o **"Configuración de Colores"**

**Opción B - URL directa:**
1. En la barra de direcciones del navegador, escribe:
   ```
   http://localhost:5000/admin/configuracion/umbrales-colores
   ```
2. Presiona Enter

**¿Qué deberías ver?**
- ✅ Una página con el título "Configuración de Umbrales de Colores"
- ✅ Una sección morada que dice "Configuración Global (Por Defecto)"
- ✅ Tres campos numéricos:
  - Verde: 8
  - Amarillo: 4
  - Rojo: 2
- ✅ Un botón "Guardar Configuración Global"

**📸 IMPORTANTE**: Si ves esta página, ¡el sistema está funcionando! Toma una captura de pantalla.

**❌ Si NO ves la página:**
- Verifica que iniciaste sesión como `global_admin`
- Revisa la consola del servidor (donde ejecutaste `flask run`) para ver errores
- Copia cualquier error que veas y me lo pasas

---

## 🎨 PASO 4: Cambiar los Umbrales (PRUEBA REAL)

Vamos a cambiar los colores para ver que funciona:

1. **En la sección "Configuración Global", cambia los valores**:
   - Verde: cambia de `8` a `10`
   - Amarillo: cambia de `4` a `5`
   - Rojo: cambia de `2` a `1`

2. **Haz clic en "Guardar Configuración Global"**

**¿Qué debería pasar?**
- ✅ Mensaje verde arriba que dice: "Configuración de umbrales guardada exitosamente"
- ✅ Los valores se mantienen en 10, 5, 1
- ✅ Aparece la fecha/hora de actualización
- ✅ Aparece tu nombre de usuario (global_admin) como quien actualizó

**❌ Si aparece un error:**
- Copia el mensaje de error exacto
- Revisa la consola del servidor

---

## 🎯 PASO 5: Verificar que los Colores Cambiaron en el Tablero

1. **Ve al Tablero de Enfermería**:
   - En el menú, haz clic en "Tablero de Enfermería" o "Nursing Board"
   - O ve a: `http://localhost:5000/tickets/nursing`

2. **Observa las tarjetas de tickets**:
   - Fíjate en los colores de las tarjetas (verde, amarillo, rojo)

3. **Verifica los nuevos umbrales**:
   - Tarjetas con MÁS de 10 horas: deberían ser VERDES 🟢
   - Tarjetas con 5-10 horas: deberían ser AMARILLAS 🟡
   - Tarjetas con MENOS de 1 hora: deberían ser ROJAS 🔴

**¿Cómo saber si funciona?**
- Abre las herramientas de desarrollo del navegador (F12)
- Ve a la pestaña "Console"
- Deberías ver un mensaje: `Umbrales de colores cargados: {green: 10, yellow: 5, red: 1}`

**📸 IMPORTANTE**: Si ves este mensaje en la consola, ¡funciona perfectamente!

---

## 🏥 PASO 6 (OPCIONAL): Configuración por Clínica

Si quieres probar la configuración específica por clínica:

1. **Vuelve a**: `/admin/configuracion/umbrales-colores`

2. **Desplázate hacia abajo** hasta ver la sección azul:
   - "Configuraciones Específicas por Clínica"

3. **Encuentra "Clínica RedSalud Providencia"** (o cualquier otra)

4. **Cambia los valores solo para esa clínica**:
   - Verde: `12`
   - Amarillo: `6`
   - Rojo: `3`

5. **Haz clic en "Guardar para [Nombre de Clínica]"**

**Resultado esperado**:
- ✅ Mensaje de éxito
- ✅ Los tickets de ESA clínica usan los nuevos umbrales (12/6/3)
- ✅ Los tickets de OTRAS clínicas siguen usando la configuración global (10/5/1)

---

## ✅ CHECKLIST RÁPIDO

Marca lo que pudiste hacer:

- [ ] Abrí el panel de configuración de colores
- [ ] Vi los valores por defecto (8, 4, 2)
- [ ] Cambié los valores a (10, 5, 1)
- [ ] Apareció el mensaje de éxito
- [ ] Vi en la consola del navegador: "Umbrales de colores cargados"
- [ ] Los colores del tablero se actualizaron

**Si marcaste TODO**: ✅ ¡El Issue #3 funciona perfectamente!

**Si NO pudiste marcar algo**: Anota qué paso falló y qué error viste.

---

## 🐛 Problemas Comunes y Soluciones

### Error: "Página no encontrada (404)"
**Solución**:
- Verifica que la URL sea correcta: `/admin/configuracion/umbrales-colores`
- Asegúrate de estar logueado como `global_admin`

### Error: "No tienes permisos"
**Solución**:
- Cierra sesión e inicia sesión nuevamente como `global_admin`

### Error: "Internal Server Error (500)"
**Solución**:
- Revisa la consola del servidor (terminal donde corre Flask)
- Verifica que ejecutaste `flask db upgrade`
- Copia el error completo

### Los colores NO cambian en el tablero
**Solución**:
1. Refresca la página del tablero (F5)
2. Limpia la caché del navegador (Ctrl+Shift+R)
3. Verifica en la consola del navegador (F12 → Console) si hay errores JavaScript

---

## 📊 Verificación en Base de Datos (OPCIONAL - Solo si quieres estar 100% seguro)

Si sabes usar SQL, puedes verificar directamente:

```sql
-- Ver la configuración global
SELECT * FROM urgency_threshold WHERE clinic_id IS NULL;

-- Deberías ver: green_threshold_hours=10, yellow_threshold_hours=5, red_threshold_hours=1
```

---

## ✨ ¿Todo Funcionó?

Si completaste todos los pasos sin errores: **¡EXCELENTE! El Issue #3 está 100% funcional.**

Si tuviste problemas: Anota:
1. ¿En qué paso tuviste el problema?
2. ¿Qué mensaje de error viste?
3. ¿Hay errores en la consola del navegador o del servidor?

Con esa información puedo ayudarte a resolverlo.
