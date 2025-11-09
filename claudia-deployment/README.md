# 🚀 Deployment Ticket Home - Ambiente Claudia

Guía completa y scripts para deployment de Ticket Home en Google Cloud Platform usando Cloud Run, Cloud SQL (IP pública), IAP y SSL.

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Prerequisitos](#prerequisitos)
- [Guía Rápida](#guía-rápida)
- [Archivos Incluidos](#archivos-incluidos)
- [Configuración Detallada](#configuración-detallada)
- [Troubleshooting](#troubleshooting)

---

## 📝 Descripción

Este directorio contiene todo lo necesario para desplegar Ticket Home en un nuevo ambiente (Claudia) con la siguiente configuración:

- ✅ **Cloud Run** - Servicio serverless para la aplicación Flask
- ✅ **Cloud SQL (IP Pública)** - Conexión directa sin VPC
- ✅ **Secret Manager** - Gestión segura de credenciales
- ✅ **Load Balancer** - HTTPS global con certificado administrado
- ✅ **IAP** - Autenticación con Google SSO
- ✅ **Artifact Registry** - Almacenamiento de imágenes Docker

**Diferencia clave:** Este deployment usa IP pública de Cloud SQL en lugar de VPC Connector.

---

## 🏗️ Arquitectura

```
Usuario → DNS → Load Balancer (HTTPS) → IAP → Cloud Run → Cloud SQL (IP Pública)
                     ↓
              Certificado SSL
              (auto-gestionado)
```

### Componentes:

1. **DNS** - Registro A apuntando a IP estática de GCP
2. **Load Balancer Global** - Balanceador HTTPS con SSL
3. **IAP (Identity-Aware Proxy)** - Capa de autenticación OAuth 2.0
4. **Cloud Run** - Aplicación Flask en contenedor
5. **Secret Manager** - DATABASE_URL, SECRET_KEY, SUPERUSER_EMAILS
6. **Cloud SQL** - PostgreSQL con acceso vía IP pública
7. **Artifact Registry** - Repositorio de imágenes Docker

---

## ✅ Prerequisitos

### Software Local

- ✅ **gcloud CLI** ([Instalar](https://cloud.google.com/sdk/docs/install))
- ✅ **Docker** ([Instalar](https://docs.docker.com/get-docker/))
- ✅ **Git** (para clonar el repositorio)

### Accesos GCP

- ✅ Cuenta de Google con permisos en el proyecto GCP
- ✅ Roles necesarios:
  - Cloud Run Admin
  - Compute Admin
  - Cloud SQL Admin
  - Secret Manager Admin
  - Service Account Admin
  - Security Admin (para IAP)

### Recursos Pre-existentes

- ✅ **Instancia Cloud SQL** ya creada
- ✅ **Dominio** configurado (ej: `claudia-ticket-home.mhwdev.dev`)
- ✅ **Acceso al DNS** del dominio para crear registros A

---

## 🚀 Guía Rápida

### Opción 1: Guía HTML Interactiva (Recomendada)

1. **Abrir la guía HTML:**
   ```bash
   cd claudia-deployment
   open docs/deployment-guide.html  # macOS
   # O
   xdg-open docs/deployment-guide.html  # Linux
   # O simplemente abre el archivo en tu navegador
   ```

2. **Completar configuración** en la guía
3. **Seguir el timeline** paso a paso
4. **Marcar checkboxes** para trackear progreso

### Opción 2: Script Maestro Automatizado

1. **Copiar y configurar archivo de variables:**
   ```bash
   cd claudia-deployment
   cp config.env config.local.env
   nano config.local.env  # O tu editor favorito
   ```

2. **Completar TODAS las variables** en `config.local.env`

3. **Validar configuración:**
   ```bash
   source config.local.env
   validate_config
   ```

4. **Ejecutar script maestro:**
   ```bash
   ./deploy-master.sh
   ```

5. **Seguir instrucciones manuales** (OAuth, DNS)

---

## 📁 Archivos Incluidos

```
claudia-deployment/
├── README.md                          # Este archivo
├── config.env                         # Plantilla de configuración (COPIAR a config.local.env)
├── deploy-master.sh                   # Script maestro automatizado
├── scripts/                           # Scripts auxiliares por fase
│   ├── phase1-cloudsql.sh            # Setup Cloud SQL y base de datos
│   ├── phase2-secrets.sh             # Crear secrets en Secret Manager
│   ├── phase3-serviceaccount.sh      # Service Account y permisos
│   ├── phase4-docker.sh              # Build y push Docker
│   ├── phase5-cloudrun.sh            # Deploy en Cloud Run
│   ├── phase6-loadbalancer.sh        # Configurar Load Balancer
│   └── phase7-iap.sh                 # Configurar IAP (parcial)
└── docs/
    ├── deployment-guide.html          # Guía interactiva (ABRIR EN NAVEGADOR)
    └── oauth-setup.md                 # Guía detallada de OAuth
```

---

## ⚙️ Configuración Detallada

### 1. Variables de Configuración

Copia `config.env` a `config.local.env` y completa:

```bash
# Proyecto GCP
export GCP_PROJECT_ID="claudia-ticket-home-xxxxx"
export GCP_REGION="southamerica-west1"

# Cloud SQL (Instancia EXISTENTE)
export CLOUDSQL_INSTANCE_NAME="ticket-home-sql-instance"
export CLOUDSQL_PUBLIC_IP=""  # Se obtendrá automáticamente

# Nueva Base de Datos
export DB_NAME="claudia_ticket_home"
export DB_USER="claudia_user"
export DB_PASSWORD=""  # GENERAR UNA CONTRASEÑA SEGURA

# Dominio
export DOMAIN_NAME="claudia-ticket-home.mhwdev.dev"

# OAuth (se completan después de crear cliente OAuth)
export OAUTH_CLIENT_ID=""
export OAUTH_CLIENT_SECRET=""

# Grupo de acceso
export IAP_ACCESS_GROUP="claudia-ticket-home@googlegroups.com"
```

### 2. Generar Valores Faltantes

**Generar contraseña de base de datos:**
```bash
openssl rand -base64 32
```

**Generar SECRET_KEY para Flask:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Obtener IP Pública de Cloud SQL

```bash
gcloud sql instances describe YOUR_INSTANCE_NAME \
  --project=YOUR_PROJECT_ID \
  --format="value(ipAddresses[0].ipAddress)"
```

Copia esta IP a `CLOUDSQL_PUBLIC_IP` en tu config.

---

## 🎯 Workflow de Deployment

### Fase 0: Prerequisitos
- ✅ Verificar gcloud CLI
- ✅ Verificar Docker
- ✅ Configurar proyecto GCP
- ✅ Habilitar APIs

### Fase 1: Cloud SQL
- ✅ Verificar instancia existente
- ✅ Obtener IP pública
- ✅ Crear usuario de base de datos
- ✅ Crear nueva base de datos
- ✅ Configurar IPs autorizadas

### Fase 2: Secret Manager
- ✅ Crear secret para DATABASE_URL
- ✅ Crear secret para SECRET_KEY
- ✅ Crear secret para SUPERUSER_EMAILS

### Fase 3: Service Account
- ✅ Crear Service Account
- ✅ Asignar rol Cloud SQL Client
- ✅ Asignar rol Secret Manager Accessor
- ✅ Permisos granulares por secret

### Fase 4: Docker
- ✅ Crear repositorio en Artifact Registry
- ✅ Configurar autenticación Docker
- ✅ Build de imagen
- ✅ Push a Artifact Registry

### Fase 5: Cloud Run
- ✅ Deploy con configuración completa
- ✅ Configurar secrets y env vars
- ✅ Verificar logs

### Fase 6: Load Balancer
- ✅ Reservar IP estática
- ✅ Crear NEG (Network Endpoint Group)
- ✅ Crear Backend Service
- ✅ Crear certificado SSL
- ✅ Crear URL Map
- ✅ Crear HTTPS Proxy
- ✅ Crear Forwarding Rule
- ⏳ Esperar provisionamiento SSL (15-60 min)

### Fase 7: IAP
- ✅ Configurar OAuth Consent Screen (MANUAL)
- ✅ Crear OAuth Client ID (MANUAL)
- ✅ Habilitar IAP en Backend Service
- ✅ Configurar acceso por grupo

### Fase 8: Verificación
- ✅ Verificar DNS
- ✅ Verificar certificado SSL activo
- ✅ Test HTTPS
- ✅ Test autenticación IAP
- ✅ Verificar logs
- ✅ Test funcional

---

## 🔐 Configuración de OAuth (Pasos Manuales)

### 1. Crear OAuth Consent Screen

1. Ir a: [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. Seleccionar "Tipo de usuario": **Externo**
3. Completar:
   - Nombre de la aplicación: `Ticket Home - Claudia`
   - Email de asistencia: tu email
   - Logo (opcional)
   - Dominios autorizados: `mhwdev.dev`
4. Ámbitos: dejar en blanco
5. Usuarios de prueba: agregar emails que tendrán acceso

### 2. Crear OAuth Client ID

1. Ir a: [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "+ CREAR CREDENCIALES" > "ID de cliente de OAuth 2.0"
3. Tipo de aplicación: **Aplicación web**
4. Nombre: `ticket-home-iap-client`
5. URIs de redirección autorizados:
   ```
   https://iap.googleapis.com/v1/oauth/clientIds/TU_CLIENT_ID:handleRedirect
   ```
   (Reemplazar `TU_CLIENT_ID` con el ID generado)
6. **COPIAR** Client ID y Client Secret
7. Actualizar `config.local.env` con estos valores

---

## 🧪 Verificación Post-Deployment

### Test 1: DNS
```bash
nslookup claudia-ticket-home.mhwdev.dev
```
Debe retornar la IP reservada.

### Test 2: Certificado SSL
```bash
gcloud compute ssl-certificates describe ticket-home-ssl \
  --global \
  --project=YOUR_PROJECT_ID
```
Estado esperado: `ACTIVE`

### Test 3: HTTPS
```bash
curl -I https://claudia-ticket-home.mhwdev.dev
```
Esperado: HTTP/2 302 (redirect a IAP)

### Test 4: Aplicación
Abrir en navegador: `https://claudia-ticket-home.mhwdev.dev`

Flujo esperado:
1. Redirect a login de Google
2. Seleccionar cuenta
3. Dar consentimiento (primera vez)
4. Redirect a aplicación
5. Ver dashboard de Ticket Home

---

## 🚨 Troubleshooting

### Error: "Secret already exists"
✅ **OK** - El script detecta secrets existentes. Puedes continuar.

### Error: "Docker build failed"
❌ **Solución:** Verifica que Docker esté corriendo
```bash
docker ps
```

### Error: "403 Forbidden" al acceder a la app
❌ **Posibles causas:**
1. IAP no configurado correctamente
2. Usuario no está en el Google Group autorizado
3. OAuth Client ID incorrecto

**Solución:**
```bash
# Verificar IAP
gcloud iap web get-iam-policy \
  --resource-type=backend-services \
  --service=ticket-home-backend \
  --project=YOUR_PROJECT_ID
```

### Error: Certificado SSL en estado "PROVISIONING"
⏳ **Normal** - El certificado puede tardar 15-60 minutos en aprovisionarse.

**Verificar progreso:**
```bash
gcloud compute ssl-certificates describe ticket-home-ssl \
  --global \
  --project=YOUR_PROJECT_ID \
  --format="get(managed.status)"
```

### Error: "Could not connect to Cloud SQL"
❌ **Posibles causas:**
1. IPs autorizadas no configuradas en Cloud SQL
2. DATABASE_URL incorrecta
3. Firewall bloqueando conexión

**Solución:**
1. Verificar IPs autorizadas en Cloud SQL incluyen el rango de Cloud Run
2. Revisar logs de Cloud Run:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" \
     --limit=50 \
     --project=YOUR_PROJECT_ID
   ```

### Error: "OAuth error" al intentar login
❌ **Solución:**
1. Verificar que el URI de redirección en OAuth Client coincide con:
   ```
   https://iap.googleapis.com/v1/oauth/clientIds/YOUR_CLIENT_ID:handleRedirect
   ```
2. Verificar que el dominio está en "Dominios autorizados" del Consent Screen

---

## 📊 Tiempos Estimados

| Fase | Descripción | Tiempo Estimado |
|------|-------------|-----------------|
| 0 | Prerequisitos y configuración | 10 minutos |
| 1 | Cloud SQL - Crear BD | 5 minutos |
| 2 | Secret Manager | 3 minutos |
| 3 | Service Account | 2 minutos |
| 4 | Build y Push Docker | 10-15 minutos |
| 5 | Cloud Run Deploy | 5 minutos |
| 6 | Load Balancer | 10 minutos |
| 7 | IAP + OAuth | 15 minutos |
| 8 | Verificación | 10 minutos |
| **Espera SSL** | Provisionamiento certificado | **15-60 minutos** |

**Total activo:** ~1 hora
**Total con espera SSL:** ~1.5-2 horas

---

## 📞 Soporte

Si encuentras problemas durante el deployment:

1. **Revisar logs de Cloud Run:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" \
     --limit=100 \
     --project=YOUR_PROJECT_ID
   ```

2. **Verificar estado de recursos:**
   ```bash
   # Cloud Run
   gcloud run services describe ticket-home \
     --region=southamerica-west1 \
     --project=YOUR_PROJECT_ID

   # Backend Service
   gcloud compute backend-services describe ticket-home-backend \
     --global \
     --project=YOUR_PROJECT_ID

   # SSL Certificate
   gcloud compute ssl-certificates describe ticket-home-ssl \
     --global \
     --project=YOUR_PROJECT_ID
   ```

3. **Consultar documentación oficial:**
   - [Cloud Run Docs](https://cloud.google.com/run/docs)
   - [IAP Docs](https://cloud.google.com/iap/docs)
   - [Cloud SQL Docs](https://cloud.google.com/sql/docs)

---

## 📚 Recursos Adicionales

- [Guía HTML Interactiva](docs/deployment-guide.html) - Abrir en navegador
- [OAuth Setup Guide](docs/oauth-setup.md) - Guía detallada de OAuth
- [RUNBOOK Original](../_otros_archivos/_docs/RUNBOOK_Despliegue_de_Aplicaci#U00f3n_Flask_con_IAP_y_SSO_en_GCP.md)

---

## 🎉 Deployment Completado

Si todos los pasos se completaron exitosamente, tu aplicación estará disponible en:

🌐 **https://claudia-ticket-home.mhwdev.dev** (o tu dominio)

Con:
- ✅ HTTPS habilitado con certificado administrado
- ✅ Autenticación vía Google SSO (IAP)
- ✅ Conexión segura a Cloud SQL
- ✅ Secrets administrados por Secret Manager
- ✅ Alta disponibilidad con Cloud Run
- ✅ CDN habilitado en Load Balancer

**Nivel de seguridad:** 9/10 🔐

---

**Creado por:** Claude Code
**Fecha:** Noviembre 2025
**Versión:** 1.0.0
**Ambiente:** Claudia
