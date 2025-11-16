# ============================================
# VARIABLES - MÓDULO LOAD BALANCER
# ============================================

# --- Básicas ---

variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
}

variable "lb_name" {
  description = "Nombre base del Load Balancer (se usará como prefijo)"
  type        = string
}

variable "domains" {
  description = "Lista de dominios para el certificado SSL"
  type        = list(string)
}

# --- Cloud Run Backend ---

variable "cloud_run_service_name" {
  description = "Nombre del servicio Cloud Run (backend)"
  type        = string
}

variable "cloud_run_region" {
  description = "Región del servicio Cloud Run"
  type        = string
}

variable "backend_timeout_sec" {
  description = "Timeout del backend en segundos"
  type        = number
  default     = 900
}

# --- CDN y Logging ---

variable "enable_cdn" {
  description = "Habilitar Cloud CDN"
  type        = bool
  default     = false
}

variable "enable_logging" {
  description = "Habilitar logging del Load Balancer"
  type        = bool
  default     = true
}

variable "log_sample_rate" {
  description = "Sample rate para logs (0.0 a 1.0)"
  type        = number
  default     = 1.0
}

# --- IAP ---

variable "enable_iap" {
  description = "Habilitar Identity-Aware Proxy"
  type        = bool
  default     = true
}

variable "iap_oauth_client_id" {
  description = "OAuth 2.0 Client ID para IAP"
  type        = string
  default     = ""
}

variable "iap_oauth_client_secret" {
  description = "OAuth 2.0 Client Secret para IAP"
  type        = string
  default     = ""
  sensitive   = true
}

variable "iap_access_members" {
  description = "Lista de members que tendrán acceso vía IAP (ej: user:email@example.com, group:group@googlegroups.com)"
  type        = list(string)
  default     = []
}

# --- HTTP Redirect ---

variable "redirect_http_to_https" {
  description = "Redirigir HTTP a HTTPS automáticamente"
  type        = bool
  default     = true
}
