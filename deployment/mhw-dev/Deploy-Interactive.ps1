<#
.SYNOPSIS
    Deployment interactivo multi-ambiente para Ticket Home en Google Cloud Platform

.DESCRIPTION
    Este script guía paso a paso en el proceso de deployment de Ticket Home
    a GCP usando Cloud Run, Cloud SQL, IAP y SSL administrado.

    Ahora soporta múltiples ambientes:
    - MHW DEV (tu cloud personal)
    - Empresa DEV (RedSalud)
    - Empresa QA (RedSalud)

.PARAMETER Environment
    Ambiente a deployar: "mhw-dev", "empresa-dev", "empresa-qa"

.PARAMETER FromPhase
    Continuar desde una fase específica (1-7)

.PARAMETER SkipValidation
    Saltar validación de credenciales (no recomendado)

.EXAMPLE
    .\Deploy-Interactive.ps1
    El script preguntará a qué ambiente deployar

.EXAMPLE
    .\Deploy-Interactive.ps1 -Environment "mhw-dev"
    Deploya directamente a MHW DEV

.EXAMPLE
    .\Deploy-Interactive.ps1 -Environment "empresa-dev" -FromPhase 3
    Continúa deployment a Empresa DEV desde la Fase 3

.NOTES
    Versión: 2.0 (Multi-ambiente)
    Autor: Claude / Jonathan Segura
    Fecha: 2025-11-15
    Requisitos: PowerShell 5.1+, gcloud CLI, Docker (solo para empresa-dev/qa)
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet("mhw-dev", "empresa-dev", "empresa-qa", "")]
    [string]$Environment = "",

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
$CONFIGS_DIR = Join-Path $SCRIPT_DIR "configs"
$MODULE_PATH = Join-Path $LIB_DIR "DeploymentFunctions.psm1"

# Importar módulo de funciones
if (-not (Test-Path $MODULE_PATH)) {
    Write-Host "ERROR: No se encontró el módulo DeploymentFunctions.psm1" -ForegroundColor Red
    Write-Host "Ruta esperada: $MODULE_PATH" -ForegroundColor Yellow
    exit 1
}

Import-Module $MODULE_PATH -Force

# ============================================
# FUNCIÓN: SELECCIONAR AMBIENTE
# ============================================

function Select-Environment {
    Write-Host ""
    Write-Header "SELECCIÓN DE AMBIENTE"
    Write-Host ""

    Write-Host "Ambientes disponibles:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [1] MHW DEV" -ForegroundColor Green
    Write-Host "      - Tu cloud personal (ticket-home-demo)" -ForegroundColor Gray
    Write-Host "      - Región: us-central1" -ForegroundColor Gray
    Write-Host "      - URL: ticket-home-beta.mhwdev.dev" -ForegroundColor Gray
    Write-Host "      - Min instances: 0 (escala a cero)" -ForegroundColor Gray
    Write-Host "      - Build: Cloud Build (rápido)" -ForegroundColor Gray
    Write-Host ""

    Write-Host "  [2] EMPRESA DEV" -ForegroundColor Yellow
    Write-Host "      - RedSalud DEV (dev-ticket-home-redsalud)" -ForegroundColor Gray
    Write-Host "      - Región: southamerica-west1 (Chile)" -ForegroundColor Gray
    Write-Host "      - URL: ticket-home.mhwdev.dev" -ForegroundColor Gray
    Write-Host "      - Min instances: 1 (siempre activo)" -ForegroundColor Gray
    Write-Host "      - Build: Docker Desktop (requerido)" -ForegroundColor Gray
    Write-Host ""

    Write-Host "  [3] EMPRESA QA" -ForegroundColor Magenta
    Write-Host "      - RedSalud QA (qa-ticket-home-redsalud)" -ForegroundColor Gray
    Write-Host "      - Región: southamerica-west1 (Chile)" -ForegroundColor Gray
    Write-Host "      - URL: qa-ticket-home.mhwdev.dev" -ForegroundColor Gray
    Write-Host "      - Min instances: 1 (siempre activo)" -ForegroundColor Gray
    Write-Host "      - Build: Docker Desktop (requerido)" -ForegroundColor Gray
    Write-Host "      - ⚠️  Solo SSO (sin login tradicional)" -ForegroundColor Yellow
    Write-Host ""

    do {
        $choice = Read-Host "Selecciona ambiente (1-3)"
    } while ($choice -notin @("1", "2", "3"))

    $envMapping = @{
        "1" = "mhw-dev"
        "2" = "empresa-dev"
        "3" = "empresa-qa"
    }

    return $envMapping[$choice]
}

# ============================================
# FUNCIÓN: CARGAR CONFIGURACIÓN POR AMBIENTE
# ============================================

function Load-EnvironmentConfig {
    param([string]$EnvName)

    $configFile = Join-Path $CONFIGS_DIR "$EnvName.env"

    if (-not (Test-Path $configFile)) {
        Write-Error "No se encontró archivo de configuración: $configFile"
        Write-Info "Ejecuta primero el setup de ese ambiente"
        exit 1
    }

    Write-Step "Cargando configuración de $EnvName..."

    # Leer archivo .env y parsear variables
    $config = @{}
    Get-Content $configFile | ForEach-Object {
        if ($_ -match '^export\s+(\w+)="(.+)"$') {
            $config[$matches[1]] = $matches[2]
        }
        elseif ($_ -match '^export\s+(\w+)=(.+)$') {
            $config[$matches[1]] = $matches[2].Trim('"')
        }
    }

    Write-Success "Configuración cargada: $($config.GCP_PROJECT_ID)"

    return $config
}

