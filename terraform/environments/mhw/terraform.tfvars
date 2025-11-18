# Este archivo contiene la configuración específica para el ambiente de MHW (personal).
# Aquí se le asignan valores a las variables definidas en el módulo.

project_id          = "ticket-home-demo"
region              = "us-central1"
service_name        = "tickethome-demo"
sql_instance_name   = "tickethome-db"
db_connection_type  = "CLOUD_SQL_PROXY"
min_instances       = 0
enable_demo_login   = true

# Nuevas variables para el servicio de Cloud Run
service_account_email = "tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com"
image_url             = "us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest"

# Nombres de los secrets para este ambiente
secret_database_url_name = "mhw-database-url"
secret_key_name          = "mhw-secret-key"
secret_superusers_name   = "mhw-superuser-emails"


