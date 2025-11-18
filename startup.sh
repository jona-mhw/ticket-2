#!/bin/bash
set -e

echo "=========================================="
echo "🚀 TICKET-HOME - INICIO"
echo "=========================================="

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no configurada"
    exit 1
fi

echo "✅ DATABASE_URL configurada"

# Resetear DB solo si la variable está activada
if [ "$RESET_DB_ON_STARTUP" = "true" ]; then
    echo ""
    echo "🔥 ============================================"
    echo "🔥 RESET_DB_ON_STARTUP=true detectado"
    echo "🔥 BORRANDO Y RECREANDO BASE DE DATOS COMPLETA"
    echo "🔥 ============================================"
    echo ""

    # Detectar si debe usar seed mínimo para QA
    if [ "$USE_QA_MINIMAL_SEED" = "true" ]; then
        echo "🔹 USE_QA_MINIMAL_SEED=true detectado"
        echo "🔹 Usando seed mínimo (solo clínicas + superusuarios)"
        echo ""

        if flask reset-db-qa-minimal; then
            echo "✅ Base de datos reseteada con seed mínimo QA exitosamente"
        else
            echo "❌ ERROR al resetear la base de datos con seed mínimo"
            exit 1
        fi
    else
        echo "🔹 Usando seed completo con datos demo"
        echo ""

        if flask reset-db; then
            echo "✅ Base de datos reseteada, superusuarios sincronizados y datos seeded exitosamente"
        else
            echo "❌ ERROR al resetear la base de datos"
            exit 1
        fi
    fi
else
    echo "ℹ️  RESET_DB_ON_STARTUP no está activo"
    echo "ℹ️  La base de datos NO será modificada"
fi

# Importar datos desde GCS si está configurado
if [ -n "$IMPORT_SQL_FROM_GCS" ]; then
    echo ""
    echo "📥 ============================================"
    echo "📥 IMPORT_SQL_FROM_GCS detectado"
    echo "📥 IMPORTANDO DATOS DESDE: $IMPORT_SQL_FROM_GCS"
    echo "📥 ============================================"
    echo ""

    # Nombre temporal del archivo SQL
    SQL_FILE="/tmp/import_db.sql"

    # Descargar archivo desde GCS
    echo "📥 Descargando archivo SQL desde GCS..."
    if gsutil cp "$IMPORT_SQL_FROM_GCS" "$SQL_FILE"; then
        echo "✅ Archivo descargado exitosamente"

        # Obtener tamaño del archivo
        FILE_SIZE=$(du -h "$SQL_FILE" | cut -f1)
        echo "📦 Tamaño del archivo: $FILE_SIZE"

        # Parsear DATABASE_URL para obtener credenciales
        echo "📥 Parseando DATABASE_URL..."

        # Extraer componentes de la URL usando Python
        DB_PARAMS=$(python3 << 'PYEOF'
import os
from urllib.parse import urlparse

url = os.environ.get('DATABASE_URL', '')
parsed = urlparse(url)

print(f"PGHOST={parsed.hostname}")
print(f"PGPORT={parsed.port or 5432}")
print(f"PGUSER={parsed.username}")
print(f"PGPASSWORD={parsed.password}")
print(f"PGDATABASE={parsed.path.lstrip('/')}")
PYEOF
)

        # Exportar variables para psql
        eval "$DB_PARAMS"
        export PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE

        echo "📥 Importando datos a la base de datos..."
        echo "   Host: $PGHOST"
        echo "   Database: $PGDATABASE"

        if psql -f "$SQL_FILE"; then
            echo "✅ Datos importados exitosamente desde GCS"

            # Limpiar archivo temporal
            rm -f "$SQL_FILE"
            echo "🧹 Archivo temporal eliminado"
        else
            echo "❌ ERROR al importar datos desde SQL"
            echo "⚠️  El archivo se mantiene en: $SQL_FILE para debugging"
            exit 1
        fi
    else
        echo "❌ ERROR al descargar archivo desde GCS"
        echo "⚠️  Verifique que la ruta es correcta: $IMPORT_SQL_FROM_GCS"
        echo "⚠️  Y que el service account tiene permisos de lectura en el bucket"
        exit 1
    fi
else
    echo "ℹ️  IMPORT_SQL_FROM_GCS no está configurado"
    echo "ℹ️  No se importarán datos desde GCS"
fi

# Aplicar migraciones de la base de datos
echo ""
echo "🔄 Aplicando migraciones de la base de datos (Alembic)..."
flask db upgrade
echo "✅ Migraciones completadas."
echo ""

# Verificar datos
echo "🔍 Verificando base de datos..."
python3 << 'PYEOF'
from app import app, db
from models import User, Clinic

try:
    with app.app_context():
        user_count = User.query.count()
        clinic_count = Clinic.query.count()
        print(f"✅ Clínicas: {clinic_count}, Usuarios: {user_count}")
except Exception as e:
    print(f"⚠️  Error verificando DB: {e}")
PYEOF

# Configurar puerto
PORT=${PORT:-8080}
echo ""
echo "🌐 Iniciando servidor en puerto: $PORT"
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
