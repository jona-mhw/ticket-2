# Runbook de Despliegue

Esta guía detalla el proceso de despliegue manual de la aplicación Flask en Cloud Run.

## Prerrequisitos

1.  **Infraestructura de GCP creada**: Todos los pasos de la guía `gcp_setup` deben estar completados.
2.  **`gcloud` CLI configurado**: Autenticado y apuntando al `PROJECT_ID` correcto.
3.  **Docker instalado**: Docker Desktop o Docker Engine debe estar en ejecución.
4.  **Código fuente listo**: Tu aplicación Flask debe estar finalizada y probada localmente.

## Flujo de Despliegue

El despliegue se realiza en 3 fases:
1.  **Construir (Build)**: Crear la imagen de Docker.
2.  **Empujar (Push)**: Subir la imagen a Artifact Registry.
3.  **Desplegar (Deploy)**: Crear o actualizar el servicio en Cloud Run.

---

### Fase 1: Construir la Imagen de Docker

Navega a la raíz de tu proyecto (donde se encuentra el `Dockerfile`) y ejecuta el siguiente comando:

```bash
# Variables
export PROJECT_ID="tu-project-id-gcp"
export REGION="southamerica-west1" # O la región de tu Artifact Registry
export REPO_NAME="app-repo" # El nombre de tu repositorio en Artifact Registry
export IMAGE_NAME="mi-nueva-app"
export TAG="latest" # O una etiqueta de versión, ej: v1.0.0

# Nombre completo de la imagen
export FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${TAG}"

# Comando de construcción
docker build -t $FULL_IMAGE_NAME .
```

### Fase 2: Empujar la Imagen a Artifact Registry

Antes del primer `push`, necesitas configurar Docker para que se autentique con Artifact Registry:

```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

Luego, empuja la imagen que construiste:

```bash
docker push $FULL_IMAGE_NAME
```

### Fase 3: Desplegar en Cloud Run

Este es el paso más complejo. El comando `gcloud run deploy` tiene muchas opciones.

#### Despliegue Inicial (o con Cambios en la DB)

Este despliegue se realiza en **dos pasos** para resetear la base de datos de forma segura.

**Paso 1: Desplegar con `RESET_DB_ON_STARTUP=true`**

Este comando crea el servicio y lo fuerza a ejecutar el reseteo de la base de datos al iniciar.

```bash
# Variables del servicio
SERVICE_NAME="mi-nueva-app"
SERVICE_ACCOUNT="app-runner@${PROJECT_ID}.iam.gserviceaccount.com"
VPC_CONNECTOR="app-vpc-connector"
DB_INSTANCE="tu-project-id-gcp:southamerica-west1:app-postgres-db"

# Despliegue
gcloud run deploy $SERVICE_NAME \
  --image=$FULL_IMAGE_NAME \
  --region=$REGION \
  --service-account=$SERVICE_ACCOUNT \
  --vpc-connector=$VPC_CONNECTOR \
  --vpc-egress=private-ranges-only \
  --no-allow-unauthenticated \
  --ingress=internal-and-cloud-load-balancing \
  --add-cloudsql-instances=$DB_INSTANCE \
  --port=8080 \
  --timeout=300 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=3 \
  --concurrency=80 \
  --set-env-vars="FLASK_ENV=production,RESET_DB_ON_STARTUP=true" \
  --set-secrets="DATABASE_URL=database-url:latest,SECRET_KEY=secret-key:latest"
```

**Paso 2: Permitir tráfico y Desplegar con `RESET_DB_ON_STARTUP=false`**

Una vez que el servicio se crea, debes permitir que reciba tráfico desde el balanceador de carga (protegido por IAP) y luego redesplegar inmediatamente con la variable de reseteo en `false` para que la base de datos no se borre en cada reinicio.

```bash
# Permitir tráfico (solo la primera vez)
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region=$REGION \
  --member="allUsers" \
  --role="roles/run.invoker"

# Redesplegar para persistir la DB
gcloud run deploy $SERVICE_NAME \
  --image=$FULL_IMAGE_NAME \
  --region=$REGION \
  --set-env-vars="FLASK_ENV=production,RESET_DB_ON_STARTUP=false"
```

#### Despliegue Normal (sin cambios en la DB)

Si solo has cambiado el código de la aplicación y no el modelo de datos, el despliegue es más simple:

```bash
gcloud run deploy $SERVICE_NAME \
  --image=$FULL_IMAGE_NAME \
  --region=$REGION \
  --set-env-vars="FLASK_ENV=production,RESET_DB_ON_STARTUP=false"
```

*(Se asume que los demás parámetros no han cambiado)*.

---

## Verificación Post-Despliegue

1.  **Accede a la URL de la aplicación**: Deberías ser redirigido a la pantalla de login de Google.
2.  **Revisa los logs**:
    ```bash
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" --project=${PROJECT_ID} --limit=50 --freshness=10m
    ```
3.  **Verifica la conexión a la base de datos**: En los logs de inicio, deberías ver los mensajes de `startup.sh` confirmando la conexión.
