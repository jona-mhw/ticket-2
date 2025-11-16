# ============================================
# OUTPUTS - MÓDULO LOAD BALANCER
# ============================================

output "lb_ip_address" {
  description = "Dirección IP pública del Load Balancer"
  value       = google_compute_global_address.lb_ip.address
}

output "lb_ip_name" {
  description = "Nombre del recurso de IP"
  value       = google_compute_global_address.lb_ip.name
}

output "ssl_certificate_id" {
  description = "ID del certificado SSL administrado"
  value       = google_compute_managed_ssl_certificate.lb_cert.id
}

output "ssl_certificate_status" {
  description = "Estado del certificado SSL (puede tardar en provisionar)"
  value       = google_compute_managed_ssl_certificate.lb_cert.managed[0].status
}

output "backend_service_id" {
  description = "ID del backend service"
  value       = google_compute_backend_service.lb_backend.id
}

output "backend_service_name" {
  description = "Nombre del backend service"
  value       = google_compute_backend_service.lb_backend.name
}

output "url_map_id" {
  description = "ID del URL map"
  value       = google_compute_url_map.lb_url_map.id
}

output "https_proxy_id" {
  description = "ID del HTTPS proxy"
  value       = google_compute_target_https_proxy.lb_https_proxy.id
}

output "dns_instructions" {
  description = "Instrucciones para configurar DNS"
  value       = "Configurar registro A para ${join(", ", var.domains)} → ${google_compute_global_address.lb_ip.address}"
}
