# ============================================================================
# DEPLOY QA - Ticket Home (CON RESET DE BD)
# ============================================================================
# Descripción: Script para deployment a QA con reset completo de base de datos
#              Útil para testing, demos o cuando necesitas datos limpios
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
Write-Host "DEPLOY QA - Ticket Home (CON RESET DE BD)" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

# Advertencia
Write-Host "⚠️  ADVERTENCIA: Este script ELIMINARÁ todos los datos de la BD en QA" -ForegroundColor Red
Write-Host "   y la repoblará con datos de demo/testing.`n" -ForegroundColor Red
$confirm = Read-Host "¿Estás seguro de continuar? (escribe 'SI' para confirmar)"
if ($confirm -ne "SI") {
    Write-Host "`nDeployment cancelado por el usuario." -ForegroundColor Yellow
    exit 0
}

# Paso 1: Configurar proyecto
Write-Host "`n[ 1/5 ] Configurando proyecto GCP..." -ForegroundColor Yellow
try {
    gcloud config set account jonathan.segura@redsalud.cl
    gcloud config set project $PROJECT_ID
    Write-Host "   ✓ Proyecto configurado: $PROJECT_ID`n" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error configurando proyecto: $_" -ForegroundColor Red
    exit 1
}

# Paso 2: Build Docker Image
Write-Host "[ 2/5 ] Construyendo imagen Docker..." -ForegroundColor Yellow
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
Write-Host "[ 3/5 ] Subiendo imagen a Artifact Registry..." -ForegroundColor Yellow
try {
    docker push $FULL_IMAGE
    Write-Host "   ✓ Imagen subida exitosamente`n" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error subiendo imagen: $_" -ForegroundColor Red
    exit 1
}

# Paso 4: Deploy a Cloud Run con RESET_DB activado
Write-Host "[ 4/5 ] Desplegando a Cloud Run CON reset de BD..." -ForegroundColor Yellow
Write-Host "   ⚠️  Se eliminarán todos los datos y se creará BD con seed minimal" -ForegroundColor Red
try {
    gcloud run services update $SERVICE_NAME `
        --region=$REGION `
        --project=$PROJECT_ID `
        --image=$FULL_IMAGE `
        --update-env-vars="RESET_DB_ON_STARTUP=true,USE_QA_MINIMAL_SEED=true"

    Write-Host "   ✓ Deployment con reset completado`n" -ForegroundColor Green

    # Esperar un momento para que el servicio inicie
    Write-Host "   - Esperando 30 segundos para que el reset complete..." -ForegroundColor Gray
    Start-Sleep -Seconds 30

} catch {
    Write-Host "   ✗ Error desplegando a Cloud Run: $_" -ForegroundColor Red
    exit 1
}

# Paso 5: Desactivar RESET_DB para futuros deploys
Write-Host "[ 5/5 ] Desactivando flag de reset para futuros deployments..." -ForegroundColor Yellow
try {
    gcloud run services update $SERVICE_NAME `
        --region=$REGION `
        --project=$PROJECT_ID `
        --update-env-vars="RESET_DB_ON_STARTUP=false"

    Write-Host "   ✓ Flag de reset desactivado (RESET_DB_ON_STARTUP=false)`n" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Advertencia: No se pudo desactivar el flag automáticamente" -ForegroundColor Yellow
    Write-Host "   Por favor ejecuta manualmente:" -ForegroundColor Yellow
    Write-Host "   gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --update-env-vars=`"RESET_DB_ON_STARTUP=false`"`n" -ForegroundColor DarkGray
}

# Resumen
Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT CON RESET EXITOSO" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "URL: https://qa-ticket-home.mhwdev.dev" -ForegroundColor White
Write-Host "Versión: V20251130" -ForegroundColor White
Write-Host "Estado BD: ✅ Reseteada con datos de seed minimal QA" -ForegroundColor White
Write-Host "`nCredenciales de prueba:" -ForegroundColor Yellow
Write-Host "  Username: admin_prov (o cualquier usuario de la seed)" -ForegroundColor Gray
Write-Host "  Password: password123" -ForegroundColor Gray
Write-Host "`nPróximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Verificar la aplicación en la URL de arriba" -ForegroundColor Gray
Write-Host "  2. Revisar logs si es necesario:" -ForegroundColor Gray
Write-Host "     gcloud logging tail --project=$PROJECT_ID --filter=`"resource.type=cloud_run_revision`"" -ForegroundColor DarkGray
Write-Host "  3. Verificar que RESET_DB_ON_STARTUP esté en false (ya debería estarlo)" -ForegroundColor Gray
Write-Host "============================================================================`n" -ForegroundColor Cyan
