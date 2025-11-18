# 📋 Log de Ejecución - Deployment Ticket Home (Ambiente MHW)

**Fecha**: 2025-11-10
**Proyecto GCP**: `ticket-home-demo`
**Dominio**: `ticket-home-beta.mhwdev.dev`
**IP Load Balancer**: `34.8.122.103`

---

## 📑 Índice

1. [Configuración Inicial](#1-configuración-inicial)
2. [Cloud SQL - Base de Datos](#2-cloud-sql---base-de-datos)
3. [Secret Manager](#3-secret-manager)
4. [Service Account y Permisos](#4-service-account-y-permisos)
5. [Docker - Build y Push](#5-docker---build-y-push)
6. [Cloud Run - Deployment](#6-cloud-run---deployment)
7. [Load Balancer y SSL](#7-load-balancer-y-ssl)
8. [IAP - Identity-Aware Proxy](#8-iap---identity-aware-proxy)
9. [Inicialización de Base de Datos](#9-inicialización-de-base-de-datos)
10. [Troubleshooting](#10-troubleshooting)
11. [Verificación Final](#11-verificación-final)

---

## 1. Configuración Inicial

### 1.1. Cambio de Cuenta de Google Cloud

```bash
# Listar cuentas disponibles
gcloud auth list

# Cambiar a cuenta específica
gcloud config set account jonathan.segura.vega@gmail.com

# Verificar cuenta activa
gcloud config get-value account
```

### 1.2. Archivo de Configuración

Se creó el archivo `mhw-deployment/config.local.env` con las siguientes variables:

```bash
# Proyecto GCP
export GCP_PROJECT_ID="ticket-home-demo"
export GCP_REGION="us-central1"
export GCP_ZONE="us-central1-c"

# Aplicación
export APP_NAME="ticket-home"
export SERVICE_NAME="tickethome-demo"
export ENVIRONMENT="mhw"

# Dominio y DNS
export DOMAIN_NAME="ticket-home-beta.mhwdev.dev"
export RESERVED_IP_NAME="${SERVICE_NAME}-ip"

# Cloud SQL (Instancia existente)
export CLOUDSQL_INSTANCE_NAME="tickethome-db"
export CLOUDSQL_INSTANCE_CONNECTION_NAME="${GCP_PROJECT_ID}:${GCP_REGION}:${CLOUDSQL_INSTANCE_NAME}"
export CLOUDSQL_PUBLIC_IP="34.60.42.106"
export CLOUDSQL_PORT="5432"

# Nueva Base de Datos
export DB_NAME="mhw_ticket_home"
export DB_USER="mhw_user"
export DB_PASSWORD="ZHB5ChBBB3IWRLSi8WvQhrBkuQFUljQNMBlStNTkQJM"

# Secrets
export SECRET_DATABASE_URL_NAME="mhw-database-url"
export SECRET_KEY_NAME="mhw-secret-key"
export SECRET_SUPERUSER_EMAILS_NAME="mhw-superuser-emails"
export SECRET_KEY="c89554257e2e8b5794f76745a5c810d9cfa359a0e15d56cd7013f6ee4c402ef6"
export SUPERUSER_EMAILS="jonathan.segura.vega@gmail.com"

# Docker & Artifact Registry
export ARTIFACT_REGISTRY_REGION="us-central1"
export ARTIFACT_REGISTRY_REPO="tickethome-repo"
export IMAGE_NAME="${ARTIFACT_REGISTRY_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${APP_NAME}"

# Service Account
export SERVICE_ACCOUNT_NAME="${SERVICE_NAME}-sa"
export SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
```

---

## 2. Cloud SQL - Base de Datos

### 2.1. Crear Nueva Base de Datos

```bash
# Crear base de datos en instancia existente
gcloud sql databases create mhw_ticket_home \
  --instance=tickethome-db \
  --project=ticket-home-demo
```

**Resultado**: ✅ Base de datos `mhw_ticket_home` creada exitosamente.

### 2.2. Crear Usuario de Base de Datos

```bash
# Crear usuario para la base de datos
gcloud sql users create mhw_user \
  --instance=tickethome-db \
  --password="ZHB5ChBBB3IWRLSi8WvQhrBkuQFUljQNMBlStNTkQJM" \
  --project=ticket-home-demo
```

**Resultado**: ✅ Usuario `mhw_user` creado exitosamente.

### 2.3. Verificar IP Pública de Cloud SQL

```bash
# Obtener IP pública de la instancia
gcloud sql instances describe tickethome-db \
  --project=ticket-home-demo \
  --format="value(ipAddresses[0].ipAddress)"
```

**Resultado**: `34.60.42.106`

---

## 3. Secret Manager

### 3.1. Crear Secret para DATABASE_URL

**Versión 1** (IP Pública - NO funcionó):
```bash
gcloud secrets create mhw-database-url \
  --data-file=- \
  --project=ticket-home-demo <<EOF
postgresql://mhw_user:ZHB5ChBBB3IWRLSi8WvQhrBkuQFUljQNMBlStNTkQJM@34.60.42.106:5432/mhw_ticket_home
EOF
```

**Versión 2** (Unix Socket - ✅ FUNCIONÓ):
```bash
# Actualizar secret con Unix socket path para Cloud SQL Proxy
echo "postgresql://mhw_user:ZHB5ChBBB3IWRLSi8WvQhrBkuQFUljQNMBlStNTkQJM@/mhw_ticket_home?host=/cloudsql/ticket-home-demo:us-central1:tickethome-db" | \
  gcloud secrets versions add mhw-database-url \
  --data-file=- \
  --project=ticket-home-demo
```

### 3.2. Crear Secret para SECRET_KEY

```bash
echo "c89554257e2e8b5794f76745a5c810d9cfa359a0e15d56cd7013f6ee4c402ef6" | \
  gcloud secrets create mhw-secret-key \
  --data-file=- \
  --project=ticket-home-demo
```

### 3.3. Crear Secret para SUPERUSER_EMAILS

```bash
echo "jonathan.segura.vega@gmail.com" | \
  gcloud secrets create mhw-superuser-emails \
  --data-file=- \
  --project=ticket-home-demo
```

**Resultado**: ✅ Todos los secrets creados exitosamente.

---

## 4. Service Account y Permisos

### 4.1. Crear Service Account

```bash
gcloud iam service-accounts create tickethome-demo-sa \
  --display-name="Service Account for Ticket Home Demo" \
  --project=ticket-home-demo
```

### 4.2. Asignar Rol Cloud SQL Client

```bash
gcloud projects add-iam-policy-binding ticket-home-demo \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 4.3. Asignar Permisos a Secrets

```bash
# Permiso para DATABASE_URL
gcloud secrets add-iam-policy-binding mhw-database-url \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo

# Permiso para SECRET_KEY
gcloud secrets add-iam-policy-binding mhw-secret-key \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo

# Permiso para SUPERUSER_EMAILS
gcloud secrets add-iam-policy-binding mhw-superuser-emails \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo
```

**Resultado**: ✅ Service Account creado con todos los permisos necesarios.

---

## 5. Docker - Build y Push

### 5.1. Corrección del Dockerfile

**Problema inicial**: El contenedor no encontraba los módulos `services`, `repositories`, `dto`, `utils`, `validators`.

**Solución**: Actualizar Dockerfile para copiar todos los directorios necesarios:

```dockerfile
# Copia los archivos y directorios de la aplicación de forma explícita
COPY app.py .
COPY config.py .
COPY models.py .
COPY commands.py .
COPY db_indexes.py .
COPY auth_iap.py .
COPY routes ./routes
COPY services ./services
COPY repositories ./repositories
COPY dto ./dto
COPY utils ./utils
COPY validators ./validators
COPY templates ./templates
COPY static ./static
COPY migrations ./migrations
COPY .env.production .env
```

### 5.2. Configurar Autenticación de Docker

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 5.3. Build de Imagen Docker

```bash
docker build -t us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest .
```

### 5.4. Push a Artifact Registry

```bash
docker push us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest
```

**Resultado**: ✅ Imagen Docker construida y subida exitosamente.

---

## 6. Cloud Run - Deployment

### 6.1. Deployment Inicial (con IP Pública - FALLÓ)

```bash
gcloud run deploy tickethome-demo \
  --image=us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --region=us-central1 \
  --service-account=tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com \
  --set-secrets="DATABASE_URL=mhw-database-url:latest,SECRET_KEY=mhw-secret-key:latest,SUPERUSER_EMAILS=mhw-superuser-emails:latest" \
  --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=false,ENABLE_IAP=false,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false,ENVIRONMENT=production" \
  --memory=1Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=3 \
  --port=8080 \
  --allow-unauthenticated
```

**Error**: `connection to server at "34.60.42.106", port 5432 failed: Connection timed out`

### 6.2. Deployment Corregido (con Cloud SQL Proxy - ✅ FUNCIONÓ)

```bash
gcloud run deploy tickethome-demo \
  --image=us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --region=us-central1 \
  --service-account=tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com \
  --set-secrets="DATABASE_URL=mhw-database-url:latest,SECRET_KEY=mhw-secret-key:latest,SUPERUSER_EMAILS=mhw-superuser-emails:latest" \
  --set-env-vars="FLASK_ENV=development,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false,ENVIRONMENT=production" \
  --set-cloudsql-instances="ticket-home-demo:us-central1:tickethome-db" \
  --memory=1Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=3 \
  --port=8080 \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated
```

**Cambios clave**:
- Agregado `--set-cloudsql-instances` para habilitar Cloud SQL Proxy
- Cambiado `DATABASE_URL` a formato Unix socket
- Configurado `--ingress=internal-and-cloud-load-balancing` para IAP
- Configurado `--no-allow-unauthenticated`
- `ENABLE_IAP=true` y `ENABLE_DEMO_LOGIN=true` (modo híbrido)

**Resultado**: ✅ Cloud Run desplegado exitosamente con revisión `tickethome-demo-00020-rmc`.

---

## 7. Load Balancer y SSL

### 7.1. Verificar IP Reservada

```bash
gcloud compute addresses describe tickethome-demo-forwarding-rule \
  --global \
  --project=ticket-home-demo \
  --format="value(address)"
```

**Resultado**: `34.8.122.103` (ya existente)

### 7.2. Verificar Network Endpoint Group (NEG)

```bash
gcloud compute network-endpoint-groups describe tickethome-demo-neg \
  --region=us-central1 \
  --project=ticket-home-demo
```

**Resultado**: ✅ NEG ya existente y configurado.

### 7.3. Verificar Backend Service

```bash
gcloud compute backend-services describe tickethome-demo-backend \
  --global \
  --project=ticket-home-demo
```

**Resultado**: ✅ Backend Service ya existente con NEG adjunto.

### 7.4. Crear Certificado SSL

```bash
gcloud compute ssl-certificates create tickethome-demo-ssl \
  --domains=ticket-home-beta.mhwdev.dev \
  --global \
  --project=ticket-home-demo
```

**Resultado**: ✅ Certificado SSL creado (estado: PROVISIONING).

### 7.5. Actualizar HTTPS Proxy

```bash
gcloud compute target-https-proxies update tickethome-demo-https-proxy \
  --ssl-certificates=tickethome-demo-ssl \
  --global \
  --project=ticket-home-demo
```

**Resultado**: ✅ HTTPS Proxy actualizado con nuevo certificado.

### 7.6. Verificar Forwarding Rule

```bash
gcloud compute forwarding-rules describe tickethome-demo-forwarding-rule \
  --global \
  --project=ticket-home-demo
```

**Resultado**: ✅ Forwarding Rule ya configurado apuntando a IP `34.8.122.103`.

---

## 8. IAP - Identity-Aware Proxy

### 8.1. Verificar Estado de IAP

```bash
gcloud compute backend-services describe tickethome-demo-backend \
  --global \
  --project=ticket-home-demo \
  --format="get(iap)"
```

**Resultado**:
```
enabled=True
oauth2ClientId=999628011891-7jrsiimc8dsefit1ntc11b721j7pnjsb.apps.googleusercontent.com
oauth2ClientSecretSha256=52fd7b4533aa1a23aa0ff65f84bedf314dbfe1a1e2233b508ef4b51eaa498cae
```

✅ IAP ya habilitado con OAuth Client ID configurado.

### 8.2. Verificar Política de Acceso IAP

```bash
gcloud iap web get-iam-policy \
  --resource-type=backend-services \
  --service=tickethome-demo-backend \
  --project=ticket-home-demo
```

**Resultado**:
```yaml
bindings:
- members:
  - group:ticket-home-demo@googlegroups.com
  role: roles/iap.httpsResourceAccessor
```

✅ Solo el grupo `ticket-home-demo@googlegroups.com` tiene acceso.

---

## 9. Inicialización de Base de Datos

### 9.1. Crear Cloud Run Job para Init DB

```bash
gcloud run jobs create init-db-job \
  --image=us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --region=us-central1 \
  --project=ticket-home-demo \
  --service-account=tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com \
  --set-secrets="DATABASE_URL=mhw-database-url:latest,SECRET_KEY=mhw-secret-key:latest,SUPERUSER_EMAILS=mhw-superuser-emails:latest" \
  --set-env-vars="FLASK_ENV=development,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false,ENVIRONMENT=production" \
  --set-cloudsql-instances="ticket-home-demo:us-central1:tickethome-db" \
  --task-timeout=900 \
  --max-retries=0 \
  --args="flask,init-db"
```

### 9.2. Ejecutar Job de Inicialización

```bash
gcloud run jobs execute init-db-job \
  --region=us-central1 \
  --project=ticket-home-demo \
  --wait
```

**Resultado**: ✅ Base de datos inicializada con seed completo (9 clínicas, usuarios, especialidades, cirugías, pacientes, tickets).

### 9.3. Crear Job para Sync Superusers

```bash
gcloud run jobs create sync-superusers-job \
  --image=us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --region=us-central1 \
  --project=ticket-home-demo \
  --service-account=tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com \
  --set-secrets="DATABASE_URL=mhw-database-url:latest,SECRET_KEY=mhw-secret-key:latest,SUPERUSER_EMAILS=mhw-superuser-emails:latest" \
  --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false,ENVIRONMENT=production" \
  --set-cloudsql-instances="ticket-home-demo:us-central1:tickethome-db" \
  --task-timeout=900 \
  --max-retries=0 \
  --args="flask,sync-superusers"
```

---

## 10. Troubleshooting

### 10.1. Error: Acceso No Autorizado (IAP)

**Problema**: Usuario autenticado por IAP pero no registrado en base de datos.

**Mensaje de error**:
```
Acceso No Autorizado
Has sido autenticado correctamente a través de tu cuenta de Google, pero no tienes permiso para acceder a esta aplicación.

Tu cuenta de Google (jonathan.segura.vega@gmail.com) no está registrada en nuestra base de datos.
```

**Solución**: Agregar email a tabla `superuser` manualmente:

```sql
INSERT INTO "public"."superuser" (email)
VALUES ('jonathan.segura.vega@gmail.com')
ON CONFLICT (email) DO NOTHING;
```

**Alternativa**: Ejecutar `flask sync-superusers` mediante Cloud Run Job (automático desde `SUPERUSER_EMAILS` secret).

### 10.2. Error: Connection Timeout a Cloud SQL

**Problema**: Cloud Run no podía conectarse a Cloud SQL via IP pública.

**Solución**:
1. Cambiar DATABASE_URL a formato Unix socket
2. Agregar `--set-cloudsql-instances` en deployment de Cloud Run

### 10.3. Error: ModuleNotFoundError en Docker

**Problema**: Container no encontraba módulos `services`, `repositories`, etc.

**Solución**: Actualizar Dockerfile para copiar todos los directorios de la aplicación.

---

## 11. Verificación Final

### 11.1. Estado del Certificado SSL

```bash
gcloud compute ssl-certificates describe tickethome-demo-ssl \
  --global \
  --project=ticket-home-demo
```

**Estado**: `PROVISIONING` (puede tardar 15-60 minutos en activarse)

### 11.2. DNS Configuration Required

**Acción Pendiente**: Crear registro A en DNS:

```
Tipo: A
Nombre: ticket-home-beta.mhwdev.dev
Valor: 34.8.122.103
TTL: 300
```

### 11.3. Acceso a la Aplicación

**URL**: https://ticket-home-beta.mhwdev.dev

**Flujo de Autenticación**:
1. Redirect a login de Google (IAP)
2. Autenticación con cuenta autorizada (miembro de `ticket-home-demo@googlegroups.com`)
3. Si el usuario está en tabla `superuser`, se crea automáticamente con rol ADMIN
4. Acceso a la aplicación

**URL Demo Login**: https://ticket-home-beta.mhwdev.dev/auth/demo-login

### 11.4. Credenciales de Base de Datos

**Para acceso directo a Cloud SQL**:
- **Host**: `34.60.42.106` (IP pública)
- **Puerto**: `5432`
- **Base de datos**: `mhw_ticket_home`
- **Usuario**: `mhw_user`
- **Contraseña**: `ZHB5ChBBB3IWRLSi8WvQhrBkuQFUljQNMBlStNTkQJM`

---

## 📊 Resumen de Recursos Creados

| Recurso | Nombre | Estado |
|---------|--------|--------|
| Base de Datos | `mhw_ticket_home` | ✅ Activo |
| Usuario DB | `mhw_user` | ✅ Activo |
| Secret Manager | `mhw-database-url` | ✅ Activo (v2) |
| Secret Manager | `mhw-secret-key` | ✅ Activo |
| Secret Manager | `mhw-superuser-emails` | ✅ Activo |
| Service Account | `tickethome-demo-sa` | ✅ Activo |
| Imagen Docker | `ticket-home:latest` | ✅ Subida |
| Cloud Run Service | `tickethome-demo` | ✅ Activo (rev 00020-rmc) |
| Cloud Run Job | `init-db-job` | ✅ Ejecutado |
| Cloud Run Job | `sync-superusers-job` | ✅ Creado |
| SSL Certificate | `tickethome-demo-ssl` | ⏳ Provisioning |
| HTTPS Proxy | `tickethome-demo-https-proxy` | ✅ Actualizado |
| Forwarding Rule | `tickethome-demo-forwarding-rule` | ✅ Activo |
| Backend Service | `tickethome-demo-backend` | ✅ Activo (IAP habilitado) |
| Network Endpoint Group | `tickethome-demo-neg` | ✅ Activo |

---

## 🎯 Configuración Final

### Variables de Entorno Cloud Run

```bash
FLASK_ENV=development
FLASK_DEBUG=false
ENABLE_IAP=true
ENABLE_DEMO_LOGIN=true
RESET_DB_ON_STARTUP=false
ENVIRONMENT=production
```

### Secrets Montados

```bash
DATABASE_URL → mhw-database-url:latest
SECRET_KEY → mhw-secret-key:latest
SUPERUSER_EMAILS → mhw-superuser-emails:latest
```

### Cloud SQL Connection

```bash
--set-cloudsql-instances="ticket-home-demo:us-central1:tickethome-db"
```

### Ingress y Autenticación

```bash
--ingress=internal-and-cloud-load-balancing
--no-allow-unauthenticated
```

---

## ✅ Checklist de Deployment Completado

- [x] Base de datos creada en Cloud SQL
- [x] Usuario de base de datos configurado
- [x] Secrets creados en Secret Manager
- [x] Service Account con permisos configurado
- [x] Dockerfile corregido
- [x] Imagen Docker construida y subida
- [x] Cloud Run desplegado con Cloud SQL Proxy
- [x] Base de datos inicializada con seed completo
- [x] Load Balancer configurado
- [x] Certificado SSL creado (en provisioning)
- [x] IAP habilitado y verificado
- [x] Política de acceso IAP configurada
- [ ] DNS configurado (pendiente por usuario)
- [ ] Certificado SSL activo (pendiente 15-60 min)
- [ ] Usuario agregado a grupo Google (ticket-home-demo@googlegroups.com)
- [ ] Usuario agregado a tabla superuser

---

## 📞 Contacto y Soporte

**Administrador**: jonathan.segura.vega@gmail.com
**Grupo de Acceso IAP**: ticket-home-demo@googlegroups.com
**Proyecto GCP**: ticket-home-demo
**Repositorio**: https://github.com/jona-mhw/ticket-2

---

**Generado por**: Claude Code
**Fecha**: 2025-11-10
**Versión**: 1.0.0
