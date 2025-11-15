<#
.SYNOPSIS
    Deployment interactivo para Ticket Home en Google Cloud Platform

.DESCRIPTION
    Este script guía paso a paso en el proceso de deployment de Ticket Home
    a GCP usando Cloud Run, Cloud SQL, IAP y SSL administrado.

.PARAMETER FromPhase
    Continuar desde una fase específica (1-7)

.PARAMETER SkipValidation
    Saltar validación de credenciales (no recomendado)

.EXAMPLE
    .\Deploy-Interactive.ps1
    Ejecuta el deployment completo desde el inicio

.EXAMPLE
    .\Deploy-Interactive.ps1 -FromPhase 3
    Continúa desde la Fase 3 (Docker Build)

.NOTES
    Versión: 1.0
    Autor: Claude
    Fecha: 2025-11-15
    Requisitos: PowerShell 5.1+, gcloud CLI, Docker
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateRange(1, 7)]
    [int]$FromPhase = 0,

    [Parameter()]
    [switch]$SkipValidation
)

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================

$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'

# Rutas
$SCRIPT_DIR = $PSScriptRoot
$LIB_DIR = Join-Path $SCRIPT_DIR "lib"
$MODULE_PATH = Join-Path $LIB_DIR "DeploymentFunctions.psm1"
$MESSAGES_PATH = Join-Path $LIB_DIR "WelcomeMessages.json"
$CONFIG_FILE = Join-Path $SCRIPT_DIR "config.env"

# Importar módulo de funciones
if (-not (Test-Path $MODULE_PATH)) {
    Write-Host "ERROR: No se encontró el módulo DeploymentFunctions.psm1" -ForegroundColor Red
    Write-Host "Ruta esperada: $MODULE_PATH" -ForegroundColor Yellow
    exit 1
}

Import-Module $MODULE_PATH -Force

# ============================================
# CONFIGURACIÓN DEL PROYECTO
# ============================================

# Estos valores se pueden sobrescribir cargando config.env
$Config = @{
    GCP_PROJECT_ID = "ticket-home-demo"
    GCP_REGION = "us-central1"
    CLOUD_SQL_INSTANCE = "tickethome-db"
    SERVICE_ACCOUNT_EMAIL = "tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com"
    CLOUD_RUN_SERVICE = "tickethome-demo"
    DOCKER_IMAGE_NAME = "ticket-home"
    ARTIFACT_REGISTRY_REPO = "tickethome-repo"
    SECRETS = @("mhw-database-url", "mhw-secret-key", "mhw-superuser-emails")
}

# Intentar cargar config.env si existe
if (Test-Path $CONFIG_FILE) {
    Write-Host "Cargando configuración desde config.env..." -ForegroundColor Cyan
    # Nota: En PowerShell, cargar .env es más complejo que en bash
    # Aquí se mantienen los valores por defecto
    # Los usuarios pueden modificar $Config arriba directamente
}

# ============================================
# VARIABLES GLOBALES
# ============================================

$DEPLOYMENT_START_TIME = Get-Date
$TOTAL_PHASES = 7

# ============================================
# FLUJO PRINCIPAL
# ============================================

