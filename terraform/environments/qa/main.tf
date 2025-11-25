terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "app" {
  source = "../../modules/app"

  project_id             = var.project_id
  region                 = var.region
  service_name           = var.service_name
  image_url              = var.image_url
  service_account_email  = var.service_account_email
  
  # Database & Secrets
  sql_instance_name      = var.sql_instance_name
  secret_database_url_name = var.secret_database_url_name
  secret_key_name        = var.secret_key_name
  secret_superusers_name = var.secret_superusers_name
  
  # QA Specifics
  environment            = "qa"
  db_connection_type     = "VPC_CONNECTOR"
  vpc_connector          = var.vpc_connector
  iap_access_group       = var.iap_access_group
  enable_demo_login      = "false"
  min_instances          = 1
  
  # Database Management
  create_sql_instance    = false # Ya existe, no se gestiona por Terraform debido a permisos
  db_tier                = "db-custom-1-3840" # Tier existente
  
  # Deployment Scenarios (Controlled via tfvars)
  reset_db_on_startup    = var.reset_db_on_startup
  use_qa_minimal_seed    = var.use_qa_minimal_seed
  superuser_emails       = var.superuser_emails
  force_deployment_timestamp = var.force_deployment_timestamp
}
