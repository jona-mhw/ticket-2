# ============================================
# DEPLOYMENT FUNCTIONS MODULE
# ============================================
# Módulo de funciones auxiliares para Deploy-Interactive.ps1
# Versión: 1.0
# Autor: Claude
# ============================================

# ============================================
# FUNCIONES DE OUTPUT CON COLORES
# ============================================

function Write-Step {
    <#
    .SYNOPSIS
        Muestra un paso en progreso con icono de reloj
    #>
    param([string]$Message)
    Write-Host "[⏳] $Message" -ForegroundColor Cyan
}

function Write-Success {
    <#
    .SYNOPSIS
        Muestra un mensaje de éxito con icono de check
    #>
    param([string]$Message)
    Write-Host "[✅] $Message" -ForegroundColor Green
}

function Write-Error {
    <#
    .SYNOPSIS
        Muestra un mensaje de error con icono X
    #>
    param([string]$Message)
    Write-Host "[❌] $Message" -ForegroundColor Red
}

function Write-Info {
    <#
    .SYNOPSIS
        Muestra información adicional con icono de pin
    #>
    param([string]$Message)
    Write-Host "[📍] $Message" -ForegroundColor Yellow
}

function Write-Warning {
    <#
    .SYNOPSIS
        Muestra una advertencia con icono de alerta
    #>
    param([string]$Message)
    Write-Host "[⚠️ ] $Message" -ForegroundColor DarkYellow
}

function Write-Header {
    <#
    .SYNOPSIS
        Muestra un header con bordes decorativos
    #>
    param(
        [string]$Message,
        [switch]$Success
    )

    Write-Host ""
    Write-Host "╔" -NoNewline -ForegroundColor Magenta
    Write-Host ("═" * 68) -NoNewline -ForegroundColor Magenta
    Write-Host "╗" -ForegroundColor Magenta

    $color = if ($Success) { "Green" } else { "Magenta" }
    $paddedMessage = $Message.PadRight(68)

    Write-Host "║" -NoNewline -ForegroundColor Magenta
    Write-Host $paddedMessage -NoNewline -ForegroundColor $color
    Write-Host "║" -ForegroundColor Magenta

    Write-Host "╚" -NoNewline -ForegroundColor Magenta
    Write-Host ("═" * 68) -NoNewline -ForegroundColor Magenta
    Write-Host "╝" -ForegroundColor Magenta
    Write-Host ""
}

# ============================================
# FUNCIONES DE INTERACCIÓN
# ============================================

function Wait-UserInput {
    <#
    .SYNOPSIS
        Pausa y espera que el usuario presione Enter
    #>
    param([string]$Message = "Presiona [ENTER] para continuar...")

    Write-Host ""
    Write-Host "   $Message" -ForegroundColor Gray
    $null = Read-Host
}

function Confirm-Action {
    <#
    .SYNOPSIS
        Solicita confirmación del usuario (S/n)
    #>
    param(
        [string]$Message,
        [switch]$DefaultYes
    )

    $prompt = if ($DefaultYes) { "$Message [S/n]" } else { "$Message [s/N]" }
    $response = Read-Host "   $prompt"

    if ($DefaultYes) {
        return ($response -eq "" -or $response -match "^[Ss]")
    } else {
        return ($response -match "^[Ss]")
    }
}

# ============================================
# FUNCIONES DE BANNER Y MENSAJES
# ============================================

