# Módulo Terraform: Cloud Run

Módulo reutilizable para crear servicios Cloud Run completamente configurados.

## Features

- ✅ Autoscaling configurable (min/max instances)
- ✅ Soporte para Cloud SQL Proxy
- ✅ Soporte para VPC Connector
- ✅ Montaje de secrets desde Secret Manager
- ✅ Variables de entorno configurables
- ✅ IAM bindings (IAP o público)
- ✅ Recursos configurables (CPU, memoria, timeout)

## Uso Básico

```hcl
module "cloud_run" {
  source = "../../modules/cloud-run"

  project_id   = "mi-proyecto"
  region       = "us-central1"
  service_name = "mi-app"
  image        = "us-central1-docker.pkg.dev/mi-proyecto/repo/app:latest"

  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"

  env_vars = {
    ENVIRONMENT = "production"
    FLASK_ENV   = "production"
  }

  secrets = {
    DATABASE_URL = {
      secret_name = "database-url"
      version     = "latest"
    }
    SECRET_KEY = {
      secret_name = "secret-key"
      version     = "latest"
    }
  }
}
```

## Ejemplo con Cloud SQL

```hcl
module "cloud_run" {
  source = "../../modules/cloud-run"

  project_id   = "mi-proyecto"
  region       = "us-central1"
  service_name = "mi-app"
  image        = "us-central1-docker.pkg.dev/mi-proyecto/repo/app:latest"

  # Cloud SQL Proxy
  cloudsql_connection_name = "mi-proyecto:us-central1:mi-db"

  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"
}
```

## Ejemplo con VPC Connector

```hcl
module "cloud_run" {
  source = "../../modules/cloud-run"

  project_id   = "mi-proyecto"
  region       = "southamerica-west1"
  service_name = "mi-app"
  image        = "southamerica-west1-docker.pkg.dev/mi-proyecto/repo/app:latest"

  # VPC Connector
  vpc_connector = "mi-vpc-connector"
  vpc_egress    = "private-ranges-only"

  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"
}
```

## Ejemplo con Autoscaling

```hcl
module "cloud_run" {
  source = "../../modules/cloud-run"

  project_id   = "mi-proyecto"
  region       = "us-central1"
  service_name = "mi-app"
  image        = "us-central1-docker.pkg.dev/mi-proyecto/repo/app:latest"

  # Autoscaling
  min_instances = "1"  # Siempre activo
  max_instances = "10" # Escala hasta 10 instancias

  # Recursos
  cpu             = "2"
  memory          = "2Gi"
  timeout_seconds = 900
  concurrency     = 80

  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"
}
```

## Variables

| Variable | Descripción | Tipo | Default | Requerido |
|----------|-------------|------|---------|-----------|
| `project_id` | ID del proyecto GCP | string | - | ✅ |
| `region` | Región de GCP | string | - | ✅ |
| `service_name` | Nombre del servicio | string | - | ✅ |
| `image` | Imagen Docker | string | - | ✅ |
| `service_account_email` | Email del SA | string | - | ✅ |
| `cpu` | CPUs | string | "2" | ❌ |
| `memory` | Memoria | string | "1Gi" | ❌ |
| `min_instances` | Instancias mínimas | string | "0" | ❌ |
| `max_instances` | Instancias máximas | string | "3" | ❌ |
| `cloudsql_connection_name` | Cloud SQL | string | "" | ❌ |
| `vpc_connector` | VPC Connector | string | "" | ❌ |
| `env_vars` | Variables de entorno | map(string) | {} | ❌ |
| `secrets` | Secrets | map(object) | {} | ❌ |
| `enable_iap` | Habilitar IAP | bool | true | ❌ |

## Outputs

| Output | Descripción |
|--------|-------------|
| `service_name` | Nombre del servicio creado |
| `service_url` | URL del servicio |
| `service_id` | ID del servicio |
| `latest_revision_name` | Última revisión |
| `service_location` | Región del servicio |

## Notas

- **Cloud SQL vs VPC Connector**: No uses ambos al mismo tiempo. Cloud SQL Proxy es para conexiones directas a Cloud SQL, VPC Connector es para redes privadas.
- **IAP**: Por default está habilitado (`enable_iap = true`). Para desarrollo local puedes usar `enable_public_access = true`.
- **Secrets**: Deben existir previamente en Secret Manager.
- **Service Account**: Debe tener permisos `roles/secretmanager.secretAccessor` para los secrets.
