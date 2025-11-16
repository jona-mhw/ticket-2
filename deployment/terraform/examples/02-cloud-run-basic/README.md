# Ejemplo 02: Cloud Run Basic

Crea un Cloud Run service simple con la imagen hello-world de Google.

## Qué aprenderás

- ✅ Crear un Cloud Run service
- ✅ Configurar recursos (CPU, memoria)
- ✅ Hacer un servicio público
- ✅ Ver la URL del servicio
- ✅ Referencias entre recursos

## Paso a Paso

### 1. Configurar Variables

```bash
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars
```

### 2. Inicializar y Aplicar

```bash
terraform init
terraform plan
terraform apply
```

### 3. Ver Outputs

```bash
terraform output

# Solo la URL
terraform output service_url
```

**Output esperado**:
```
service_url = "https://hello-terraform-abc123-uc.a.run.app"
```

### 4. Probar el Servicio

```bash
# Con curl
curl $(terraform output -raw service_url)

# En el navegador
# Abrir la URL del output
```

**Respuesta esperada**:
```
Hello World!

This is a sample response from Cloud Run.
```

### 5. Ver en GCP Console

```bash
# URL del Console
echo "https://console.cloud.google.com/run/detail/$(terraform output -raw service_location)/$(terraform output -raw service_name)"
```

### 6. Modificar Recursos

Edita `main.tf` y cambia la memoria:

```hcl
resources {
  limits = {
    cpu    = "1"
    memory = "1Gi"  # <- Cambiar de 512Mi a 1Gi
  }
}
```

Aplica el cambio:

```bash
terraform plan
terraform apply
```

**Nota**: Esto crea una nueva revisión de Cloud Run.

### 7. Ver Revisiones

```bash
gcloud run revisions list \
  --service=hello-terraform \
  --region=$(terraform output -raw service_location)
```

**Output**:
```
REVISION                  ACTIVE  SERVICE           TRAFFIC  DEPLOYED
hello-terraform-00002-abc ✓       hello-terraform   100      2025-11-16 10:45:00
hello-terraform-00001-xyz         hello-terraform   0        2025-11-16 10:30:00
```

### 8. Destruir

```bash
terraform destroy
```

## Conceptos Aprendidos

### 1. Cloud Run Service

```hcl
resource "google_cloud_run_service" "hello" {
  name     = "hello-terraform"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/cloudrun/hello"
        # ...
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
```

**Estructura**:
- `name`: nombre único del servicio
- `location`: región de deployment
- `template`: configuración del contenedor
- `traffic`: distribución de tráfico

### 2. Container Spec

```hcl
containers {
  image = "gcr.io/cloudrun/hello"

  resources {
    limits = {
      cpu    = "1"
      memory = "512Mi"
    }
  }

  ports {
    container_port = 8080
  }
}
```

**Configuración**:
- `image`: imagen Docker (puede ser pública o privada)
- `resources.limits`: CPU y memoria
- `ports`: puerto del contenedor (Cloud Run asume 8080 si no se especifica)

### 3. IAM Policy Binding

```hcl
resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_service.hello.location
  service  = google_cloud_run_service.hello.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

**Qué hace**:
- Otorga rol `run.invoker` a `allUsers`
- Hace el servicio accesible sin autenticación
- **Producción**: usar IAP en vez de `allUsers`

### 4. Referencias entre Recursos

```hcl
google_cloud_run_service.hello.location
google_cloud_run_service.hello.name
google_cloud_run_service.hello.status[0].url
```

**Cómo funciona**:
- Terraform crea un grafo de dependencias
- Recursos se crean en orden correcto
- Si un recurso falla, los dependientes no se crean

### 5. Atributos Computados

Algunos atributos solo se conocen después de crear el recurso:

```hcl
google_cloud_run_service.hello.status[0].url  # URL generada por Cloud Run
google_cloud_run_service.hello.id             # ID del recurso
```

**Durante plan**:
```
+ url = (known after apply)
```

**Después de apply**:
```
url = "https://hello-terraform-abc123-uc.a.run.app"
```

## Experimentar

### Cambiar la Imagen

Prueba con otra imagen pública:

```hcl
image = "gcr.io/google-samples/hello-app:1.0"
```

### Cambiar Recursos

```hcl
resources {
  limits = {
    cpu    = "2"      # Más CPU
    memory = "1Gi"    # Más memoria
  }
}
```

### Agregar Variables de Entorno

```hcl
containers {
  image = "gcr.io/cloudrun/hello"

  env {
    name  = "MY_VAR"
    value = "hello"
  }

  # ... resto
}
```

### Agregar Autoscaling

```hcl
template {
  metadata {
    annotations = {
      "autoscaling.knative.dev/minScale" = "0"
      "autoscaling.knative.dev/maxScale" = "3"
    }
  }

  spec {
    # ... containers
  }
}
```

## Troubleshooting

### Error: "Service already exists"

Si el servicio ya existe fuera de Terraform:

```bash
# Opción 1: Importar
terraform import google_cloud_run_service.hello projects/PROJECT_ID/locations/REGION/services/hello-terraform

# Opción 2: Eliminar y recrear
gcloud run services delete hello-terraform --region=us-central1
terraform apply
```

### Error: "Permission denied"

Verifica que tu cuenta tenga el rol:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:tu-email@example.com" \
  --role="roles/run.admin"
```

### Servicio no accesible

Verifica la IAM policy:

```bash
gcloud run services get-iam-policy hello-terraform \
  --region=us-central1
```

Debe incluir:
```yaml
bindings:
- members:
  - allUsers
  role: roles/run.invoker
```

## Próximos Pasos

✅ Completaste el Ejemplo 02!

Ahora tienes un Cloud Run funcionando. Prueba:
- [Ejemplo 03: Cloud Run with Secret](../03-cloud-run-with-secret/)

---

**Tiempo estimado**: 15 minutos
