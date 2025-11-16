# ============================================
# BACKEND CONFIGURATION - MHW DEV
# ============================================
# Configura dónde Terraform guarda el state file

# OPCIÓN 1: Local (para empezar)
# Por default, Terraform guarda el state localmente en terraform.tfstate
# Esto es OK para desarrollo individual

# OPCIÓN 2: Google Cloud Storage (recomendado para producción)
# Descomentar el bloque de abajo para usar GCS backend

# terraform {
#   backend "gcs" {
#     bucket = "ticket-home-terraform-state"
#     prefix = "environments/mhw-dev"
#   }
# }

# Crear el bucket primero con:
#   gcloud storage buckets create gs://ticket-home-terraform-state \
#     --project=ticket-home-demo \
#     --location=us-central1 \
#     --uniform-bucket-level-access
#
#   gcloud storage buckets update gs://ticket-home-terraform-state \
#     --versioning

# Luego migrar el state local a GCS:
#   terraform init -migrate-state
