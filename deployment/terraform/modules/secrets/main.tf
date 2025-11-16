# ============================================
# MÓDULO: SECRET MANAGER
# ============================================
# Este módulo crea secrets en Google Secret Manager

resource "google_secret_manager_secret" "secret" {
  secret_id = var.secret_id
  project   = var.project_id

  replication {
    dynamic "user_managed" {
      for_each = var.replication_locations != null ? [1] : []
      content {
        dynamic "replicas" {
          for_each = var.replication_locations
          content {
            location = replicas.value
          }
        }
      }
    }

    dynamic "automatic" {
      for_each = var.replication_locations == null ? [1] : []
      content {}
    }
  }

  labels = var.labels
}

# ============================================
# IAM BINDING
# ============================================
# Dar acceso al Service Account para leer el secret

resource "google_secret_manager_secret_iam_member" "accessor" {
  count = var.service_account_email != "" ? 1 : 0

  project   = var.project_id
  secret_id = google_secret_manager_secret.secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

# ============================================
# SECRET VERSION (OPCIONAL)
# ============================================
# NOTA: Solo crear version si se provee secret_data
# En producción, se recomienda crear el secret vacío y
# agregar el valor manualmente con gcloud

resource "google_secret_manager_secret_version" "version" {
  count = var.secret_data != "" ? 1 : 0

  secret      = google_secret_manager_secret.secret.id
  secret_data = var.secret_data
}
