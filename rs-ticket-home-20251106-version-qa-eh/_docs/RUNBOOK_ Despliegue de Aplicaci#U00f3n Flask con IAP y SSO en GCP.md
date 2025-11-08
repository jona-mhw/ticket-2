# RUNBOOK: Despliegue de Aplicación Flask con IAP y SSO en GCP

Este documento es la guía maestra y el registro paso a paso para desplegar la aplicación **Ticket-Home** en un entorno de Google Cloud Platform, asegurada con IAP y SSO.

**Objetivo:** Crear un proceso replicable para futuros proyectos web basados en Flask en la organización.

---

## Estado del Despliegue

- [x] **Fase 1:** Configuración Inicial y Prerrequisitos  
- [x] **Fase 2:** Ajustes del Código y CI/CD  
- [x] **Fase 3 (Alternativa):** Despliegue con Build Local  
- [x] **Fase 4:** Despliegue en Cloud Run  
- [ ] **Fase 5:** Configuración de Red, Dominio y IAP ⬅️ **ESTAMOS AQUÍ**  
- [ ] **Fase 5:** Configuración de Red, Dominio y IAP  
- [ ] **Fase 6:** Base de Datos y Verificación Final

**Paso Actual:** Estamos en la **Fase 4**, esperando los permisos para crear el **Conector de Acceso a VPC** (`roles/vpcaccess.admin`), necesario para que Cloud Run se comunique con la base de datos de forma segura.

---

## Historial Detallado del Despliegue

### Fase 1: Configuración Inicial y Prerrequisitos

...

### Fase 2: Ajustes del Código y CI/CD

...

### Fase 3 (Alternativa): Despliegue con Build Local

...

### Fase 4: Despliegue en Cloud Run

Con la imagen en Artifact Registry, ahora la desplegamos como un servicio en Cloud Run. Este servicio se configurará como **privado**, accesible solo a través del futuro Load Balancer con IAP.

#### 4.1. Crear Conector de Acceso a VPC

- [x] **(Completado)** Crear el conector para permitir que Cloud Run acceda a la red privada de la base de datos.  
        
      **Nota:** El conector `ticket-home-connector` se creó exitosamente después de resolver los conflictos de IP y obtener los permisos necesarios.  
        
      gcloud compute networks vpc-access connectors create ticket-home-connector \`  
        
          \--network vpc-dev-ticket-home \`  
        
          \--region $env:REGION \`  
        
          \--range "10.9.0.0/28"

      #### 4.2. Ejecutar el Despliegue

- [ ] Desplegar la imagen en Cloud Run con los secretos como variables de entorno.  
        
      **Explicación:** Este comando crea el servicio en Cloud Run. `--no-allow-unauthenticated` y `--ingress=internal-and-cloud-load-balancing` son cruciales para la seguridad. Las variables de entorno se pasan con `--set-env-vars`.  
        
      gcloud run deploy $env:SERVICE\_NAME \`  
        
          \--image $env:IMAGE\_NAME \`  
        
          \--region $env:REGION \`  
        
          \--no-allow-unauthenticated \`  
        
          \--ingress=internal-and-cloud-load-balancing \`  
        
          \--vpc-connector ticket-home-connector \`  
        
          \--set-env-vars="ENABLE\_IAP=true,DATABASE\_URL=\<TU\_DATABASE\_URL\_AQUI\>,SECRET\_KEY=\<TU\_SECRET\_KEY\_AQUI\>"

---

## Fase 5: Configuración de Red, Dominio y IAP

Ahora que la aplicación funciona de forma privada, construiremos el acceso público y seguro a través de un Load Balancer con IAP.

### 5.1. Reservar y Configurar DNS

- [x] Reservar una IP que será el punto de entrada para los usuarios.  
      - **IP Reservada:** `34.50.157.116`  
- [x] Crear un registro DNS de tipo `A`.  
      - **Dominio Configurado:** `ticket-home.mhwdev.dev`

### 5.3. Crear el Load Balancer

Ahora ensamblamos el Load Balancer pieza por pieza.

### 5.4. Configurar IAP (Identity-Aware Proxy)

Ahora que el Load Balancer está montado, le añadimos la capa de seguridad de IAP.

#### 5.4.1. Configurar la Pantalla de Consentimiento de OAuth

- [ ] **(Manual)** Ir a la [Pantalla de Consentimiento de OAuth](https://console.cloud.google.com/apis/credentials/consent) y asegurarse de que esté configurada. Si es la primera vez, se debe crear una, seleccionando "Externo" y llenando los datos básicos (nombre de la app, email de soporte).

      #### 5.4.2. Crear Credenciales de Cliente OAuth 2.0

- [ ] **(Manual)** Ir a la [página de Credenciales](https://console.cloud.google.com/apis/credentials), hacer clic en "+ CREAR CREDENCIALES" y seleccionar "ID de cliente de OAuth".  
        
      - **Tipo de aplicación:** Aplicación web.  
      - **Nombre:** `ticket-home-iap-client` (o similar).  
      - **URI de redireccionamiento autorizados:** Añadir `https://iap.googleapis.com/v1/oauth/clientIds/TU_ID_DE_CLIENTE:handleRedirect` (reemplazando `TU_ID_DE_CLIENTE` con el ID que se generará).

      

- [ ] **(Crucial)** Copiar el **ID de cliente** y el **Secreto del cliente** generados.  
        
      gcloud compute forwarding-rules create ${env:SERVICE\_NAME}-forwarding-rule \--address=${env:SERVICE\_NAME}-ip \--target-https-proxy=${env:SERVICE\_NAME}-https-proxy \--global \--ports=443  
        
      gcloud compute target-https-proxies create ${env:SERVICE\_NAME}-https-proxy \--url-map=${env:SERVICE\_NAME}-url-map \--ssl-certificates=${env:SERVICE\_NAME}-ssl  
        
      gcloud compute url-maps create ${env:SERVICE\_NAME}-url-map \--default-service=${env:SERVICE\_NAME}-backend  
        
      gcloud compute backend-services add-backend ${env:SERVICE\_NAME}-backend \`  
        
          \--global \`  
        
          \--network-endpoint-group=${env:SERVICE\_NAME}-neg \`  
        
          \--network-endpoint-group-region=${env:REGION}  
        
      gcloud compute backend-services create ${env:SERVICE\_NAME}-backend \--global  
        
      gcloud compute network-endpoint-groups create ${env:SERVICE\_NAME}-neg \`  
        
          \--region=${env:REGION} \`  
        
          \--network-endpoint-type=serverless \`  
        
          \--cloud-run-service=${env:SERVICE\_NAME}  
        
      gcloud compute ssl-certificates create ${env:SERVICE\_NAME}-ssl \--domains=ticket-home.mhwdev.dev \--global

### Fase 6: Base de Datos y Verificación Final

...  
