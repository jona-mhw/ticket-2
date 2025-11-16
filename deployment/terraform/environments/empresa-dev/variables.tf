# ============================================
# VARIABLES - EMPRESA DEV ENVIRONMENT
# ============================================

# --- GCP Project ---

variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
}

variable "region" {
  description = "Región de GCP"
  type        = string
  default     = "southamerica-west1"
}

variable "environment" {
  description = "Nombre del ambiente"
  type        = string
  default     = "empresa-dev"
}

# --- Aplicación ---

variable "service_name" {
  description = "Nombre del servicio Cloud Run"
  type        = string
}

variable "docker_image" {
  description = "Imagen Docker completa (registry/proyecto/repo:tag)"
  type        = string
}

# --- VPC ---

variable "vpc_connector" {
  description = "Nombre del VPC Connector (para conexión privada a Cloud SQL)"
  type        = string
}

# --- Dominio ---

variable "domain_name" {
  description = "Dominio principal de la aplicación"
  type        = string
}

# --- Service Account ---

variable "service_account_email" {
  description = "Email del service account de la aplicación"
  type        = string
}

# --- IAP ---

variable "iap_oauth_client_id" {
  description = "OAuth 2.0 Client ID para IAP"
  type        = string
}

variable "iap_oauth_client_secret" {
  description = "OAuth 2.0 Client Secret para IAP"
  type        = string
  sensitive   = true
}

variable "iap_access_members" {
  description = "Lista de usuarios/grupos con acceso vía IAP"
  type        = list(string)
  default     = []
}
