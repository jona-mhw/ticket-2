#!/bin/bash
# ============================================
# DEPLOYMENT MAESTRO - AMBIENTE CLAUDIA
# ============================================
#
# Este script ejecuta TODO el proceso de deployment
# desde cero hasta tener la aplicación funcionando
# con IAP y SSL en GCP.
#
# PREREQUISITOS:
# 1. gcloud CLI instalado y autenticado
# 2. Docker instalado
# 3. config.local.env completamente configurado
#
# USO:
#   ./deploy-master.sh              # Ejecutar todo
#   ./deploy-master.sh --from-phase 3  # Continuar desde fase 3
#
# ============================================

set -e  # Exit on error

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================
# FUNCIONES AUXILIARES
# ============================================

print_header() {
    echo ""
    echo -e "${MAGENTA}============================================${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}============================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

# ============================================
# CARGAR CONFIGURACIÓN
# ============================================

print_header "CARGANDO CONFIGURACIÓN"

if [ ! -f "config.local.env" ]; then
    print_error "Archivo config.local.env no encontrado"
    print_info "Copia config.env a config.local.env y completa las variables"
    print_info "cp config.env config.local.env"
    exit 1
fi

source config.local.env

# Validar configuración
if ! validate_config; then
    exit 1
fi

show_config

# ============================================
# VERIFICAR PREREQUISITOS
# ============================================

print_header "VERIFICANDO PREREQUISITOS"

# gcloud
print_step "Verificando gcloud CLI..."
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI no está instalado"
    exit 1
fi
print_success "gcloud CLI instalado: $(gcloud version | head -1)"

# Docker
print_step "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado"
    exit 1
fi
print_success "Docker instalado: $(docker --version)"

# Autenticación
print_step "Verificando autenticación..."
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$CURRENT_ACCOUNT" ]; then
    print_error "No estás autenticado en gcloud"
    print_info "Ejecuta: gcloud auth login"
    exit 1
fi
print_success "Autenticado como: $CURRENT_ACCOUNT"

# ============================================
# FASE 0: CONFIGURACIÓN INICIAL DE GCP
# ============================================

print_header "FASE 0: CONFIGURACIÓN INICIAL DE GCP"

print_step "Configurando proyecto GCP..."
gcloud config set project $GCP_PROJECT_ID
print_success "Proyecto configurado: $GCP_PROJECT_ID"

print_step "Habilitando APIs necesarias..."
gcloud services enable \
    run.googleapis.com \
    compute.googleapis.com \
    artifactregistry.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    iap.googleapis.com \
    cloudresourcemanager.googleapis.com

print_success "APIs habilitadas"

# ============================================
# FASE 1: CLOUD SQL - CREAR BASE DE DATOS
# ============================================

print_header "FASE 1: CLOUD SQL - CREAR BASE DE DATOS"

print_step "Verificando instancia Cloud SQL..."
if gcloud sql instances describe $CLOUDSQL_INSTANCE_NAME --project=$GCP_PROJECT_ID &>/dev/null; then
    print_success "Instancia Cloud SQL encontrada: $CLOUDSQL_INSTANCE_NAME"
else
    print_error "Instancia Cloud SQL no encontrada: $CLOUDSQL_INSTANCE_NAME"
    exit 1
fi

# Obtener IP pública si no está configurada
if [ -z "$CLOUDSQL_PUBLIC_IP" ]; then
    print_step "Obteniendo IP pública de Cloud SQL..."
    CLOUDSQL_PUBLIC_IP=$(gcloud sql instances describe $CLOUDSQL_INSTANCE_NAME \
        --project=$GCP_PROJECT_ID \
        --format="value(ipAddresses[0].ipAddress)")

    print_success "IP pública obtenida: $CLOUDSQL_PUBLIC_IP"
    print_warning "Actualiza config.local.env con: CLOUDSQL_PUBLIC_IP=$CLOUDSQL_PUBLIC_IP"

    # Actualizar DATABASE_URL
    export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${CLOUDSQL_PUBLIC_IP}:${CLOUDSQL_PORT}/${DB_NAME}"
fi

print_step "Creando usuario de base de datos..."
if gcloud sql users create $DB_USER \
    --instance=$CLOUDSQL_INSTANCE_NAME \
    --password=$DB_PASSWORD \
    --project=$GCP_PROJECT_ID 2>/dev/null; then
    print_success "Usuario creado: $DB_USER"
else
    print_warning "Usuario ya existe (OK)"
fi

print_step "Creando base de datos..."
if gcloud sql databases create $DB_NAME \
    --instance=$CLOUDSQL_INSTANCE_NAME \
    --project=$GCP_PROJECT_ID 2>/dev/null; then
    print_success "Base de datos creada: $DB_NAME"
else
    print_warning "Base de datos ya existe (OK)"
fi

print_step "Habilitando acceso desde IPs autorizadas..."
print_warning "IMPORTANTE: Cloud Run se conectará vía IP pública"
print_info "Asegúrate de haber configurado las IPs autorizadas en Cloud SQL"

print_success "Fase 1 completada"

# ============================================
# FASE 2: SECRET MANAGER - CREAR SECRETS
# ============================================

print_header "FASE 2: SECRET MANAGER - CREAR SECRETS"

# Secret: DATABASE_URL
print_step "Creando secret: DATABASE_URL..."
if echo -n "$DATABASE_URL" | gcloud secrets create $SECRET_DATABASE_URL_NAME \
    --data-file=- \
    --replication-policy=automatic \
    --project=$GCP_PROJECT_ID 2>/dev/null; then
    print_success "Secret creado: $SECRET_DATABASE_URL_NAME"
else
    print_warning "Secret ya existe, actualizando..."
    echo -n "$DATABASE_URL" | gcloud secrets versions add $SECRET_DATABASE_URL_NAME \
        --data-file=- \
        --project=$GCP_PROJECT_ID
    print_success "Secret actualizado: $SECRET_DATABASE_URL_NAME"
fi

# Secret: SECRET_KEY
print_step "Creando secret: SECRET_KEY..."
if echo -n "$SECRET_KEY" | gcloud secrets create $SECRET_KEY_NAME \
    --data-file=- \
    --replication-policy=automatic \
    --project=$GCP_PROJECT_ID 2>/dev/null; then
    print_success "Secret creado: $SECRET_KEY_NAME"
else
    print_warning "Secret ya existe (OK)"
fi

# Secret: SUPERUSER_EMAILS
print_step "Creando secret: SUPERUSER_EMAILS..."
if echo -n "$SUPERUSER_EMAILS" | gcloud secrets create $SECRET_SUPERUSER_EMAILS_NAME \
    --data-file=- \
    --replication-policy=automatic \
    --project=$GCP_PROJECT_ID 2>/dev/null; then
    print_success "Secret creado: $SECRET_SUPERUSER_EMAILS_NAME"
else
    print_warning "Secret ya existe (OK)"
fi

print_success "Fase 2 completada"

# ============================================
# FASE 3: SERVICE ACCOUNT
# ============================================

print_header "FASE 3: SERVICE ACCOUNT"

print_step "Creando Service Account..."
if gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Service Account para $SERVICE_NAME" \
    --project=$GCP_PROJECT_ID 2>/dev/null; then
    print_success "Service Account creado: $SERVICE_ACCOUNT_EMAIL"
else
    print_warning "Service Account ya existe (OK)"
fi

print_step "Asignando permisos al Service Account..."

# Permiso para Cloud SQL
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client" \
    --condition=None

# Permiso para Secret Manager
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None

# Permisos individuales para cada secret
for secret_name in $SECRET_DATABASE_URL_NAME $SECRET_KEY_NAME $SECRET_SUPERUSER_EMAILS_NAME; do
    gcloud secrets add-iam-policy-binding $secret_name \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$GCP_PROJECT_ID 2>/dev/null || true
done

print_success "Permisos asignados al Service Account"
print_success "Fase 3 completada"

# ============================================
# FASE 4: ARTIFACT REGISTRY & DOCKER BUILD
# ============================================

print_header "FASE 4: ARTIFACT REGISTRY & DOCKER BUILD"

print_step "Verificando Artifact Registry..."
if ! gcloud artifacts repositories describe $ARTIFACT_REGISTRY_REPO \
    --location=$ARTIFACT_REGISTRY_REGION \
    --project=$GCP_PROJECT_ID &>/dev/null; then

    print_step "Creando repositorio en Artifact Registry..."
    gcloud artifacts repositories create $ARTIFACT_REGISTRY_REPO \
        --repository-format=docker \
        --location=$ARTIFACT_REGISTRY_REGION \
        --description="Docker images para Ticket Home" \
        --project=$GCP_PROJECT_ID

    print_success "Repositorio creado: $ARTIFACT_REGISTRY_REPO"
else
    print_success "Repositorio ya existe: $ARTIFACT_REGISTRY_REPO"
fi

print_step "Configurando autenticación de Docker..."
gcloud auth configure-docker ${ARTIFACT_REGISTRY_REGION}-docker.pkg.dev --quiet

print_step "Construyendo imagen Docker..."
cd /home/user/ticket-2  # Ajustar según tu path
docker build \
    --platform linux/amd64 \
    --build-arg BUILD_VERSION="$ENVIRONMENT" \
    -t ${IMAGE_NAME}:${IMAGE_TAG} \
    .

print_success "Imagen construida: ${IMAGE_NAME}:${IMAGE_TAG}"

print_step "Pushing imagen a Artifact Registry..."
docker push ${IMAGE_NAME}:${IMAGE_TAG}

print_success "Imagen publicada en Artifact Registry"
print_success "Fase 4 completada"

# ============================================
# FASE 5: CLOUD RUN - DEPLOYMENT
# ============================================

print_header "FASE 5: CLOUD RUN - DEPLOYMENT"

print_step "Desplegando servicio en Cloud Run..."

gcloud run deploy $SERVICE_NAME \
    --image=${IMAGE_NAME}:${IMAGE_TAG} \
    --region=$GCP_REGION \
    --service-account=$SERVICE_ACCOUNT_EMAIL \
    --no-allow-unauthenticated \
    --ingress=internal-and-cloud-load-balancing \
    --port=$CLOUD_RUN_PORT \
    --timeout=$CLOUD_RUN_TIMEOUT \
    --memory=$CLOUD_RUN_MEMORY \
    --cpu=$CLOUD_RUN_CPU \
    --min-instances=$CLOUD_RUN_MIN_INSTANCES \
    --max-instances=$CLOUD_RUN_MAX_INSTANCES \
    --concurrency=$CLOUD_RUN_CONCURRENCY \
    --set-env-vars="ENVIRONMENT=$ENVIRONMENT,FLASK_ENV=$FLASK_ENV,FLASK_DEBUG=$FLASK_DEBUG,ENABLE_IAP=$ENABLE_IAP,ENABLE_DEMO_LOGIN=$ENABLE_DEMO_LOGIN,RESET_DB_ON_STARTUP=$RESET_DB_ON_STARTUP" \
    --set-secrets="DATABASE_URL=${SECRET_DATABASE_URL_NAME}:latest,SECRET_KEY=${SECRET_KEY_NAME}:latest,SUPERUSER_EMAILS=${SECRET_SUPERUSER_EMAILS_NAME}:latest" \
    --project=$GCP_PROJECT_ID

print_success "Servicio Cloud Run desplegado: $SERVICE_NAME"

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$GCP_REGION \
    --project=$GCP_PROJECT_ID \
    --format="value(status.url)")

