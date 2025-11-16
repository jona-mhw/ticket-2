# ============================================
# VARIABLES
# ============================================
# Define las variables que el usuario debe proveer

variable "project_id" {
  description = "ID del proyecto GCP donde crear el secret"
  type        = string
}

variable "region" {
  description = "Región de GCP (opcional para Secret Manager)"
  type        = string
  default     = "us-central1"
}

# ============================================
# EXPLICACIÓN
# ============================================
#
# 1. VARIABLE BLOCK:
#    - Define variables de entrada
#    - type: string, number, bool, list, map, object
#    - default: valor por defecto (opcional)
#    - description: documentación
#
# 2. USAR VARIABLES:
#    - En código: var.project_id
#    - Proveer valor: terraform.tfvars o -var flag
#
# 3. VALIDACIÓN (opcional):
#    validation {
#      condition     = length(var.project_id) > 0
#      error_message = "Project ID no puede estar vacío"
#    }
