# 5. Configuración de IAP y SSO

Identity-Aware Proxy (IAP) es el núcleo de nuestra estrategia de autenticación. Actúa como una barrera que verifica la identidad del usuario antes de que el tráfico llegue a la aplicación.

## 5.1. Configurar la Pantalla de Consentimiento de OAuth

Antes de usar IAP, debes configurar la pantalla de consentimiento.

1.  En la consola de GCP, ve a **"APIs y servicios" > "Pantalla de consentimiento de OAuth"**.
2.  **Tipo de usuario**: `Interno`. Esto restringe el acceso solo a los usuarios dentro de tu organización de Google Workspace.
3.  **Información de la aplicación**:
    *   **Nombre de la aplicación**: El nombre que verán los usuarios al autenticarse (ej. "Mi Aplicación Corporativa").
    *   **Correo electrónico de asistencia al usuario**: Tu correo o el de un grupo de soporte.
4.  Guarda los cambios.

## 5.2. Crear un Balanceador de Carga HTTPS

IAP se adjunta a un backend de un balanceador de carga.

1.  En la consola de GCP, ve a **"Servicios de red" > "Balanceo de cargas"**.
2.  Haz clic en **"Crear balanceador de cargas"**.
3.  Elige **"Balanceador de cargas de aplicaciones (HTTP/S)"** y haz clic en **"Iniciar configuración"**.
4.  **De Internet a mis VMs o servicios sin servidor**: Selecciona esta opción.
5.  **Nombre del balanceador**: `app-lb`.
6.  **Configuración de frontend**:
    *   **Protocolo**: `HTTPS`.
    *   **Dirección IP**: Crea una nueva dirección IP estática (ej. `app-lb-ip`).
    *   **Certificado**: Crea un certificado gestionado por Google. Necesitarás un dominio verificado para esto.
7.  **Configuración de backend**:
    *   Crea un **"Servicio de backend"**.
    *   **Tipo de backend**: `Grupo de extremos de red sin servidor (Serverless NEG)`.
    *   En la sección **"Backends"**, crea un nuevo NEG sin servidor y asócialo a tu servicio de Cloud Run (lo podrás hacer después del primer despliegue).
8.  Sigue los pasos para crear el balanceador.

## 5.3. Habilitar IAP

1.  Ve a **"Seguridad" > "Identity-Aware Proxy"**.
2.  Busca el servicio de backend que creaste para el balanceador de carga.
3.  En la columna **"IAP"**, activa el interruptor.
4.  Se abrirá un panel a la derecha. Haz clic en **"Añadir principal"**.
5.  **Nuevos principales**:
    *   Para dar acceso a todos los usuarios de tu dominio: `domain:tudominio.com`.
    *   Para dar acceso a un grupo de Google: `group:nombre-del-grupo@tudominio.com`.
    *   Para dar acceso a un usuario individual: `user:usuario@tudominio.com`.
6.  **Rol**: `Usuario de aplicación web protegida con IAP`.
7.  Haz clic en **"Guardar"**.

## 5.4. (Opcional) Crear un Grupo de Google para el Acceso

Es una buena práctica gestionar el acceso a través de un Grupo de Google en lugar de usuarios individuales.

1.  Ve a [Google Groups](https://groups.google.com/).
2.  Crea un nuevo grupo (ej. `app-access-group@tudominio.com`).
3.  Añade los miembros que necesiten acceso a la aplicación.
4.  Usa este grupo como principal al habilitar IAP.

---

**Has completado la configuración de la infraestructura en GCP.**

**Próximo paso:** [Guía de Configuración de la Aplicación](../app_setup/01-flask-project-structure.md)
