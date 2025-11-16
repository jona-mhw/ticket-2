# 🚀 Instructivo Terraform - Paso a Paso

**Guía práctica para deployar Ticket Home con Terraform**

---

## 📋 Prerequisitos

### 1. Instalar Terraform

**macOS**:
```bash
brew install terraform
```

**Windows**:
```powershell
choco install terraform
# O descargar de: https://www.terraform.io/downloads
```

**Linux**:
```bash
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Verificar**:
```bash
terraform --version
# Debe mostrar: Terraform v1.6.0 o superior
```

### 2. Instalar gcloud CLI

```bash
# Ya lo tienes, pero asegúrate de estar autenticado
gcloud auth login
gcloud auth application-default login  # Para Terraform
```

### 3. Permisos Necesarios

Tu cuenta de Google debe tener estos roles en el proyecto:
- Editor
- Security Admin (para IAP)
- Secret Manager Admin

---

## 🎯 Flujo Completo de Terraform

```
┌─────────────┐
│  terraform  │
│    init     │  ← Descarga providers y módulos
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  terraform  │
│   validate  │  ← Valida sintaxis
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  terraform  │
│    plan     │  ← Muestra QUÉ va a hacer (sin hacer cambios)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  terraform  │
│    apply    │  ← Crea/modifica recursos en GCP
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Recursos   │
│  creados    │
│  en GCP     │
└─────────────┘
```

---

## 🏃 Quick Start - 5 Minutos

### Ejemplo 1: Crear un Cloud Run Simple

```bash
# 1. Ir a la carpeta de ejemplos
cd deployment/terraform/examples

# 2. Inicializar Terraform
terraform init

# 3. Ver qué va a crear
terraform plan

# 4. Crear el recurso
terraform apply
# Escribir "yes" cuando pregunte

# 5. Ver lo que se creó
terraform show

# 6. Destruir (limpiar)
terraform destroy
# Escribir "yes" cuando pregunte
```

¡Listo! Acabas de crear y destruir tu primer recurso con Terraform.

---

## 📚 Paso a Paso Detallado

### Paso 1: Entender la Estructura

```
deployment/terraform/
├── environments/
│   └── mhw-dev/           # Empezaremos con este
│       ├── main.tf        # Configuración principal
│       ├── variables.tf   # Declaración de variables
│       ├── terraform.tfvars  # Valores de variables (secreto)
│       └── backend.tf     # Configuración del state
```

### Paso 2: Configurar Variables

```bash
cd deployment/terraform/environments/mhw-dev

# Copiar archivo de ejemplo
cp terraform.tfvars.example terraform.tfvars

# Editar con tus valores
vim terraform.tfvars
```

**Contenido de `terraform.tfvars`**:
```hcl
# GCP
project_id = "ticket-home-demo"
region     = "us-central1"

# Aplicación
service_name = "tickethome-demo"
environment  = "mhw-dev"

# Docker
docker_image = "us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest"

# Cloud SQL
cloudsql_instance_name        = "tickethome-db"
cloudsql_database_name        = "mhw_ticket_home"
cloudsql_connection_name      = "ticket-home-demo:us-central1:tickethome-db"

# Dominio
domain_name = "ticket-home-beta.mhwdev.dev"

# Service Account
service_account_email = "tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com"
```

### Paso 3: Inicializar Terraform

```bash
terraform init
```

**Output esperado**:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
- Installing hashicorp/google v5.7.0...
- Installed hashicorp/google v5.7.0

Terraform has been successfully initialized!
```

**Qué hace `init`**:
- Descarga el provider de Google Cloud
- Configura el backend (dónde guardar el state)
- Descarga módulos si los hay

### Paso 4: Validar Sintaxis

```bash
terraform validate
```

**Output esperado**:
```
Success! The configuration is valid.
```

Si hay errores, los muestra claramente.

### Paso 5: Ver el Plan

```bash
terraform plan
```

**Output ejemplo**:
```
Terraform will perform the following actions:

  # google_cloud_run_service.app will be created
  + resource "google_cloud_run_service" "app" {
      + id       = (known after apply)
      + name     = "tickethome-demo"
      + location = "us-central1"
      + status   = (known after apply)

      + template {
          + metadata {
              + generation = (known after apply)
              + name       = (known after apply)
            }

          + spec {
              + container_concurrency = 80
              + service_account_name  = "tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com"
              + timeout_seconds       = 900

              + containers {
                  + image = "us-central1-docker.pkg.dev/..."
                  # ...
                }
            }
        }
    }

  # google_service_account_iam_member.secret_accessor will be created
  + resource "google_service_account_iam_member" "secret_accessor" {
      + id                = (known after apply)
      # ...
    }

Plan: 15 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + cloud_run_url = (known after apply)
```

**Qué hacer con el plan**:
- ✅ Revisar que va a crear lo correcto
- ✅ Verificar nombres de recursos
- ✅ Confirmar que no va a destruir nada importante

