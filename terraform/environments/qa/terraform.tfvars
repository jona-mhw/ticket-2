project_id             = "qa-ticket-home-redsalud"
region                 = "southamerica-west1"
service_name           = "ticket-home"
image_url              = "southamerica-west1-docker.pkg.dev/qa-ticket-home-redsalud/tickethome-repo/ticket-home:latest" # Ajustar si cambia
service_account_email  = "qa-ticket-home@qa-ticket-home-redsalud.iam.gserviceaccount.com"
sql_instance_name      = "qa-ticket-home"
secret_database_url_name = "tickethome-db-url"
secret_key_name        = "tickethome-secret-key"
secret_superusers_name = "superuser-emails"
vpc_connector          = "projects/qa-ticket-home-redsalud/locations/southamerica-west1/connectors/tckthome-conn-qa-sa-west1"
iap_access_group       = "qa-ticket-home-rs@googlegroups.com"

superuser_emails = [
  "global_admin@tickethome.com",
  "jonathan.segura@redsalud.cl",
  "admin@tickethome.com"
]