# ============================================
# FUNCIÓN: MOSTRAR RESUMEN DE CONFIGURACIÓN
# ============================================

function Show-ConfigSummary {
    param([hashtable]$Config)

    Write-Host ""
    Write-Header "RESUMEN DE CONFIGURACIÓN"
    Write-Host ""
    Write-Host "Proyecto GCP:     " -NoNewline -ForegroundColor Gray
    Write-Host $Config.GCP_PROJECT_ID -ForegroundColor Cyan
    Write-Host "Región:           " -NoNewline -ForegroundColor Gray
    Write-Host $Config.GCP_REGION -ForegroundColor Cyan
    Write-Host "Ambiente:         " -NoNewline -ForegroundColor Gray
    Write-Host $Config.ENVIRONMENT -ForegroundColor Cyan
    Write-Host "Dominio:          " -NoNewline -ForegroundColor Gray
    Write-Host $Config.DOMAIN_NAME -ForegroundColor Cyan
    Write-Host "Cloud SQL:        " -NoNewline -ForegroundColor Gray
    Write-Host $Config.CLOUDSQL_INSTANCE_NAME -ForegroundColor Cyan
    Write-Host "Service Account:  " -NoNewline -ForegroundColor Gray
    Write-Host $Config.SERVICE_ACCOUNT_EMAIL -ForegroundColor Cyan
    Write-Host "Build Method:     " -NoNewline -ForegroundColor Gray

    if ($Config.BUILD_METHOD -eq "docker-desktop") {
        Write-Host "Docker Desktop (local)" -ForegroundColor Yellow
        Write-Info "Asegúrate de que Docker Desktop esté corriendo"
    } else {
        Write-Host "Cloud Build (remoto)" -ForegroundColor Green
    }

    Write-Host ""
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
    # PANTALLA 0: SELECCIÓN DE AMBIENTE
    # ============================================

    if ($Environment -eq "") {
        Clear-Host
        Show-Banner
        $Environment = Select-Environment
    }

    # Cargar configuración del ambiente seleccionado
    $Config = Load-EnvironmentConfig -EnvName $Environment

    # ============================================
    # PANTALLA 1: BIENVENIDA Y CONFIRMACIÓN
    # ============================================

    Clear-Host
    Show-Banner
    Show-RandomWelcome

    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                                                                    ║" -ForegroundColor Magenta
    Write-Host "║  " -NoNewline -ForegroundColor Magenta
    Write-Host "Ambiente seleccionado: " -NoNewline -ForegroundColor White
    Write-Host "$Environment".PadRight(47) -NoNewline -ForegroundColor Cyan
    Write-Host " ║" -ForegroundColor Magenta
    Write-Host "║                                                                    ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""

    Show-ConfigSummary -Config $Config

    Wait-UserInput

    # Confirmar que quiere continuar
    if (-not (Confirm-Action "¿Deseas continuar con el deployment a $Environment")) {
        Write-Warning "Deployment cancelado por el usuario"
        exit 0
    }

    # ============================================
    # VALIDACIÓN DE PREREQUISITOS
    # ============================================

    if (-not $SkipValidation) {
        Write-Header "VALIDACIÓN DE PREREQUISITOS"
        Write-Host ""

        # Validar gcloud
        if (-not (Test-GCloudAuth)) {
            Write-Error "gcloud CLI no está autenticado"
            exit 1
        }
        Write-Success "gcloud CLI autenticado"

        # Validar proyecto correcto
        if (-not (Test-GCloudProject -ProjectId $Config.GCP_PROJECT_ID)) {
            Write-Warning "Proyecto actual diferente al esperado"
            if (Confirm-Action "¿Cambiar al proyecto $($Config.GCP_PROJECT_ID)") {
                gcloud config set project $Config.GCP_PROJECT_ID
            } else {
                exit 1
            }
        }
        Write-Success "Proyecto GCP: $($Config.GCP_PROJECT_ID)"

        # Validar Docker (solo si es requerido)
        if ($Config.BUILD_METHOD -eq "docker-desktop") {
            if (-not (Test-Docker)) {
                Write-Error "Docker Desktop no está corriendo"
                Write-Info "Inicia Docker Desktop y vuelve a ejecutar el script"
                exit 1
            }
            Write-Success "Docker Desktop corriendo"
        }

        Write-Host ""
        Wait-UserInput
    }

    # ============================================
    # DEPLOYMENT - RESTO DEL SCRIPT
    # ============================================

    Write-Info "Continuando con deployment..."
    Write-Info "Fase inicial: $FromPhase"
    Write-Info "Total de fases: $TOTAL_PHASES"
    Write-Host ""

    # NOTA: Aquí continuaría el resto del deployment existente
    # Por ahora solo muestro el concepto de selección de ambiente

    Write-Success "Script de selección de ambiente funcionando correctamente"
    Write-Info "El deployment completo se agregará en la siguiente versión"

} catch {
    Write-Error "Error durante el deployment: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""
