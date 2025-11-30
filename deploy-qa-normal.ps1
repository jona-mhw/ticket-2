# ============================================================================
# DEPLOY QA - Ticket Home (SIN RESET DE BD)
# ============================================================================
# Descripción: Script para deployment normal a QA sin resetear la base de datos
# Fecha: 2025-11-30
# Versión: V20251130
# ============================================================================

$ErrorActionPreference = "Stop"

# Configuración
$REGION = "southamerica-west1"
$PROJECT_ID = "qa-ticket-home-redsalud"
$SERVICE_NAME = "ticket-home"
$REPO_NAME = "tickethome-repo"
$IMAGE_NAME = "ticket-home"
$IMAGE_TAG = "latest"
$FULL_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:$IMAGE_TAG"

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOY QA - Ticket Home (Sin Reset DB)" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

# Paso 1: Configurar proyecto
Write-Host "[ 1/4 ] Configurando proyecto GCP..." -ForegroundColor Yellow
try {
    gcloud config set account jonathan.segura@redsalud.cl
    gcloud config set project $PROJECT_ID
    Write-Host "   ✓ Proyecto configurado: $PROJECT_ID`n" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error configurando proyecto: $_" -ForegroundColor Red
    exit 1
}

# Paso 2: Build Docker Image
Write-Host "[ 2/4 ] Construyendo imagen Docker..." -ForegroundColor Yellow
Write-Host "   Imagen: $FULL_IMAGE" -ForegroundColor Gray

try {
    # Autenticar Docker
    Write-Host "   - Autenticando Docker..." -ForegroundColor Gray
    gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

    # Build
    Write-Host "   - Construyendo imagen (esto puede tomar varios minutos)..." -ForegroundColor Gray
    docker build -t $FULL_IMAGE .

    Write-Host "   ✓ Imagen construida exitosamente`n" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error construyendo imagen: $_" -ForegroundColor Red
    exit 1
}

# Paso 3: Push Docker Image
Write-Host "[ 3/4 ] Subiendo imagen a Artifact Registry..." -ForegroundColor Yellow
try {
    docker push $FULL_IMAGE
    Write-Host "   ✓ Imagen subida exitosamente`n" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error subiendo imagen: $_" -ForegroundColor Red
    exit 1
}

# Paso 4: Deploy a Cloud Run
Write-Host "[ 4/4 ] Desplegando a Cloud Run (sin reset de BD)..." -ForegroundColor Yellow
try {
    gcloud run services update $SERVICE_NAME `
        --region=$REGION `
        --project=$PROJECT_ID `
        --image=$FULL_IMAGE

    Write-Host "   ✓ Deployment completado exitosamente`n" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error desplegando a Cloud Run: $_" -ForegroundColor Red
    exit 1
}

# Resumen
Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT EXITOSO" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "URL: https://qa-ticket-home.mhwdev.dev" -ForegroundColor White
Write-Host "Versión: V20251130" -ForegroundColor White
Write-Host "Estado BD: Sin cambios (deployment normal)" -ForegroundColor White
Write-Host "`nPróximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Verificar la aplicación en la URL de arriba" -ForegroundColor Gray
Write-Host "  2. Revisar logs si es necesario:" -ForegroundColor Gray
Write-Host "     gcloud logging tail --project=$PROJECT_ID --filter=`"resource.type=cloud_run_revision`"" -ForegroundColor DarkGray
Write-Host "============================================================================`n" -ForegroundColor Cyan
