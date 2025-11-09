# 🔍 GUÍA SIMPLE: Cómo Verificar Filtros por Rol (Issue #5)

## 🎯 ¿Qué Vamos a Probar?

Vamos a verificar que:
- **Superusuarios** (`global_admin`) ven tickets de TODAS las clínicas
- **Otros usuarios** (admin, clínico) solo ven tickets de SU clínica

---

## 🚀 PASO 1: Preparar Datos de Prueba

Necesitas tener tickets de DIFERENTES clínicas. Si acabas de hacer `flask reset-db`, ya los tienes.

Si no estás seguro, ejecuta:

```bash
flask reset-db
```

Esto crea:
- 9 clínicas
- Tickets en múltiples clínicas
- Usuarios para cada clínica

---

## 🔓 PASO 2: Probar como SUPERUSUARIO

### 2.1 Iniciar Sesión
1. **Abre el navegador** en: `http://localhost:5000`
2. **Inicia sesión** con:
   - Usuario: `global_admin`
   - Contraseña: `password123`

### 2.2 Ir al Dashboard
1. En el menú, haz clic en **"Dashboard"**
2. O ve directamente a: `http://localhost:5000/dashboard`

### 2.3 ¿Qué Deberías Ver?

**✅ CORRECTO - Si ves esto**:
- Tickets de MÚLTIPLES clínicas mezclados
- En los IDs de tickets, verás diferentes códigos:
  - `TH-IQUI-2025-001` (Iquique)
  - `TH-PROV-2025-002` (Providencia)
  - `TH-SANT-2025-003` (Santiago)
  - `TH-ELQU-2025-004` (Elqui)
  - etc.
- El contador de "Total de tickets" incluye TODAS las clínicas

**❌ INCORRECTO - Si ves esto**:
- Solo tickets de UNA clínica
- Todos los IDs tienen el mismo código (ej: solo `TH-PROV-...`)

### 2.4 Verificar en Tablero de Enfermería

1. Ve a **"Tablero de Enfermería"**: `http://localhost:5000/tickets/nursing`
2. **Observa los IDs de las tarjetas de tickets**

**✅ CORRECTO**:
- Ves tarjetas con IDs de DIFERENTES clínicas
- Ejemplo: `TH-IQUI-2025-001`, `TH-VALP-2025-002`, etc.

**📸 IMPORTANTE**: Toma una captura mostrando tickets de MÚLTIPLES clínicas.

---

## 👤 PASO 3: Probar como ADMINISTRADOR de Clínica

### 3.1 Cerrar Sesión y Cambiar Usuario
1. **Cierra sesión** (busca el botón de "Cerrar Sesión" o "Logout")
2. **Vuelve al login**

### 3.2 Iniciar Sesión como Admin de Providencia
- Usuario: `admin_prov`
- Contraseña: `password123`

### 3.3 Ir al Dashboard
1. Ve a **"Dashboard"**: `http://localhost:5000/dashboard`

### 3.4 ¿Qué Deberías Ver?

**✅ CORRECTO - Si ves esto**:
- SOLO tickets de Clínica Providencia
- Todos los IDs empiezan con `TH-PROV-...`
- NO ves tickets de otras clínicas (Iquique, Santiago, etc.)
- El contador de "Total de tickets" solo cuenta los de Providencia

**❌ INCORRECTO - Si ves esto**:
- Tickets de múltiples clínicas
- IDs con diferentes códigos (`TH-IQUI`, `TH-SANT`, etc.)

### 3.5 Verificar en Tablero de Enfermería

1. Ve a: `http://localhost:5000/tickets/nursing`
2. **Verifica que TODAS las tarjetas sean de Providencia**

**✅ CORRECTO**:
- Todas las tarjetas tienen ID: `TH-PROV-2025-XXX`
- NO hay tarjetas de otras clínicas

**📸 IMPORTANTE**: Toma una captura mostrando SOLO tickets de Providencia.

---

## 👨‍⚕️ PASO 4: Probar como USUARIO CLÍNICO

### 4.1 Cerrar Sesión y Cambiar Usuario
1. **Cierra sesión**
2. **Inicia sesión** con:
   - Usuario: `clinical_prov`
   - Contraseña: `password123`

### 4.2 Verificar Dashboard y Tablero

Igual que en el Paso 3, deberías ver:
- ✅ SOLO tickets de Providencia
- ✅ NO tickets de otras clínicas

---

## 🧪 PASO 5: Prueba de Seguridad (IMPORTANTE)

Vamos a intentar acceder a un ticket de OTRA clínica directamente por URL.

### 5.1 Como usuario `admin_prov` (Providencia)

