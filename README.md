# 🏥 Ticket Home - RedSalud

Sistema de gestión de tickets y admisión hospitalaria para RedSalud. Este proyecto permite la administración eficiente de pacientes, tickets de atención y asignación de camas/pabellones.

## 📋 Características Principales

*   **Gestión de Pacientes**: Registro y seguimiento de historial.
*   **Tickets de Atención**: Flujo completo desde admisión hasta alta.
*   **Asignación de Recursos**: Gestión de camas y pabellones en tiempo real.
*   **Integración IAP**: Seguridad corporativa mediante Identity-Aware Proxy.
*   **Reportes**: Exportación de datos y métricas de operación.

## 🚀 Guía de Despliegue (QA)

El despliegue en el ambiente de QA (`qa-ticket-home-redsalud`) está completamente automatizado mediante PowerShell y Terraform.

### Prerrequisitos
*   Docker Desktop (Corriendo)
*   Google Cloud SDK (`gcloud`) autenticado

### Comandos de Despliegue

El script maestro `deploy-qa.ps1` maneja la construcción de la imagen Docker y la aplicación de infraestructura.

Ubicación: `_otros_archivos\_deployment_scripts\deploy-qa.ps1`

| Escenario | Comando | Descripción |
|-----------|---------|-------------|
| **Normal** | `.\deploy-qa.ps1 -Scenario no-reset` | Despliegue de código. Mantiene la BD intacta. |
| **Cambios BD** | `.\deploy-qa.ps1 -Scenario reset-minimal` | **Borra datos**. Recrea esquema y carga datos base. |
| **Demo** | `.\deploy-qa.ps1 -Scenario reset-full` | **Borra datos**. Carga datos de prueba completos. |

## 🛠️ Desarrollo Local

1.  **Clonar repositorio**:
    ```bash
    git clone <repo-url>
    ```
2.  **Configurar entorno**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Variables de Entorno**:
    Copiar `.env.example` a `.env` y configurar credenciales locales.

4.  **Ejecutar**:
    ```bash
    flask run
    ```

## 📂 Estructura del Proyecto

*   `app.py`: Punto de entrada de la aplicación Flask.
*   `models.py`: Definición de modelos de base de datos (SQLAlchemy).
*   `routes/`: Controladores y lógica de endpoints.
*   `templates/`: Vistas HTML (Jinja2).
*   `terraform/`: Infraestructura como Código (IaC) para GCP.
*   `_otros_archivos/`: Scripts de despliegue y documentación adicional.

## 🔗 Enlaces Útiles

*   [Ambiente QA](https://qa-ticket-home.mhwdev.dev)
*   [Reporte de Éxito QA](_otros_archivos/deployment/qa_success_report.html)

---
© 2025 RedSalud - Equipo de Desarrollo
