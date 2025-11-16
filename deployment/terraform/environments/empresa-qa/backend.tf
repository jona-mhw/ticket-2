# ============================================
# BACKEND CONFIGURATION - EMPRESA QA
# ============================================

# OPCIÓN 1: Local (por ahora)
# Por default, Terraform guarda el state localmente

# OPCIÓN 2: Google Cloud Storage (recomendado para QA/Producción)
# Descomentar cuando estés listo:

# terraform {
#   backend "gcs" {
#     bucket = "redsalud-terraform-state"
#     prefix = "environments/empresa-qa"
#   }
# }

# Crear bucket primero:
#   gcloud storage buckets create gs://redsalud-terraform-state \
#     --project=qa-ticket-home-redsalud \
#     --location=southamerica-west1 \
#     --uniform-bucket-level-access
#
#   gcloud storage buckets update gs://redsalud-terraform-state \
#     --versioning

# Migrar state:
#   terraform init -migrate-state
