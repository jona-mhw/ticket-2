# 🏗️ Terraform para Ticket Home - Guía Educativa

**Última actualización**: 2025-11-15

---

## 📚 ¿Qué es Terraform?

**Terraform** es una herramienta de **Infrastructure as Code (IaC)** que te permite definir tu infraestructura cloud usando archivos de configuración en lugar de crear recursos manualmente.

### Analogía Simple

**Imagina que estás construyendo una casa:**

**Sin Terraform** (método actual):
- Llamas al albañil y le dices: "Pon un ladrillo aquí"
- Llamas al electricista: "Instala un cable allá"
- Llamas al plomero: "Pon una tubería acá"
- Si quieres otra casa igual, tienes que repetir todas las llamadas

**Con Terraform**:
- Escribes un plano (archivo `.tf`)
- Ejecutas `terraform apply`
- Terraform construye toda la casa automáticamente
- Si quieres otra casa igual, solo ejecutas `terraform apply` de nuevo

---

## 🆚 Comparación: Sistema Actual vs Terraform

### Sistema Actual (Scripts + gcloud)

```bash
# 1. Crear secrets manualmente
gcloud secrets create mhw-database-url --data-file=...
gcloud secrets create mhw-secret-key --data-file=...

# 2. Crear service account manualmente
gcloud iam service-accounts create tickethome-demo-sa

# 3. Asignar permisos manualmente
gcloud projects add-iam-policy-binding ...

# 4. Build Docker
docker build -t IMAGE .
docker push IMAGE

# 5. Deploy Cloud Run
gcloud run deploy tickethome-demo \
  --image=IMAGE \
  --set-secrets=... \
  --set-env-vars=... \
  --vpc-connector=... \
  # ... 20 parámetros más
```

**Problemas**:
- ❌ Tienes que ejecutar 15+ comandos en orden
- ❌ Si falla uno, tienes que arreglarlo manualmente
- ❌ No sabes qué recursos existen (no hay inventario)
- ❌ Para replicar en otro ambiente, ejecutas todo de nuevo
- ❌ No hay historial de cambios
- ❌ Difícil de auditar

### Con Terraform

```hcl
# main.tf - TODO en un solo archivo
resource "google_secret_manager_secret" "database_url" {
  secret_id = "mhw-database-url"
  # ... config
}

resource "google_service_account" "app" {
  account_id = "tickethome-demo-sa"
}

resource "google_cloud_run_service" "app" {
  name     = "tickethome-demo"
  location = "us-central1"

  template {
    spec {
      service_account_name = google_service_account.app.email
      # ... resto de config
    }
  }
}
```

**Ejecutar**:
```bash
terraform plan   # Ver qué va a crear
terraform apply  # Crear todo
```

**Ventajas**:
- ✅ **Un solo comando** crea toda la infraestructura
- ✅ **Idempotente**: Puedes ejecutar 100 veces y siempre queda igual
- ✅ **State file**: Terraform sabe qué existe y qué no
- ✅ **Plan antes de aplicar**: Ves los cambios antes de hacerlos
- ✅ **Versionado en Git**: Historial completo de cambios
- ✅ **Reutilizable**: Mismo código para 3 ambientes (solo cambian variables)
- ✅ **Destrucción fácil**: `terraform destroy` elimina todo
- ✅ **Documentación viva**: El código ES la documentación

---

## 📊 Comparación Detallada

| Aspecto | Scripts Actuales | Terraform |
|---------|------------------|-----------|
| **Creación** | 15+ comandos manuales | 1 comando (`terraform apply`) |
| **Replicación** | Ejecutar todos los scripts de nuevo | Cambiar variables y `apply` |
| **Cambios** | Modificar y re-ejecutar scripts | Modificar `.tf` y `apply` |
| **Destrucción** | Eliminar recursos manualmente (peligroso) | `terraform destroy` |
| **Inventario** | No sabes qué existe | State file con todo |
| **Historial** | No hay (solo commits de scripts) | Git + State file |
| **Validación** | Ejecutar y esperar errores | `terraform plan` antes |
| **Errores** | Difícil recuperarse | Terraform corrige automáticamente |
| **Auditoría** | Revisar logs de GCP | Ver diffs en Git |
| **Curva aprendizaje** | Baja (bash/batch) | Media (HCL syntax) |
| **Mantenibilidad** | Baja (scripts largos) | Alta (código declarativo) |
| **Colaboración** | Difícil (conflictos) | Fácil (Git + Terraform Cloud) |

