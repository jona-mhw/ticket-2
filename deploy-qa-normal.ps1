# ============================================================================
# DEPLOY QA - Ticket Home (SIN RESET DE BD)
# ============================================================================
# Descripcion: Script para deployment normal a QA sin resetear la base de datos
# Fecha: 2025-11-30
# Version: V20251130
# ============================================================================

# Configuracion
$REGION = "southamerica-west1"
$PROJECT_ID = "qa-ticket-home-redsalud"
$SERVICE_NAME = "ticket-home"
$REPO_NAME = "tickethome-repo"
$IMAGE_NAME = "ticket-home"
$IMAGE_TAG = "latest"
$FULL_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:$IMAGE_TAG"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOY QA - Ticket Home - Sin Reset DB" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Configurar proyecto
Write-Host "[ 1/4 ] Configurando proyecto GCP..." -ForegroundColor Yellow
gcloud config set account jonathan.segura@redsalud.cl
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al configurar proyecto" -ForegroundColor Red
    exit 1
}
Write-Host "   OK Proyecto configurado: $PROJECT_ID" -ForegroundColor Green
Write-Host ""

# Paso 2: Build Docker Image
Write-Host "[ 2/4 ] Construyendo imagen Docker..." -ForegroundColor Yellow
Write-Host "   Imagen: $FULL_IMAGE" -ForegroundColor Gray
Write-Host ""

Write-Host "   - Autenticando Docker..." -ForegroundColor Gray
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al autenticar Docker" -ForegroundColor Red
    exit 1
}

Write-Host "   - Construyendo imagen - esto puede tomar varios minutos..." -ForegroundColor Gray
docker build -t $FULL_IMAGE .
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al construir imagen" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "   OK Imagen construida exitosamente" -ForegroundColor Green
Write-Host ""

# Paso 3: Push Docker Image
Write-Host "[ 3/4 ] Subiendo imagen a Artifact Registry..." -ForegroundColor Yellow
docker push $FULL_IMAGE
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al subir imagen" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "   OK Imagen subida exitosamente" -ForegroundColor Green
Write-Host ""

# Paso 4: Deploy a Cloud Run
Write-Host "[ 4/4 ] Desplegando a Cloud Run - sin reset de BD..." -ForegroundColor Yellow
gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --image=$FULL_IMAGE
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al desplegar a Cloud Run" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "   OK Deployment completado exitosamente" -ForegroundColor Green
Write-Host ""

# Resumen
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT EXITOSO" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "URL: https://qa-ticket-home.mhwdev.dev" -ForegroundColor White
Write-Host "Version: V20251130" -ForegroundColor White
Write-Host "Estado BD: Sin cambios - deployment normal" -ForegroundColor White
Write-Host ""
Write-Host "Proximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Verificar la aplicacion en la URL de arriba" -ForegroundColor Gray
Write-Host "  2. Revisar logs si es necesario:" -ForegroundColor Gray
Write-Host "     gcloud logging tail --project=$PROJECT_ID --filter=`"resource.type=cloud_run_revision`"" -ForegroundColor DarkGray
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
