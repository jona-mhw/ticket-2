# 🏢 Deployment - Empresa DEV (RedSalud)

**Proyecto GCP**: `dev-ticket-home-redsalud`
**Región**: `southamerica-west1` (Chile)
**URL**: https://ticket-home.mhwdev.dev

---

## 📋 Prerequisitos

### Software
- ✅ Windows 10/11
- ✅ **Docker Desktop** instalado y **corriendo** (obligatorio)
- ✅ gcloud CLI instalado
- ✅ Acceso al proyecto `dev-ticket-home-redsalud`

### Permisos
- ✅ Miembro del grupo Google: `rs-ticket-home@googlegroups.com`
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

**Requisitos**:
- Docker Desktop **debe estar corriendo**
- Verifica con: `docker ps`

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
ENABLE_DEMO_LOGIN=true          # ✅ Login tradicional habilitado en DEV
RESET_DB_ON_STARTUP=false       # (true en 3-deploy-reset-db.bat)
```

### Secrets Montados

```bash
DATABASE_URL → tickethome-db-url:latest
SECRET_KEY → tickethome-secret-key:latest
SUPERUSER_EMAILS → superuser-emails:latest
```

### Conexión a Base de Datos

- **Método**: VPC Connector (`tckthome-conn-sa-west1`)
- **VPC Egress**: `private-ranges-only`
- **Cloud SQL**: `dev-ticket-home` (IP privada)

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
  --project=dev-ticket-home-redsalud
```

### 2. Verificar acceso web

```
URL: https://ticket-home.mhwdev.dev
```

- Debe redirigir a login de Google (IAP)
- Autentícate con tu cuenta autorizada
- También puedes usar login tradicional (usuario/password)

### 3. Verificar logs

```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=20 \
  --project=dev-ticket-home-redsalud
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
- Verifica que seas miembro de: `rs-ticket-home@googlegroups.com`
- O usa el endpoint de demo login: `https://ticket-home.mhwdev.dev/auth/demo-login`

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

## 📝 Diferencias con MHW DEV

| Aspecto | Empresa DEV | MHW DEV |
|---------|-------------|---------|
| **Proyecto** | dev-ticket-home-redsalud | ticket-home-demo |
| **Región** | southamerica-west1 🇨🇱 | us-central1 🇺🇸 |
| **Conexión BD** | VPC Connector | Cloud SQL Proxy |
| **Build** | Docker Desktop (local) | Cloud Build (remoto) |
| **Min Instances** | 1 (siempre activo) | 0 (escala a cero) |
| **Costos** | RedSalud paga | Tú pagas |

---

## 📚 Recursos Adicionales

- [Guía de Deployment](../README.md) - Comparación de todos los ambientes
- [Guía de Secretos](../mhw-dev/docs/SECRETS_GUIDE.md) - Cómo gestionar secrets
- [Arquitectura](../../docs/ARQUITECTURA.md) - Arquitectura del proyecto

---

**Última actualización**: 2025-11-15
**Mantenido por**: Jonathan Segura