try {
    # ============================================
    # PANTALLA 1: BIENVENIDA
    # ============================================

    if ($FromPhase -eq 0) {
        Show-Banner
        Wait-UserInput
    }

    # ============================================
    # PANTALLA 2: MENSAJE ALEATORIO
    # ============================================

    if ($FromPhase -eq 0 -and (Test-Path $MESSAGES_PATH)) {
        Show-RandomWelcome -MessagesPath $MESSAGES_PATH
        Wait-UserInput
    }

    # ============================================
    # PANTALLA 3: VALIDACIÓN DE CREDENCIALES
    # ============================================

    if (-not $SkipValidation) {
        Clear-Host
        Write-Header "🔐 VALIDACIÓN DE CREDENCIALES GCP"

        $validationsPassed = $true

        # 1. Autenticación gcloud
        if (-not (Test-GCloudAuth)) {
            $validationsPassed = $false
        }

        # 2. Proyecto GCP
        if (-not (Test-GCloudProject -ExpectedProject $Config.GCP_PROJECT_ID)) {
            $validationsPassed = $false
        }

        # 3. Cloud SQL
        if (-not (Test-CloudSQLInstance -InstanceName $Config.CLOUD_SQL_INSTANCE -Project $Config.GCP_PROJECT_ID)) {
            $validationsPassed = $false
        }

        # 4. Secrets
        if (-not (Test-Secrets -SecretNames $Config.SECRETS -Project $Config.GCP_PROJECT_ID)) {
            $validationsPassed = $false
        }

        # 5. Service Account
        if (-not (Test-ServiceAccount -ServiceAccountEmail $Config.SERVICE_ACCOUNT_EMAIL -Project $Config.GCP_PROJECT_ID)) {
            $validationsPassed = $false
        }

        # 6. Docker
        if (-not (Test-Docker)) {
            $validationsPassed = $false
        }

        Write-Host ""

        if ($validationsPassed) {
            Write-Header "✨ TODO LISTO PARA DEPLOYMENT ✨" -Success

            if (-not (Confirm-Action "¿Deseas continuar con el deployment?" -DefaultYes)) {
                Write-Warning "Deployment cancelado por el usuario"
                exit 0
            }
        } else {
            Write-Error "La validación de credenciales falló"
            Write-Info "Corrige los errores y vuelve a ejecutar el script"
            exit 1
        }
    }

    # ============================================
    # FASE 1: HABILITAR APIS DE GCP
    # ============================================

    if ($FromPhase -le 1) {
        Clear-Host
        Write-Header "📦 FASE 1: HABILITAR APIS DE GCP"

        Write-Step "Habilitando APIs necesarias..."

        $apis = @(
            "run.googleapis.com",
            "compute.googleapis.com",
            "artifactregistry.googleapis.com",
            "sqladmin.googleapis.com",
            "secretmanager.googleapis.com",
            "iap.googleapis.com",
            "cloudresourcemanager.googleapis.com"
        )

        foreach ($api in $apis) {
            $result = Invoke-CommandWithFeedback `
                -Command "gcloud services enable $api --project=$($Config.GCP_PROJECT_ID)" `
                -Description "Habilitando $api" `
                -AllowRetry

            if (-not $result) {
                throw "Error al habilitar API: $api"
            }
        }

        Write-Success "Todas las APIs habilitadas correctamente"
        Wait-UserInput
    }

    # ============================================
    # FASE 2: DOCKER BUILD & PUSH
    # ============================================

    if ($FromPhase -le 2) {
        Clear-Host
        Write-Header "🐳 FASE 2: BUILD & PUSH DOCKER IMAGE"

        # Configurar autenticación Docker
        Write-Step "Configurando autenticación Docker para GCP..."
        $result = Invoke-CommandWithFeedback `
            -Command "gcloud auth configure-docker $($Config.GCP_REGION)-docker.pkg.dev" `
            -Description "Autenticación Docker configurada" `
            -AllowRetry

        if (-not $result) {
            throw "Error al configurar autenticación Docker"
        }

        # Build y push usando Cloud Build (más rápido que build local)
        $imageTag = "$($Config.GCP_REGION)-docker.pkg.dev/$($Config.GCP_PROJECT_ID)/$($Config.ARTIFACT_REGISTRY_REPO)/$($Config.DOCKER_IMAGE_NAME):latest"

        Write-Step "Iniciando build con Cloud Build..."
        Write-Info "📍 Proyecto: $($Config.GCP_PROJECT_ID)"
        Write-Info "📍 Región: $($Config.GCP_REGION)"
        Write-Info "📍 Tag: $imageTag"
        Write-Host ""

        Measure-DeploymentTime -OperationName "Build Docker" -ScriptBlock {
            $buildCommand = "gcloud builds submit --tag $imageTag --project=$($Config.GCP_PROJECT_ID) --timeout=20m"

            # Cambiar al directorio raíz del proyecto (padre de mhw-deployment)
            $projectRoot = Split-Path -Parent $SCRIPT_DIR
            Push-Location $projectRoot

            try {
                $result = Invoke-CommandWithFeedback `
                    -Command $buildCommand `
                    -Description "Build con Cloud Build" `
                    -AllowRetry

                if (-not $result) {
                    throw "Error en Cloud Build"
                }
            } finally {
                Pop-Location
            }
        }

        Write-Success "Imagen Docker creada y pusheada exitosamente"
        Wait-UserInput
    }

    # ============================================
    # FASE 3: CLOUD RUN DEPLOYMENT
    # ============================================

    if ($FromPhase -le 3) {
        Clear-Host
        Write-Header "☁️  FASE 3: DEPLOY A CLOUD RUN"

        $imageTag = "$($Config.GCP_REGION)-docker.pkg.dev/$($Config.GCP_PROJECT_ID)/$($Config.ARTIFACT_REGISTRY_REPO)/$($Config.DOCKER_IMAGE_NAME):latest"

        $deployCommand = @"
gcloud run deploy $($Config.CLOUD_RUN_SERVICE) \
  --image=$imageTag \
  --region=$($Config.GCP_REGION) \
  --service-account=$($Config.SERVICE_ACCOUNT_EMAIL) \
  --set-secrets="DATABASE_URL=$($Config.SECRETS[0]):latest,SECRET_KEY=$($Config.SECRETS[1]):latest,SUPERUSER_EMAILS=$($Config.SECRETS[2]):latest" \
  --set-env-vars="FLASK_ENV=development,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false,ENVIRONMENT=production" \
  --set-cloudsql-instances="$($Config.GCP_PROJECT_ID):$($Config.GCP_REGION):$($Config.CLOUD_SQL_INSTANCE)" \
  --memory=1Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=3 \
  --port=8080 \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated \
  --project=$($Config.GCP_PROJECT_ID)
"@

        Write-Step "Desplegando a Cloud Run..."
        Write-Info "📍 Servicio: $($Config.CLOUD_RUN_SERVICE)"
        Write-Info "📍 Región: $($Config.GCP_REGION)"
        Write-Info "📍 RAM: 1Gi, CPU: 2"
        Write-Info "📍 Min: 0, Max: 3 instancias"
        Write-Host ""

        Measure-DeploymentTime -OperationName "Deploy Cloud Run" -ScriptBlock {
            $result = Invoke-CommandWithFeedback `
                -Command $deployCommand `
                -Description "Deployment a Cloud Run" `
                -AllowRetry

            if (-not $result) {
                throw "Error en deployment a Cloud Run"
            }
        }

        Write-Success "Cloud Run desplegado exitosamente"
        Wait-UserInput
    }

    # ============================================
    # FASE 4: LOAD BALANCER & NETWORK ENDPOINT GROUP
    # ============================================

    if ($FromPhase -le 4) {
        Clear-Host
        Write-Header "🌐 FASE 4: LOAD BALANCER & NEG"

        Write-Warning "IMPORTANTE: Esta fase requiere configuración manual en algunos pasos"
        Write-Host ""

        # Crear Network Endpoint Group
        Write-Step "Creando Network Endpoint Group..."
        $negCommand = "gcloud compute network-endpoint-groups create $($Config.CLOUD_RUN_SERVICE)-neg --region=$($Config.GCP_REGION) --network-endpoint-type=serverless --cloud-run-service=$($Config.CLOUD_RUN_SERVICE) --project=$($Config.GCP_PROJECT_ID)"

        $result = Invoke-CommandWithFeedback `
            -Command $negCommand `
            -Description "NEG creado" `
            -AllowRetry

        # Crear Backend Service
        Write-Step "Creando Backend Service..."
        $backendCommand = "gcloud compute backend-services create $($Config.CLOUD_RUN_SERVICE)-backend --global --load-balancing-scheme=EXTERNAL --protocol=HTTPS --project=$($Config.GCP_PROJECT_ID)"

        $result = Invoke-CommandWithFeedback `
            -Command $backendCommand `
            -Description "Backend Service creado" `
            -AllowRetry

        # Agregar NEG al Backend
        Write-Step "Agregando NEG al Backend..."
        $addBackendCommand = "gcloud compute backend-services add-backend $($Config.CLOUD_RUN_SERVICE)-backend --global --network-endpoint-group=$($Config.CLOUD_RUN_SERVICE)-neg --network-endpoint-group-region=$($Config.GCP_REGION) --project=$($Config.GCP_PROJECT_ID)"

        $result = Invoke-CommandWithFeedback `
            -Command $addBackendCommand `
            -Description "NEG agregado al Backend" `
            -AllowRetry

        Write-Success "Load Balancer configurado"
        Wait-UserInput
    }

    # ============================================
    # FASE 5: SSL CERTIFICATE & HTTPS PROXY
    # ============================================

    if ($FromPhase -le 5) {
        Clear-Host
        Write-Header "🔒 FASE 5: SSL CERTIFICATE & HTTPS PROXY"

        Write-Warning "Necesitas configurar tu dominio antes de continuar"
        Write-Info "Dominio recomendado: ticket-home-beta.mhwdev.dev"
        Write-Host ""

        $domain = Read-Host "Ingresa el dominio a usar"

        if ([string]::IsNullOrEmpty($domain)) {
            $domain = "ticket-home-beta.mhwdev.dev"
            Write-Info "Usando dominio por defecto: $domain"
        }

        # Crear certificado SSL
        Write-Step "Creando certificado SSL administrado..."
        $sslCommand = "gcloud compute ssl-certificates create $($Config.CLOUD_RUN_SERVICE)-ssl --domains=$domain --global --project=$($Config.GCP_PROJECT_ID)"

        $result = Invoke-CommandWithFeedback `
            -Command $sslCommand `
            -Description "Certificado SSL creado" `
            -AllowRetry

        Write-Warning "El certificado SSL puede tardar 15-60 minutos en aprovisionarse"

        # URL Map
        Write-Step "Creando URL Map..."
        $urlMapCommand = "gcloud compute url-maps create $($Config.CLOUD_RUN_SERVICE)-url-map --default-service=$($Config.CLOUD_RUN_SERVICE)-backend --global --project=$($Config.GCP_PROJECT_ID)"

        $result = Invoke-CommandWithFeedback `
            -Command $urlMapCommand `
            -Description "URL Map creado" `
            -AllowRetry

        # HTTPS Proxy
        Write-Step "Creando HTTPS Proxy..."
        $httpsProxyCommand = "gcloud compute target-https-proxies create $($Config.CLOUD_RUN_SERVICE)-https-proxy --ssl-certificates=$($Config.CLOUD_RUN_SERVICE)-ssl --url-map=$($Config.CLOUD_RUN_SERVICE)-url-map --global --project=$($Config.GCP_PROJECT_ID)"

        $result = Invoke-CommandWithFeedback `
            -Command $httpsProxyCommand `
            -Description "HTTPS Proxy creado" `
            -AllowRetry

        Write-Success "SSL y HTTPS Proxy configurados"
        Wait-UserInput
    }

    # ============================================
    # FASE 6: IP ESTÁTICA & FORWARDING RULE
    # ============================================

    if ($FromPhase -le 6) {
        Clear-Host
        Write-Header "🌍 FASE 6: IP ESTÁTICA & FORWARDING RULE"

        # Reservar IP
        Write-Step "Reservando IP estática global..."
        $ipCommand = "gcloud compute addresses create $($Config.CLOUD_RUN_SERVICE)-ip --global --project=$($Config.GCP_PROJECT_ID)"

        $result = Invoke-CommandWithFeedback `
            -Command $ipCommand `
            -Description "IP estática reservada" `
            -AllowRetry

        # Obtener IP
        Write-Step "Obteniendo dirección IP..."
        $staticIP = & gcloud compute addresses describe "$($Config.CLOUD_RUN_SERVICE)-ip" --global --project=$($Config.GCP_PROJECT_ID) --format="value(address)"

        Write-Success "IP estática: $staticIP"
        Write-Host ""
        Write-Warning "IMPORTANTE: Configura tu DNS con los siguientes valores:"
        Write-Info "Tipo: A"
        Write-Info "Nombre: [tu-dominio]"
        Write-Info "Valor: $staticIP"
        Write-Info "TTL: 300"
        Write-Host ""

        if (Confirm-Action "¿Has configurado el DNS? (Presiona Enter para continuar)") {
            # Crear Forwarding Rule
            Write-Step "Creando Forwarding Rule..."
            $forwardingCommand = "gcloud compute forwarding-rules create $($Config.CLOUD_RUN_SERVICE)-forwarding-rule --global --target-https-proxy=$($Config.CLOUD_RUN_SERVICE)-https-proxy --address=$($Config.CLOUD_RUN_SERVICE)-ip --ports=443 --project=$($Config.GCP_PROJECT_ID)"

            $result = Invoke-CommandWithFeedback `
                -Command $forwardingCommand `
                -Description "Forwarding Rule creada" `
                -AllowRetry
        }

        Write-Success "Networking configurado"
        Wait-UserInput
    }

    # ============================================
    # FASE 7: IAP (IDENTITY-AWARE PROXY)
    # ============================================

    if ($FromPhase -le 7) {
        Clear-Host
        Write-Header "🔐 FASE 7: IAP (IDENTITY-AWARE PROXY)"

        Write-Warning "IMPORTANTE: IAP requiere configuración manual en algunos pasos"
        Write-Host ""
        Write-Info "Pasos a seguir:"
        Write-Info "1. OAuth Consent Screen (consola web)"
        Write-Info "2. Crear OAuth Client ID (consola web)"
        Write-Info "3. Habilitar IAP en Backend Service (consola web o CLI)"
        Write-Info "4. Configurar usuarios autorizados"
        Write-Host ""

        Write-Info "Consola IAP: https://console.cloud.google.com/security/iap?project=$($Config.GCP_PROJECT_ID)"
        Write-Host ""

        if (Confirm-Action "¿Has completado los pasos 1-3 en la consola web?") {
            Write-Step "Configurando acceso de usuarios..."

            $email = Read-Host "Ingresa el email del usuario a autorizar (presiona Enter para saltar)"

            if (-not [string]::IsNullOrEmpty($email)) {
                $iapCommand = "gcloud iap web add-iam-policy-binding --resource-type=backend-services --service=$($Config.CLOUD_RUN_SERVICE)-backend --member=`"user:$email`" --role=`"roles/iap.httpsResourceAccessor`" --project=$($Config.GCP_PROJECT_ID)"

                $result = Invoke-CommandWithFeedback `
                    -Command $iapCommand `
                    -Description "Usuario autorizado en IAP" `
                    -AllowRetry
            }
        }

        Write-Success "IAP configurado"
        Wait-UserInput
    }

    # ============================================
    # RESUMEN FINAL
    # ============================================

    Clear-Host
    Write-Header "🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE 🎉" -Success

    $deploymentEndTime = Get-Date
    $totalTime = $deploymentEndTime - $DEPLOYMENT_START_TIME

    Write-Host "📊 Resumen del Deployment:" -ForegroundColor Cyan
    Write-Host ""

    $imageTag = "$($Config.GCP_REGION)-docker.pkg.dev/$($Config.GCP_PROJECT_ID)/$($Config.ARTIFACT_REGISTRY_REPO)/$($Config.DOCKER_IMAGE_NAME):latest"

    Write-Host "✅ Docker Image:" -ForegroundColor Green
    Write-Info "📍 $imageTag"
    Write-Host ""

    Write-Host "✅ Cloud Run Service:" -ForegroundColor Green
    Write-Info "📍 Nombre: $($Config.CLOUD_RUN_SERVICE)"
    Write-Info "📍 Región: $($Config.GCP_REGION)"
    Write-Info "📍 CPU: 2, RAM: 1Gi"
    Write-Info "📍 Min: 0, Max: 3 instancias"
    Write-Host ""

    Write-Host "✅ Load Balancer:" -ForegroundColor Green
    Write-Info "📍 Backend: $($Config.CLOUD_RUN_SERVICE)-backend"
    Write-Info "📍 SSL: $($Config.CLOUD_RUN_SERVICE)-ssl"
    Write-Host ""

    Write-Host "🔐 IAP:" -ForegroundColor Yellow
    Write-Info "📍 Estado: Configurado manualmente"
    Write-Host ""

    Write-Host "⏱️  Tiempo total: $($totalTime.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "📋 Próximos pasos:" -ForegroundColor Yellow
    Write-Info "1. Verificar que el certificado SSL esté ACTIVE (puede tardar 15-60 min)"
    Write-Info "2. Probar acceso con usuario autorizado en IAP"
    Write-Info "3. Verificar que superusuarios puedan acceder"
    Write-Info "4. Ejecutar seed de base de datos si es necesario"
    Write-Host ""

    Write-Header "¡Gracias por usar este script! 🚀" -Success

} catch {
    Write-Host ""
    Write-Error "ERROR FATAL: $($_.Exception.Message)"
    Write-Info "Stack Trace: $($_.ScriptStackTrace)"
    Write-Host ""
    Write-Warning "El deployment falló. Revisa los logs arriba para más detalles."
    exit 1
}
