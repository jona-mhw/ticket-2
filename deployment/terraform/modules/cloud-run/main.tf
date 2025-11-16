# ============================================
# MÓDULO: CLOUD RUN SERVICE
# ============================================
# Este módulo crea un servicio Cloud Run completamente configurado

resource "google_cloud_run_service" "app" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances

        # Conexión a Cloud SQL (si se provee)
        "run.googleapis.com/cloudsql-instances" = var.cloudsql_connection_name != "" ? var.cloudsql_connection_name : null

        # VPC Connector (si se provee)
        "run.googleapis.com/vpc-access-connector" = var.vpc_connector != "" ? var.vpc_connector : null
        "run.googleapis.com/vpc-access-egress"    = var.vpc_connector != "" ? var.vpc_egress : null
      }
    }

    spec {
      container_concurrency = var.concurrency
      timeout_seconds       = var.timeout_seconds
      service_account_name  = var.service_account_email

      containers {
        image = var.image

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        # Variables de entorno (no sensibles)
        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        # Secrets montados desde Secret Manager
        dynamic "env" {
          for_each = var.secrets
          content {
            name = env.key
            value_from {
              secret_key_ref {
                name = env.value.secret_name
                key  = env.value.version
              }
            }
          }
        }

        # Ports
        ports {
          container_port = var.container_port
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  # Ignorar cambios en template.metadata.annotations si se actualizan externamente
  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
    ]
  }
}

# ============================================
# IAM POLICY BINDING
# ============================================
# Hace el servicio accesible solo vía IAP

resource "google_cloud_run_service_iam_member" "invoker" {
  count = var.enable_iap ? 1 : 0

  project  = var.project_id
  location = var.region
  service  = google_cloud_run_service.app.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.iap_service_account}"
}

# Si está en modo público (desarrollo)
resource "google_cloud_run_service_iam_member" "public" {
  count = var.enable_public_access ? 1 : 0

  project  = var.project_id
  location = var.region
  service  = google_cloud_run_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
