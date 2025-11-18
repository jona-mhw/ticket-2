# Guía de Despliegue con Terraform

Este documento resume el flujo de trabajo para realizar despliegues usando Terraform.

## Escenario A: Solo Cambios de Código de la Aplicación

Este es el flujo más común (cambios en archivos Python, HTML, etc., pero **sin** cambios en `models.py`).

### Paso 1: Construir Nueva Imagen de Docker

Ejecuta este comando para construir la imagen con tus cambios y subirla al registro de Google:

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/ticket-home-demo/tickethome-repo/ticket-home:latest --project=ticket-home-demo --timeout=20m
```

### Paso 2: Desplegar con Terraform

Navega a la carpeta de tu ambiente y ejecuta `terraform apply`. Esto forzará un redespliegue de Cloud Run con la nueva imagen que acabas de construir.

```bash
# Navega al directorio correcto
cd terraform/environments/mhw

# Aplica los cambios para redesplegar
terraform apply
```
Terraform detectará un cambio en la anotación `timestamp` y creará una nueva revisión del servicio.

## Escenario B: Cambios en la Base de Datos (`models.py`)

Si modificas los modelos de la base de datos, necesitas generar un archivo de migración antes de construir la imagen.

### Paso 1: Generar el Archivo de Migración

Desde la raíz del proyecto y con tu ambiente virtual (`.venv`) activado, ejecuta:

```bash
# Reemplaza el mensaje con una descripción de tus cambios
flask db migrate -m "Añadida nueva columna a la tabla de usuarios"
```
Esto creará un nuevo archivo en la carpeta `migrations/versions`.

### Paso 2: Construir y Desplegar

Después de generar la migración, sigue exactamente los mismos pasos del **Escenario A**. El script `startup.sh` que corregimos se encargará de aplicar la nueva migración en la base de datos automáticamente durante el despliegue.

## ¿Cómo Resetear la Base de Datos con Datos de Prueba?

Si necesitas borrar la base de datos y llenarla con datos de prueba, puedes hacerlo controlando una variable en Terraform.

1.  **Habilita el Reset:**
    Abre el archivo `terraform/environments/mhw/terraform.tfvars` y añade o modifica la siguiente línea:
    ```terraform
    reset_db_on_startup = true
    ```

2.  **Despliega:**
    Ejecuta `terraform apply`. Durante el inicio, la aplicación borrará y re-creará la base de datos.

3.  **⚠️ Deshabilita el Reset:**
    Una vez que el despliegue termine, **es muy importante** que vuelvas a poner la variable en `false` para evitar borrar la base de datos en futuros despliegues:
    ```terraform
    reset_db_on_startup = false
    ```
    Luego, ejecuta `terraform apply` una vez más para que el servicio quede configurado sin la variable de reset.
