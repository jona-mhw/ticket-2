# ============================================
# OUTPUTS - MÓDULO CLOUD RUN
# ============================================

output "service_name" {
  description = "Nombre del servicio Cloud Run creado"
  value       = google_cloud_run_service.app.name
}

output "service_url" {
  description = "URL del servicio Cloud Run"
  value       = google_cloud_run_service.app.status[0].url
}

output "service_id" {
  description = "ID del servicio Cloud Run"
  value       = google_cloud_run_service.app.id
}

output "latest_revision_name" {
  description = "Nombre de la última revisión deployada"
  value       = google_cloud_run_service.app.status[0].latest_ready_revision_name
}

output "service_location" {
  description = "Región donde está deployado el servicio"
  value       = google_cloud_run_service.app.location
}
