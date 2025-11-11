# 📁 Scripts SQL - Ticket Home

Esta carpeta contiene scripts SQL para gestión de datos en la base de datos de Ticket Home.

---

## 📋 Scripts Disponibles

### 1. `01_cleanup_keep_essentials.sql`
**Propósito**: Limpia la base de datos manteniendo solo la estructura esencial.

**Conserva**:
- ✅ Clínicas (9 clínicas RedSalud)
- ✅ Rangos horarios (discharge_time_slot)
- ✅ Superusuarios (tabla superuser)
- ✅ Control de migraciones (alembic_version)

**Elimina**:
- ❌ Usuarios
- ❌ Pacientes
- ❌ Tickets
- ❌ Especialidades
- ❌ Cirugías
- ❌ Doctores
- ❌ Razones estandarizadas
- ❌ Modificaciones de FPA
- ❌ Auditoría (login_audit, action_audit)

**Uso**:
```sql
-- Ejecutar en consola GCP SQL
-- Base de datos: mhw_ticket_home
-- Instancia: tickethome-db
```

---

### 2. `02_seed_full_demo_data.sql`
**Propósito**: Agrega datos de demostración completos para testing/demo.

**Crea**:
- 👥 28 usuarios (1 admin global + 27 usuarios de clínica)
  - Por cada clínica: admin, clinical, visualizador
  - Contraseña para todos: `password123`
- 🏥 36 especialidades (4 por clínica)
- 🔪 36 cirugías (4 por clínica)
- 👨‍⚕️ 18 doctores (2 por clínica)
- 📋 144 razones estandarizadas (16 por clínica)
- 🧑‍🦱 45 pacientes (5 por clínica)
- 🎫 135 tickets (15 por clínica)

**Prefijos de clínicas**:
- `IQQ` - Iquique
- `ELQ` - Elqui
- `VAL` - Valparaíso
- `PRO` - Providencia
- `STG` - Santiago
- `VIT` - Vitacura
- `RAN` - Rancagua
- `TEM` - Temuco
- `MAG` - Magallanes

**Usuarios de ejemplo**:
```
admin_IQQ@tickethome.com
clinical_VAL@tickethome.com
visualizador_STG@tickethome.com
```

---

## 🚀 Instrucciones de Uso

### Opción A: Limpiar y mantener solo esenciales

1. Ir a: [GCP SQL Query Editor](https://console.cloud.google.com/sql/instances/tickethome-db/query?project=ticket-home-demo)
2. Conectar a base de datos: `mhw_ticket_home`
3. Copiar y ejecutar: `01_cleanup_keep_essentials.sql`
4. Verificar resultado con el query de verificación incluido

### Opción B: Agregar datos de demo

1. (Opcional) Ejecutar primero `01_cleanup_keep_essentials.sql`
2. Copiar y ejecutar: `02_seed_full_demo_data.sql`
3. Verificar resultado con el query de verificación incluido

### Opción C: Reset completo con datos de demo

1. Ejecutar: `01_cleanup_keep_essentials.sql`
2. Ejecutar: `02_seed_full_demo_data.sql`
3. ✅ Base de datos lista con estructura base + datos de demo

---

## ⚠️ Advertencias

- **IMPORTANTE**: `01_cleanup_keep_essentials.sql` elimina TODOS los datos excepto clínicas, rangos horarios y superusuarios
- **BACKUP**: Siempre hacer backup antes de ejecutar scripts destructivos
- **PRODUCCIÓN**: NO ejecutar `02_seed_full_demo_data.sql` en ambientes de producción
- **TRANSACCIONES**: Ambos scripts usan `BEGIN/COMMIT` para atomicidad

---

## 📊 Datos Esperados Después de Ejecutar Ambos Scripts

| Tabla | Cantidad |
|-------|----------|
| Clínicas | 9 |
| Rangos horarios | 108 |
| Superusuarios | 2 |
| Usuarios | 28 |
| Especialidades | 36 |
| Cirugías | 36 |
| Doctores | 18 |
| Razones estandarizadas | 144 |
| Pacientes | 45 |
| Tickets | 135 |

---

## 🔐 Credenciales

**Usuarios de demo**:
- Usuario: `admin_[PREFIJO]` / `clinical_[PREFIJO]` / `visualizador_[PREFIJO]`
- Contraseña: `password123`

**Superusuarios** (acceso via IAP):
- `jonathan.segura@redsalud.cl`
- `jonathan.segura.vega@gmail.com`

---

## 📝 Notas

- Los scripts están diseñados para ser idempotentes donde sea posible
- Se usan transacciones para garantizar consistencia
- Incluyen queries de verificación al final
- Los hashes de contraseñas son generados con scrypt

---

**Fecha de creación**: 2025-11-10
**Versión**: V1 - beta RS
