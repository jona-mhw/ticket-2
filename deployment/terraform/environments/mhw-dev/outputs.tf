# ============================================
# OUTPUTS - MHW DEV ENVIRONMENT
# ============================================

# --- Cloud Run ---

output "cloud_run_url" {
  description = "URL interna del servicio Cloud Run"
  value       = module.cloud_run.service_url
}

output "cloud_run_service_name" {
  description = "Nombre del servicio Cloud Run"
  value       = module.cloud_run.service_name
}

# --- Load Balancer ---

output "load_balancer_ip" {
  description = "IP pública del Load Balancer"
  value       = module.load_balancer.lb_ip_address
}

output "ssl_certificate_status" {
  description = "Estado del certificado SSL (debe ser ACTIVE)"
  value       = module.load_balancer.ssl_certificate_status
}

# --- Secrets ---

output "secrets_created" {
  description = "Lista de secrets creados"
  value = [
    module.database_url_secret.secret_name,
    module.secret_key_secret.secret_name,
    module.superuser_emails_secret.secret_name,
  ]
}

# --- DNS Instructions ---

output "dns_configuration" {
  description = "Instrucciones para configurar DNS"
  value       = <<-EOT
    Configura un registro A en tu DNS:

    Nombre: ${var.domain_name}
    Tipo:   A
    Valor:  ${module.load_balancer.lb_ip_address}
    TTL:    300

    Verificar con: dig ${var.domain_name} +short
  EOT
}

# --- Next Steps ---

output "next_steps" {
  description = "Próximos pasos después del deployment"
  value       = <<-EOT
    ✅ Deployment completado!

    Próximos pasos:

    1. Agregar valores a los secrets:

       # DATABASE_URL
       echo "postgresql://user:pass@/cloudsql/${var.cloudsql_connection_name}/${var.cloudsql_database_name}?host=/cloudsql/${var.cloudsql_connection_name}" | \
         gcloud secrets versions add mhw-database-url --data-file=-

       # SECRET_KEY
       python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
         gcloud secrets versions add mhw-secret-key --data-file=-

       # SUPERUSER_EMAILS
       echo "tu-email@ejemplo.com" | \
         gcloud secrets versions add mhw-superuser-emails --data-file=-

    2. Configurar DNS (ver output 'dns_configuration')

    3. Esperar ~15-30 min para que el certificado SSL se provisione

       gcloud compute ssl-certificates describe ${var.service_name}-lb-cert \
         --global \
         --project=${var.project_id}

    4. Acceder a: https://${var.domain_name}

    5. Verificar logs:

       gcloud logging read "resource.type=cloud_run_revision" \
         --limit=50 \
         --project=${var.project_id}
  EOT
}
