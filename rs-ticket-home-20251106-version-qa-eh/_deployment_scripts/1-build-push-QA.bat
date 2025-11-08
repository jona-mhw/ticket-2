@echo off
REM ================================================
REM SCRIPT 1: BUILD Y PUSH - QA
REM ================================================
echo ================================================
echo 📦 BUILD Y PUSH IMAGEN DOCKER - QA
echo ================================================
echo.

set PROJECT_ID=qa-ticket-home-redsalud
set REGION=us-central1
set IMAGE=%REGION%-docker.pkg.dev/%PROJECT_ID%/tickethome-repo/ticket-home:latest

echo 🔨 Paso 1/2: Construyendo imagen...
docker build -t %IMAGE% .

if %ERRORLEVEL% neq 0 (
    echo ❌ Error al construir imagen
    pause
    exit /b 1
)

echo.
echo ⬆️  Paso 2/2: Subiendo a Artifact Registry...
docker push %IMAGE%

if %ERRORLEVEL% neq 0 (
    echo ❌ Error al subir imagen
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ IMAGEN LISTA - QA
echo ================================================
echo.
echo 📌 Imagen: %IMAGE%
echo.
echo 🚀 Próximo paso:
echo    - Script 2: Deploy con reset DB (primera vez / cambios en DB)
echo    - Script 3: Deploy normal (cambios de código)
echo.
pause
