# ============================================================================
# DEPLOY QA - Ticket Home (CON RESET DE BD)
# ============================================================================
# Descripcion: Script para deployment a QA con reset completo de base de datos
#              Util para testing, demos o cuando necesitas datos limpios
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
Write-Host "DEPLOY QA - Ticket Home - CON RESET DE BD" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Advertencia
Write-Host "ADVERTENCIA: Este script ELIMINARA todos los datos de la BD en QA" -ForegroundColor Red
Write-Host "y la repoblara con datos de demo/testing." -ForegroundColor Red
Write-Host ""
$confirm = Read-Host "Estas seguro de continuar? (escribe 'SI' para confirmar)"
if ($confirm -ne "SI") {
    Write-Host ""
    Write-Host "Deployment cancelado por el usuario." -ForegroundColor Yellow
    exit 0
}

# Paso 1: Configurar proyecto
Write-Host ""
Write-Host "[ 1/5 ] Configurando proyecto GCP..." -ForegroundColor Yellow
gcloud config set account jonathan.segura@redsalud.cl
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al configurar proyecto" -ForegroundColor Red
    exit 1
}
Write-Host "   OK Proyecto configurado: $PROJECT_ID" -ForegroundColor Green
Write-Host ""

# Paso 2: Build Docker Image
Write-Host "[ 2/5 ] Construyendo imagen Docker..." -ForegroundColor Yellow
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
Write-Host "[ 3/5 ] Subiendo imagen a Artifact Registry..." -ForegroundColor Yellow
docker push $FULL_IMAGE
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al subir imagen" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "   OK Imagen subida exitosamente" -ForegroundColor Green
Write-Host ""

# Paso 4: Deploy a Cloud Run con RESET_DB activado
Write-Host "[ 4/5 ] Desplegando a Cloud Run CON reset de BD..." -ForegroundColor Yellow
Write-Host "   ADVERTENCIA: Se eliminaran todos los datos y se creara BD con seed minimal" -ForegroundColor Red
gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --image=$FULL_IMAGE --update-env-vars="RESET_DB_ON_STARTUP=true,USE_QA_MINIMAL_SEED=true"
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al desplegar a Cloud Run" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "   OK Deployment con reset completado" -ForegroundColor Green
Write-Host ""

# Esperar un momento para que el servicio inicie
Write-Host "   - Esperando 30 segundos para que el reset complete..." -ForegroundColor Gray
Start-Sleep -Seconds 30

# Paso 5: Desactivar RESET_DB para futuros deploys
Write-Host "[ 5/5 ] Desactivando flag de reset para futuros deployments..." -ForegroundColor Yellow
gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --update-env-vars="RESET_DB_ON_STARTUP=false"
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ADVERTENCIA: No se pudo desactivar el flag automaticamente" -ForegroundColor Yellow
    Write-Host "   Por favor ejecuta manualmente:" -ForegroundColor Yellow
    Write-Host "   gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --update-env-vars=`"RESET_DB_ON_STARTUP=false`"" -ForegroundColor DarkGray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "   OK Flag de reset desactivado (RESET_DB_ON_STARTUP=false)" -ForegroundColor Green
    Write-Host ""
}

# Resumen
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT CON RESET EXITOSO" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "URL: https://qa-ticket-home.mhwdev.dev" -ForegroundColor White
Write-Host "Version: V20251130" -ForegroundColor White
Write-Host "Estado BD: RESETEADA con seed minimal de QA" -ForegroundColor White
Write-Host ""
Write-Host "Credenciales de prueba:" -ForegroundColor Yellow
Write-Host "  Username: admin_prov (o cualquier usuario de la seed)" -ForegroundColor Gray
Write-Host "  Password: Revisa la seed en data/qa_minimal_seed.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Proximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Verificar la aplicacion en la URL de arriba" -ForegroundColor Gray
Write-Host "  2. Hacer login con las credenciales de la seed" -ForegroundColor Gray
Write-Host "  3. Verificar que RESET_DB_ON_STARTUP este en false (ya deberia estarlo)" -ForegroundColor Gray
Write-Host "  4. Revisar logs si es necesario:" -ForegroundColor Gray
Write-Host "     gcloud logging tail --project=$PROJECT_ID --filter=`"resource.type=cloud_run_revision`"" -ForegroundColor DarkGray
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
