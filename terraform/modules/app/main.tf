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
        value = var.environment
      }
      env {
        name  = "ENABLE_DEMO_LOGIN"
        value = var.enable_demo_login
      }
      env {
        name  = "RESET_DB_ON_STARTUP"
        value = tostring(var.reset_db_on_startup)
      }
      env {
        name  = "USE_QA_MINIMAL_SEED"
        value = tostring(var.use_qa_minimal_seed)
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
        connector = var.vpc_connector
        egress    = "PRIVATE_RANGES_ONLY"
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

# IAM Policy Binding para acceso público (solo si NO hay IAP group definido)
resource "google_cloud_run_service_iam_binding" "public_invoker" {
  count    = var.iap_access_group == null ? 1 : 0
  location = google_cloud_run_v2_service.default.location
  service  = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}

# IAM Policy Binding para acceso IAP (solo si hay IAP group definido)
resource "google_cloud_run_service_iam_binding" "iap_invoker" {
  count    = var.iap_access_group != null ? 1 : 0
  location = google_cloud_run_v2_service.default.location
  service  = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  members = [
    "group:${var.iap_access_group}",
    "serviceAccount:service-85153475663@gcp-sa-iap.iam.gserviceaccount.com"
  ]
}

# --- Cloud SQL Resources ---

resource "google_sql_database_instance" "default" {
  count            = var.create_sql_instance ? 1 : 0
  name             = var.sql_instance_name
  database_version = "POSTGRES_17"
  region           = var.region

  settings {
    tier = var.db_tier
    
    # Configuración básica para QA/Dev
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = "projects/${var.project_id}/global/networks/default" # Asumiendo red default, ajustar si es necesario
    }
  }
  
  deletion_protection = false # Cuidado en producción
}

resource "google_sql_database" "default" {
  count    = var.create_sql_instance ? 1 : 0
  name     = replace(var.service_name, "-", "_") # ej. ticket-home -> ticket_home
  instance = google_sql_database_instance.default[0].name
}

resource "google_sql_user" "default" {
  count    = var.create_sql_instance ? 1 : 0
  name     = replace(var.service_name, "-", "_") # usuario igual a db name
  instance = google_sql_database_instance.default[0].name
  password = "changeme" # La contraseña real debe gestionarse fuera o via Secret Manager
}

# --- Secret Manager Resources ---

resource "google_secret_manager_secret" "superusers" {
  count     = length(var.superuser_emails) > 0 ? 1 : 0
  secret_id = var.secret_superusers_name
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Gestionar la versión del secreto de superusuarios
resource "google_secret_manager_secret_version" "superusers" {
  count       = length(var.superuser_emails) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.superusers[0].id
  secret_data = join(";", var.superuser_emails)
}