function Show-Banner {
    <#
    .SYNOPSIS
        Muestra el banner de bienvenida con ASCII art
    #>
    Clear-Host

    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                                                                    ║" -ForegroundColor Magenta
    Write-Host "║   " -NoNewline -ForegroundColor Magenta
    Write-Host "████████╗██╗ ██████╗██╗  ██╗███████╗████████╗" -NoNewline -ForegroundColor Cyan
    Write-Host "    " -NoNewline -ForegroundColor Magenta
    Write-Host "██╗  ██╗ ██████╗ ███╗   ███╗███████╗" -NoNewline -ForegroundColor Green
    Write-Host "   ║" -ForegroundColor Magenta

    Write-Host "║   " -NoNewline -ForegroundColor Magenta
    Write-Host "╚══██╔══╝██║██╔════╝██║ ██╔╝██╔════╝╚══██╔══╝" -NoNewline -ForegroundColor Cyan
    Write-Host "    " -NoNewline -ForegroundColor Magenta
    Write-Host "██║  ██║██╔═══██╗████╗ ████║██╔════╝" -NoNewline -ForegroundColor Green
    Write-Host "   ║" -ForegroundColor Magenta

    Write-Host "║   " -NoNewline -ForegroundColor Magenta
    Write-Host "   ██║   ██║██║     █████╔╝ █████╗     ██║   " -NoNewline -ForegroundColor Cyan
    Write-Host "    " -NoNewline -ForegroundColor Magenta
    Write-Host "   ███████║██║   ██║██╔████╔██║█████╗  " -NoNewline -ForegroundColor Green
    Write-Host "   ║" -ForegroundColor Magenta

    Write-Host "║   " -NoNewline -ForegroundColor Magenta
    Write-Host "   ██║   ██║██║     ██╔═██╗ ██╔══╝     ██║   " -NoNewline -ForegroundColor Cyan
    Write-Host "    " -NoNewline -ForegroundColor Magenta
    Write-Host "   ██╔══██║██║   ██║██║╚██╔╝██║██╔══╝  " -NoNewline -ForegroundColor Green
    Write-Host "   ║" -ForegroundColor Magenta

    Write-Host "║   " -NoNewline -ForegroundColor Magenta
    Write-Host "   ██║   ██║╚██████╗██║  ██╗███████╗   ██║   " -NoNewline -ForegroundColor Cyan
    Write-Host "    " -NoNewline -ForegroundColor Magenta
    Write-Host "   ██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗" -NoNewline -ForegroundColor Green
    Write-Host "   ║" -ForegroundColor Magenta

    Write-Host "║   " -NoNewline -ForegroundColor Magenta
    Write-Host "   ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝   " -NoNewline -ForegroundColor Cyan
    Write-Host "    " -NoNewline -ForegroundColor Magenta
    Write-Host "   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝" -NoNewline -ForegroundColor Green
    Write-Host "   ║" -ForegroundColor Magenta

    Write-Host "║                                                                    ║" -ForegroundColor Magenta
    Write-Host "║                   " -NoNewline -ForegroundColor Magenta
    Write-Host "🚀 DEPLOYMENT INTERACTIVO - GCP 🚀" -NoNewline -ForegroundColor Yellow
    Write-Host "               ║" -ForegroundColor Magenta
    Write-Host "║                         " -NoNewline -ForegroundColor Magenta
    Write-Host "Versión 1.0 Beta RS" -NoNewline -ForegroundColor White
    Write-Host "                        ║" -ForegroundColor Magenta
    Write-Host "║                                                                    ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""

    Write-Host "   Bienvenido al asistente de deployment de Ticket Home." -ForegroundColor White
    Write-Host "   Este script te guiará paso a paso en el despliegue a Google Cloud Platform." -ForegroundColor Gray
    Write-Host ""
    Write-Host "   📦 Proyecto: " -NoNewline -ForegroundColor Cyan
    Write-Host "ticket-home-demo" -ForegroundColor Yellow
    Write-Host "   🌍 Región: " -NoNewline -ForegroundColor Cyan
    Write-Host "us-central1" -ForegroundColor Yellow
    Write-Host "   🔐 Modo: " -NoNewline -ForegroundColor Cyan
    Write-Host "IAP + SSL + Cloud Run" -ForegroundColor Yellow
    Write-Host ""
}

