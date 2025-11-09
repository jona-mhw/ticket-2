#!/bin/bash
# ================================================
# SCRIPT 1: BUILD Y PUSH IMAGEN DOCKER - QA
# ================================================

set -e  # Exit on error

echo "================================================"
echo "🔨 BUILD Y PUSH IMAGEN DOCKER - QA"
echo "================================================"
echo ""

# Variables
PROJECT_ID="qa-ticket-home-redsalud"
REGION="us-central1"
REPOSITORY="tickethome-repo"
IMAGE_NAME="ticket-home"
TAG="latest"
FULL_IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

echo "📦 Configuración:"
echo "   Proyecto: $PROJECT_ID"
echo "   Imagen: $FULL_IMAGE_PATH"
echo ""

# Verificar que estamos en el directorio raíz del proyecto
if [ ! -f "app.py" ]; then
    echo "❌ Error: Debes ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

# Configurar Docker para usar gcloud como credential helper
echo "🔐 Configurando autenticación de Docker..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

echo ""
echo "🏗️  Construyendo imagen Docker..."
docker build \
    --platform linux/amd64 \
    --build-arg BUILD_VERSION="qa" \
    -t ${FULL_IMAGE_PATH} \
    .

if [ $? -eq 0 ]; then
    echo "✅ Build completado exitosamente"
else
    echo "❌ Error en build de Docker"
    exit 1
fi

echo ""
echo "📤 Pushing imagen a Artifact Registry..."
docker push ${FULL_IMAGE_PATH}

if [ $? -eq 0 ]; then
    echo "✅ Push completado exitosamente"
else
    echo "❌ Error en push de Docker"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ BUILD Y PUSH COMPLETADOS - QA"
echo "================================================"
echo ""
echo "Imagen: ${FULL_IMAGE_PATH}"
echo ""
echo "Próximo paso:"
echo "   Ejecutar deployment: ./deploy-scripts/3-deploy-QA-normal.sh"
echo ""
