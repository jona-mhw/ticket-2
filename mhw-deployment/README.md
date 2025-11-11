# 🚀 Deployment Ticket Home - Ambiente MHW (GCP)

**Versión:** V1 - Beta RS
**Última actualización:** 2025-11-10
**Ambiente:** Producción MHW con IAP

Guía completa para deployment de Ticket Home en Google Cloud Platform usando Cloud Run, Cloud SQL, IAP, Load Balancer y SSL administrado.

---

## 📋 Tabla de Contenidos

- [Resumen Ejecutivo](#-resumen-ejecutivo)
- [Arquitectura](#-arquitectura)
- [Prerequisitos](#-prerequisitos)
- [Guía de Deployment](#-guía-de-deployment)
- [Configuración de Base de Datos](#-configuración-de-base-de-datos)
- [Troubleshooting](#-troubleshooting)
- [Mantenimiento](#-mantenimiento)

---

## 📊 Resumen Ejecutivo

### Deployment Actual (Referencia)

| Componente | Valor |
|------------|-------|
| **Proyecto GCP** | `ticket-home-demo` |
| **Región** | `us-central1` |
| **Dominio** | `ticket-home-beta.mhwdev.dev` |
| **IP Load Balancer** | `34.8.122.103` |
| **Cloud Run** | `tickethome-demo` |
| **Cloud SQL** | `tickethome-db` (IP: 34.60.42.106) |
| **Base de Datos** | `mhw_ticket_home` |
| **Repositorio Docker** | `us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo` |

### Características

- ✅ **Cloud Run** - Servicio serverless con autoscaling
- ✅ **Cloud SQL Proxy** - Conexión segura via Unix socket
- ✅ **Secret Manager** - Gestión de credenciales
- ✅ **Load Balancer HTTPS** - Certificado SSL administrado por Google
- ✅ **IAP** - Autenticación con Google SSO
- ✅ **Modo Híbrido** - IAP + Demo Login habilitado
- ✅ **Seed Minimalista** - Solo clínicas y rangos horarios

---

## 🏗️ Arquitectura

```
Usuario
  ↓
DNS (ticket-home-beta.mhwdev.dev → 34.8.122.103)
  ↓
Load Balancer Global (HTTPS)
  ↓
SSL Certificate (Google-managed)
  ↓
HTTPS Target Proxy
  ↓
Backend Service (IAP habilitado)
  ↓
Network Endpoint Group (Serverless NEG)
  ↓
Cloud Run Service (tickethome-demo)
  ├→ Cloud SQL Proxy (Unix socket)
  └→ Secret Manager (DATABASE_URL, SECRET_KEY, SUPERUSER_EMAILS)
     ↓
  Cloud SQL (mhw_ticket_home)
```

### Componentes Clave

1. **Load Balancer**: IP estática global con SSL
2. **IAP**: Autenticación OAuth 2.0 con Google
3. **Cloud Run**: Container con Cloud SQL Proxy integrado
4. **Secrets**: Almacenados en Secret Manager
5. **Database**: PostgreSQL en Cloud SQL

---

## ✅ Prerequisitos

### Software

- ✅ `gcloud CLI` instalado y configurado
- ✅ `docker` (para builds locales) o usar Cloud Build
- ✅ Acceso al proyecto GCP con permisos de admin

### Recursos GCP

- ✅ **Proyecto GCP** creado
- ✅ **Instancia Cloud SQL** (PostgreSQL)
- ✅ **Dominio** configurado
- ✅ **Acceso DNS** para crear registro A

### Permisos Necesarios

```
- Cloud Run Admin
- Compute Admin
- Cloud SQL Admin
- Secret Manager Admin
- Service Account Admin
- Security Admin (para IAP)
```

---

## 🚀 Guía de Deployment

### Paso 0: Preparación

1. **Configurar cuenta GCP**:
```bash
gcloud auth login
gcloud config set project ticket-home-demo
gcloud config set account jonathan.segura.vega@gmail.com
```

2. **Clonar repositorio**:
```bash
git clone https://github.com/jona-mhw/ticket-2
cd ticket-2
```

3. **Crear archivo de configuración**:
```bash
cd mhw-deployment
cp config.env config.local.env
# Editar config.local.env con tus valores
```

---

### Paso 1: Cloud SQL - Base de Datos

**1.1. Crear nueva base de datos** (si no existe):
```bash
gcloud sql databases create mhw_ticket_home \
  --instance=tickethome-db \
  --project=ticket-home-demo
```

**1.2. Crear usuario de base de datos**:
```bash
# Generar contraseña segura
DB_PASSWORD=$(openssl rand -base64 32)
echo "Guardar esta contraseña: $DB_PASSWORD"

# Crear usuario
gcloud sql users create mhw_user \
  --instance=tickethome-db \
  --password="$DB_PASSWORD" \
  --project=ticket-home-demo
```

**1.3. Obtener información de conexión**:
```bash
# IP pública de Cloud SQL
gcloud sql instances describe tickethome-db \
  --project=ticket-home-demo \
  --format="value(ipAddresses[0].ipAddress)"

# Connection name para Cloud SQL Proxy
gcloud sql instances describe tickethome-db \
  --project=ticket-home-demo \
  --format="value(connectionName)"
# Resultado: ticket-home-demo:us-central1:tickethome-db
```

---

### Paso 2: Secret Manager

**2.1. Crear DATABASE_URL** (usando Unix socket para Cloud SQL Proxy):
```bash
# Formato: postgresql://USER:PASSWORD@/DATABASE?host=/cloudsql/CONNECTION_NAME
DATABASE_URL="postgresql://mhw_user:YOUR_PASSWORD@/mhw_ticket_home?host=/cloudsql/ticket-home-demo:us-central1:tickethome-db"

echo "$DATABASE_URL" | gcloud secrets create mhw-database-url \
  --data-file=- \
  --project=ticket-home-demo
```

**2.2. Crear SECRET_KEY**:
```bash
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo "$SECRET_KEY" | gcloud secrets create mhw-secret-key \
  --data-file=- \
  --project=ticket-home-demo
```

**2.3. Crear SUPERUSER_EMAILS**:
```bash
# Separar emails con punto y coma (;)
SUPERUSER_EMAILS="jonathan.segura@redsalud.cl;jonathan.segura.vega@gmail.com"

echo "$SUPERUSER_EMAILS" | gcloud secrets create mhw-superuser-emails \
  --data-file=- \
  --project=ticket-home-demo
```

---

### Paso 3: Service Account

**3.1. Crear Service Account**:
```bash
gcloud iam service-accounts create tickethome-demo-sa \
  --display-name="Service Account for Ticket Home Demo" \
  --project=ticket-home-demo
```

**3.2. Asignar rol Cloud SQL Client**:
```bash
gcloud projects add-iam-policy-binding ticket-home-demo \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

**3.3. Dar acceso a los secrets**:
```bash
# DATABASE_URL
gcloud secrets add-iam-policy-binding mhw-database-url \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo

# SECRET_KEY
gcloud secrets add-iam-policy-binding mhw-secret-key \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo

# SUPERUSER_EMAILS
gcloud secrets add-iam-policy-binding mhw-superuser-emails \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo
```

---

### Paso 4: Docker Build & Push

**IMPORTANTE**: El Dockerfile ya está configurado correctamente. NO necesita modificaciones.

**Opción A: Build local** (requiere Docker Desktop ejecutándose):
```bash
cd .. # Volver a la raíz del proyecto

# Configurar autenticación
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build
docker build -t us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest .

# Push
docker push us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest
```

**Opción B: Cloud Build** (recomendado - más rápido):
```bash
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --project=ticket-home-demo \
  --timeout=20m
```

---

### Paso 5: Cloud Run Deployment

**5.1. Deploy inicial**:
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
  --no-allow-unauthenticated \
  --project=ticket-home-demo
```

**Notas importantes**:
- `--set-cloudsql-instances`: Habilita Cloud SQL Proxy (conexión via Unix socket)
- `--ingress=internal-and-cloud-load-balancing`: Solo accesible via Load Balancer
- `--no-allow-unauthenticated`: Requiere autenticación (IAP)
- `ENABLE_IAP=true` y `ENABLE_DEMO_LOGIN=true`: Modo híbrido

---

### Paso 6: Load Balancer + SSL

**6.1. Crear Network Endpoint Group (NEG)**:
```bash
gcloud compute network-endpoint-groups create tickethome-demo-neg \
  --region=us-central1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=tickethome-demo \
  --project=ticket-home-demo
```

**6.2. Crear Backend Service**:
```bash
gcloud compute backend-services create tickethome-demo-backend \
  --global \
  --load-balancing-scheme=EXTERNAL \
  --protocol=HTTPS \
  --project=ticket-home-demo

# Agregar NEG al backend
gcloud compute backend-services add-backend tickethome-demo-backend \
  --global \
  --network-endpoint-group=tickethome-demo-neg \
  --network-endpoint-group-region=us-central1 \
  --project=ticket-home-demo
```

**6.3. Crear certificado SSL**:
```bash
gcloud compute ssl-certificates create tickethome-demo-ssl \
  --domains=ticket-home-beta.mhwdev.dev \
  --global \
  --project=ticket-home-demo
```

**6.4. Crear URL Map**:
```bash
gcloud compute url-maps create tickethome-demo-url-map \
  --default-service=tickethome-demo-backend \
  --global \
  --project=ticket-home-demo
```

**6.5. Crear HTTPS Proxy**:
```bash
gcloud compute target-https-proxies create tickethome-demo-https-proxy \
  --ssl-certificates=tickethome-demo-ssl \
  --url-map=tickethome-demo-url-map \
  --global \
  --project=ticket-home-demo
```

**6.6. Reservar IP y crear Forwarding Rule**:
```bash
# Reservar IP estática
gcloud compute addresses create tickethome-demo-ip \
  --global \
  --project=ticket-home-demo

# Obtener la IP
gcloud compute addresses describe tickethome-demo-ip \
  --global \
  --project=ticket-home-demo \
  --format="value(address)"

# Crear Forwarding Rule
gcloud compute forwarding-rules create tickethome-demo-forwarding-rule \
  --global \
  --target-https-proxy=tickethome-demo-https-proxy \
  --address=tickethome-demo-ip \
  --ports=443 \
  --project=ticket-home-demo
```

**6.7. Configurar DNS**:
```
Tipo: A
Nombre: ticket-home-beta.mhwdev.dev
Valor: [IP del paso anterior]
TTL: 300
```

---

### Paso 7: IAP (Identity-Aware Proxy)

**IMPORTANTE**: Algunos pasos de IAP deben hacerse manualmente en la consola web.

**7.1. Configurar OAuth Consent Screen** (MANUAL):

1. Ir a: https://console.cloud.google.com/apis/credentials/consent?project=ticket-home-demo
2. Configurar:
   - Tipo: Interno o Externo (según necesidad)
   - Nombre: "Ticket Home"
   - Email de soporte: tu email
   - Dominios autorizados: `mhwdev.dev`

**7.2. Crear OAuth Client ID** (MANUAL):

1. Ir a: https://console.cloud.google.com/apis/credentials?project=ticket-home-demo
2. Crear credenciales > OAuth Client ID
3. Tipo: Aplicación web
4. URIs de redirección: Dejar vacío (IAP lo maneja)
5. Guardar Client ID y Client Secret

**7.3. Habilitar IAP en Backend Service** (MANUAL o via CLI):

Via CLI (requiere Client ID):
```bash
gcloud iap web enable \
  --resource-type=backend-services \
  --oauth2-client-id=YOUR_CLIENT_ID \
  --oauth2-client-secret=YOUR_CLIENT_SECRET \
  --service=tickethome-demo-backend \
  --project=ticket-home-demo
```

Via Console (más fácil):
1. Ir a: https://console.cloud.google.com/security/iap?project=ticket-home-demo
2. Buscar `tickethome-demo-backend`
3. Toggle IAP a ON
4. Seleccionar OAuth Client creado

**7.4. Configurar acceso** (quien puede acceder):
```bash
# Opción A: Por grupo de Google
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=tickethome-demo-backend \
  --member="group:ticket-home-demo@googlegroups.com" \
  --role="roles/iap.httpsResourceAccessor" \
  --project=ticket-home-demo

# Opción B: Por usuario individual
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=tickethome-demo-backend \
  --member="user:jonathan.segura.vega@gmail.com" \
  --role="roles/iap.httpsResourceAccessor" \
  --project=ticket-home-demo
```

---

## 💾 Configuración de Base de Datos

### Opción 1: Inicializar con Seed Minimalista (Recomendado para Producción)

Ejecuta este script SQL en la consola de GCP:

```sql
-- Agregar superusuarios
INSERT INTO public.superuser (email) VALUES
    ('jonathan.segura@redsalud.cl'),
    ('jonathan.segura.vega@gmail.com')
ON CONFLICT (email) DO NOTHING;
```

Luego, cuando accedas via IAP, tu usuario se creará automáticamente con rol ADMIN.

### Opción 2: Limpiar Base de Datos

Ejecutar: `_sql/01_cleanup_keep_essentials.sql`

Este script:
- ✅ Mantiene: clínicas, rangos horarios, superusuarios
- ❌ Elimina: usuarios, pacientes, tickets, especialidades, cirugías, doctores, auditoría

### Opción 3: Agregar Datos de Demo

Ejecutar: `_sql/02_seed_full_demo_data.sql`

Este script crea:
- 28 usuarios (contraseña: `password123`)
- 36 especialidades
- 36 cirugías
- 18 doctores
- 144 razones estandarizadas
- 45 pacientes
- 135 tickets

---

## 🔧 Mantenimiento

### Actualizar Aplicación (Re-deploy)

```bash
# 1. Build nueva imagen
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --project=ticket-home-demo

# 2. Deploy (usa el mismo comando del Paso 5.1)
gcloud run deploy tickethome-demo \
  --image=us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --region=us-central1 \
  [... resto de parámetros ...]
```

### Actualizar Secrets

```bash
# Actualizar DATABASE_URL (ejemplo)
echo "NEW_VALUE" | gcloud secrets versions add mhw-database-url \
  --data-file=- \
  --project=ticket-home-demo

# Re-deploy Cloud Run para usar nueva versión
gcloud run services update tickethome-demo \
  --region=us-central1 \
  --project=ticket-home-demo
```

### Ver Logs

```bash
# Logs de Cloud Run
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --project=ticket-home-demo \
  --format="table(timestamp,severity,textPayload)"

# Logs en tiempo real
gcloud logging tail "resource.type=cloud_run_revision" \
  --project=ticket-home-demo
```

---

## 🚨 Troubleshooting

### Error: "Connection timeout" a Cloud SQL

**Causa**: DATABASE_URL mal configurado o Cloud SQL Proxy no conectado.

**Solución**:
1. Verificar que DATABASE_URL use formato Unix socket:
   ```
   postgresql://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE
   ```
2. Verificar que Cloud Run tenga `--set-cloudsql-instances` configurado

### Error: "Access denied" al acceder a la app

**Causa**: Usuario no autorizado en IAP.

**Solución**:
1. Verificar que el usuario esté en el grupo de Google autorizado
2. O agregar usuario individual:
   ```bash
   gcloud iap web add-iam-policy-binding \
     --resource-type=backend-services \
     --service=tickethome-demo-backend \
     --member="user:EMAIL@example.com" \
     --role="roles/iap.httpsResourceAccessor" \
     --project=ticket-home-demo
   ```

### Error: Certificado SSL en "PROVISIONING"

**Causa**: Normal, el certificado tarda 15-60 minutos en aprovisionarse.

**Solución**: Esperar y verificar:
```bash
gcloud compute ssl-certificates describe tickethome-demo-ssl \
  --global \
  --project=ticket-home-demo \
  --format="get(managed.status)"
```

Estado esperado final: `ACTIVE`

### Error: "Usuario no registrado" después de autenticarse con IAP

**Causa**: Email no está en tabla `superuser`.

**Solución**:
```sql
INSERT INTO public.superuser (email) VALUES ('tu-email@example.com');
```

### Error: "Multiple users with same email"

**Causa**: Conflicto de emails duplicados (ya no debería pasar con V1).

**Solución**: La validación en `auth_iap.py` previene esto. Si ocurre, eliminar usuarios duplicados:
```sql
-- Ver usuarios duplicados
SELECT email, COUNT(*) FROM public.user GROUP BY email HAVING COUNT(*) > 1;

-- Eliminar duplicados manualmente
```

---

## 📊 Verificación Post-Deployment

### Checklist de Verificación

- [ ] DNS apunta a IP correcta (`nslookup ticket-home-beta.mhwdev.dev`)
- [ ] Certificado SSL activo (`gcloud compute ssl-certificates describe ...`)
- [ ] Cloud Run desplegado (`gcloud run services describe tickethome-demo ...`)
- [ ] IAP habilitado (`gcloud compute backend-services describe ...`)
- [ ] Acceso web funcional (https://ticket-home-beta.mhwdev.dev)
- [ ] Login IAP funcional
- [ ] Superusuarios pueden acceder
- [ ] Clínicas cargadas en BD
- [ ] Rangos horarios creados

---

## 📚 Referencias

### Archivos Importantes

- `_sql/01_cleanup_keep_essentials.sql` - Limpiar BD
- `_sql/02_seed_full_demo_data.sql` - Datos de demo
- `DEPLOYMENT_LOG.md` - Log detallado del primer deployment
- `Dockerfile` - Ya configurado correctamente

### Comandos Útiles

```bash
# Estado de Cloud Run
gcloud run services describe tickethome-demo --region=us-central1

# Estado de Backend Service
gcloud compute backend-services describe tickethome-demo-backend --global

# Estado de SSL
gcloud compute ssl-certificates list --global

# Logs en tiempo real
gcloud logging tail "resource.type=cloud_run_revision"

# Listar secrets
gcloud secrets list

# Ver versiones de un secret
gcloud secrets versions list mhw-database-url
```

---

## 🎯 Valores de Referencia (Deployment Actual)

Usar estos valores como referencia para deployments similares:

```bash
# Proyecto y Región
PROJECT_ID="ticket-home-demo"
REGION="us-central1"

# Service Account
SA_EMAIL="tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com"

# Cloud SQL
INSTANCE_NAME="tickethome-db"
CONNECTION_NAME="ticket-home-demo:us-central1:tickethome-db"
DB_NAME="mhw_ticket_home"
DB_USER="mhw_user"

# Secrets
SECRET_DATABASE_URL="mhw-database-url"
SECRET_KEY_NAME="mhw-secret-key"
SECRET_SUPERUSERS="mhw-superuser-emails"

# Docker
IMAGE_URL="us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest"

# Load Balancer
NEG_NAME="tickethome-demo-neg"
BACKEND_SERVICE="tickethome-demo-backend"
SSL_CERT="tickethome-demo-ssl"
URL_MAP="tickethome-demo-url-map"
HTTPS_PROXY="tickethome-demo-https-proxy"
FORWARDING_RULE="tickethome-demo-forwarding-rule"
STATIC_IP_NAME="tickethome-demo-ip"

# Dominio
DOMAIN="ticket-home-beta.mhwdev.dev"
STATIC_IP="34.8.122.103"

# Cloud Run
SERVICE_NAME="tickethome-demo"
```

---

**Creado por:** Claude Code
**Versión:** V1 - Beta RS
**Fecha:** 2025-11-10
**GitHub:** https://github.com/jona-mhw/ticket-2
**Tag:** v1.0-beta-rs
