# 1. Configuración del Proyecto en GCP

Antes de desplegar la aplicación, es fundamental configurar correctamente el proyecto en Google Cloud Platform.

## 1.1. Crear un Nuevo Proyecto

1.  Ve a la [Consola de GCP](https://console.cloud.google.com/).
2.  En el selector de proyectos, haz clic en **"Proyecto Nuevo"**.
3.  Asigna un nombre al proyecto (ej. `mi-nueva-app-produccion`).
4.  Selecciona una organización y ubicación si es aplicable.
5.  Haz clic en **"Crear"**.

## 1.2. Habilitar APIs Requeridas

Para que la aplicación funcione, necesitas habilitar las siguientes APIs en tu nuevo proyecto. Puedes hacerlo usando `gcloud` o desde la consola.

```bash
# Reemplaza [PROJECT_ID] con el ID de tu proyecto
gcloud config set project [PROJECT_ID]

# Habilitar las APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iap.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com
```

**APIs y su propósito:**

-   **Cloud Run API (`run.googleapis.com`)**: Para desplegar la aplicación serverless.
-   **Cloud SQL Admin API (`sqladmin.googleapis.com`)**: Para gestionar la base de datos PostgreSQL.
-   **Secret Manager API (`secretmanager.googleapis.com`)**: Para almacenar de forma segura las credenciales.
-   **Artifact Registry API (`artifactregistry.googleapis.com`)**: Para almacenar las imágenes de Docker.
-   **Cloud Build API (`cloudbuild.googleapis.com`)**: (Opcional, para CI/CD) Para construir las imágenes de Docker automáticamente.
-   **Identity-Aware Proxy (IAP) API (`iap.googleapis.com`)**: Para la autenticación y SSO.
-   **Compute Engine API (`compute.googleapis.com`)**: Necesaria para el balanceador de carga y networking.
-   **Service Networking API (`servicenetworking.googleapis.com`)**: Para la conexión privada entre Cloud Run y Cloud SQL.

## 1.3. Configurar la Facturación

Asegúrate de que el proyecto esté vinculado a una cuenta de facturación activa. Sin esto, no podrás utilizar los servicios de GCP.

1.  En el menú de navegación, ve a **"Facturación"**.
2.  Si el proyecto no tiene una cuenta de facturación, se te pedirá que vincules una.

## 1.4. Instalar y Configurar gcloud CLI

Si aún no lo has hecho, instala el [SDK de Google Cloud](https://cloud.google.com/sdk/docs/install) en tu máquina local.

Luego, autentícate e inicializa el SDK:

```bash
# Iniciar sesión con tu cuenta de Google
gcloud auth login

# Configurar el proyecto por defecto
gcloud config set project [PROJECT_ID]

# (Opcional) Configurar la región por defecto
gcloud config set run/region southamerica-west1
gcloud config set compute/region southamerica-west1
```

---

**Próximo paso:** [2. Configuración de Red y VPC](./02-networking-vpc.md)
