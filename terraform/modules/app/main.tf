# Este archivo define los recursos de infraestructura que necesita la aplicación.
# Ahora, añadimos el recurso principal: el servicio de Cloud Run.

terraform {
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

# Definición del servicio de Cloud Run
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.region

  # Plantilla de configuración para la revisión del servicio
  template {
    # Añadimos una anotación para forzar el redespliegue cuando cambie el timestamp
    annotations = {
      "client.knative.dev/nonce" = var.force_deployment_timestamp
    }

    service_account = var.service_account_email

    containers {
      image = var.image_url

      ports {
        container_port = 8080
      }

      # Aquí definimos las variables de entorno para la aplicación
      env {
        name  = "FLASK_ENV"
        value = "production"
      }
      env {
        name  = "FLASK_DEBUG"
        value = "false"
      }
      env {
        name  = "ENABLE_IAP"
        value = "true"
      }
      env {
        name  = "ENVIRONMENT"
        value = "mhw" # Específico para este ambiente
      }
      env {
        name  = "ENABLE_DEMO_LOGIN"
        value = var.enable_demo_login
      }

      # Conectar variables de entorno a los secrets de Secret Manager
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = var.secret_database_url_name
            version = "latest"
          }
        }
      }
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_key_name
            version = "latest"
          }
        }
      }
      env {
        name = "SUPERUSER_EMAILS"
        value_source {
          secret_key_ref {
            secret  = var.secret_superusers_name
            version = "latest"
          }
        }
      }

      # Montar el volumen de Cloud SQL solo si el tipo de conexión es CLOUD_SQL_PROXY
      dynamic "volume_mounts" {
        for_each = var.db_connection_type == "CLOUD_SQL_PROXY" ? [1] : []
        content {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }
    }

    # Configuración de escalado
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = 3 # Valor fijo por ahora
    }

    # Definir el volumen de Cloud SQL solo si el tipo de conexión es CLOUD_SQL_PROXY
    dynamic "volumes" {
      for_each = var.db_connection_type == "CLOUD_SQL_PROXY" ? [1] : []
      content {
        name = "cloudsql"
        cloud_sql_instance {
          instances = ["${var.project_id}:${var.region}:${var.sql_instance_name}"]
        }
      }
    }

    # Definir el acceso VPC solo si el tipo de conexión es VPC_CONNECTOR
    dynamic "vpc_access" {
      for_each = var.db_connection_type == "VPC_CONNECTOR" ? [1] : []
      content {
        # El conector se definirá como una variable en el futuro
        # connector = var.vpc_connector_id
        egress = "PRIVATE_RANGES_ONLY"
      }
    }
  }

  # Configuración de tráfico y seguridad
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}