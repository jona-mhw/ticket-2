#!/bin/bash
# ================================================
# SCRIPT 3: DEPLOY NORMAL (SIN RESET DB) - DEV
# ================================================
# Usa este script cuando:
# - Cambios solo de código (HTML, CSS, JS, Python)
# - NO cambios en models.py
# ================================================

set -e  # Exit on error

echo "================================================"
echo "🚀 DEPLOY NORMAL - DEV"
echo "================================================"
echo ""

gcloud run deploy ticket-home \
  --image=us-central1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:latest \
  --region=southamerica-west1 \
  --service-account=dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com \
  --vpc-connector=tckthome-conn-sa-west1 \
  --vpc-egress=private-ranges-only \
  --no-allow-unauthenticated \
  --ingress=internal-and-cloud-load-balancing \
  --add-cloudsql-instances=dev-ticket-home-redsalud:southamerica-west1:dev-ticket-home \
  --port=8080 \
  --timeout=900 \
  --memory=1Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=3 \
  --concurrency=80 \
  --set-env-vars="ENVIRONMENT=production,FLASK_ENV=production,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false" \
  --set-secrets="DATABASE_URL=tickethome-db-url:latest,SECRET_KEY=tickethome-secret-key:latest,SUPERUSER_EMAILS=superuser-emails:latest" \
  --project=dev-ticket-home-redsalud

if [ $? -ne 0 ]; then
    echo "❌ Error en deployment"
    exit 1
fi

echo ""
echo "🔐 Aplicando IAM policy binding..."
gcloud run services add-iam-policy-binding ticket-home \
  --region=southamerica-west1 \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project=dev-ticket-home-redsalud

gcloud run services add-iam-policy-binding ticket-home \
  --region=southamerica-west1 \
  --member="group:rs-ticket-home@googlegroups.com" \
  --role="roles/run.invoker" \
  --project=dev-ticket-home-redsalud

echo ""
echo "================================================"
echo "✅ DEPLOYMENT COMPLETADO - DEV"
echo "================================================"
echo ""
echo "🌐 URL: https://ticket-home.mhwdev.dev"
echo "🔐 Grupo: rs-ticket-home@googlegroups.com"
echo ""
echo "🧪 Verificar deployment:"
echo "   curl -I https://ticket-home.mhwdev.dev"
echo ""
