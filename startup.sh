#!/bin/bash
set -e

echo "=========================================="
echo "TICKET-HOME - CLOUD RUN STARTUP"
echo "=========================================="

# Configurar puerto
PORT=${PORT:-8080}

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "ADVERTENCIA: DATABASE_URL no configurada"
    echo "Continuando...el servicio puede fallar sin esta variable"
fi

echo "Iniciando aplicacion Flask"

# Aplicar migraciones y seed (si DATABASE_URL esta disponible)
if [ -n "$DATABASE_URL" ]; then

    # Verificar si hay que resetear la BD
    if [ "$RESET_DB_ON_STARTUP" = "true" ]; then
        # Bloquear reset en producción
        if [ "$ENVIRONMENT" = "production" ]; then
            echo "ERROR: RESET_DB_ON_STARTUP no está permitido en producción. Abortando."
            exit 1
        fi

        echo ""
        echo "RESET_DB_ON_STARTUP=true detectado"
        echo "Reseteando base de datos..."

        if [ "$USE_QA_MINIMAL_SEED" = "true" ]; then
            echo "USE_QA_MINIMAL_SEED=true - Usando seed minimal (solo clinicas + superusers)"
            flask reset-db-qa-minimal 2>&1 || echo "Advertencia: Error en reset-db-qa-minimal"
        else
            echo "Usando seed completo con datos demo"
            flask reset-db 2>&1 || echo "Advertencia: Error en reset-db"
        fi
        echo "Reset de base de datos completado"
    else
        echo ""
        echo "Aplicando migraciones de base de datos..."
        flask db upgrade 2>&1 || { echo "ERROR: Las migraciones de base de datos fallaron. Abortando."; exit 1; }
        echo "Migraciones procesadas"

        echo ""
        echo "Sincronizando superusers..."
        flask sync-superusers 2>&1 || echo "Advertencia: No se pudieron sincronizar superusers"
        echo "Superusers sincronizados"
    fi
fi

echo ""
echo "Iniciando Gunicorn en puerto $PORT"
echo "=========================================="

# Iniciar Gunicorn
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 8 \
    --timeout 120 \
    --graceful-timeout 300 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app