1. **Anota un ID de ticket de OTRA clínica** (cuando estabas como `global_admin` viste varios)
   - Por ejemplo: `TH-SANT-2025-001` (Santiago)

2. **Intenta acceder directamente** escribiendo en la barra de direcciones:
   ```
   http://localhost:5000/tickets/detail/TH-SANT-2025-001
   ```

**✅ CORRECTO - Resultado esperado**:
- Mensaje de error: "Ticket no encontrado" o "404 Not Found"
- O te redirige al dashboard
- NO te muestra el ticket

**❌ INCORRECTO**:
- Te muestra el detalle del ticket de Santiago
- Puedes ver información del ticket

---

## 🔄 PASO 6: Comparación Lado a Lado

Crea una tabla comparativa de lo que ves:

| Usuario | Dashboard (Total Tickets) | Códigos de Tickets Visibles | ¿Puede ver otras clínicas? |
|---------|---------------------------|----------------------------|---------------------------|
| `global_admin` | ___ | TH-IQUI, TH-PROV, TH-SANT, etc. | ✅ SÍ |
| `admin_prov` | ___ | Solo TH-PROV | ❌ NO |
| `clinical_prov` | ___ | Solo TH-PROV | ❌ NO |

**Si tu tabla se ve así**: ✅ ¡Los filtros funcionan perfectamente!

---

## ✅ CHECKLIST RÁPIDO

Marca lo que verificaste:

- [ ] Como `global_admin` vi tickets de MÚLTIPLES clínicas
- [ ] Como `admin_prov` vi SOLO tickets de Providencia
- [ ] Como `clinical_prov` vi SOLO tickets de Providencia
- [ ] No pude acceder a tickets de otra clínica mediante URL directa
- [ ] El dashboard muestra diferentes totales según el usuario
- [ ] El tablero de enfermería filtra correctamente

**Si marcaste TODO**: ✅ ¡El Issue #5 funciona perfectamente!

**Si NO pudiste marcar algo**: Anota qué falló.

---

## 🐛 Problemas Comunes

### Veo tickets de todas las clínicas con `admin_prov`
**PROBLEMA**: Los filtros NO están funcionando correctamente.

**Solución**:
1. Verifica que el usuario tenga `clinic_id` asignado:
   ```sql
   SELECT username, email, role, clinic_id FROM user WHERE username = 'admin_prov';
   ```
   - Debería tener `clinic_id` diferente de `NULL`

2. Si `clinic_id` es `NULL`, ese es el problema.

### Como `global_admin` solo veo una clínica
**PROBLEMA**: El superusuario está actuando como usuario normal.

**Solución**:
1. Verifica que `global_admin` esté en la tabla de superusers:
   ```sql
   SELECT * FROM superuser WHERE email = 'global_admin@tickethome.com';
   ```

2. Verifica que `global_admin` tenga `clinic_id = NULL`:
   ```sql
   SELECT username, clinic_id FROM user WHERE username = 'global_admin';
   ```

---

## 📊 Verificación en Base de Datos (OPCIONAL)

Si quieres verificar directamente en la base de datos:

```sql
-- Ver usuarios y sus clínicas
SELECT u.username, u.role, u.clinic_id, c.name as clinic_name
FROM user u
LEFT JOIN clinic c ON u.clinic_id = c.id
ORDER BY u.clinic_id, u.username;

-- Ver tickets por clínica
SELECT
    c.name as clinica,
    COUNT(t.id) as total_tickets
FROM ticket t
JOIN clinic c ON t.clinic_id = c.id
GROUP BY c.name
ORDER BY total_tickets DESC;

-- Verificar superusers
SELECT * FROM superuser;
```

---

## ✨ ¿Todo Funcionó?

### Si marcaste TODO el checklist:
**✅ ¡PERFECTO! El Issue #5 está funcionando correctamente.**

Los filtros por rol están bien implementados:
- Superusuarios ven TODO
- Otros usuarios solo ven su clínica
- No se puede acceder a tickets de otras clínicas

### Si algo no funcionó:

Anota lo siguiente:
1. ¿Qué usuario estabas usando?
2. ¿Qué tickets viste? (anota algunos IDs)
3. ¿Qué esperabas ver?
4. Captura de pantalla de lo que viste

---

## 🎓 Explicación Técnica (Opcional)

Los filtros se aplican en:

1. **`repositories/ticket_repository.py`** (líneas 78-83):
   ```python
   # Apply clinic filter for non-superusers
   if not current_user.is_superuser:
       query = query.filter(
           Ticket.clinic_id == current_user.clinic_id,
           ...
       )
   ```

2. **`routes/dashboard.py`** (líneas 22-27):
   - Función que aplica filtros de clínica según el rol

Si los filtros NO funcionan, el problema está en una de estas dos partes.