function Show-RandomWelcome {
    <#
    .SYNOPSIS
        Muestra un mensaje aleatorio del pool de WelcomeMessages.json
    #>
    param([string]$MessagesPath)

    try {
        Clear-Host

        $messagesJson = Get-Content -Path $MessagesPath -Raw | ConvertFrom-Json
        $randomMessage = $messagesJson.messages | Get-Random

        Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
        Write-Host "║                                                                    ║" -ForegroundColor Magenta

        # Mostrar contenido del mensaje centrado
        $lines = $randomMessage.content -split "`n"
        foreach ($line in $lines) {
            $paddedLine = $line.PadLeft(([Math]::Floor($line.Length + (68 - $line.Length) / 2))).PadRight(68)
            Write-Host "║" -NoNewline -ForegroundColor Magenta
            Write-Host $paddedLine -NoNewline -ForegroundColor Cyan
            Write-Host "║" -ForegroundColor Magenta
        }

        Write-Host "║                                                                    ║" -ForegroundColor Magenta
        Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
        Write-Host ""

    } catch {
        Write-Warning "No se pudo cargar mensaje aleatorio: $_"
    }
}

# ============================================
# FUNCIONES DE VALIDACIÓN
# ============================================

function Test-GCloudAuth {
    <#
    .SYNOPSIS
        Verifica que gcloud esté autenticado
    #>
    Write-Step "Verificando autenticación con gcloud..."

    try {
        $account = & gcloud config get-value account 2>$null

        if ([string]::IsNullOrEmpty($account)) {
            Write-Error "No autenticado en gcloud"
            Write-Info "Ejecuta: gcloud auth login"
            return $false
        }

        Write-Success "Autenticado como: $account"
        return $true

    } catch {
        Write-Error "Error al verificar autenticación: $_"
        return $false
    }
}

function Test-GCloudProject {
    <#
    .SYNOPSIS
        Verifica que el proyecto GCP esté configurado
    #>
    param([string]$ExpectedProject)

    Write-Step "Verificando proyecto GCP..."

    try {
        $currentProject = & gcloud config get-value project 2>$null

        if ([string]::IsNullOrEmpty($currentProject)) {
            Write-Error "No hay proyecto configurado"
            Write-Info "Ejecuta: gcloud config set project $ExpectedProject"
            return $false
        }

        if ($ExpectedProject -and $currentProject -ne $ExpectedProject) {
            Write-Warning "Proyecto actual: $currentProject (esperado: $ExpectedProject)"

            if (Confirm-Action "¿Cambiar al proyecto $ExpectedProject?" -DefaultYes) {
                & gcloud config set project $ExpectedProject
                Write-Success "Proyecto cambiado a: $ExpectedProject"
            } else {
                return $false
            }
        } else {
            Write-Success "Proyecto activo: $currentProject"
        }

        return $true

    } catch {
        Write-Error "Error al verificar proyecto: $_"
        return $false
    }
}

function Test-CloudSQLInstance {
    <#
    .SYNOPSIS
        Verifica acceso a la instancia Cloud SQL
    #>
    param(
        [string]$InstanceName,
        [string]$Project
    )

    Write-Step "Validando acceso a Cloud SQL..."

    try {
        $instanceIP = & gcloud sql instances describe $InstanceName `
            --project=$Project `
            --format="value(ipAddresses[0].ipAddress)" 2>$null

        if ([string]::IsNullOrEmpty($instanceIP)) {
            Write-Error "No se pudo acceder a la instancia: $InstanceName"
            return $false
        }

        Write-Success "Instancia encontrada: $InstanceName (IP: $instanceIP)"
        return $true

    } catch {
        Write-Error "Error al verificar Cloud SQL: $_"
        return $false
    }
}

