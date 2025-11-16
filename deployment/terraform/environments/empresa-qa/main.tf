# ============================================
# TERRAFORM CONFIGURATION - EMPRESA QA
# ============================================
# Ambiente: RedSalud QA (Pre-producción)
# Proyecto: qa-ticket-home-redsalud
# Región: southamerica-west1

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ============================================
# DATA SOURCES
# ============================================

data "google_project" "project" {
  project_id = var.project_id
}

# ============================================
# SECRETS
# ============================================

module "database_url_secret" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  secret_id             = "tickethome-db-url"
  service_account_email = var.service_account_email
}

module "secret_key_secret" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  secret_id             = "tickethome-secret-key"
  service_account_email = var.service_account_email
}

module "superuser_emails_secret" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  secret_id             = "superuser-emails"
  service_account_email = var.service_account_email
}

# ============================================
# CLOUD RUN SERVICE
# ============================================

module "cloud_run" {
  source = "../../modules/cloud-run"

  project_id   = var.project_id
  region       = var.region
  service_name = var.service_name
  image        = var.docker_image

  # Service Account
  service_account_email = var.service_account_email

  # Recursos
  cpu             = "2"
  memory          = "1Gi"
  timeout_seconds = 900
  concurrency     = 80

  # Autoscaling (siempre activo, similar a producción)
  min_instances = "1"
  max_instances = "3"

  # VPC Connector (no Cloud SQL Proxy)
  vpc_connector = var.vpc_connector
  vpc_egress    = "private-ranges-only"

  # Variables de entorno
  env_vars = {
    ENVIRONMENT       = var.environment
    FLASK_ENV         = "production"
    FLASK_DEBUG       = "false"
    ENABLE_IAP        = "true"
    ENABLE_DEMO_LOGIN = "false" # ⚠️ QA es solo SSO (sin login tradicional)
  }

  # Secrets montados
  secrets = {
    DATABASE_URL = {
      secret_name = module.database_url_secret.secret_name
      version     = "latest"
    }
    SECRET_KEY = {
      secret_name = module.secret_key_secret.secret_name
      version     = "latest"
    }
    SUPERUSER_EMAILS = {
      secret_name = module.superuser_emails_secret.secret_name
      version     = "latest"
    }
  }

  # IAP
  enable_iap          = true
  iap_service_account = "service-${data.google_project.project.number}@gcp-sa-iap.iam.gserviceaccount.com"

  enable_public_access = false
}

# ============================================
# LOAD BALANCER + IAP + SSL
# ============================================

module "load_balancer" {
  source = "../../modules/load-balancer"

  project_id = var.project_id
  lb_name    = "${var.service_name}-lb"

  # Dominios
  domains = [var.domain_name]

  # Cloud Run backend
  cloud_run_service_name = module.cloud_run.service_name
  cloud_run_region       = var.region

  # Backend config
  backend_timeout_sec = 900

  # CDN deshabilitado
  enable_cdn = false

  # IAP
  enable_iap              = true
  iap_oauth_client_id     = var.iap_oauth_client_id
  iap_oauth_client_secret = var.iap_oauth_client_secret

  # Acceso IAP (grupo específico de QA)
  iap_access_members = var.iap_access_members

  # HTTP → HTTPS redirect
  redirect_http_to_https = true

  # Logging
  enable_logging  = true
  log_sample_rate = 1.0
}