---

## 🎯 ¿Por Qué Tu Empresa Quiere Terraform?

### Razones Comunes en Empresas

1. **Compliance y Auditoría**
   - Necesitan saber exactamente qué existe en cloud
   - Poder replicar ambientes idénticos
   - Historial de cambios para auditorías

2. **Escalabilidad**
   - Van a crear más ambientes (staging, producción, DR)
   - No quieren scripts manuales para cada uno

3. **Estandarización**
   - Todos los proyectos usan Terraform
   - Políticas de seguridad centralizadas
   - Módulos compartidos entre equipos

4. **Seguridad**
   - Menos errores humanos
   - Validación antes de aplicar
   - No dar permisos de admin a todos (solo a Terraform)

5. **Disaster Recovery**
   - Si se cae todo, ejecutas `terraform apply` y vuelve

---

## 🏗️ Conceptos Básicos de Terraform

### 1. Providers

Un **provider** es el conector a un cloud provider (GCP, AWS, Azure).

```hcl
# Conectar a GCP
provider "google" {
  project = "ticket-home-demo"
  region  = "us-central1"
}
```

### 2. Resources

Un **resource** es un componente de infraestructura (VM, database, storage, etc).

```hcl
# Crear un Cloud Run service
resource "google_cloud_run_service" "app" {
  name     = "tickethome-demo"
  location = "us-central1"
}
```

### 3. Variables

Las **variables** permiten reutilizar código con diferentes valores.

```hcl
# Definir variable
variable "project_id" {
  type    = string
  default = "ticket-home-demo"
}

# Usar variable
project = var.project_id
```

### 4. Outputs

Los **outputs** muestran información después de crear recursos.

```hcl
output "cloud_run_url" {
  value = google_cloud_run_service.app.status[0].url
}
```

### 5. State

El **state** es un archivo que Terraform usa para saber qué existe.

```
terraform.tfstate  # NO commitear a Git (tiene secretos)
```

### 6. Modules

Los **modules** son bloques reutilizables de código.

```hcl
# Usar módulo
module "cloud_run" {
  source = "./modules/cloud-run"

  service_name = "tickethome-demo"
  image        = "gcr.io/..."
}
```

---

## 📁 Estructura de Este Proyecto

```
deployment/terraform/
├── README.md                    # Este archivo (educativo)
├── INSTRUCTIVO.md               # Paso a paso cómo usar
│
├── modules/                     # Módulos reutilizables
│   ├── cloud-run/              # Módulo para Cloud Run
│   ├── cloud-sql/              # Módulo para Cloud SQL
│   ├── load-balancer/          # Módulo para Load Balancer
│   └── secrets/                # Módulo para Secret Manager
│
├── environments/                # Configuración por ambiente
│   ├── mhw-dev/
│   │   ├── main.tf             # Infraestructura MHW DEV
│   │   ├── variables.tf        # Variables
│   │   ├── terraform.tfvars    # Valores de variables
│   │   └── README.md           # Guía específica
│   ├── empresa-dev/
│   └── empresa-qa/
│
└── examples/                    # Ejemplos para aprender
    └── simple-cloud-run.tf
```

---

## 🚀 Flujo de Trabajo con Terraform

### Paso 1: Escribir código

```hcl
# main.tf
resource "google_cloud_run_service" "app" {
  name = "tickethome-demo"
  # ...
}
```

### Paso 2: Inicializar

```bash
terraform init
```

