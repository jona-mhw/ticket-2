param (
    [ValidateSet("no-reset", "reset-minimal", "reset-full")]
    [string]$Scenario = "no-reset"
)

$ErrorActionPreference = "Stop"

# Directorio base del script
$ScriptDir = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🚀 DESPLIEGUE QA - ESCENARIO: $Scenario" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Build & Push
Write-Host ""
Write-Host "📦 [1/2] Construyendo y subiendo imagen Docker..." -ForegroundColor Yellow
# Llamamos al bat existente. cmd /c es necesario para ejecutar .bat desde PowerShell correctamente
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$ScriptDir\4-build-and-push-qa.bat`"" -Wait -NoNewWindow

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Error en Build & Push. Abortando."
    exit 1
}

# 2. Terraform Apply
Write-Host ""
Write-Host "🏗️  [2/2] Aplicando configuración Terraform..." -ForegroundColor Yellow

# Navegar al directorio de Terraform
$TerraformDir = Join-Path $ScriptDir "..\..\terraform\environments\qa"
Push-Location $TerraformDir

try {
    # Configurar credenciales para evitar problemas de quota/permisos
    Write-Host "🔑 Generando token de acceso..."
    $env:GOOGLE_CLOUD_QUOTA_PROJECT = 'qa-ticket-home-redsalud'
    $token = gcloud auth print-access-token
    if (-not $token) { throw "No se pudo generar el token de gcloud" }
    $env:GOOGLE_OAUTH_ACCESS_TOKEN = $token

    # Ejecutar Terraform
    terraform apply -var-file="terraform.tfvars" -var-file="qa-$Scenario.tfvars" -auto-approve
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ ¡Despliegue completado exitosamente!" -ForegroundColor Green
        Write-Host "🌍 URL: https://qa-ticket-home.mhwdev.dev"
    } else {
        throw "Terraform apply falló"
    }
}
catch {
    Write-Error "❌ Error durante el despliegue: $_"
    exit 1
}
finally {
    Pop-Location
}
