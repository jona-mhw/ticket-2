# Script de despliegue para QA
# 1. Construye la imagen en Cloud Build
# 2. Despliega la infraestructura en QA con la nueva imagen

$ErrorActionPreference = "Stop"

# Intentar encontrar terraform en el PATH o en la ubicación de WinGet
if (Get-Command terraform -ErrorAction SilentlyContinue) {
    $TerraformExe = "terraform"
} else {
    $WinGetPath = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Hashicorp.Terraform_Microsoft.Winget.Source_8wekyb3d8bbwe\terraform.exe"
    if (Test-Path $WinGetPath) {
        $TerraformExe = $WinGetPath
        Write-Host "Terraform encontrado en: $TerraformExe" -ForegroundColor Gray
    } else {
        Write-Error "No se pudo encontrar terraform. Por favor asegúrate de que está instalado y en el PATH."
        exit 1
    }
}

# Asegurar que estamos en el directorio del script
Set-Location $PSScriptRoot

Write-Host "=== [1/2] Iniciando Build en GCP ===" -ForegroundColor Cyan
# Ya estamos en terraform/QA-buildGCP gracias a Set-Location $PSScriptRoot
& $TerraformExe init -upgrade
& $TerraformExe apply -auto-approve
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n=== [2/2] Desplegando en QA ===" -ForegroundColor Cyan
Set-Location "../qa"
& $TerraformExe init -upgrade

# Generar timestamp para forzar redespliegue
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
Write-Host "Timestamp de despliegue: $timestamp" -ForegroundColor Yellow

& $TerraformExe apply -auto-approve -var="force_deployment_timestamp=$timestamp" -var-file="qa-reset-minimal.tfvars"
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n=== Despliegue Completado Exitosamente ===" -ForegroundColor Green