Descarga providers y módulos.

### Paso 3: Planear

```bash
terraform plan
```

Muestra qué va a crear/modificar/destruir **sin hacer cambios**.

**Output ejemplo**:
```
Terraform will perform the following actions:

  # google_cloud_run_service.app will be created
  + resource "google_cloud_run_service" "app" {
      + name     = "tickethome-demo"
      + location = "us-central1"
      # ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

### Paso 4: Aplicar

```bash
terraform apply
```

Crea los recursos en GCP.

### Paso 5: Ver estado

```bash
terraform show
terraform state list
```

### Paso 6: Destruir (si es necesario)

```bash
terraform destroy
```

---

## 💡 Ejemplo Práctico: Cloud Run

### Sistema Actual (Script)

```bash
# 50+ líneas de script
gcloud run deploy tickethome-demo \
  --image=us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest \
  --region=us-central1 \
  --service-account=tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com \
  --set-secrets="DATABASE_URL=mhw-database-url:latest,SECRET_KEY=mhw-secret-key:latest,SUPERUSER_EMAILS=mhw-superuser-emails:latest" \
  --set-env-vars="FLASK_ENV=development,FLASK_DEBUG=false,ENABLE_IAP=true,ENABLE_DEMO_LOGIN=true,RESET_DB_ON_STARTUP=false,ENVIRONMENT=production" \
  --set-cloudsql-instances="ticket-home-demo:us-central1:tickethome-db" \
  --memory=1Gi \
  --cpu=2 \
  --timeout=900 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=3 \
  --port=8080 \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated
