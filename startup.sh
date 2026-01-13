#!/bin/bash
set -e

echo "=========================================="
echo "🚀 TICKET-HOME - CLOUD RUN STARTUP"
echo "=========================================="

# Configurar puerto
PORT=${PORT:-8080}

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  ADVERTENCIA: DATABASE_URL no configurada"
    echo "Continuando...el servicio puede fallar sin esta variable"
fi

echo "✅ Iniciando aplicación Flask"

# Aplicar migraciones (si DATABASE_URL está disponible)
if [ -n "$DATABASE_URL" ]; then
    echo ""
    echo "🔄 Aplicando migraciones de base de datos..."
    flask db upgrade 2>/dev/null || echo "⚠️  Advertencia: No se pudieron aplicar todas las migraciones"
    echo "✅ Migraciones procesadas"
fi

echo ""
echo "🌐 Iniciando Gunicorn en puerto $PORT"
echo "=========================================="

# Iniciar Gunicorn
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 8 \
    --timeout 0 \
    --graceful-timeout 300 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app
