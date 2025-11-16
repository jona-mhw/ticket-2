# Terraform - MHW DEV Environment

Configuración de Terraform para el ambiente **MHW DEV** (tu nube personal de desarrollo).

## Características

- **Proyecto**: `ticket-home-demo`
- **Región**: `us-central1`
- **Conexión BD**: Cloud SQL Proxy (no VPC Connector)
- **Autoscaling**: Min 0, Max 3 (escala a cero para ahorrar costos)
- **Build**: Cloud Build (remoto, más rápido)
- **Autenticación**: IAP + Login tradicional

## Quick Start

### 1. Configurar Variables

```bash
cd deployment/terraform/environments/mhw-dev

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

Revisa cuidadosamente qué recursos se van a crear.

### 4. Aplicar

```bash
terraform apply
```

Escribe `yes` para confirmar.

### 5. Configurar Secrets

Los secrets se crean vacíos. Agregar valores:

```bash
# DATABASE_URL
echo "postgresql://user:pass@/cloudsql/PROJECT:REGION:INSTANCE/DB?host=/cloudsql/PROJECT:REGION:INSTANCE" | \
  gcloud secrets versions add mhw-database-url --data-file=-

# SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
  gcloud secrets versions add mhw-secret-key --data-file=-

# SUPERUSER_EMAILS
echo "tu-email@ejemplo.com" | \
  gcloud secrets versions add mhw-superuser-emails --data-file=-
```

### 6. Configurar DNS

```bash
# Obtener IP del Load Balancer
terraform output load_balancer_ip

# Crear registro A en tu DNS
# Nombre: ticket-home-beta.mhwdev.dev
# Tipo: A
# Valor: [IP del output anterior]
```

### 7. Verificar Certificado SSL

```bash
# El certificado tarda ~15-30 minutos en provisionar
gcloud compute ssl-certificates describe tickethome-demo-lb-cert \
  --global \
  --project=ticket-home-demo
```

Esperar hasta que `status: ACTIVE`.

### 8. Acceder a la App

```
https://ticket-home-beta.mhwdev.dev
```

## Actualizar Deployment

### Cambiar Imagen Docker

```bash
# Editar terraform.tfvars
vim terraform.tfvars

# Cambiar:
# docker_image = "us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:v1.2.3"

# Aplicar
terraform plan
terraform apply
```

### Cambiar Configuración

```bash
# Editar main.tf según necesites
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

# Refrescar state (sin modificar recursos)
terraform refresh

# Validar sintaxis
terraform validate

# Formatear archivos
terraform fmt
```

## Destruir Infraestructura

⚠️ **CUIDADO**: Esto elimina TODOS los recursos.

```bash
terraform destroy
```

## Diferencias con Deployment Manual

| Aspecto | Scripts Actuales | Terraform |
|---------|------------------|-----------|
| **Método** | gcloud commands en shell | Declarativo (HCL) |
| **Idempotencia** | ❌ Difícil | ✅ Garantizada |
| **State** | ❌ No existe | ✅ terraform.tfstate |
| **Plan** | ❌ No hay preview | ✅ terraform plan |
| **Rollback** | ❌ Manual | ✅ Fácil (git revert) |
| **Reutilizable** | ❌ Hardcoded | ✅ Módulos |
| **Equipo** | ❌ Difícil colaborar | ✅ State compartido |

## Troubleshooting

### Error: "Secrets not found"

Los secrets se crean vacíos. Debes agregar valores manualmente (ver paso 5).

### Error: "Certificate provisioning failed"

Verifica que DNS apunta correctamente a la IP del Load Balancer:

```bash
dig ticket-home-beta.mhwdev.dev +short
# Debe mostrar la IP del terraform output
```

### Error: "Backend initialization required"

```bash
terraform init -reconfigure
```

### Ver qué cambió desde último apply

```bash
terraform plan -detailed-exitcode
# Exit code:
# 0 = sin cambios
# 1 = error
# 2 = hay cambios pendientes
```

## State Management

### Backend Local (Default)

Por default, el state se guarda en `terraform.tfstate` localmente.

⚠️ **Problema**: Si trabajas en equipo o desde múltiples computadoras, el state se desincroniza.

### Backend Remoto (Recomendado)

1. Crear bucket para state:

```bash
gcloud storage buckets create gs://ticket-home-terraform-state \
  --project=ticket-home-demo \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://ticket-home-terraform-state \
  --versioning
```

2. Editar `backend.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket = "ticket-home-terraform-state"
    prefix = "environments/mhw-dev"
  }
}
```

3. Migrar state:

```bash
terraform init -migrate-state
```

✅ **Beneficios**:
- State compartido entre equipo
- Versionado automático
- Locking (evita conflictos)
- Backup automático

## Próximos Pasos

1. ✅ Revisar el `terraform.tfvars.example`
2. ✅ Crear tu `terraform.tfvars` con valores reales
3. ✅ Ejecutar `terraform init`
4. ✅ Revisar `terraform plan`
5. ✅ Aplicar con `terraform apply`
6. ✅ Agregar valores a secrets
7. ✅ Configurar DNS
8. ✅ Esperar certificado SSL
9. ✅ Acceder a la app

---

**Última actualización**: 2025-11-16
**Mantenido por**: Jonathan Segura