### Paso 6: Aplicar Cambios

```bash
terraform apply
```

**Interactive prompt**:
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes    # Escribir "yes"
```

**Output esperado**:
```
google_service_account.app: Creating...
google_service_account.app: Creation complete after 3s [id=projects/ticket-home-demo/serviceAccounts/...]

google_secret_manager_secret.database_url: Creating...
google_secret_manager_secret.database_url: Creation complete after 2s [id=...]

google_cloud_run_service.app: Creating...
google_cloud_run_service.app: Still creating... [10s elapsed]
google_cloud_run_service.app: Still creating... [20s elapsed]
google_cloud_run_service.app: Creation complete after 25s [id=...]

Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:

cloud_run_url = "https://tickethome-demo-abc123-uc.a.run.app"
service_account_email = "tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com"
```

**¡Listo!** Tu infraestructura está creada.

### Paso 7: Verificar en GCP

```bash
# Ver Cloud Run
gcloud run services list --project=ticket-home-demo

# Ver Service Accounts
gcloud iam service-accounts list --project=ticket-home-demo

# Ver Secrets
gcloud secrets list --project=ticket-home-demo
```

### Paso 8: Ver el State

```bash
# Ver todos los recursos administrados por Terraform
terraform state list

# Ver detalles de un recurso específico
terraform state show google_cloud_run_service.app

# Ver todo el state
terraform show
```

---

## 🔄 Flujo de Trabajo Diario

### Escenario 1: Cambiar Configuración

**Ejemplo**: Aumentar memoria de Cloud Run de 1Gi a 2Gi

```bash
# 1. Editar main.tf
vim main.tf

# Cambiar:
# memory = "1Gi"
# Por:
# memory = "2Gi"

# 2. Ver qué va a cambiar
terraform plan

# Output:
# ~ resource "google_cloud_run_service" "app" {
#     ~ template {
#         ~ spec {
#             ~ containers {
#                 ~ resources {
#                     ~ limits = {
#                         ~ memory = "1Gi" -> "2Gi"
#                       }
#                   }
#               }
#           }
#       }
#   }

# 3. Aplicar cambio
terraform apply
```

### Escenario 2: Agregar Nuevo Recurso

**Ejemplo**: Agregar un nuevo secret

```bash
# 1. Editar main.tf, agregar:
resource "google_secret_manager_secret" "new_api_key" {
  secret_id = "api-key"

  replication {
    automatic = true
  }
}

# 2. Ver qué va a crear
terraform plan

# 3. Aplicar
terraform apply
```

### Escenario 3: Eliminar Recurso

```bash
# 1. Eliminar el recurso de main.tf

# 2. Ver qué va a destruir
terraform plan

# Output:
# Plan: 0 to add, 0 to change, 1 to destroy.

# 3. Aplicar
terraform apply
```

---

## 🌍 Trabajar con Múltiples Ambientes

### Opción 1: Workspaces

```bash
# Crear workspace para cada ambiente
terraform workspace new mhw-dev
terraform workspace new empresa-dev
terraform workspace new empresa-qa

# Listar workspaces
terraform workspace list

# Cambiar de workspace
terraform workspace select mhw-dev

# Ver workspace actual
terraform workspace show

# Aplicar en el workspace actual
terraform apply
```

### Opción 2: Directorios Separados (Recomendado)

```bash
# Cada ambiente tiene su propia carpeta
cd environments/mhw-dev
terraform apply

cd environments/empresa-dev
terraform apply

cd environments/empresa-qa
terraform apply
```

---

## 🔐 Manejo de Secrets

### ⚠️ IMPORTANTE: NO poner secrets en .tf

**MAL** ❌:
```hcl
resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = "mi-password-123"  # ❌ NUNCA HACER ESTO
}
```

**BIEN** ✅:
```hcl
# Terraform solo CREA el secret (sin valor)
resource "google_secret_manager_secret" "db_password" {
  secret_id = "database-password"

  replication {
    automatic = true
  }
}

# El valor se pone manualmente FUERA de Terraform
```

Luego manualmente:
```bash
echo "mi-password-seguro" | \
  gcloud secrets versions add database-password --data-file=-
```

---

## 📊 Estado del State File

### ¿Qué es el State?

El `terraform.tfstate` es un archivo JSON que contiene:
- Todos los recursos que Terraform administra
- IDs de recursos en GCP
- Metadatos
- **Información sensible** (IPs, nombres, etc.)

### ⚠️ NUNCA commitear terraform.tfstate

```bash
# .gitignore
*.tfstate
*.tfstate.*
*.tfvars  # Contiene valores sensibles
```

### Backend Remoto (Recomendado para Producción)

**backend.tf**:
```hcl
terraform {
  backend "gcs" {
    bucket = "ticket-home-terraform-state"
    prefix = "environments/mhw-dev"
  }
}
```

**Ventajas**:
- ✅ State compartido entre equipo
- ✅ Locking automático (evita conflictos)
- ✅ Versionado
- ✅ Encriptado

**Crear bucket**:
```bash
gcloud storage buckets create gs://ticket-home-terraform-state \
  --project=ticket-home-demo \
  --location=us-central1 \
  --uniform-bucket-level-access

