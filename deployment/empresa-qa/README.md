# 🏢 Deployment - Empresa QA (RedSalud)

**Proyecto GCP**: `qa-ticket-home-redsalud`
**Región**: `southamerica-west1` (Chile)
**URL**: https://qa-ticket-home.mhwdev.dev

---

## ⚠️ IMPORTANTE - QA vs DEV

**Empresa QA** está configurado para ser **lo más cercano posible a producción**:

- ✅ **Solo SSO/IAP** (sin login tradicional)
- ✅ Grupo Google separado (`qa-ticket-home-rs@googlegroups.com`)
- ✅ Testing final antes de producción

---

## 📋 Prerequisitos

### Software
- ✅ Windows 10/11
- ✅ **Docker Desktop** instalado y **corriendo** (obligatorio)
- ✅ gcloud CLI instalado
- ✅ Acceso al proyecto `qa-ticket-home-redsalud`

### Permisos
- ✅ Miembro del grupo Google: `qa-ticket-home-rs@googlegroups.com`
- ✅ Roles GCP necesarios:
  - Cloud Run Admin
  - Artifact Registry Writer

---

## 🚀 Deployment Normal (Más Común)

Usa este workflow cuando cambies solo código (HTML, CSS, JS, Python) **sin cambios en models.py**.

### Paso 1: Build con Docker Desktop

```batch
1-build-push-local.bat
```

**Qué hace**:
- Build de imagen Docker **localmente** con Docker Desktop
- Push a Artifact Registry

**Tiempo**: ~5-10 minutos

### Paso 2: Deploy a Cloud Run

```batch
2-deploy-normal.bat
```

**Qué hace**:
- Deploy a Cloud Run con `RESET_DB_ON_STARTUP=false`
- Configura secrets, env vars, VPC Connector
- Aplica IAM policy bindings

**Tiempo**: ~3-5 minutos

---

## 🔄 Deployment con Reset DB (Cambios en Base de Datos)

Usa este workflow cuando:
- Cambios en `models.py` (nuevas tablas, campos, etc.)
- Primera vez deployando
- Necesitas recrear la base de datos

### Paso 1: Build (igual que antes)

```batch
1-build-push-local.bat
```

### Paso 2: Deploy con Reset DB

```batch
3-deploy-reset-db.bat
```

**⚠️ ADVERTENCIA**: Esto **borrará todos los datos** de la base de datos.

---

## 🔐 Setup Inicial de Secrets (Solo Primera Vez)

Si es la primera vez deployando o necesitas crear los secrets:

```batch
0-setup-secrets.bat
```

**Qué hace**:
- Crea secret `superuser-emails` en Secret Manager
- Asigna permisos al Service Account
- Verifica que los secrets se crearon correctamente

**Nota**: Los secrets `tickethome-db-url` y `tickethome-secret-key` ya existen.

---

## 📊 Configuración del Ambiente

### Variables de Entorno Cloud Run

```bash
ENVIRONMENT=production
FLASK_ENV=production
FLASK_DEBUG=false
ENABLE_IAP=true
ENABLE_DEMO_LOGIN=false         # ⚠️ Solo SSO en QA (sin login tradicional)
RESET_DB_ON_STARTUP=false       # (true en 3-deploy-reset-db.bat)
```

### Secrets Montados

```bash
DATABASE_URL → tickethome-db-url:latest
SECRET_KEY → tickethome-secret-key:latest
SUPERUSER_EMAILS → superuser-emails:latest
```

### Conexión a Base de Datos

- **Método**: VPC Connector (`tckthome-conn-qa-sa-west1`)
- **VPC Egress**: `private-ranges-only`
- **Cloud SQL**: `qa-ticket-home` (IP privada)

### Recursos Cloud Run

```bash
Min Instances: 1        # Siempre activo
Max Instances: 3
Memory: 1Gi
CPU: 2
Timeout: 900s (15 min)
Concurrency: 80
```

---

## 🔍 Verificación Post-Deployment

### 1. Verificar que el servicio está corriendo

```bash
gcloud run services describe ticket-home \
  --region=southamerica-west1 \
  --project=qa-ticket-home-redsalud
```

### 2. Verificar acceso web

```
URL: https://qa-ticket-home.mhwdev.dev
```

- **Debe redirigir a login de Google (IAP)**
- Autentícate con tu cuenta autorizada
- ⚠️ **NO hay login tradicional** en QA (solo SSO)

### 3. Verificar logs

```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=20 \
  --project=qa-ticket-home-redsalud
```

Busca errores o warnings.

---

## 🐛 Troubleshooting

### Error: "Docker Desktop no está corriendo"

**Solución**:
1. Inicia Docker Desktop
2. Espera a que muestre "Running"
3. Verifica: `docker ps`

### Error: "403 Forbidden" al acceder a la app

**Causa**: No estás en el grupo Google autorizado.

**Solución**:
- Verifica que seas miembro de: `qa-ticket-home-rs@googlegroups.com`
- **Nota**: En QA **NO hay** endpoint de demo login (solo SSO)

### Error: "Build failed" en Docker

**Causas comunes**:
- Docker Desktop sin memoria suficiente
- Dockerfile con errores

**Solución**:
1. Docker Desktop → Settings → Resources → Aumentar Memory a 4GB+
2. Verificar logs de build
3. Reiniciar Docker Desktop

### Error: "Secret not found"

**Solución**: Ejecuta `0-setup-secrets.bat`

---

## 📝 Diferencias con Empresa DEV

| Aspecto | Empresa QA | Empresa DEV |
|---------|------------|-------------|
| **Autenticación** | Solo SSO/IAP ⚠️ | SSO + Login tradicional |
| **Grupo Google** | qa-ticket-home-rs | rs-ticket-home |
| **Propósito** | Pre-producción | Testing funcional |
| **Login Demo** | ❌ Deshabilitado | ✅ Habilitado |

**Todo lo demás es idéntico** (región, build method, recursos, etc.)

---

## 📝 Diferencias con MHW DEV

| Aspecto | Empresa QA | MHW DEV |
|---------|------------|---------|
| **Proyecto** | qa-ticket-home-redsalud | ticket-home-demo |
| **Región** | southamerica-west1 🇨🇱 | us-central1 🇺🇸 |
| **Conexión BD** | VPC Connector | Cloud SQL Proxy |
| **Build** | Docker Desktop (local) | Cloud Build (remoto) |
| **Min Instances** | 1 (siempre activo) | 0 (escala a cero) |
| **Costos** | RedSalud paga | Tú pagas |
| **Autenticación** | Solo SSO ⚠️ | SSO + Login tradicional |

---

## ✅ Checklist de Testing en QA

Antes de dar OK para producción, verifica:

- [ ] Aplicación carga sin errores
- [ ] **Solo SSO funciona** (no hay login tradicional)
- [ ] Dashboard muestra datos correctos
- [ ] Panel de enfermería funciona
- [ ] Exportaciones funcionan (PDF, Excel)
- [ ] Búsqueda funciona
- [ ] Formularios validan correctamente
- [ ] Performance aceptable
- [ ] No hay errores en logs
- [ ] Usuarios correctos en tabla `superuser`

---

## 📚 Recursos Adicionales

- [Guía de Deployment](../README.md) - Comparación de todos los ambientes
- [Guía de Secretos](../mhw-dev/docs/SECRETS_GUIDE.md) - Cómo gestionar secrets
- [Arquitectura](../../docs/ARQUITECTURA.md) - Arquitectura del proyecto

---

**Última actualización**: 2025-11-15
**Mantenido por**: Jonathan Segura
