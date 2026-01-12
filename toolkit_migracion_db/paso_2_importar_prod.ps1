# ============================================================================
# TOOLKIT DE MIGRACION: QA -> PROD (PASO 2)
# ============================================================================
# Este script importa el archivo generado en el paso 1 hacia PROD.
# ============================================================================

$PROD_PROJECT = "prod-ticket-home-redsalud"
$PROD_INSTANCE = "prod-ticket-home"
$DB_NAME = "tickethome"

# BUSCAR EL ARCHIVO MAS RECIENTE EN EL BUCKET
Write-Host "Buscando archivos de backup en el bucket..." -ForegroundColor Cyan
$BACKUP_FILE = gsutil ls "gs://prod-ticket-home-backup/backup-migration-*.sql" | Sort-Object -Descending | Select-Object -First 1

if (-not $BACKUP_FILE) {
    Write-Host "No se encontro ningun archivo de backup en gs://prod-ticket-home-backup/" -ForegroundColor Red
    exit 1
}

Write-Host "Archivo detectado: $BACKUP_FILE" -ForegroundColor Green

# 1. Detener Cloud Run temporalmente (para evitar conexiones activas)
Write-Host "Pausando Cloud Run para liberar conexiones..." -ForegroundColor Yellow
gcloud run services update ticket-home-prod --region=southamerica-west1 --min-instances=0 --max-instances=1 --project=$PROD_PROJECT --quiet

Write-Host "Esperando 10 segundos..."
Start-Sleep -Seconds 10

# 2. Importar usando el usuario postgres
Write-Host "Iniciando Importacion en Cloud SQL (PROD)..." -ForegroundColor Cyan
gcloud sql import sql $PROD_INSTANCE $BACKUP_FILE --database=$DB_NAME --user=postgres --project=$PROD_PROJECT --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR EN IMPORTACION. Revisa si necesitas limpiar el esquema primero." -ForegroundColor Red
    exit 1
}

# 3. Levantar Cloud Run
Write-Host "Reiniciando Cloud Run..." -ForegroundColor Green
gcloud run services update ticket-home-prod --region=southamerica-west1 --min-instances=1 --max-instances=3 --project=$PROD_PROJECT --quiet

Write-Host ""
Write-Host "PROCESO FINALIZADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "Recuerda ejecutar los comandos de SQL STUDIO si es la primera vez que recreas el esquema." -ForegroundColor Yellow
