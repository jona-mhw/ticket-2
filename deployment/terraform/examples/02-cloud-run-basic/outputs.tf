# ============================================
# OUTPUTS - EJEMPLO 02
# ============================================

output "service_url" {
  description = "URL del servicio Cloud Run"
  value       = google_cloud_run_service.hello.status[0].url
}

output "service_name" {
  description = "Nombre del servicio"
  value       = google_cloud_run_service.hello.name
}

output "service_location" {
  description = "Región del servicio"
  value       = google_cloud_run_service.hello.location
}

output "test_command" {
  description = "Comando para probar el servicio"
  value       = "curl ${google_cloud_run_service.hello.status[0].url}"
}

output "next_steps" {
  description = "Próximos pasos"
  value       = <<-EOT
    ✅ Cloud Run service creado!

    URL del servicio: ${google_cloud_run_service.hello.status[0].url}

    Probar en el navegador:
    ${google_cloud_run_service.hello.status[0].url}

    Probar con curl:
    curl ${google_cloud_run_service.hello.status[0].url}

    Ver logs:
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=hello-terraform" --limit=20 --project=${var.project_id}

    Ver en GCP Console:
    https://console.cloud.google.com/run/detail/${var.region}/hello-terraform

    Ver revisiones:
    gcloud run revisions list --service=hello-terraform --region=${var.region}
  EOT
}