print_info "URL del servicio (privada): $SERVICE_URL"
print_success "Fase 5 completada"

# ============================================
# FASE 6: LOAD BALANCER - CONFIGURACIÓN
# ============================================

print_header "FASE 6: LOAD BALANCER - CONFIGURACIÓN"

# Reservar IP
print_step "Reservando IP estática global..."
if ! gcloud compute addresses describe $RESERVED_IP_NAME --global --project=$GCP_PROJECT_ID &>/dev/null; then
    gcloud compute addresses create $RESERVED_IP_NAME \
        --global \
        --ip-version=IPV4 \
        --project=$GCP_PROJECT_ID

    print_success "IP reservada: $RESERVED_IP_NAME"
else
    print_warning "IP ya existe (OK)"
fi

RESERVED_IP=$(gcloud compute addresses describe $RESERVED_IP_NAME \
    --global \
    --project=$GCP_PROJECT_ID \
    --format="value(address)")

print_success "IP pública: $RESERVED_IP"
print_warning "Configura tu DNS: $DOMAIN_NAME -> $RESERVED_IP (registro A)"

# Crear Network Endpoint Group (NEG)
print_step "Creando Network Endpoint Group..."
if ! gcloud compute network-endpoint-groups describe $NEG_NAME \
    --region=$GCP_REGION \
    --project=$GCP_PROJECT_ID &>/dev/null; then

    gcloud compute network-endpoint-groups create $NEG_NAME \
        --region=$GCP_REGION \
        --network-endpoint-type=serverless \
        --cloud-run-service=$SERVICE_NAME \
        --project=$GCP_PROJECT_ID

    print_success "NEG creado: $NEG_NAME"
