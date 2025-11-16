# ============================================
# VARIABLES - MÓDULO CLOUD RUN
# ============================================

# --- Básicas ---

variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
}

variable "region" {
  description = "Región de GCP donde deployar Cloud Run"
  type        = string
}

variable "service_name" {
  description = "Nombre del servicio Cloud Run"
  type        = string
}

variable "image" {
  description = "Imagen Docker completa (ej: us-central1-docker.pkg.dev/proyecto/repo/app:tag)"
  type        = string
}

# --- Service Account ---

variable "service_account_email" {
  description = "Email del service account que ejecutará el servicio"
  type        = string
}

# --- Recursos ---

variable "cpu" {
  description = "CPUs asignadas al contenedor"
  type        = string
  default     = "2"
}

variable "memory" {
  description = "Memoria asignada (ej: 1Gi, 2Gi)"
  type        = string
  default     = "1Gi"
}

variable "timeout_seconds" {
  description = "Timeout de request en segundos"
  type        = number
  default     = 900 # 15 minutos
}

variable "concurrency" {
  description = "Requests concurrentes por instancia"
  type        = number
  default     = 80
}

variable "container_port" {
  description = "Puerto del contenedor"
  type        = number
  default     = 8080
}

# --- Autoscaling ---

variable "min_instances" {
  description = "Instancias mínimas (0 para escalar a cero)"
  type        = string
  default     = "0"
}

variable "max_instances" {
  description = "Instancias máximas"
  type        = string
  default     = "3"
}

# --- Conectividad ---

variable "cloudsql_connection_name" {
  description = "Nombre de conexión de Cloud SQL (proyecto:región:instancia) o vacío si no se usa"
  type        = string
  default     = ""
}

variable "vpc_connector" {
  description = "Nombre del VPC Connector o vacío si no se usa"
  type        = string
  default     = ""
}

variable "vpc_egress" {
  description = "Configuración de VPC egress (private-ranges-only o all-traffic)"
  type        = string
  default     = "private-ranges-only"
}

# --- Variables de Entorno ---

variable "env_vars" {
  description = "Variables de entorno no sensibles (key-value map)"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets de Secret Manager a montar como env vars"
  type = map(object({
    secret_name = string
    version     = string
  }))
  default = {}
}

# --- IAM y Seguridad ---

variable "enable_iap" {
  description = "Habilitar acceso solo vía IAP"
  type        = bool
  default     = true
}

variable "iap_service_account" {
  description = "Service account del IAP backend"
  type        = string
  default     = "service-PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com"
}

variable "enable_public_access" {
  description = "Permitir acceso público (solo para desarrollo)"
  type        = bool
  default     = false
}
