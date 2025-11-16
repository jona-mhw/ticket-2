# ============================================
# EJEMPLO 01: SIMPLE SECRET
# ============================================
# Este ejemplo crea un secret básico en Secret Manager
#
# Objetivos de aprendizaje:
# - Sintaxis básica de Terraform (HCL)
# - Providers
# - Resources
# - Variables
# - Outputs

# ============================================
# TERRAFORM BLOCK
# ============================================
# Define la versión de Terraform y los providers necesarios

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ============================================
# PROVIDER
# ============================================
# Configura el provider de Google Cloud

provider "google" {
  project = var.project_id
  region  = var.region
}

# ============================================
# RESOURCE
# ============================================
# Crea un secret en Secret Manager

resource "google_secret_manager_secret" "example" {
  # ID único del secret
  secret_id = "ejemplo-terraform-secret"

  # Configuración de replicación
  replication {
    automatic = true
  }

  # Labels opcionales
  labels = {
    created-by = "terraform"
    example    = "01-simple-secret"
  }
}

# ============================================
# EXPLICACIÓN
# ============================================
#
# 1. TERRAFORM BLOCK:
#    - Define qué versión de Terraform usar
#    - Define qué providers necesitamos (Google Cloud)
#    - Especifica versiones de providers (~> 5.0 = 5.x)
#
# 2. PROVIDER BLOCK:
#    - Configura el provider de Google
#    - Usa variables para project_id y region
#
# 3. RESOURCE BLOCK:
#    - Tipo: google_secret_manager_secret
#    - Nombre local: example
#    - Referencia completa: google_secret_manager_secret.example
#
# 4. REPLICACIÓN:
#    - automatic = true: Google decide dónde replica
#    - manual: Tú especificas las regiones
#
# 5. LABELS:
#    - Metadata para organizar recursos
#    - Útil para billing y filtrado