# Habilitar versionado
gcloud storage buckets update gs://ticket-home-terraform-state \
  --versioning
```

---

## 🐛 Troubleshooting

### Error: "Provider configuration not present"

```
Error: Provider configuration not present

To work with google_cloud_run_service.app its original provider configuration at
provider["registry.terraform.io/hashicorp/google"] is required, but it has been
removed. This occurs when a provider configuration is removed while objects
created by that provider still exist in the state.
```

**Solución**:
```bash
# Re-ejecutar init
terraform init
```

### Error: "Backend initialization required"

```bash
# Re-inicializar backend
terraform init -reconfigure
```

### Error: "Resource already exists"

Si un recurso ya existe en GCP:

**Opción 1**: Importar el recurso existente
```bash
terraform import google_cloud_run_service.app projects/ticket-home-demo/locations/us-central1/services/tickethome-demo
```

**Opción 2**: Eliminar del state y recrear
```bash
terraform state rm google_cloud_run_service.app
terraform apply
```

### Error: "Lock acquisition failed"

Otro usuario está ejecutando Terraform:

```bash
# Forzar unlock (solo si estás seguro que nadie más está ejecutando)
terraform force-unlock LOCK_ID
```

### Ver qué va a cambiar sin aplicar

```bash
# Guardar plan en archivo
terraform plan -out=tfplan

# Ver el plan guardado
terraform show tfplan

# Aplicar el plan guardado (sin preguntar)
terraform apply tfplan
```

---

## 📋 Cheat Sheet

### Comandos Básicos

```bash
terraform init          # Inicializar (primera vez)
terraform validate      # Validar sintaxis
terraform fmt           # Formatear archivos .tf
terraform plan          # Ver qué va a cambiar
terraform apply         # Aplicar cambios
terraform destroy       # Destruir todo
terraform show          # Ver state actual
terraform output        # Ver outputs
```

### State Management

```bash
terraform state list                              # Listar recursos
terraform state show RESOURCE                     # Ver detalles de recurso
terraform state rm RESOURCE                       # Remover de state
terraform state mv RESOURCE_OLD RESOURCE_NEW      # Renombrar recurso
terraform import RESOURCE ID                      # Importar recurso existente
terraform refresh                                 # Actualizar state
```

### Workspaces

```bash
terraform workspace list              # Listar workspaces
terraform workspace new WORKSPACE     # Crear workspace
terraform workspace select WORKSPACE  # Cambiar workspace
terraform workspace delete WORKSPACE  # Eliminar workspace
```

### Debugging

```bash
terraform plan -out=plan.tfplan       # Guardar plan
terraform show plan.tfplan            # Ver plan guardado
terraform apply -auto-approve         # Aplicar sin preguntar
TF_LOG=DEBUG terraform apply          # Ver logs detallados
terraform console                     # Consola interactiva
```

---

## 🎯 Mejores Prácticas

### 1. Versionado

```hcl
# Siempre especificar versión de providers
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"  # Versión específica
    }
  }
}
```

### 2. Variables

```hcl
# Siempre usar variables, no hardcodear
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

# NO hacer:
project = "ticket-home-demo"  # ❌

# Hacer:
project = var.project_id      # ✅
```

### 3. Outputs

```hcl
# Siempre crear outputs para información importante
output "cloud_run_url" {
  description = "URL del Cloud Run service"
  value       = google_cloud_run_service.app.status[0].url
}
```

### 4. Módulos

```hcl
# Reutilizar código con módulos
module "cloud_run" {
  source = "../../modules/cloud-run"

  service_name = var.service_name
  image        = var.docker_image
}
```

### 5. Comentarios

```hcl
# SIEMPRE comentar código no obvio
resource "google_cloud_run_service" "app" {
  # Usamos us-central1 porque es más barato que southamerica-west1
  location = "us-central1"
}
```

---

## 🚀 Próximos Pasos

1. ✅ **Leer** este instructivo completo
2. ✅ **Probar** `examples/simple-cloud-run.tf`
3. ✅ **Revisar** `environments/mhw-dev/main.tf`
4. ✅ **Aplicar** a tu ambiente MHW DEV
5. ✅ **Replicar** para Empresa DEV y QA

---

## 📚 Recursos Adicionales

- [Terraform CLI Docs](https://www.terraform.io/cli)
- [Google Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)

---

**Creado por**: Jonathan Segura
**Fecha**: 2025-11-15
**Versión**: 1.0
