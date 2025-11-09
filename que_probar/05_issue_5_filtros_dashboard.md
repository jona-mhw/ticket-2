# QA Issue #5: Filtros de Dashboard según Rol de Usuario

## 📝 Descripción del Cambio
Verificación de que los filtros de dashboard y todas las vistas funcionan correctamente según el rol del usuario. Los superusuarios deben ver información de todas las clínicas, mientras que otros usuarios solo ven datos de su clínica.

## 🎯 Objetivo de la Prueba
Confirmar que el sistema de filtros por rol funciona correctamente en todas las vistas principales: dashboard, tablero de enfermería, y listados de tickets.

## ✅ Pre-requisitos
- Múltiples clínicas con datos en la base de datos
- Usuarios de diferentes roles en diferentes clínicas
- Tickets creados en múltiples clínicas

## 📋 Casos de Prueba

### Caso 1: Dashboard como Superusuario
**Pasos:**
1. Iniciar sesión como `global_admin` / `password123`
2. Ir a "Dashboard" (`/dashboard`)
3. Observar los KPIs y estadísticas mostradas

**Resultado Esperado:**
- ✅ Muestra tickets de TODAS las clínicas
- ✅ KPIs incluyen datos globales (no filtrados por clínica)
- ✅ Gráficos muestran tendencias de todas las clínicas
- ✅ "Tickets recientes" incluye tickets de múltiples clínicas
- ✅ Estadísticas de cirugías incluyen todas las clínicas

**Verificar Específicamente:**
```
Total de tickets: ___ (debe incluir todas las clínicas)
Tickets activos: ___ (todas las clínicas)
Tickets anulados: ___ (todas las clínicas)
```

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 2: Dashboard como Administrador de Clínica
**Pasos:**
1. Iniciar sesión como `admin_prov` / `password123` (admin de Providencia)
2. Ir a "Dashboard"
3. Observar los KPIs y estadísticas

**Resultado Esperado:**
- ✅ Muestra SOLO tickets de Clínica Providencia
- ✅ KPIs están filtrados por Providencia
- ✅ NO muestra tickets de otras clínicas (Iquique, Elqui, etc.)
- ✅ Gráficos solo incluyen datos de Providencia

**Verificar Específicamente:**
```
Total de tickets: ___ (solo Providencia)
Verificar que NO aparecen tickets de otras clínicas en "Tickets recientes"
```

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 3: Tablero de Enfermería como Superusuario
**Pasos:**
1. Como `global_admin`, ir a "Tablero de Enfermería" (`/tickets/nursing`)
2. Observar todas las tarjetas de tickets mostradas
3. Verificar los IDs de los tickets (incluyen el código de clínica)

**Resultado Esperado:**
- ✅ Muestra tickets con códigos de DIFERENTES clínicas:
  - `TH-IQUI-...` (Iquique)
  - `TH-ELQU-...` (Elqui)
  - `TH-VALP-...` (Valparaíso)
  - `TH-PROV-...` (Providencia)
  - etc.
- ✅ NO hay filtro de clínica aplicado

**Tickets Visibles:**
```
[Listar algunos IDs de tickets visibles y sus clínicas]
TH-XXXX-2025-001: ___
TH-YYYY-2025-002: ___
TH-ZZZZ-2025-003: ___
```

**Resultado Obtenido:**
- [ ] ✅ Aprobado - Se ven tickets de múltiples clínicas
- [ ] ❌ Fallido - Solo se ve una clínica

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 4: Tablero de Enfermería como Usuario Clínico
**Pasos:**
1. Cerrar sesión
2. Iniciar sesión como `clinical_sant` / `password123` (clínico de Santiago)
3. Ir a "Tablero de Enfermería"
4. Verificar los tickets mostrados

**Resultado Esperado:**
- ✅ Muestra SOLO tickets de Clínica Santiago (`TH-SANT-...`)
- ✅ NO muestra tickets de otras clínicas
- ✅ Todos los tickets visibles pertenecen a la misma clínica

**Tickets Visibles:**
```
[Verificar que TODOS los IDs son TH-SANT-...]
```

**Resultado Obtenido:**
- [ ] ✅ Aprobado - Solo tickets de Santiago
- [ ] ❌ Fallido - Se ven tickets de otras clínicas

**Notas:**
```
[Si se ven tickets de otras clínicas, listarlos aquí]
```

---

### Caso 5: Creación de Tickets como Superusuario
**Pasos:**
1. Como `global_admin`, ir a "Crear Ticket"
2. Verificar el formulario

