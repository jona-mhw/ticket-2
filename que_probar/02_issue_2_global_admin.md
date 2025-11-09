# QA Issue #2: Visualización de Usuario Global Admin

## 📝 Descripción del Cambio
Se agregó la visualización del usuario `global_admin` en la tabla de credenciales de la pantalla de login, con estilo distintivo.

## 🎯 Objetivo de la Prueba
Verificar que el usuario superusuario `global_admin` es visible y claramente identificable en la pantalla de login.

## ✅ Pre-requisitos
- Ninguno (prueba visual en pantalla de login)
- No requiere estar autenticado

## 📋 Casos de Prueba

### Caso 1: Visualización en Pantalla de Login
**Pasos:**
1. Cerrar sesión si está abierta
2. Navegar a `/auth/login` o `/auth/demo/login`
3. Observar la tabla de "Credenciales para Demo"

**Resultado Esperado:**
- ✅ Aparece una fila DESTACADA antes de la tabla de clínicas
- ✅ Fondo de color morado/purple (`bg-purple-50`)
- ✅ Texto dice "SUPERUSUARIO / GLOBAL ADMIN"
- ✅ Muestra el usuario: `global_admin`
- ✅ Incluye icono de escudo
- ✅ Texto explicativo: "(Acceso a todas las clínicas)"

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Captura de pantalla:**
```
[Adjuntar captura o describir lo que se ve]
```

---

### Caso 2: Login con Global Admin
**Pasos:**
1. En la pantalla de login
2. Ingresar credenciales:
   - Usuario: `global_admin`
   - Password: `password123`
3. Hacer clic en "Iniciar Sesión"

**Resultado Esperado:**
- ✅ Login exitoso
- ✅ Mensaje: "¡Bienvenido, global_admin!"
- ✅ Redirige a tablero de tickets o dashboard

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 3: Verificar Acceso a Todas las Clínicas
**Pasos:**
1. Iniciar sesión como `global_admin` / `password123`
2. Ir a "Dashboard" o "Tablero de Enfermería"
3. Observar los tickets visibles

**Resultado Esperado:**
- ✅ Muestra tickets de TODAS las clínicas
- ✅ No hay filtro de clínica aplicado automáticamente

**Resultado Obtenido:**
- [ ] ✅ Aprobado
- [ ] ❌ Fallido

**Notas:**
```
[Espacio para observaciones del QA]
```

---

### Caso 4: Comparación Visual con Otros Usuarios
**Pasos:**
1. Observar la tabla de credenciales completa
2. Comparar la fila de `global_admin` con las filas de clínicas

**Resultado Esperado:**
- ✅ Fila de global_admin es visualmente DISTINTA
- ✅ Color de fondo diferente (morado vs blanco)
- ✅ Ocupa todo el ancho de la tabla (colspan="4")
- ✅ Es la primera fila, arriba de las clínicas

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
-- Verificar que el usuario existe
SELECT id, username, email, role, clinic_id
FROM user
WHERE username = 'global_admin';

-- Verificar que está en tabla Superuser
SELECT id, email
FROM superuser
WHERE email = 'global_admin@tickethome.com';
```

**Resultado esperado de consultas:**
- Usuario existe con `clinic_id = NULL`
- Email está en tabla `superuser`

### Pruebas de Responsive
- [ ] Se ve bien en desktop (1920x1080)
- [ ] Se ve bien en laptop (1366x768)
- [ ] Se ve bien en tablet (768px)
- [ ] Se ve bien en móvil (375px)

## 📊 Resumen de Resultados

**Total de casos:** 4
**Aprobados:** ___
**Fallidos:** ___
**Observaciones generales:**
```
[Espacio para resumen del QA]
```

## 🐛 Bugs Encontrados
```
[Si se encontraron bugs, listarlos aquí con detalles]
```
