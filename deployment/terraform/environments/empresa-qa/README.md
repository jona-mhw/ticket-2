# Terraform - Empresa QA Environment

Configuración de Terraform para el ambiente **Empresa QA** (RedSalud QA - Pre-producción).

## Características

- **Proyecto**: `qa-ticket-home-redsalud`
- **Región**: `southamerica-west1` (Chile)
- **Conexión BD**: VPC Connector (IP privada)
- **Autoscaling**: Min 1, Max 3 (siempre activo)
- **Build**: Docker Desktop (local)
- **Autenticación**: **SOLO SSO** ⚠️ (sin login tradicional)

## ⚠️ Diferencias Críticas con DEV

| Aspecto | Empresa QA | Empresa DEV |
|---------|------------|-------------|
| **Proyecto** | qa-ticket-home-redsalud | dev-ticket-home-redsalud |
| **Autenticación** | **Solo SSO** ⚠️ | SSO + Login tradicional |
| **Grupo Google** | qa-ticket-home-rs | rs-ticket-home |
| **Propósito** | Pre-producción | Testing funcional |
| **ENABLE_DEMO_LOGIN** | `false` | `true` |

**QA debe ser lo más cercano posible a producción**, por eso no tiene login tradicional.

## Quick Start

### 1. Configurar Variables

```bash
cd deployment/terraform/environments/empresa-qa

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
echo "admin@redsalud.cl,qa-lead@redsalud.cl" | \
  gcloud secrets versions add superuser-emails --data-file=-
```

### 6. Configurar DNS

```bash
# Obtener IP del Load Balancer
terraform output load_balancer_ip

# Crear registro A
# Nombre: qa-ticket-home.mhwdev.dev
# Tipo: A
# Valor: [IP del output]
```

### 7. Verificar

```bash
# Certificado SSL (esperar ~15-30 min)
gcloud compute ssl-certificates describe ticket-home-lb-cert \
  --global \
  --project=qa-ticket-home-redsalud

# Acceder a la app (SOLO vía SSO)
https://qa-ticket-home.mhwdev.dev
```

## Prerequisitos de Infraestructura

⚠️ **IMPORTANTE**: Estos recursos deben existir ANTES de ejecutar Terraform:

### 1. VPC Connector (QA)

```bash
gcloud compute networks vpc-access connectors describe tckthome-conn-qa-sa-west1 \
  --region=southamerica-west1 \
  --project=qa-ticket-home-redsalud
```

Si no existe:

```bash
gcloud compute networks vpc-access connectors create tckthome-conn-qa-sa-west1 \
  --region=southamerica-west1 \
  --network=default \
  --range=10.9.0.0/28 \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-micro \
  --project=qa-ticket-home-redsalud
```

### 2. Cloud SQL Instance (QA)

```bash
gcloud sql instances describe qa-ticket-home \
  --project=qa-ticket-home-redsalud
```

### 3. Service Account (QA)

```bash
gcloud iam service-accounts describe ticket-home-sa@qa-ticket-home-redsalud.iam.gserviceaccount.com \
  --project=qa-ticket-home-redsalud
```

### 4. Artifact Registry (QA)

```bash
gcloud artifacts repositories describe tickethome-repo \
  --location=southamerica-west1 \
  --project=qa-ticket-home-redsalud
```

### 5. Grupo Google para IAP

**Grupo específico de QA**: `qa-ticket-home-rs@googlegroups.com`

Miembros deben ser agregados manualmente al grupo.

## Build de Imagen Docker

```bash
# Desde la raíz del proyecto
cd /ruta/a/ticket-2

# Autenticar
gcloud auth configure-docker southamerica-west1-docker.pkg.dev

# Build y push a QA
docker build -t southamerica-west1-docker.pkg.dev/qa-ticket-home-redsalud/tickethome-repo/ticket-home:latest .
docker push southamerica-west1-docker.pkg.dev/qa-ticket-home-redsalud/tickethome-repo/ticket-home:latest
```

## Checklist de Testing en QA

Antes de aprobar para producción, verificar:

- [ ] Aplicación carga sin errores
- [ ] **Solo SSO funciona** (no hay login tradicional disponible)
- [ ] Dashboard muestra datos correctos
- [ ] Panel de enfermería funciona
- [ ] Exportaciones funcionan (PDF, Excel)
- [ ] Búsqueda funciona
- [ ] Formularios validan correctamente
- [ ] Performance aceptable (< 2s carga inicial)
- [ ] No hay errores en logs
- [ ] Usuarios correctos en tabla `superuser`
- [ ] Redirección HTTP → HTTPS funciona
- [ ] Certificado SSL válido

## Comandos de Verificación

```bash
# 1. Cloud Run está corriendo
gcloud run services describe ticket-home \
  --region=southamerica-west1 \
  --project=qa-ticket-home-redsalud

# 2. Logs recientes
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --project=qa-ticket-home-redsalud

# 3. Estado del Load Balancer
gcloud compute backend-services describe ticket-home-lb-backend \
  --global \
  --project=qa-ticket-home-redsalud

# 4. Verificar acceso IAP
gcloud iap web get-iam-policy ticket-home-lb-backend \
  --project=qa-ticket-home-redsalud

# 5. Probar endpoint
curl -I https://qa-ticket-home.mhwdev.dev
# Debe redirigir a Google login (IAP)
```

## Promoción a Producción

Una vez que QA está aprobado:

1. **Tag de versión**:

```bash
# Tagear la imagen Docker
docker tag \
  southamerica-west1-docker.pkg.dev/qa-ticket-home-redsalud/tickethome-repo/ticket-home:latest \
  southamerica-west1-docker.pkg.dev/PROD-PROJECT/tickethome-repo/ticket-home:v1.0.0

docker push southamerica-west1-docker.pkg.dev/PROD-PROJECT/tickethome-repo/ticket-home:v1.0.0
```

2. **Crear environment de producción**:

```bash
# Copiar configuración de QA a producción
cp -r deployment/terraform/environments/empresa-qa \
      deployment/terraform/environments/empresa-prod

# Editar valores de producción
cd deployment/terraform/environments/empresa-prod
vim terraform.tfvars
```

3. **Aplicar en producción**:

```bash
terraform init
terraform plan
terraform apply
```

## Troubleshooting

### Error: "403 Forbidden" en la app

**Causa**: Usuario no está en el grupo QA.

**Solución**: Verificar membresía en `qa-ticket-home-rs@googlegroups.com`

### Error: "No demo login available"

**Causa**: QA no tiene login tradicional (esperado).

**Solución**: Usar solo SSO. Si necesitas login tradicional, usa Empresa DEV en su lugar.

### Error: "VPC Connector QA not found"

Verifica el nombre correcto del VPC Connector de QA:

```bash
gcloud compute networks vpc-access connectors list \
  --region=southamerica-west1 \
  --project=qa-ticket-home-redsalud
```

## Rollback

Si necesitas rollback a versión anterior:

```bash
# 1. Cambiar tag de imagen en terraform.tfvars
vim terraform.tfvars
# docker_image = ".../ticket-home:v1.0.0" (versión anterior)

# 2. Aplicar
terraform apply

# 3. Verificar
gcloud run revisions list \
  --service=ticket-home \
  --region=southamerica-west1 \
  --project=qa-ticket-home-redsalud
```

---

**Última actualización**: 2025-11-16
**Mantenido por**: Jonathan Segura
