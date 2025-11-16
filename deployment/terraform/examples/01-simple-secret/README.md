# Ejemplo 01: Simple Secret

Tu primer recurso con Terraform - un secret en Google Secret Manager.

## Qué aprenderás

- ✅ Estructura básica de archivos Terraform
- ✅ Sintaxis HCL (HashiCorp Configuration Language)
- ✅ Crear un recurso en GCP
- ✅ Usar variables
- ✅ Ver outputs

## Archivos

```
01-simple-secret/
├── main.tf                    # Configuración principal
├── variables.tf               # Declaración de variables
├── outputs.tf                 # Outputs
├── terraform.tfvars.example   # Ejemplo de valores
└── README.md                  # Esta guía
```

## Paso a Paso

### 1. Configurar Variables

```bash
# Copiar archivo de ejemplo
cp terraform.tfvars.example terraform.tfvars

# Editar con tu proyecto
vim terraform.tfvars
```

Contenido de `terraform.tfvars`:
```hcl
project_id = "mi-proyecto-real"
```

### 2. Inicializar Terraform

```bash
terraform init
```

**Qué hace**:
- Descarga el provider de Google Cloud
- Crea directorio `.terraform/`
- Crea archivo `.terraform.lock.hcl`

### 3. Validar Sintaxis

```bash
terraform validate
```

**Output esperado**:
```
Success! The configuration is valid.
```

### 4. Ver el Plan

```bash
terraform plan
```

**Output esperado**:
```
Terraform will perform the following actions:

  # google_secret_manager_secret.example will be created
  + resource "google_secret_manager_secret" "example" {
      + create_time = (known after apply)
      + id          = (known after apply)
      + labels      = {
          + "created-by" = "terraform"
          + "example"    = "01-simple-secret"
        }
      + name        = (known after apply)
      + project     = "mi-proyecto-real"
      + secret_id   = "ejemplo-terraform-secret"

      + replication {
          + automatic = true
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

**Qué significa**:
- `+` = recurso a crear
- `~` = recurso a modificar
- `-` = recurso a destruir
- `(known after apply)` = valor se conoce después de crear

### 5. Aplicar

```bash
terraform apply
```

**Terraform preguntará**:
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**Output esperado**:
```
google_secret_manager_secret.example: Creating...
google_secret_manager_secret.example: Creation complete after 2s [id=projects/123456789/secrets/ejemplo-terraform-secret]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

next_steps = <<EOT
✅ Secret creado exitosamente!
...
EOT
secret_id = "projects/123456789/secrets/ejemplo-terraform-secret"
secret_name = "ejemplo-terraform-secret"
```

### 6. Ver el State

```bash
# Ver todos los recursos
terraform state list

# Ver detalles del secret
terraform state show google_secret_manager_secret.example
```

### 7. Ver Outputs

```bash
# Ver todos los outputs
terraform output

# Ver uno específico
terraform output secret_name

# Ver en formato JSON
terraform output -json
```

### 8. Agregar Valor al Secret

El secret está creado pero vacío. Agregar valor:

```bash
echo "mi-valor-secreto-123" | \
  gcloud secrets versions add ejemplo-terraform-secret --data-file=-
```

Verificar:

```bash
# Listar versiones
gcloud secrets versions list ejemplo-terraform-secret

# Ver valor (requiere permisos)
gcloud secrets versions access latest --secret=ejemplo-terraform-secret
```

### 9. Modificar el Recurso

Edita `main.tf` y agrega un label:

```hcl
  labels = {
    created-by = "terraform"
    example    = "01-simple-secret"
    owner      = "tu-nombre"  # <- Nuevo
  }
```

Aplica el cambio:

```bash
terraform plan
terraform apply
```

**Output**:
```
  ~ resource "google_secret_manager_secret" "example" {
      ~ labels      = {
          + "owner"      = "tu-nombre"
            # (2 unchanged elements hidden)
        }
        # (5 unchanged attributes hidden)
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

Nota el `~` indicando modificación (no recreación).

### 10. Destruir

```bash
terraform destroy
```

**Output**:
```
Plan: 0 to add, 0 to change, 1 to destroy.

Do you really want to destroy all resources?
  Enter a value: yes

google_secret_manager_secret.example: Destroying...
google_secret_manager_secret.example: Destruction complete after 1s

Destroy complete! Resources: 1 destroyed.
```

## Conceptos Aprendidos

### 1. Terraform Block

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}
```

**Qué hace**:
- Especifica versión mínima de Terraform
- Define providers necesarios
- Especifica versiones de providers

### 2. Provider Block

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}
```

**Qué hace**:
- Configura el provider de Google Cloud
- Usa variables para project y region

### 3. Resource Block

```hcl
resource "tipo_recurso" "nombre_local" {
  argumento = "valor"
}
```

**Estructura**:
- `tipo_recurso`: tipo del recurso (ej: `google_secret_manager_secret`)
- `nombre_local`: nombre para referenciar (ej: `example`)
- Referencia completa: `google_secret_manager_secret.example`

### 4. Variables

```hcl
variable "nombre" {
  description = "Descripción"
  type        = string
  default     = "valor-por-defecto"
}
```

**Uso**:
- Declarar en `variables.tf`
- Proveer valor en `terraform.tfvars`
- Referenciar con `var.nombre`

### 5. Outputs

```hcl
output "nombre" {
  description = "Descripción"
  value       = recurso.atributo
}
```

**Uso**:
- Ver con `terraform output`
- Útil para mostrar IPs, URLs, etc.

## Archivos Creados

Después de `terraform init` y `terraform apply`:

```
.terraform/              # Directorio de Terraform (ignorar en git)
.terraform.lock.hcl      # Lock de versiones de providers
terraform.tfstate        # State file (NUNCA commitear)
terraform.tfvars         # Tus valores (NUNCA commitear)
```

**⚠️ Importante**: Agregar a `.gitignore`:
```
.terraform/
*.tfstate
*.tfstate.*
terraform.tfvars
```

## Próximos Pasos

✅ Completaste el Ejemplo 01!

Ahora prueba:
- [Ejemplo 02: Cloud Run Basic](../02-cloud-run-basic/)

---

**Tiempo estimado**: 10-15 minutos