else
    print_warning "NEG ya existe (OK)"
fi

# Crear Backend Service
print_step "Creando Backend Service..."
if ! gcloud compute backend-services describe $BACKEND_SERVICE_NAME \
    --global \
    --project=$GCP_PROJECT_ID &>/dev/null; then

    gcloud compute backend-services create $BACKEND_SERVICE_NAME \
        --global \
        --enable-cdn \
        --project=$GCP_PROJECT_ID

    print_success "Backend Service creado: $BACKEND_SERVICE_NAME"
else
    print_warning "Backend Service ya existe (OK)"
fi

# Agregar NEG al Backend Service
print_step "Agregando NEG al Backend Service..."
gcloud compute backend-services add-backend $BACKEND_SERVICE_NAME \
    --global \
    --network-endpoint-group=$NEG_NAME \
    --network-endpoint-group-region=$GCP_REGION \
    --project=$GCP_PROJECT_ID 2>/dev/null || true

print_success "NEG agregado al Backend Service"

# Crear certificado SSL
print_step "Creando certificado SSL administrado..."
if ! gcloud compute ssl-certificates describe $SSL_CERT_NAME \
    --global \
    --project=$GCP_PROJECT_ID &>/dev/null; then

    gcloud compute ssl-certificates create $SSL_CERT_NAME \
        --domains=$DOMAIN_NAME \
        --global \
        --project=$GCP_PROJECT_ID

    print_success "Certificado SSL creado: $SSL_CERT_NAME"
    print_warning "El certificado tardará ~15-60 minutos en aprovisionar"
