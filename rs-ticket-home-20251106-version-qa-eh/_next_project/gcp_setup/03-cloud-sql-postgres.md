# 3. Configuración de Cloud SQL con PostgreSQL

La base de datos es un componente crítico. Usaremos Cloud SQL con PostgreSQL por su robustez y compatibilidad con SQLAlchemy.

## 3.1. Crear la Instancia de Cloud SQL

1.  En la consola de GCP, ve a **"SQL"**.
2.  Haz clic en **"Crear instancia"**.
3.  Elige **"PostgreSQL"**.
4.  **ID de instancia**: `app-postgres-db` (o un nombre único).
5.  **Contraseña de postgres**: Genera y guarda una contraseña segura. La necesitarás para el `DATABASE_URL`.
6.  **Versión de la base de datos**: Elige la versión más reciente de PostgreSQL (ej. `PostgreSQL 14` o superior).
7.  **Elige una región y zona**: `southamerica-west1-a`.
8.  **Configuración de la instancia**:
    *   Haz clic en **"Mostrar opciones de configuración"**.
    *   **Conectividad**:
        *   Selecciona **"IP privada"**.
        *   **Red**: Elige la VPC que creaste (`app-vpc`).
        *   Se te pedirá que configures el acceso a servicios privados si no lo has hecho.
        *   La instancia recibirá una IP privada en el rango que asignaste (ej. `10.1.x.x`).
    *   **Tipo de máquina**: Para empezar, `db-custom-1-3840` (1 vCPU, 3.75 GB RAM) es suficiente.
    *   **Almacenamiento**: 10 GB de SSD es un buen punto de partida. Habilita el **"Aumento de almacenamiento automático"**.
    *   **Copias de seguridad**: Habilita las copias de seguridad automáticas y la recuperación de un momento dado (`point-in-time recovery`).

9.  Haz clic en **"Crear instancia"**.

## 3.2. Crear la Base de Datos

Una vez que la instancia esté creada:

1.  Selecciona la instancia en la consola de SQL.
2.  Ve a la pestaña **"Bases de datos"**.
3.  Haz clic en **"Crear base de datos"**.
4.  **Nombre de la base de datos**: `app_db` (o el que prefieras).
5.  Haz clic en **"Crear"**.

## 3.3. Crear el Secreto en Secret Manager

Nunca expongas la URL de la base de datos directamente. Guárdala en Secret Manager.

1.  Construye la URL de la base de datos:
    `postgresql://postgres:[TU_CONTRASENA]@[IP_PRIVADA_DE_CLOUD_SQL]:5432/app_db`
2.  En la consola de GCP, ve a **"Secret Manager"**.
3.  Haz clic en **"Crear secreto"**.
4.  **Nombre**: `database-url`.
5.  **Valor del secreto**: Pega la URL de la base de datos que construiste.
6.  Deja las demás opciones por defecto y haz clic en **"Crear secreto"**.

---

**Próximo paso:** [4. Configuración de IAM y Cuentas de Servicio](./04-iam-and-service-accounts.md)
