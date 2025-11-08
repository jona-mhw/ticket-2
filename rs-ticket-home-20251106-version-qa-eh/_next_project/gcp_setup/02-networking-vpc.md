# 2. Configuración de Red y VPC

Para asegurar que Cloud Run y Cloud SQL se comuniquen de forma privada y segura, es necesario configurar una red VPC y un conector de acceso a VPC sin servidor.

## 2.1. Crear una Red VPC

Aunque puedes usar la red `default`, se recomienda crear una red personalizada para aislar los recursos.

1.  En la consola de GCP, ve a **"Red de VPC"**.
2.  Haz clic en **"Crear red de VPC"**.
3.  **Nombre**: `app-vpc` (o el nombre que prefieras).
4.  **Modo de creación de subred**: `Personalizado`.
5.  **Nueva subred**:
    *   **Nombre**: `app-subnet-sawest1`
    *   **Región**: `southamerica-west1` (o la que vayas a usar).
    *   **Rango de direcciones IP**: `10.0.0.0/20` (o un rango CIDR que no se solape con otras redes).
6.  Haz clic en **"Crear"**.

## 2.2. Configurar Acceso Privado a Servicios

Para que Cloud SQL sea accesible desde la VPC, debes configurar el acceso privado a servicios.

```bash
# Asigna un rango de IPs para los servicios de Google (como Cloud SQL)
gcloud compute addresses create google-managed-services-app-vpc \
    --global \
    --purpose=VPC_PEERING \
    --addresses=10.1.0.0 \
    --prefix-length=16 \
    --description="Peering range for Google services" \
    --network=app-vpc

# Crea la conexión de peering
gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=google-managed-services-app-vpc \
    --network=app-vpc
```

## 2.3. Crear un Conector de Acceso a VPC sin Servidor

Este conector permite que tu servicio de Cloud Run se comunique con los recursos dentro de tu VPC (como la IP privada de Cloud SQL).

1.  En la consola de GCP, ve a **"Acceso a VPC sin servidor"**.
2.  Haz clic en **"Crear conector"**.
3.  **Nombre**: `app-vpc-connector`
4.  **Región**: `southamerica-west1` (la misma que tu subred).
5.  **Red**: `app-vpc`.
6.  **Subred**: `app-subnet-sawest1`.
7.  **Rango de IP**: `10.8.0.0/28` (un rango `/28` que no se use, para el conector).
8.  Haz clic en **"Crear"**. La creación puede tardar unos minutos.

Este conector se asociará a tu servicio de Cloud Run durante el despliegue.

---

**Próximo paso:** [3. Configuración de Cloud SQL con PostgreSQL](./03-cloud-sql-postgres.md)