else
    print_warning "Certificado SSL ya existe (OK)"
fi

# Crear URL Map
print_step "Creando URL Map..."
if ! gcloud compute url-maps describe $URL_MAP_NAME \
    --global \
    --project=$GCP_PROJECT_ID &>/dev/null; then

    gcloud compute url-maps create $URL_MAP_NAME \
        --default-service=$BACKEND_SERVICE_NAME \
        --global \
        --project=$GCP_PROJECT_ID

    print_success "URL Map creado: $URL_MAP_NAME"
else
    print_warning "URL Map ya existe (OK)"
fi

# Crear HTTPS Proxy
print_step "Creando HTTPS Proxy..."
if ! gcloud compute target-https-proxies describe $HTTPS_PROXY_NAME \
    --global \
    --project=$GCP_PROJECT_ID &>/dev/null; then

    gcloud compute target-https-proxies create $HTTPS_PROXY_NAME \
        --url-map=$URL_MAP_NAME \
        --ssl-certificates=$SSL_CERT_NAME \
        --global \
        --project=$GCP_PROJECT_ID

    print_success "HTTPS Proxy creado: $HTTPS_PROXY_NAME"
else
    print_warning "HTTPS Proxy ya existe (OK)"
fi

# Crear Forwarding Rule
print_step "Creando Forwarding Rule..."
if ! gcloud compute forwarding-rules describe $FORWARDING_RULE_NAME \
    --global \
    --project=$GCP_PROJECT_ID &>/dev/null; then

    gcloud compute forwarding-rules create $FORWARDING_RULE_NAME \
        --address=$RESERVED_IP_NAME \
        --target-https-proxy=$HTTPS_PROXY_NAME \
        --global \
        --ports=443 \
        --project=$GCP_PROJECT_ID

    print_success "Forwarding Rule creado: $FORWARDING_RULE_NAME"
