# Terraform - Empresa DEV Environment

Configuración de Terraform para el ambiente **Empresa DEV** (RedSalud DEV).

## Características

- **Proyecto**: `dev-ticket-home-redsalud`
- **Región**: `southamerica-west1` (Chile)
- **Conexión BD**: VPC Connector (IP privada)
- **Autoscaling**: Min 1, Max 3 (siempre activo)
- **Build**: Docker Desktop (local)
- **Autenticación**: IAP + Login tradicional

## Diferencias con MHW DEV

| Aspecto | Empresa DEV | MHW DEV |
|---------|-------------|---------|
| **Proyecto** | dev-ticket-home-redsalud | ticket-home-demo |
| **Región** | southamerica-west1 🇨🇱 | us-central1 🇺🇸 |
| **Conexión BD** | VPC Connector | Cloud SQL Proxy |
| **Min Instances** | 1 (siempre activo) | 0 (escala a cero) |
| **Build** | Docker Desktop | Cloud Build |
| **Grupo IAP** | rs-ticket-home | (individual) |

## Quick Start

### 1. Configurar Variables

```bash
cd deployment/terraform/environments/empresa-dev

# Copiar archivo de ejemplo
cp terraform.tfvars.example terraform.tfvars

# Editar con tus valores
vim terraform.tfvars
```

### 2. Inicializar Terraform

```bash
terraform init
```

### 3. Ver el Plan

```bash
terraform plan
```

### 4. Aplicar

```bash
terraform apply
```

### 5. Configurar Secrets

```bash
# DATABASE_URL (con IP privada de Cloud SQL)
echo "postgresql://tickethome_user:PASSWORD@10.x.x.x:5432/tickethome_db" | \
  gcloud secrets versions add tickethome-db-url --data-file=-

# SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
  gcloud secrets versions add tickethome-secret-key --data-file=-

# SUPERUSER_EMAILS
echo "admin@redsalud.cl,otro@redsalud.cl" | \
  gcloud secrets versions add superuser-emails --data-file=-
```

### 6. Configurar DNS

```bash
# Obtener IP del Load Balancer
terraform output load_balancer_ip

# Crear registro A
# Nombre: ticket-home.mhwdev.dev
# Tipo: A
# Valor: [IP del output]
```

### 7. Verificar

```bash
# Certificado SSL (esperar ~15-30 min)
gcloud compute ssl-certificates describe ticket-home-lb-cert \
  --global \
  --project=dev-ticket-home-redsalud

# Acceder a la app
https://ticket-home.mhwdev.dev
```

## Prerequisitos de Infraestructura

⚠️ **IMPORTANTE**: Estos recursos deben existir ANTES de ejecutar Terraform:

### 1. VPC Connector

```bash
gcloud compute networks vpc-access connectors describe tckthome-conn-sa-west1 \
  --region=southamerica-west1 \
  --project=dev-ticket-home-redsalud
```

Si no existe, crear:

```bash
gcloud compute networks vpc-access connectors create tckthome-conn-sa-west1 \
  --region=southamerica-west1 \
  --network=default \
  --range=10.8.0.0/28 \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-micro \
  --project=dev-ticket-home-redsalud
```

### 2. Cloud SQL Instance

Cloud SQL debe estar creado con IP privada:

```bash
gcloud sql instances describe dev-ticket-home \
  --project=dev-ticket-home-redsalud
```

### 3. Service Account

```bash
gcloud iam service-accounts describe ticket-home-sa@dev-ticket-home-redsalud.iam.gserviceaccount.com \
  --project=dev-ticket-home-redsalud
```

Si no existe:

```bash
gcloud iam service-accounts create ticket-home-sa \
  --display-name="Ticket Home Service Account" \
  --project=dev-ticket-home-redsalud

# Dar permisos necesarios
gcloud projects add-iam-policy-binding dev-ticket-home-redsalud \
  --member="serviceAccount:ticket-home-sa@dev-ticket-home-redsalud.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding dev-ticket-home-redsalud \
  --member="serviceAccount:ticket-home-sa@dev-ticket-home-redsalud.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 4. Artifact Registry

```bash
gcloud artifacts repositories describe tickethome-repo \
  --location=southamerica-west1 \
  --project=dev-ticket-home-redsalud
```

Si no existe:

```bash
gcloud artifacts repositories create tickethome-repo \
  --repository-format=docker \
  --location=southamerica-west1 \
  --description="Docker images for Ticket Home" \
  --project=dev-ticket-home-redsalud
```

## Build de Imagen Docker

Terraform NO hace build de Docker. Debes hacer el build manualmente:

```bash
# Desde la raíz del proyecto
cd /ruta/a/ticket-2

# Autenticar con Artifact Registry
gcloud auth configure-docker southamerica-west1-docker.pkg.dev

# Build y push
docker build -t southamerica-west1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:latest .
docker push southamerica-west1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:latest

# Actualizar terraform.tfvars con el nuevo tag si cambiaste la versión
```

## Actualizar Deployment

### Cambiar Imagen Docker

```bash
# 1. Build nueva imagen
docker build -t southamerica-west1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:v1.2.3 .
docker push southamerica-west1-docker.pkg.dev/dev-ticket-home-redsalud/tickethome-repo/ticket-home:v1.2.3

# 2. Editar terraform.tfvars
vim terraform.tfvars
# Cambiar: docker_image = ".../:v1.2.3"

# 3. Aplicar
terraform apply
```

### Cambiar Configuración

```bash
# Editar main.tf o variables
vim main.tf

# Ver cambios
terraform plan

# Aplicar
terraform apply
```

## Comandos Útiles

```bash
# Ver outputs
terraform output

# Ver state
terraform show

# Listar recursos
terraform state list

# Validar
terraform validate

# Formatear
terraform fmt
```

## Troubleshooting

### Error: "VPC Connector not found"

Verifica que el VPC Connector existe:

```bash
gcloud compute networks vpc-access connectors list \
  --region=southamerica-west1 \
  --project=dev-ticket-home-redsalud
```

### Error: "Cannot connect to Cloud SQL"

Verifica que:
1. Cloud SQL tiene IP privada en la misma VPC
2. VPC Connector está en la misma red que Cloud SQL
3. Service Account tiene rol `cloudsql.client`

```bash
# Ver IP privada de Cloud SQL
gcloud sql instances describe dev-ticket-home \
  --project=dev-ticket-home-redsalud \
  --format="get(ipAddresses.ipAddress)"
```

### Error: "Secrets not accessible"

Verifica permisos del Service Account:

```bash
gcloud secrets get-iam-policy tickethome-db-url \
  --project=dev-ticket-home-redsalud
```

Debe tener:
```
members:
- serviceAccount:ticket-home-sa@dev-ticket-home-redsalud.iam.gserviceaccount.com
role: roles/secretmanager.secretAccessor
```

---

**Última actualización**: 2025-11-16
**Mantenido por**: Jonathan Segura
