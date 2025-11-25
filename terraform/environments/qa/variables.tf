variable "project_id" {}
variable "region" {}
variable "service_name" {}
variable "image_url" {}
variable "service_account_email" {}
variable "sql_instance_name" {}
variable "secret_database_url_name" {}
variable "secret_key_name" {}
variable "secret_superusers_name" {}
variable "vpc_connector" {}
variable "iap_access_group" {}
variable "reset_db_on_startup" { default = false }
variable "use_qa_minimal_seed" { default = false }
variable "superuser_emails" { type = list(string) }
variable "force_deployment_timestamp" { default = "" }