**Resultado Esperado:**
- ✅ Aparece dropdown/selector de "Clínica"
- ✅ Se pueden ver TODAS las clínicas activas en el selector
- ✅ Al seleccionar una clínica, se cargan especialidades/cirugías de esa clínica

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 6: Creación de Tickets como Administrador de Clínica
**Pasos:**
1. Como `admin_prov`, ir a "Crear Ticket"
2. Verificar el formulario

**Resultado Esperado:**
- ✅ NO aparece selector de clínica
- ✅ La clínica está predeterminada (Providencia)
- ✅ Solo se cargan especialidades/cirugías de Providencia

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 7: Listado de Tickets para Gestión
**Pasos:**
1. Como `global_admin`, ir a "Gestionar Tickets" o listado administrativo
2. Verificar los tickets en la tabla

**Resultado Esperado:**
- ✅ Muestra tickets de todas las clínicas
- ✅ Tiene opción de filtrar por clínica si se desea

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

---

**Pasos:**
1. Como `admin_prov`, ir a la misma vista
2. Verificar los tickets en la tabla

**Resultado Esperado:**
- ✅ Muestra SOLO tickets de Providencia
- ✅ NO hay opción de cambiar de clínica

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 8: Detalle de Ticket - Permisos por Clínica
**Pasos:**
1. Como `admin_prov` (Providencia)
2. Intentar acceder directamente a un ticket de OTRA clínica
   Ej: `/tickets/detail/TH-SANT-2025-001` (ticket de Santiago)

**Resultado Esperado:**
- ✅ Muestra error 404 o "Acceso denegado"
- ✅ NO permite ver tickets de otras clínicas

**Resultado Obtenido:**
- [ ] ✅ Aprobado - No puede acceder
- [ ] ❌ Fallido - Puede ver el ticket

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 9: Búsqueda Global (Superusuario)
**Pasos:**
1. Como `global_admin`
2. Usar la búsqueda del tablero de enfermería
3. Buscar por: "María" o cualquier nombre común

**Resultado Esperado:**
- ✅ Resultados incluyen pacientes de TODAS las clínicas
- ✅ Se muestran tickets de múltiples clínicas en resultados

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

---

**Pasos:**
1. Como `clinical_sant` (Santiago)
2. Buscar el mismo término: "María"

**Resultado Esperado:**
- ✅ Resultados incluyen SOLO pacientes de Santiago
- ✅ NO aparecen resultados de otras clínicas

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

## 🔍 Verificaciones Adicionales

### Verificar en Base de Datos
```sql
-- Contar tickets por clínica
SELECT c.name, COUNT(t.id) as ticket_count
FROM ticket t
JOIN clinic c ON t.clinic_id = c.id
GROUP BY c.name
ORDER BY c.name;

-- Verificar clinic_id de usuarios
SELECT username, role, clinic_id
FROM user
ORDER BY clinic_id, role;
```

### Verificar en Código
Archivos clave a revisar:
- `repositories/ticket_repository.py` - Método `build_filtered_query()` (línea 78-83)
- `routes/dashboard.py` - Función `apply_clinic_filter()` (línea 22-27)
- `routes/tickets.py` - Verificar filtros en todas las vistas

### Matriz de Permisos

| Vista | Superusuario | Admin Clínica | Clínico | Visualizador |
|-------|--------------|---------------|---------|--------------|
| Dashboard | Todas las clínicas | Solo su clínica | Solo su clínica | Solo su clínica |
| Tablero Enfermería | Todas las clínicas | Solo su clínica | Solo su clínica | Solo su clínica |
| Crear Ticket | Puede elegir clínica | Solo su clínica | Solo su clínica | N/A |
| Ver Detalle | Todos los tickets | Solo su clínica | Solo su clínica | Solo su clínica |
| Editar Ticket | Todos los tickets | Solo su clínica | Solo su clínica | N/A |

## 📊 Resumen de Resultados

**Total de casos:** 9
**Aprobados:** ___
**Fallidos:** ___
**Observaciones generales:**
```
[Espacio para resumen del QA]
```

## ✅ Checklist de Verificación Final

- [ ] Superusuario ve TODAS las clínicas en todas las vistas
- [ ] Admin de clínica ve SOLO su clínica
- [ ] Clínico ve SOLO su clínica
- [ ] Visualizador ve SOLO su clínica
- [ ] No se puede acceder a tickets de otras clínicas mediante URL directa
- [ ] Búsquedas respetan el filtro de clínica
- [ ] Estadísticas y KPIs están correctamente filtrados
- [ ] No hay errores de permisos en los logs

## 🐛 Bugs Encontrados
```
[Si se encontraron problemas de permisos, listarlos aquí con detalles]
```

## 🔒 Verificaciones de Seguridad
- [ ] No se puede saltear el filtro mediante parámetros URL
- [ ] Las queries SQL aplican correctamente el filtro WHERE
- [ ] No hay leaks de información entre clínicas
