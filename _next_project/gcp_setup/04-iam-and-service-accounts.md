# 4. Configuración de IAM y Cuentas de Servicio

La seguridad se basa en el principio de mínimo privilegio. Crearemos una cuenta de servicio dedicada para nuestro servicio de Cloud Run con los permisos justos y necesarios.

## 4.1. Crear una Cuenta de Servicio

1.  En la consola de GCP, ve a **"IAM y administración" > "Cuentas de servicio"**.
2.  Haz clic en **"Crear cuenta de servicio"**.
3.  **Nombre de la cuenta de servicio**: `app-runner` (o un nombre descriptivo).
4.  **ID de la cuenta de servicio**: Se generará automáticamente.
5.  **Descripción**: "Cuenta de servicio para el despliegue de la aplicación en Cloud Run".
6.  Haz clic en **"Crear y continuar"**.

## 4.2. Asignar Roles a la Cuenta de Servicio

En el paso **"Conceder a esta cuenta de servicio acceso al proyecto"**, asigna los siguientes roles:

1.  **Cloud SQL Client (`roles/cloudsql.client`)**: Permite a la cuenta de servicio conectarse a la instancia de Cloud SQL a través del proxy o IP privada.
2.  **Secret Manager Secret Accessor (`roles/secretmanager.secretAccessor`)**: Permite acceder al valor de los secretos (como la URL de la base de datos).
3.  **(Opcional) Storage Object Viewer (`roles/storage.objectViewer`)**: Si la aplicación necesita leer archivos de buckets de Cloud Storage.

Haz clic en **"Continuar"** y luego en **"Listo"**.

## 4.3. Permisos Adicionales para el Despliegue

El usuario o la cuenta de servicio que ejecute el despliegue (por ejemplo, desde tu máquina local con `gcloud` o en un pipeline de CI/CD) necesita permisos para actuar como la cuenta de servicio que acabas de crear.

1.  Ve a **"IAM y administración" > "IAM"**.
2.  Busca la cuenta de servicio `app-runner`.
3.  Ve a la pestaña **"Permisos"**.
4.  Busca el principal (tu email de usuario o la cuenta de servicio de Cloud Build) y asígnale el rol **"Usuario de cuenta de servicio" (`roles/iam.serviceAccountUser`)**.

Esto permite al principal "adjuntar" la cuenta de servicio `app-runner` al nuevo servicio de Cloud Run durante el despliegue.

---

**Próximo paso:** [5. Configuración de IAP y SSO](./05-iap-and-sso-setup.md)
