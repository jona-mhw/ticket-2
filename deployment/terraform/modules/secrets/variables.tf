# ============================================
# VARIABLES - MÓDULO SECRETS
# ============================================

variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
}

variable "secret_id" {
  description = "ID del secret (nombre único en Secret Manager)"
  type        = string
}

variable "secret_data" {
  description = "Valor del secret (vacío para crear solo el contenedor)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "service_account_email" {
  description = "Email del service account que tendrá acceso al secret"
  type        = string
  default     = ""
}

variable "replication_locations" {
  description = "Locations para replicación manual (null para replicación automática)"
  type        = list(string)
  default     = null
}

variable "labels" {
  description = "Labels para el secret"
  type        = map(string)
  default     = {}
}
