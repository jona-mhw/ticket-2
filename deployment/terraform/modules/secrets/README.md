# Módulo Terraform: Secrets

Módulo reutilizable para crear secrets en Google Secret Manager con permisos IAM.

## Features

- ✅ Crea secrets en Secret Manager
- ✅ Asigna permisos al Service Account automáticamente
- ✅ Soporte para replicación automática o manual
- ✅ Opción de crear secret vacío (sin valor)
- ✅ Labels configurables

## Uso Básico

```hcl
module "database_url_secret" {
  source = "../../modules/secrets"

  project_id            = "mi-proyecto"
  secret_id             = "database-url"
  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"

  # NO poner secret_data aquí (déjalo vacío)
  # Agregar valor manualmente con gcloud
}
```

Luego manualmente:
```bash
echo "postgresql://user:pass@host/db" | \
  gcloud secrets versions add database-url --data-file=-
```

## ⚠️ IMPORTANTE: Manejo de Valores Sensibles

**NUNCA** pongas valores sensibles directamente en Terraform:

```hcl
# ❌ MAL - NO HACER ESTO
module "secret" {
  source      = "../../modules/secrets"
  secret_data = "mi-password-123"  # ❌ Quedará en el state!
}
```

**Mejor práctica**:

```hcl
# ✅ BIEN - Crear secret vacío
module "secret" {
  source = "../../modules/secrets"

  project_id = "mi-proyecto"
  secret_id  = "database-password"

  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"

  # NO especificar secret_data
}
```

Luego agregar valor manualmente:
```bash
# Opción 1: Desde prompt
gcloud secrets versions add database-password --data-file=-
# Escribir el valor y presionar Ctrl+D

# Opción 2: Desde archivo
echo "mi-password-seguro" | gcloud secrets versions add database-password --data-file=-

# Opción 3: Desde variable de entorno
echo $MY_PASSWORD | gcloud secrets versions add database-password --data-file=-
```

## Uso con Replicación Manual

```hcl
module "secret" {
  source = "../../modules/secrets"

  project_id = "mi-proyecto"
  secret_id  = "api-key"

  # Replicación en regiones específicas
  replication_locations = [
    "us-central1",
    "southamerica-west1"
  ]

  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"
}
```

## Uso con Labels

```hcl
module "secret" {
  source = "../../modules/secrets"

  project_id = "mi-proyecto"
  secret_id  = "database-url"

  labels = {
    environment = "production"
    app         = "ticket-home"
    managed-by  = "terraform"
  }

  service_account_email = "mi-sa@mi-proyecto.iam.gserviceaccount.com"
}
```

## Variables

| Variable | Descripción | Tipo | Default | Requerido |
|----------|-------------|------|---------|-----------|
| `project_id` | ID del proyecto GCP | string | - | ✅ |
| `secret_id` | ID del secret | string | - | ✅ |
| `secret_data` | Valor del secret | string | "" | ❌ |
| `service_account_email` | Email del SA | string | "" | ❌ |
| `replication_locations` | Regiones de replicación | list(string) | null | ❌ |
| `labels` | Labels | map(string) | {} | ❌ |

## Outputs

| Output | Descripción |
|--------|-------------|
| `secret_id` | ID completo del secret |
| `secret_name` | Nombre corto del secret |
| `version_id` | ID de la versión (si se creó) |

## Ejemplo Completo en Ambiente

```hcl
# Crear 3 secrets para la aplicación
module "database_url" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  secret_id             = "database-url"
  service_account_email = var.service_account_email
}

module "secret_key" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  secret_id             = "secret-key"
  service_account_email = var.service_account_email
}

module "superuser_emails" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  secret_id             = "superuser-emails"
  service_account_email = var.service_account_email
}

# Usar en Cloud Run
module "cloud_run" {
  source = "../../modules/cloud-run"

  # ... otras configs ...

  secrets = {
    DATABASE_URL = {
      secret_name = module.database_url.secret_name
      version     = "latest"
    }
    SECRET_KEY = {
      secret_name = module.secret_key.secret_name
      version     = "latest"
    }
    SUPERUSER_EMAILS = {
      secret_name = module.superuser_emails.secret_name
      version     = "latest"
    }
  }
}
```

## Verificar Secrets

```bash
# Listar secrets
gcloud secrets list --project=mi-proyecto

# Ver versiones de un secret
gcloud secrets versions list database-url --project=mi-proyecto

# Acceder al valor (requiere permisos)
gcloud secrets versions access latest --secret=database-url
```

## Notas

- **Replicación automática** (default): Google maneja dónde replica el secret
- **Replicación manual**: Tú especificas las regiones exactas
- **IAM**: El módulo automáticamente da permiso `secretAccessor` al Service Account
- **State file**: Si usas `secret_data`, el valor quedará en el state (por eso NO se recomienda)
