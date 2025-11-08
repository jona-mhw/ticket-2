# 1. Estructura del Proyecto Flask

Una estructura de proyecto bien organizada es clave para la mantenibilidad. Este framework utiliza un enfoque modular basado en Blueprints y el patrón de Application Factory.

## Estructura de Directorios Recomendada

```
/mi-nueva-app
├── app.py                    # Punto de entrada y Factory de la app
├── config.py                 # Clases de configuración (Dev, Prod)
├── models.py                 # Modelos de datos de SQLAlchemy
├── commands.py               # Comandos CLI personalizados de Flask
├── auth_iap.py               # Lógica de validación de JWT de IAP
│
├── routes/                   # Directorio para los Blueprints
│   ├── __init__.py
│   ├── home.py               # Blueprint para las rutas principales
│   ├── admin.py              # Blueprint para el panel de administración
│   └── ...                   # Otros blueprints que necesites
│
├── templates/                # Plantillas de Jinja2
│   ├── base.html             # Plantilla base con la estructura principal
│   ├── index.html
│   └── ...
│
├── static/                   # Archivos estáticos
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── logo.svg
│
├── migrations/               # Directorio de Alembic para migraciones de DB
│
├── .gitignore
├── requirements.txt          # Dependencias de Python
├── Dockerfile                # Para construir la imagen de la aplicación
└── startup.sh                # Script de inicio del contenedor
```

## Componentes Clave

-   **`app.py`**: Contiene la función `create_app()`. Inicializa Flask, carga la configuración, registra los Blueprints y las extensiones (como `db` y `migrate`).
-   **`config.py`**: Define diferentes clases de configuración (ej. `Config`, `DevelopmentConfig`, `ProductionConfig`) para manejar variables de entorno y secretos en diferentes ambientes.
-   **`models.py`**: Define la estructura de tu base de datos usando modelos de SQLAlchemy. Aquí es donde se implementa la lógica multi-tenant.
-   **`routes/`**: Cada archivo `.py` dentro de este directorio (o subdirectorios) define un `Blueprint`, que es un conjunto de rutas relacionadas. Esto ayuda a modularizar la aplicación.
-   **`templates/`**: Contiene los archivos HTML que renderiza la aplicación. Se recomienda usar la herencia de plantillas de Jinja2 con un `base.html`.
-   **`static/`**: Almacena CSS, JavaScript, imágenes y otros archivos que se sirven directamente al cliente.
-   **`Dockerfile` y `startup.sh`**: Definen cómo se empaqueta y se ejecuta la aplicación en un contenedor, listo para ser desplegado en Cloud Run.

---

**Próximo paso:** [2. Manejo de Dependencias](./02-dependencies.md)
