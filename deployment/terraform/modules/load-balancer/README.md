# Módulo Terraform: Load Balancer + IAP + SSL

Módulo completo para crear un Load Balancer HTTPS con Cloud Run backend, certificado SSL administrado e Identity-Aware Proxy.

## Features

- ✅ IP estática global
- ✅ Certificado SSL administrado (Let's Encrypt automático)
- ✅ Backend a Cloud Run (Serverless NEG)
- ✅ Identity-Aware Proxy (IAP) configurado
- ✅ Redirección HTTP → HTTPS automática
- ✅ Cloud CDN (opcional)
- ✅ Logging configurable

## Uso Básico

```hcl
module "load_balancer" {
  source = "../../modules/load-balancer"

  project_id = "mi-proyecto"
  lb_name    = "tickethome-lb"

  domains = ["ticket-home.mhwdev.dev"]

  # Cloud Run backend
  cloud_run_service_name = "ticket-home"
  cloud_run_region       = "us-central1"

  # IAP
  enable_iap               = true
  iap_oauth_client_id      = "123456789-xxx.apps.googleusercontent.com"
  iap_oauth_client_secret  = var.iap_client_secret  # Desde variable

  iap_access_members = [
    "user:jonathan@mhwdev.dev",
    "group:ticket-home@googlegroups.com"
  ]
}
```

## Configuración DNS

Después de crear el Load Balancer, debes configurar DNS:

```bash
# 1. Obtener la IP del Load Balancer
terraform output lb_ip_address
# Output: 34.120.45.67

# 2. Crear registro A en tu DNS
# Nombre: ticket-home.mhwdev.dev
# Tipo: A
# Valor: 34.120.45.67
```

**Verificar certificado SSL**:
```bash
# El certificado tarda ~15-30 minutos en provisionar
gcloud compute ssl-certificates describe tickethome-lb-cert \
  --global \
  --project=mi-proyecto
```

Estado esperado:
```
status: ACTIVE
domainStatus:
  ticket-home.mhwdev.dev: ACTIVE
```

## Ejemplo Completo con IAP

```hcl
# 1. Crear secret para IAP client secret
module "iap_secret" {
  source = "../../modules/secrets"

  project_id = "mi-proyecto"
  secret_id  = "iap-oauth-client-secret"
}

# Agregar valor manualmente:
# echo "TU_CLIENT_SECRET" | gcloud secrets versions add iap-oauth-client-secret --data-file=-

# 2. Obtener el client secret desde Secret Manager (data source)
data "google_secret_manager_secret_version" "iap_secret" {
  secret  = module.iap_secret.secret_name
  version = "latest"
}

# 3. Crear Load Balancer con IAP
module "load_balancer" {
  source = "../../modules/load-balancer"

  project_id = "mi-proyecto"
  lb_name    = "tickethome-lb"

  domains = ["ticket-home.mhwdev.dev"]

  cloud_run_service_name = module.cloud_run.service_name
  cloud_run_region       = "us-central1"

  enable_iap = true
  iap_oauth_client_id      = "123456-xxx.apps.googleusercontent.com"
  iap_oauth_client_secret  = data.google_secret_manager_secret_version.iap_secret.secret_data

  iap_access_members = [
    "user:jonathan@mhwdev.dev",
    "group:ticket-home@googlegroups.com"
  ]

  redirect_http_to_https = true
}
```

## Ejemplo sin IAP (Desarrollo)

```hcl
module "load_balancer" {
  source = "../../modules/load-balancer"

  project_id = "mi-proyecto"
  lb_name    = "tickethome-dev-lb"

  domains = ["dev.ticket-home.mhwdev.dev"]

  cloud_run_service_name = "ticket-home-dev"
  cloud_run_region       = "us-central1"

  # Deshabilitar IAP para desarrollo
  enable_iap = false

  redirect_http_to_https = true
}
```

## Ejemplo con CDN

```hcl
module "load_balancer" {
  source = "../../modules/load-balancer"

  project_id = "mi-proyecto"
  lb_name    = "tickethome-lb"

  domains = ["ticket-home.mhwdev.dev"]

  cloud_run_service_name = "ticket-home"
  cloud_run_region       = "us-central1"

  # Habilitar CDN
  enable_cdn = true

  # Configurar IAP
  enable_iap              = true
  iap_oauth_client_id     = var.iap_client_id
  iap_oauth_client_secret = var.iap_client_secret

  iap_access_members = [
    "group:ticket-home@googlegroups.com"
  ]
}
```

## Variables

| Variable | Descripción | Tipo | Default | Requerido |
|----------|-------------|------|---------|-----------|
| `project_id` | ID del proyecto GCP | string | - | ✅ |
| `lb_name` | Nombre base del LB | string | - | ✅ |
| `domains` | Lista de dominios | list(string) | - | ✅ |
| `cloud_run_service_name` | Nombre del servicio Cloud Run | string | - | ✅ |
| `cloud_run_region` | Región del Cloud Run | string | - | ✅ |
| `enable_iap` | Habilitar IAP | bool | true | ❌ |
| `iap_oauth_client_id` | OAuth Client ID | string | "" | Condicional* |
| `iap_oauth_client_secret` | OAuth Client Secret | string | "" | Condicional* |
| `iap_access_members` | Members con acceso IAP | list(string) | [] | ❌ |
| `enable_cdn` | Habilitar CDN | bool | false | ❌ |
| `redirect_http_to_https` | Redirect HTTP→HTTPS | bool | true | ❌ |

\* Requerido si `enable_iap = true`

## Outputs

| Output | Descripción |
|--------|-------------|
| `lb_ip_address` | IP pública del Load Balancer |
| `ssl_certificate_status` | Estado del certificado SSL |
| `backend_service_name` | Nombre del backend service |
| `dns_instructions` | Instrucciones para DNS |

## Configurar OAuth Client para IAP

### Paso 1: Crear OAuth Client

```bash
# Ve a: Cloud Console → APIs & Services → Credentials
# Click: Create Credentials → OAuth 2.0 Client ID

# Tipo: Web application
# Nombre: tickethome-iap
# Authorized redirect URIs:
#   https://iap.googleapis.com/v1/oauth/clientIds/YOUR_CLIENT_ID:handleRedirect
```

### Paso 2: Guardar Credenciales

```bash
# Client ID (público, puede ir en terraform.tfvars)
CLIENT_ID="123456789-xxx.apps.googleusercontent.com"

# Client Secret (sensible, va a Secret Manager)
echo "YOUR_CLIENT_SECRET" | \
  gcloud secrets versions add iap-oauth-client-secret --data-file=-
```

### Paso 3: Configurar IAP Access

```hcl
iap_access_members = [
  # Usuarios individuales
  "user:jonathan@mhwdev.dev",
  "user:maria@redsalud.cl",

  # Grupos de Google
  "group:ticket-home@googlegroups.com",

  # Service Accounts
  "serviceAccount:ci-cd@mi-proyecto.iam.gserviceaccount.com"
]
```

## Verificación Post-Deployment

### 1. Verificar IP

```bash
terraform output lb_ip_address
# 34.120.45.67
```

### 2. Verificar Certificado SSL

```bash
gcloud compute ssl-certificates describe CERT_NAME \
  --global \
  --project=mi-proyecto

# Esperar hasta que status sea ACTIVE
```

### 3. Probar HTTP → HTTPS Redirect

```bash
curl -I http://ticket-home.mhwdev.dev
# HTTP/1.1 301 Moved Permanently
# Location: https://ticket-home.mhwdev.dev/
```

### 4. Verificar IAP

```bash
curl -I https://ticket-home.mhwdev.dev
# HTTP/2 302
# location: https://accounts.google.com/...
```

## Troubleshooting

### Error: "Certificate provisioning failed"

**Causa**: DNS no apunta correctamente a la IP del LB

**Solución**:
```bash
# 1. Verificar IP del LB
terraform output lb_ip_address

# 2. Verificar DNS
dig ticket-home.mhwdev.dev +short
# Debe mostrar la IP del paso 1

# 3. Esperar 15-30 min para que el certificado se provisione
```

### Error: "IAP not working"

**Causa**: OAuth client mal configurado

**Solución**:
1. Verificar que el Client ID y Secret son correctos
2. Verificar redirect URI en OAuth client
3. Verificar que los members tienen el rol correcto

### Error: "Backend unhealthy"

**Causa**: Cloud Run no está accesible

**Solución**:
```bash
# Verificar que Cloud Run está corriendo
gcloud run services describe ticket-home \
  --region=us-central1 \
  --project=mi-proyecto

# Verificar IAM bindings
gcloud run services get-iam-policy ticket-home \
  --region=us-central1 \
  --project=mi-proyecto
```

## Notas

- **Certificado SSL**: Tarda 15-30 minutos en provisionar después de configurar DNS
- **Multi-domain**: Puedes agregar múltiples dominios en la lista `domains`
- **IAP + CDN**: IAP funciona con CDN, pero el contenido autenticado no se cachea
- **Costos**: Load Balancer tiene costo base (~$18/mes) + por GB transferido
