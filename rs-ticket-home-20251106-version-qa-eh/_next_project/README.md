# Framework para Aplicaciones Flask en GCP con IAP

Este repositorio sirve como un framework y una guía de inicio rápido para construir y desplegar aplicaciones web seguras y escalables en Google Cloud Platform (GCP), utilizando Flask, Docker e Identity-Aware Proxy (IAP) para la autenticación.

El objetivo es replicar la arquitectura, el stack tecnológico y la experiencia de usuario del proyecto "Ticket Home", proporcionando una base sólida para nuevos proyectos.

## 📚 Estructura de la Documentación

Esta guía está dividida en cuatro secciones principales:

1.  **[Configuración de GCP (`gcp_setup`)](./gcp_setup/01-gcp-project-setup.md)**: Pasos para configurar la infraestructura necesaria en GCP, desde el proyecto hasta la configuración de red y IAP.
2.  **[Configuración de la Aplicación (`app_setup`)](./app_setup/01-flask-project-structure.md)**: Guía para estructurar y desarrollar la aplicación Flask, incluyendo el patrón de fábrica, el modelo de datos multi-tenant y la integración con IAP.
3.  **[Diseño y Estética (`design`)](./design/01-look-and-feel.md)**: Directrices sobre el look and feel, la paleta de colores y los assets estáticos para mantener una experiencia de usuario consistente.
4.  **[Despliegue (`deployment`)](./deployment/RUNBOOK.md)**: Un runbook detallado que explica cómo construir, empaquetar y desplegar la aplicación en Cloud Run.

## ✨ Características Principales del Framework

-   **Stack Tecnológico Moderno**: Python 3.11, Flask, SQLAlchemy y PostgreSQL.
-   **Seguridad por Diseño**: Autenticación robusta con Google SSO a través de IAP, sin necesidad de gestionar usuarios y contraseñas en la aplicación.
-   **Arquitectura Serverless**: Desplegado en Cloud Run para escalabilidad automática y pago por uso.
-   **Infraestructura como Código (Manual)**: Scripts y guías para replicar la infraestructura de manera consistente.
-   **Modelo Multi-tenant**: Preparado para dar servicio a múltiples clientes o entidades desde una única base de código y base de datos.
-   **Experiencia de Usuario Refinada**: Un diseño limpio, profesional y responsive, con componentes reutilizables.

## 🚀 Cómo Empezar

1.  Sigue la guía de **[Configuración de GCP](./gcp_setup/01-gcp-project-setup.md)** para preparar tu entorno en la nube.
2.  Utiliza la sección de **[Configuración de la Aplicación](./app_setup/01-flask-project-structure.md)** para desarrollar tu lógica de negocio sobre la base del framework.
3.  Consulta la guía de **[Diseño](./design/01-look-and-feel.md)** para mantener la consistencia visual.
4.  Finalmente, sigue el **[Runbook de Despliegue](./deployment/RUNBOOK.md)** para lanzar tu aplicación.

---
*Este framework fue generado a partir del proyecto `rs-ticket-home`.*
