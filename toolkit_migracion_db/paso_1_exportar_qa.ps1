# ============================================================================
# TOOLKIT DE MIGRACION: QA -> PROD (PASO 1)
# ============================================================================
# Este script exporta la Base de Datos de QA y la prepara en un bucket local
# para que Cloud SQL de PROD la pueda leer.
# ============================================================================

# --- CONFIGURACION ---
$QA_PROJECT = "qa-ticket-home-redsalud"
$QA_INSTANCE = "qa-ticket-home"
$QA_REGION = "southamerica-west1"
$DB_NAME = "tickethome"

$PROD_PROJECT = "prod-ticket-home-redsalud"
$PROD_SA = "p215530940953-13xehm@gcp-sa-cloud-sql.iam.gserviceaccount.com"

# Bucket unico para el transporte
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$BUCKET_NAME = "gs://prod-ticket-home-backup"
$BACKUP_FILE = "$BUCKET_NAME/backup-migration-$TIMESTAMP.sql"

Write-Host "INICIANDO EXPORTACION DESDE QA..." -ForegroundColor Cyan

# 1. Asegurar Bucket en PROD
gcloud config set project $PROD_PROJECT
$bucketExists = gsutil ls -b $BUCKET_NAME 2>$null
if (-not $bucketExists) {
    Write-Host "Creando bucket en PROD..."
    gsutil mb -p $PROD_PROJECT -l $QA_REGION $BUCKET_NAME
}

# 2. Permisos para SA de QA en el bucket de transporte
gcloud config set project $QA_PROJECT
$QA_SA = gcloud sql instances describe $QA_INSTANCE --format='value(serviceAccountEmailAddress)'
gsutil iam ch "serviceAccount:${QA_SA}:objectAdmin" $BUCKET_NAME

# 3. Exportar
Write-Host "Exportando base de datos $DB_NAME..." -ForegroundColor Yellow
gcloud sql export sql $QA_INSTANCE $BACKUP_FILE --database=$DB_NAME --project=$QA_PROJECT --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR EN EXPORTACION" -ForegroundColor Red
    exit 1
}

# 4. Asegurar permisos para SA de PROD
Write-Host "Configurando permisos para lectura en PROD..." -ForegroundColor Cyan
gsutil iam ch "serviceAccount:${PROD_SA}:objectViewer" $BUCKET_NAME

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "LISTO PARA IMPORTAR" -ForegroundColor Green
Write-Host "Archivo: $BACKUP_FILE" -ForegroundColor White
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "Siguiente paso: Ejecutar paso_2_importar_prod.ps1" -ForegroundColor Yellow
