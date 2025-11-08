# Backlog - Ticket Home

Registro de tareas pendientes, mejoras futuras y roadmap del proyecto.

---

## 🚀 En Progreso

### Próxima versión - Por definir
- Ninguna tarea en progreso actualmente

---

## 📋 Backlog Priorizado

### Alta Prioridad

#### Testing Automatizado
- [ ] Configurar pytest
- [ ] Tests unitarios para modelos
- [ ] Tests de integración para rutas críticas
- [ ] Tests para cálculo de FPA
- [ ] Tests para autenticación IAP
- [ ] CI/CD básico (cuando tengamos permisos)

#### Seguridad
- [ ] Auditoría de seguridad completa
- [ ] Implementar rate limiting
- [ ] Agregar CSRF tokens a todos los formularios
- [ ] Revisar y fortalecer validación de inputs
- [ ] Implementar logs de seguridad

#### Producción
- [ ] Planificar ambiente de producción
- [ ] Configurar backups automáticos de DB
- [ ] Configurar alertas de monitoreo
- [ ] Documentar plan de rollback
- [ ] Configurar domain production

### Media Prioridad

#### UX/UI
- [ ] Mejorar diseño responsive para tablets
- [ ] Agregar loading spinners en operaciones largas
- [ ] Implementar confirmaciones antes de acciones destructivas
- [ ] Mejorar mensajes de error (más descriptivos)
- [ ] Agregar shortcuts de teclado para operaciones comunes

#### Funcionalidad
- [ ] Exportar reportes a CSV (además de Excel)
- [ ] Filtros avanzados en listado de tickets
- [ ] Búsqueda de tickets por múltiples criterios
- [ ] Dashboard con KPIs más detallados
- [ ] Notificaciones por email para cambios de FPA

#### Performance
- [ ] Optimizar queries SQL (agregar índices)
- [ ] Implementar paginación en listados largos
- [ ] Cachear datos maestros (especialidades, cirugías)
- [ ] Optimizar carga de assets frontend
- [ ] Revisar y optimizar N+1 queries

### Baja Prioridad

#### Mejoras Técnicas
- [ ] Migrar de vanilla JS a framework (Vue.js o Alpine.js)
- [ ] Implementar API REST para integraciones futuras
- [ ] Agregar linting automático (flake8, black)
- [ ] Documentar API endpoints (si se crea API)
- [ ] Containerizar desarrollo local (docker-compose)

#### Documentación
- [ ] Video tutorial de uso del sistema
- [ ] Manual de usuario completo (PDF)
- [ ] Diagramas de flujo de procesos
- [ ] Documentar casos de uso edge
- [ ] FAQ para usuarios finales

#### Integraciones
- [ ] Integración con sistema HIS de RedSalud (futuro)
- [ ] Integración con calendario Google/Outlook
- [ ] Webhooks para eventos importantes
- [ ] SSO corporativo (si aplica)

---

## 💡 Ideas / Wishlist

### Funcionalidades Nuevas
- [ ] App móvil (React Native o Flutter)
- [ ] Notificaciones push
- [ ] Exportar a Google Calendar
- [ ] Predicción de FPA usando ML (basado en históricos)
- [ ] Chat interno entre usuarios
- [ ] Comentarios en tickets
- [ ] Adjuntar documentos a tickets

### Optimizaciones
- [ ] Migrar a PostgreSQL 16+
- [ ] Usar Cloud Run v2
- [ ] Implementar CDN para assets estáticos
- [ ] Usar Firestore para sesiones (vs memoria)
- [ ] Implementar service workers para offline

---

## 🐛 Bugs Conocidos

### Críticos
- Ninguno reportado actualmente

### Menores
- Ninguno reportado actualmente

---

## ✅ Completado Recientemente

### 2025-11-01 (v1.9.1 Superuser)
- [x] Gestión completa de superusuarios desde UI
  - Agregar opción "Superusuario" en formularios de creación/edición
  - Implementar lógica de creación de superusuarios desde UI
  - Implementar lógica de edición con gestión de tabla Superuser
  - Badge visual distintivo para superusuarios
- [x] Corregir método `is_admin()` para incluir superusuarios
- [x] Documentar funcionalidad en `resumen.md`
- [x] Crear `changelog.md` y `backlog.md`
- [x] Probar en local exhaustivamente
- [x] Versión v1.9.1 Superuser lista para deploy

### 2025-11-01 (v1.9.0 Foundation)
- [x] Documentación ejecutiva completa (resumen.md)
- [x] Documentación técnica completa (arquitectura-tecnica.md)
- [x] Seed mínimo para QA
- [x] Scripts de deployment actualizados
- [x] Deploy exitoso a DEV y QA

---

## 📊 Métricas

### Estado del Proyecto
- **Versión actual**: v1.9.1 Superuser (2025-11-01)
- **Ambientes activos**: DEV, QA (v1.9.0), próximo deploy v1.9.1
- **Cobertura de tests**: 0% (pendiente implementar)
- **Deuda técnica**: Baja
- **Documentación**: Alta (resumen.md + arquitectura-tecnica.md + changelog.md + backlog.md)

### Próximos Hitos
1. **v1.9.1**: Deploy a DEV y QA (próximos días)
2. **v2.0.0**: Testing automatizado + PROD (fecha TBD)
3. **v2.1.0**: Mejoras UX/UI (fecha TBD)

---

## 📝 Notas

- Este backlog se actualiza después de cada sesión de desarrollo
- Prioridades pueden cambiar según feedback del cliente (RedSalud)
- Items marcados con ⚠️ requieren aprobación del cliente
- Items marcados con 🔒 requieren permisos adicionales en GCP

---

**Última actualización**: 2025-11-01