function Test-Secrets {
    <#
    .SYNOPSIS
        Verifica que los secrets existan en Secret Manager
    #>
    param(
        [string[]]$SecretNames,
        [string]$Project
    )

    Write-Step "Verificando Secret Manager..."

    $allSecretsExist = $true

    foreach ($secretName in $SecretNames) {
        try {
            $version = & gcloud secrets versions list $secretName `
                --project=$Project `
                --limit=1 `
                --format="value(name)" 2>$null

            if ([string]::IsNullOrEmpty($version)) {
                Write-Error "Secret no encontrado: $secretName"
                $allSecretsExist = $false
            } else {
                Write-Success "$secretName (última versión: $version)"
            }

        } catch {
            Write-Error "Error al verificar secret $secretName : $_"
            $allSecretsExist = $false
        }
    }

    return $allSecretsExist
}

function Test-ServiceAccount {
    <#
    .SYNOPSIS
        Verifica que la Service Account exista y tenga permisos
    #>
    param(
        [string]$ServiceAccountEmail,
        [string]$Project
    )

    Write-Step "Validando Service Account..."

    try {
        # Verificar que existe
        $sa = & gcloud iam service-accounts describe $ServiceAccountEmail `
            --project=$Project 2>$null

        if ([string]::IsNullOrEmpty($sa)) {
            Write-Error "Service Account no encontrada: $ServiceAccountEmail"
            return $false
        }

        Write-Success $ServiceAccountEmail

        # Listar roles
        Write-Info "Verificando roles..."
        $roles = & gcloud projects get-iam-policy $Project `
            --flatten="bindings[].members" `
            --filter="bindings.members:serviceAccount:$ServiceAccountEmail" `
            --format="value(bindings.role)" 2>$null

        if ($roles) {
            foreach ($role in $roles) {
                Write-Info "  ├─ $role ✅"
            }
        } else {
            Write-Warning "No se encontraron roles asignados"
        }

        return $true

    } catch {
        Write-Error "Error al verificar Service Account: $_"
        return $false
    }
}

function Test-Docker {
    <#
    .SYNOPSIS
        Verifica que Docker esté corriendo
    #>
    Write-Step "Verificando Docker..."

    try {
        $dockerVersion = & docker --version 2>$null

        if ([string]::IsNullOrEmpty($dockerVersion)) {
            Write-Error "Docker no está instalado o no está en el PATH"
            return $false
        }

        # Verificar que Docker daemon esté corriendo
        $null = & docker ps 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker Desktop no está corriendo"
            Write-Info "Inicia Docker Desktop y vuelve a intentar"
            return $false
        }

        Write-Success "Docker Desktop corriendo ($dockerVersion)"
        return $true

    } catch {
        Write-Error "Error al verificar Docker: $_"
        return $false
    }
}

# ============================================
# FUNCIONES DE DEPLOYMENT
# ============================================

function Invoke-CommandWithFeedback {
    <#
    .SYNOPSIS
        Ejecuta un comando y muestra feedback visual
    #>
    param(
        [string]$Command,
        [string]$Description,
        [switch]$AllowRetry
    )

    Write-Step $Description

    try {
        $output = Invoke-Expression $Command 2>&1

        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falló: $Description"
            Write-Info "Comando: $Command"
            Write-Info "Salida: $output"

            if ($AllowRetry) {
                if (Confirm-Action "¿Deseas reintentar?") {
                    return Invoke-CommandWithFeedback -Command $Command -Description $Description -AllowRetry
                }
            }

            return $false
        }

        Write-Success $Description
        return $true

    } catch {
        Write-Error "Error inesperado: $($_.Exception.Message)"

        if ($AllowRetry) {
            if (Confirm-Action "¿Deseas reintentar?") {
                return Invoke-CommandWithFeedback -Command $Command -Description $Description -AllowRetry
            }
        }

        return $false
    }
}

function Measure-DeploymentTime {
    <#
    .SYNOPSIS
        Mide el tiempo de ejecución de una operación
    #>
    param(
        [scriptblock]$ScriptBlock,
        [string]$OperationName
    )

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        & $ScriptBlock
    } finally {
        $stopwatch.Stop()
        $elapsed = $stopwatch.Elapsed
        Write-Info "$OperationName completado en $($elapsed.ToString('mm\:ss'))"
    }
}

# Exportar funciones
Export-ModuleMember -Function @(
    'Write-Step',
    'Write-Success',
    'Write-Error',
    'Write-Info',
    'Write-Warning',
    'Write-Header',
    'Wait-UserInput',
    'Confirm-Action',
    'Show-Banner',
    'Show-RandomWelcome',
    'Test-GCloudAuth',
    'Test-GCloudProject',
    'Test-CloudSQLInstance',
    'Test-Secrets',
    'Test-ServiceAccount',
    'Test-Docker',
    'Invoke-CommandWithFeedback',
    'Measure-DeploymentTime'
)
