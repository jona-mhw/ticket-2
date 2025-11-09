# Guía de QA - Mejoras del Sistema de Tickets

Esta carpeta contiene toda la documentación necesaria para realizar el QA de las mejoras implementadas en el sistema de tickets.

## 📋 Issues Resueltos

### ✅ Issue #1: Validación de Hora de Pabellón en el Futuro
- **Archivo modificado**: `validators/ticket_validator.py`
- **Cambio**: Se eliminó la validación que impedía crear tickets con hora de fin de pabellón en el futuro

### ✅ Issue #2: Usuario Global Admin Visible
- **Archivo modificado**: `templates/login.html`
- **Cambio**: Se agregó visualización del usuario `global_admin` en la pantalla de login

### ✅ Issue #3: Sistema de Configuración de Colores
- **Archivos nuevos**:
  - `models.py` (modelo UrgencyThreshold)
  - `migrations/versions/e7f8g9h0i1j2_add_urgency_threshold_table.py`
  - `routes/admin.py` (nuevas rutas)
  - `templates/admin/color_thresholds.html`
- **Archivos modificados**:
  - `templates/tickets/nursing_board.html`
- **Cambio**: Sistema completo para configurar umbrales de colores de tickets

### ✅ Issue #4: Optimización de Tamaño de Tarjetas
- **Archivo modificado**: `templates/tickets/nursing_board.html` (CSS)
- **Cambio**: Reducción de tamaño de tarjetas de 380px a 320px manteniendo toda la información

### ✅ Issue #5: Filtros de Dashboard según Rol
- **Estado**: Verificado - Ya implementado correctamente
- **Confirmación**: Los filtros funcionan correctamente en dashboard y todas las vistas

## 📁 Documentos de QA

- [01_issue_1_validacion_pabellon.md](01_issue_1_validacion_pabellon.md) - Pruebas de creación de tickets con pabellón futuro
- [02_issue_2_global_admin.md](02_issue_2_global_admin.md) - Pruebas de visualización del superusuario
- [03_issue_3_colores_configurables.md](03_issue_3_colores_configurables.md) - Pruebas del sistema de configuración de colores
- [04_issue_4_optimizacion_tarjetas.md](04_issue_4_optimizacion_tarjetas.md) - Pruebas de visualización de tarjetas optimizadas
- [05_issue_5_filtros_dashboard.md](05_issue_5_filtros_dashboard.md) - Pruebas de filtros por rol

## 🚀 Configuración Inicial para QA

### Requisitos Previos
1. Base de datos configurada con datos de prueba
2. Aplicación corriendo en entorno local
3. Usuarios de prueba creados (ver credenciales más abajo)

### Configuración de Base de Datos
```bash
# Opción 1: Resetear BD con datos de demo
flask reset-db

# Opción 2: Aplicar solo la nueva migración
flask db upgrade
```

### Usuarios de Prueba
**Usuario Superusuario:**
- Usuario: `global_admin`
- Password: `password123`
- Acceso: Todas las clínicas

**Usuario Administrador (ejemplo):**
- Usuario: `admin_prov`
- Password: `password123`
- Acceso: Solo Clínica Providencia

**Usuario Clínico (ejemplo):**
- Usuario: `clinical_prov`
- Password: `password123`
- Acceso: Solo Clínica Providencia

## ⚠️ Puntos Críticos a Probar

1. **Creación de Tickets Futuros**: Verificar que NO aparezca error al crear tickets con fecha futura
2. **Visualización de Global Admin**: Debe ser claramente visible en la pantalla de login
3. **Configuración de Colores**: Cambios deben reflejarse inmediatamente en el tablero
4. **Tamaño de Tarjetas**: Debe verse más compacto pero legible
5. **Filtros por Rol**: Superusuarios ven todo, otros solo su clínica

## 📊 Orden Recomendado de Pruebas

1. Primero: Issue #2 (verificar login)
2. Segundo: Issue #5 (verificar filtros con diferentes usuarios)
3. Tercero: Issue #1 (crear tickets con fecha futura)
4. Cuarto: Issue #4 (verificar visualización de tarjetas)
5. Quinto: Issue #3 (configurar y probar colores)

## 🐛 Reporte de Bugs

Si encuentras algún problema durante el QA, por favor documentar:
- Issue relacionado
- Pasos para reproducir
- Resultado esperado vs resultado obtenido
- Usuario con el que se probó
- Captura de pantalla si es relevante
