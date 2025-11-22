@echo off
echo ===============================================
echo BUILD AND PUSH DOCKER IMAGE - QA
echo ===============================================
echo.

set PROJECT_ID=qa-ticket-home-redsalud
set REGION=southamerica-west1
set REPO_NAME=tickethome-repo
set IMAGE_NAME=ticket-home
set TAG=latest

set FULL_IMAGE_NAME=%REGION%-docker.pkg.dev/%PROJECT_ID%/%REPO_NAME%/%IMAGE_NAME%:%TAG%

echo 1. Configurando autenticacion de Docker...
gcloud auth configure-docker %REGION%-docker.pkg.dev --quiet

echo.
echo 2. Construyendo imagen Docker...
echo    Imagen: %FULL_IMAGE_NAME%
docker build -t %FULL_IMAGE_NAME% ../../..
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Fallo al construir la imagen.
    exit /b %ERRORLEVEL%
)

echo.
echo 3. Subiendo imagen a Artifact Registry...
docker push %FULL_IMAGE_NAME%
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Fallo al subir la imagen.
    exit /b %ERRORLEVEL%
)

echo.
echo ✅ Build y Push completados exitosamente.
echo.
pause
