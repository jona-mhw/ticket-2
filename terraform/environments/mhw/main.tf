# Este archivo es el punto de entrada para el ambiente de MHW.
# Llama al módulo principal de la aplicación y le pasa las variables
# definidas en el archivo terraform.tfvars.

# 1. Declarar las variables que este ambiente espera recibir.
# Terraform cargará automáticamente los valores desde terraform.tfvars.
variable "project_id" {}
variable "region" {}
variable "service_name" {}
variable "sql_instance_name" {}
variable "db_connection_type" {}
variable "min_instances" {}
variable "enable_demo_login" {}
variable "service_account_email" {}
variable "image_url" {}
variable "secret_database_url_name" {}
variable "secret_key_name" {}
variable "secret_superusers_name" {}
variable "force_deployment_timestamp" {
  default = null
}

# 2. Llamar al módulo 'app' y pasarle las variables.
module "app" {
  source = "../../modules/app"

  project_id               = var.project_id
  region                   = var.region
  service_name             = var.service_name
  sql_instance_name        = var.sql_instance_name
  db_connection_type       = var.db_connection_type
  min_instances            = var.min_instances
  enable_demo_login        = var.enable_demo_login
  service_account_email    = var.service_account_email
  image_url                = var.image_url
  secret_database_url_name = var.secret_database_url_name
  secret_key_name          = var.secret_key_name
  secret_superusers_name   = var.secret_superusers_name

  # Añadimos una anotación con la fecha para forzar el redespliegue
  force_deployment_timestamp = timestamp()
}