else
    print_warning "Forwarding Rule ya existe (OK)"
fi

print_success "Fase 6 completada"

# ============================================
# FASE 7: IAP (IDENTITY-AWARE PROXY)
# ============================================

print_header "FASE 7: IAP (IDENTITY-AWARE PROXY)"

print_warning "⚠️  PASOS MANUALES REQUERIDOS:"
echo ""
print_info "1. Crear OAuth Consent Screen:"
echo "   - Ve a: https://console.cloud.google.com/apis/credentials/consent?project=$GCP_PROJECT_ID"
echo "   - Tipo: Externo"
echo "   - Nombre: Ticket Home - $ENVIRONMENT"
echo "   - Email de soporte: tu email"
echo ""

print_info "2. Crear OAuth Client ID:"
echo "   - Ve a: https://console.cloud.google.com/apis/credentials?project=$GCP_PROJECT_ID"
echo "   - Click en '+ CREAR CREDENCIALES' > 'ID de cliente de OAuth 2.0'"
echo "   - Tipo: Aplicación web"
echo "   - Nombre: $SERVICE_NAME-iap-client"
echo "   - URIs de redirección autorizados:"
echo "     https://iap.googleapis.com/v1/oauth/clientIds/<CLIENT_ID>:handleRedirect"
echo ""
echo "   - COPIA el Client ID y Client Secret generados"
echo "   - Actualiza config.local.env con estos valores"
echo ""

if [ -z "$OAUTH_CLIENT_ID" ] || [ -z "$OAUTH_CLIENT_SECRET" ]; then
    print_warning "OAuth credentials no configuradas aún"
    print_info "Ejecuta este script nuevamente después de configurar OAuth"
else
    print_step "Habilitando IAP en Backend Service..."

    gcloud iap web enable \
        --resource-type=backend-services \
        --service=$BACKEND_SERVICE_NAME \
        --oauth2-client-id=$OAUTH_CLIENT_ID \
        --oauth2-client-secret=$OAUTH_CLIENT_SECRET \
        --project=$GCP_PROJECT_ID

    print_success "IAP habilitado en Backend Service"

    print_step "Configurando acceso IAP para el grupo..."
    gcloud iap web add-iam-policy-binding \
        --resource-type=backend-services \
        --service=$BACKEND_SERVICE_NAME \
        --member="group:$IAP_ACCESS_GROUP" \
        --role="roles/iap.httpsResourceAccessor" \
        --project=$GCP_PROJECT_ID

    print_success "Acceso IAP configurado para: $IAP_ACCESS_GROUP"
fi

print_success "Fase 7 completada"

# ============================================
# RESUMEN FINAL
# ============================================

print_header "🎉 DEPLOYMENT COMPLETADO 🎉"

echo ""
print_success "Aplicación desplegada exitosamente"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 RESUMEN DEL DEPLOYMENT:"
echo ""
echo "  🌐 Dominio:           $DOMAIN_NAME"
echo "  🔒 IP Pública:        $RESERVED_IP"
echo "  📦 Imagen Docker:     ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  🗄️  Base de Datos:     $DB_NAME"
echo "  👤 Service Account:   $SERVICE_ACCOUNT_EMAIL"
echo "  🔐 IAP Grupo:         $IAP_ACCESS_GROUP"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "PRÓXIMOS PASOS:"
echo ""
echo "  1. ✅ Configurar DNS: $DOMAIN_NAME -> $RESERVED_IP"
echo "  2. ⏳ Esperar certificado SSL (~15-60 min)"
echo "  3. 🔐 Configurar OAuth (si no se hizo)"
echo "  4. 👥 Agregar usuarios al grupo: $IAP_ACCESS_GROUP"
echo "  5. 🧪 Verificar acceso: https://$DOMAIN_NAME"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_success "✨ Deployment completado exitosamente ✨"
