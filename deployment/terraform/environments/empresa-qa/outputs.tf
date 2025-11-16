# ============================================
# OUTPUTS - EMPRESA QA ENVIRONMENT
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

    ⚠️  IMPORTANTE: Este es el ambiente QA (pre-producción)
    - Solo SSO habilitado (NO hay login tradicional)
    - Grupo autorizado: qa-ticket-home-rs@googlegroups.com

    Próximos pasos:

    1. Agregar valores a los secrets:

       # DATABASE_URL (IP privada de Cloud SQL)
       echo "postgresql://user:pass@10.x.x.x:5432/database_name" | \
         gcloud secrets versions add tickethome-db-url --data-file=-

       # SECRET_KEY
       python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
         gcloud secrets versions add tickethome-secret-key --data-file=-

       # SUPERUSER_EMAILS
       echo "admin@redsalud.cl" | \
         gcloud secrets versions add superuser-emails --data-file=-

    2. Configurar DNS (ver output 'dns_configuration')

    3. Esperar ~15-30 min para que el certificado SSL se provisione

       gcloud compute ssl-certificates describe ${var.service_name}-lb-cert \
         --global \
         --project=${var.project_id}

    4. Acceder a: https://${var.domain_name}
       (Solo vía SSO - no hay login tradicional)

    5. Checklist de testing:
       - [ ] Aplicación carga sin errores
       - [ ] Solo SSO funciona (no login tradicional)
       - [ ] Dashboard muestra datos correctos
       - [ ] Panel de enfermería funciona
       - [ ] Exportaciones funcionan (PDF, Excel)
       - [ ] Performance aceptable
       - [ ] No hay errores en logs
  EOT
}
