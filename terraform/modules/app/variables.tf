# Define las variables que el módulo de la aplicación necesita.
# Estos son los "parámetros" que se pueden configurar para cada ambiente.

variable "project_id" {
  description = "El ID del proyecto de Google Cloud."
  type        = string
}

variable "region" {
  description = "La región de GCP donde se desplegarán los recursos."
  type        = string
}

variable "service_name" {
  description = "El nombre del servicio de Cloud Run."
  type        = string
}

variable "sql_instance_name" {
  description = "El nombre de la instancia de Cloud SQL."
  type        = string
}

variable "db_connection_type" {
  description = "El método de conexión a la base de datos ('VPC_CONNECTOR' o 'CLOUD_SQL_PROXY')."
  type        = string
  default     = "CLOUD_SQL_PROXY"
}

variable "min_instances" {
  description = "El número mínimo de instancias de Cloud Run."
  type        = number
  default     = 0
}

variable "enable_demo_login" {
  description = "Si se debe habilitar el login de demostración."
  type        = bool
  default     = true
}

variable "service_account_email" {
  description = "El email de la cuenta de servicio que usará Cloud Run."
  type        = string
}

variable "image_url" {
  description = "La URL completa de la imagen de Docker en Artifact Registry."
  type        = string
}

variable "secret_database_url_name" {
  description = "El nombre del secret en Secret Manager para la DATABASE_URL."
  type        = string
}

variable "secret_key_name" {
  description = "El nombre del secret en Secret Manager para la SECRET_KEY."
  type        = string
}

variable "secret_superusers_name" {
  description = "El nombre del secret en Secret Manager para los SUPERUSER_EMAILS."
  type        = string
}

variable "force_deployment_timestamp" {
  description = "Un timestamp para forzar un redespliegue cuando sea necesario."
  type        = string
  default     = ""
}

variable "environment" {
  description = "El nombre del ambiente (ej. 'dev', 'qa', 'prod')."
  type        = string
  default     = "dev"
}

variable "vpc_connector" {
  description = "El ID del conector VPC para acceso Serverless (opcional)."
  type        = string
  default     = null
}

variable "iap_access_group" {
  description = "El email del grupo de Google para acceso IAP (opcional)."
  type        = string
  default     = null
}

variable "db_tier" {
  description = "El tier de la instancia de Cloud SQL."
  type        = string
  default     = "db-f1-micro"
}

variable "create_sql_instance" {
  description = "Indica si se debe crear/gestionar la instancia de Cloud SQL."
  type        = bool
  default     = false
}

variable "reset_db_on_startup" {
  description = "Si es true, la aplicación reseteará la base de datos al iniciar."
  type        = bool
  default     = false
}

variable "use_qa_minimal_seed" {
  description = "Si es true y reset_db_on_startup es true, usa un seed mínimo para QA."
  type        = bool
  default     = false
}

variable "superuser_emails" {
  description = "Lista de emails de superusuarios para configurar en el sistema."
  type        = list(string)
  default     = []
}
