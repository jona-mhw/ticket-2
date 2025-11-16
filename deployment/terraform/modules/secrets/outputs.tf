# ============================================
# OUTPUTS - MÓDULO SECRETS
# ============================================

output "secret_id" {
  description = "ID del secret creado"
  value       = google_secret_manager_secret.secret.id
}

output "secret_name" {
  description = "Nombre del secret (short name)"
  value       = google_secret_manager_secret.secret.secret_id
}

output "version_id" {
  description = "ID de la versión del secret (si se creó)"
  value       = length(google_secret_manager_secret_version.version) > 0 ? google_secret_manager_secret_version.version[0].id : null
}
