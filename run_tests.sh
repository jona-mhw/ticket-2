#!/bin/bash

# Script para ejecutar todos los tests del proyecto

echo "================================================"
echo "   EJECUTANDO TESTS DEL SISTEMA DE TICKETS"
echo "================================================"
echo ""

# Verificar que pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo "⚠️  pytest no está instalado"
    echo "Instalando pytest..."
    pip install pytest pytest-cov
fi

echo "📋 Ejecutando tests..."
echo ""

# Ejecutar tests con verbose y coverage
python -m pytest tests/ -v --tb=short 2>&1

EXIT_CODE=$?

echo ""
echo "================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ TODOS LOS TESTS PASARON EXITOSAMENTE"
else
    echo "❌ ALGUNOS TESTS FALLARON (código: $EXIT_CODE)"
fi
echo "================================================"

exit $EXIT_CODE
