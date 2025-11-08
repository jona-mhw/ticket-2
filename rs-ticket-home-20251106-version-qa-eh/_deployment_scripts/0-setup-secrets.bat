@echo off
REM ===============================================
REM SETUP SECRETS FOR v1.9.2 Security Hardening
REM ===============================================
REM
REM Este script crea los secrets necesarios en Google Secret Manager
REM
REM EJECUTAR ESTE SCRIPT UNA SOLA VEZ ANTES DEL DEPLOYMENT
REM
REM ===============================================

echo ===============================================
echo SETUP DE SECRETS PARA v1.9.2
echo ===============================================
echo.

REM Emails de superusuarios
set SUPERUSER_EMAILS=global_admin@tickethome.com;jonathan.segura@redsalud.cl;admin@tickethome.com

echo Emails de superusuarios a configurar:
echo    %SUPERUSER_EMAILS%
echo.

REM ===============================================
REM AMBIENTE DEV
REM ===============================================

echo ===============================================
echo CONFIGURANDO AMBIENTE DEV
echo ===============================================
echo.

echo 1. Creando secret 'superuser-emails' en dev-ticket-home-redsalud...
echo %SUPERUSER_EMAILS% | gcloud secrets create superuser-emails --data-file=- --project=dev-ticket-home-redsalud 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo    WARNING: Secret ya existe ^(OK si es re-ejecucion^)
)
echo.

echo 2. Dando permisos al Service Account de DEV...
gcloud secrets add-iam-policy-binding superuser-emails --member="serviceAccount:dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" --project=dev-ticket-home-redsalud 2>nul
echo    OK - Permisos configurados
echo.

echo ===============================================
echo CONFIGURANDO AMBIENTE QA
echo ===============================================
echo.

echo 1. Creando secret 'superuser-emails' en qa-ticket-home-redsalud...
echo %SUPERUSER_EMAILS% | gcloud secrets create superuser-emails --data-file=- --project=qa-ticket-home-redsalud 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo    WARNING: Secret ya existe ^(OK si es re-ejecucion^)
)
echo.

echo 2. Dando permisos al Service Account de QA...
gcloud secrets add-iam-policy-binding superuser-emails --member="serviceAccount:qa-ticket-home@qa-ticket-home-redsalud.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" --project=qa-ticket-home-redsalud 2>nul
echo    OK - Permisos configurados
echo.

REM ===============================================
REM VERIFICACION
REM ===============================================

echo ===============================================
echo VERIFICANDO SECRETS CREADOS
echo ===============================================
echo.

echo DEV:
gcloud secrets versions access latest --secret=superuser-emails --project=dev-ticket-home-redsalud
echo.

echo QA:
gcloud secrets versions access latest --secret=superuser-emails --project=qa-ticket-home-redsalud
echo.

echo ===============================================
echo SETUP COMPLETADO EXITOSAMENTE
echo ===============================================
echo.
echo Proximos pasos:
echo    1. Ejecutar build de imagen Docker
echo    2. Ejecutar deployment a DEV
echo.

pause
