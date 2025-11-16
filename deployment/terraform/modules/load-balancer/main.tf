# ============================================
# MÓDULO: LOAD BALANCER + IAP + SSL
# ============================================
# Este módulo crea un Load Balancer HTTPS con:
# - Backend a Cloud Run
# - Certificado SSL administrado
# - IAP configurado
# - IP estática

# ============================================
# IP ESTÁTICA
# ============================================

resource "google_compute_global_address" "lb_ip" {
  name    = "${var.lb_name}-ip"
  project = var.project_id
}

# ============================================
# CERTIFICADO SSL ADMINISTRADO
# ============================================

resource "google_compute_managed_ssl_certificate" "lb_cert" {
  name    = "${var.lb_name}-cert"
  project = var.project_id

  managed {
    domains = var.domains
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================
# SERVERLESS NEG (CLOUD RUN)
# ============================================

resource "google_compute_region_network_endpoint_group" "cloud_run_neg" {
  name                  = "${var.lb_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.cloud_run_region
  project               = var.project_id

  cloud_run {
    service = var.cloud_run_service_name
  }
}

# ============================================
# BACKEND SERVICE
# ============================================

resource "google_compute_backend_service" "lb_backend" {
  name                  = "${var.lb_name}-backend"
  project               = var.project_id
  protocol              = "HTTPS"
  port_name             = "http"
  timeout_sec           = var.backend_timeout_sec
  enable_cdn            = var.enable_cdn
  session_affinity      = "NONE"
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.cloud_run_neg.id
  }

  # ============================================
  # IAP CONFIGURATION
  # ============================================

  dynamic "iap" {
    for_each = var.enable_iap ? [1] : []
    content {
      oauth2_client_id     = var.iap_oauth_client_id
      oauth2_client_secret = var.iap_oauth_client_secret
    }
  }

  log_config {
    enable      = var.enable_logging
    sample_rate = var.log_sample_rate
  }
}

# ============================================
# IAP IAM BINDING
# ============================================

resource "google_iap_web_backend_service_iam_member" "iap_access" {
  for_each = var.enable_iap ? toset(var.iap_access_members) : []

  project             = var.project_id
  web_backend_service = google_compute_backend_service.lb_backend.name
  role                = "roles/iap.httpsResourceAccessor"
  member              = each.value
}

# ============================================
# URL MAP
# ============================================

resource "google_compute_url_map" "lb_url_map" {
  name            = "${var.lb_name}-url-map"
  project         = var.project_id
  default_service = google_compute_backend_service.lb_backend.id

  # Redirección HTTP → HTTPS (si se habilita)
  dynamic "host_rule" {
    for_each = var.redirect_http_to_https ? var.domains : []
    content {
      hosts        = [host_rule.value]
      path_matcher = "allpaths"
    }
  }

  dynamic "path_matcher" {
    for_each = var.redirect_http_to_https ? [1] : []
    content {
      name            = "allpaths"
      default_service = google_compute_backend_service.lb_backend.id
    }
  }
}

# ============================================
# HTTPS PROXY
# ============================================

resource "google_compute_target_https_proxy" "lb_https_proxy" {
  name             = "${var.lb_name}-https-proxy"
  project          = var.project_id
  url_map          = google_compute_url_map.lb_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.lb_cert.id]
}

# ============================================
# FORWARDING RULE (HTTPS)
# ============================================

resource "google_compute_global_forwarding_rule" "lb_https" {
  name                  = "${var.lb_name}-https-rule"
  project               = var.project_id
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "443"
  target                = google_compute_target_https_proxy.lb_https_proxy.id
  ip_address            = google_compute_global_address.lb_ip.id
}

# ============================================
# HTTP → HTTPS REDIRECT (OPCIONAL)
# ============================================

resource "google_compute_url_map" "http_redirect" {
  count   = var.redirect_http_to_https ? 1 : 0
  name    = "${var.lb_name}-http-redirect"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "http_proxy" {
  count   = var.redirect_http_to_https ? 1 : 0
  name    = "${var.lb_name}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.http_redirect[0].id
}

resource "google_compute_global_forwarding_rule" "http" {
  count                 = var.redirect_http_to_https ? 1 : 0
  name                  = "${var.lb_name}-http-rule"
  project               = var.project_id
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "80"
  target                = google_compute_target_http_proxy.http_proxy[0].id
  ip_address            = google_compute_global_address.lb_ip.id
}