```

### Con Terraform

```hcl
# main.tf
resource "google_cloud_run_service" "app" {
  name     = "tickethome-demo"
  location = "us-central1"

  template {
    spec {
      service_account_name = google_service_account.app.email

      containers {
        image = var.docker_image

        env {
          name  = "FLASK_ENV"
          value = "development"
        }
        # ... más env vars

        resources {
          limits = {
            cpu    = "2"
            memory = "1Gi"
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "3"
        "run.googleapis.com/cloudsql-instances" = var.cloudsql_connection_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
```

**Ventajas**:
- ✅ Más legible
- ✅ Reutilizable
- ✅ Versionable
- ✅ Validable antes de aplicar

---

## 🎓 Curva de Aprendizaje

### Nivel 1: Básico (1-2 días)
- Entender qué es IaC
- Sintaxis HCL básica
- `terraform init`, `plan`, `apply`
- Crear un Cloud Run simple

### Nivel 2: Intermedio (1 semana)
- Variables y outputs
- Módulos simples
- State management
- Backends remotos (GCS)

### Nivel 3: Avanzado (2-4 semanas)
- Módulos complejos
- Workspaces para ambientes
- Terraform Cloud
- CI/CD con Terraform

---

## 🔧 Herramientas Necesarias

```bash
# Instalar Terraform
# macOS
brew install terraform

# Windows
choco install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verificar instalación
terraform --version
```

---

## 📊 Estado Actual vs Propuesta Terraform

### Estado Actual
```
deployment/
├── mhw-dev/
│   ├── Deploy-Interactive.ps1    # 500+ líneas
│   └── deploy-master.sh          # 400+ líneas
├── empresa-dev/
│   ├── 1-build-push-local.bat    # Build manual
│   └── 2-deploy-normal.bat       # Deploy manual
└── empresa-qa/
    └── ...
```

**Características**:
- Scripts imperativos ("haz esto, luego esto")
- Difícil de mantener
- Propenso a errores
- No hay inventario

### Propuesta Terraform
```
deployment/terraform/
├── modules/                      # Módulos reutilizables
│   ├── cloud-run/
│   ├── cloud-sql/
│   └── secrets/
└── environments/
    ├── mhw-dev/
    │   └── main.tf               # 100 líneas declarativas
    ├── empresa-dev/
    │   └── main.tf               # 100 líneas declarativas
    └── empresa-qa/
        └── main.tf               # 100 líneas declarativas
```

**Características**:
- Código declarativo ("quiero esto")
- Fácil de mantener
- Robusto
- State file con inventario completo

---

## 🎯 Beneficios para Ticket Home

### 1. **Replicación de Ambientes**

Actualmente para crear un nuevo ambiente:
- ❌ Ejecutar 15+ scripts
- ❌ Modificar variables en cada script
- ❌ Esperar que nada falle

Con Terraform:
- ✅ Copiar carpeta de ambiente
- ✅ Cambiar `terraform.tfvars`
- ✅ `terraform apply`

### 2. **Disaster Recovery**

Si se cae todo:
- ❌ Ejecutar scripts manualmente uno por uno
- ❌ Recordar el orden correcto
- ❌ Rezar que funcione

Con Terraform:
- ✅ `terraform apply` y todo vuelve
- ✅ En 15 minutos todo funciona

### 3. **Auditoría**

Actualmente:
- ❌ No sabes qué recursos existen
- ❌ No sabes quién hizo qué cambio
- ❌ No puedes revertir cambios fácilmente

Con Terraform:
- ✅ `terraform state list` muestra todo
- ✅ Git muestra historial completo
- ✅ `git revert` + `terraform apply` revierte cambios

### 4. **Onboarding**

Nuevo desarrollador:
- ❌ Leer 10 READMEs
- ❌ Ejecutar 15 scripts en orden
- ❌ Debuggear errores

Con Terraform:
- ✅ `terraform apply`
- ✅ Todo funciona

---

## 📚 Recursos para Aprender

### Documentación Oficial
- https://www.terraform.io/docs
- https://registry.terraform.io/providers/hashicorp/google/latest/docs

### Tutoriales
- Terraform Getting Started: https://learn.hashicorp.com/terraform
- GCP + Terraform: https://cloud.google.com/docs/terraform

### Cursos
- HashiCorp Terraform Associate Certification

---

## ⚠️ Consideraciones Importantes

### Secrets en Terraform

**NO hacer**:
```hcl
resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = "mi-password-123"  # ❌ Nunca hardcodear secrets
}
```

**Sí hacer**:
```hcl
# Terraform solo CREA el secret, el valor se pone manualmente
resource "google_secret_manager_secret" "db_password" {
  secret_id = "database-password"
  # NO poner el valor aquí
}
```

Luego manualmente:
```bash
echo "mi-password" | gcloud secrets versions add database-password --data-file=-
```

### State File

El `terraform.tfstate` contiene información sensible:
- ❌ NO commitear a Git
- ✅ Usar backend remoto (GCS)
- ✅ Encriptar state file

---

## 🚀 Próximos Pasos

1. **Leer** `INSTRUCTIVO.md` - Paso a paso cómo usar Terraform
2. **Probar** `examples/simple-cloud-run.tf` - Ejemplo simple
3. **Revisar** `environments/mhw-dev/` - Config completa
4. **Aplicar** a tu ambiente de desarrollo

---

## 🤔 Preguntas Frecuentes

**P: ¿Reemplaza Terraform completamente los scripts?**
R: No necesariamente. Terraform maneja **infraestructura**, pero el **build de Docker** puede seguir siendo un script aparte.

**P: ¿Puedo usar Terraform y scripts juntos?**
R: Sí. Por ejemplo: Script para build + Terraform para deploy.

**P: ¿Terraform es gratis?**
R: Sí, Terraform CLI es open source y gratis. Terraform Cloud (colaboración) tiene plan gratuito y pago.

**P: ¿Qué pasa si dos personas ejecutan Terraform al mismo tiempo?**
R: Terraform usa **locking** en el state file para evitar conflictos.

**P: ¿Terraform funciona con otros clouds?**
R: Sí, AWS, Azure, Kubernetes, etc. Mismo código, diferentes providers.

---

**Creado por**: Jonathan Segura
**Fecha**: 2025-11-15
**Versión**: 1.0
