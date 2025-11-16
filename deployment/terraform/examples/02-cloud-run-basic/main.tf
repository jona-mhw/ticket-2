# ============================================
# EJEMPLO 02: CLOUD RUN BASIC
# ============================================
# Crea un Cloud Run service simple con imagen hello-world
#
# Objetivos de aprendizaje:
# - Crear Cloud Run con Terraform
# - Configurar recursos (CPU, memoria)
# - Hacer servicio público
# - Ver URL del servicio

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ============================================
# CLOUD RUN SERVICE
# ============================================

resource "google_cloud_run_service" "hello" {
  name     = "hello-terraform"
  location = var.region

  template {
    spec {
      containers {
        # Imagen hello-world de Google (pública, no requiere autenticación)
        image = "gcr.io/cloudrun/hello"

        # Recursos
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        # Puerto donde escucha el contenedor
        ports {
          container_port = 8080
        }
      }
    }
  }

  # Routing - 100% del tráfico a la última revisión
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# ============================================
# IAM POLICY - HACER SERVICIO PÚBLICO
# ============================================

resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_service.hello.location
  service  = google_cloud_run_service.hello.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================
# EXPLICACIÓN
# ============================================
#
# 1. CLOUD RUN SERVICE:
#    - name: nombre único en la región
#    - location: región donde deployar
#    - template: configuración del contenedor
#    - traffic: distribución de tráfico entre revisiones
#
# 2. TEMPLATE SPEC:
#    - containers: lista de contenedores (Cloud Run soporta 1)
#    - image: imagen Docker a usar
#    - resources.limits: CPU y memoria máxima
#    - ports: puerto donde escucha el contenedor
#
# 3. IAM MEMBER:
#    - Otorga permiso run.invoker a allUsers
#    - Hace el servicio accesible públicamente
#    - Sin esto, solo service accounts autenticados pueden acceder
#
# 4. REFERENCIAS ENTRE RECURSOS:
#    - google_cloud_run_service.hello.location
#    - Terraform entiende las dependencias automáticamente
#    - Crea recursos en el orden correcto
