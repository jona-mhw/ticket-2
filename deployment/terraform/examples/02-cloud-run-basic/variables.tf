# ============================================
# VARIABLES - EJEMPLO 02
# ============================================

variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
}

variable "region" {
  description = "Región de GCP para Cloud Run"
  type        = string
  default     = "us-central1"
}
