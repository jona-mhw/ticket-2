# 3. El Patrón de Application Factory

El patrón de "Application Factory" es una forma estándar y recomendada de estructurar aplicaciones Flask. En lugar de crear una instancia de `Flask` globalmente, la creas dentro de una función. Esto ofrece varias ventajas, como facilitar las pruebas y la gestión de múltiples configuraciones.

## `app.py` - El Corazón de la Fábrica

El archivo `app.py` es donde reside la función `create_app`.

```python
# app.py

from flask import Flask
from .config import Config
from .models import db
from .routes import home_bp, admin_bp # Importa tus blueprints
from flask_migrate import Migrate

# Inicializa las extensiones sin una app
migrate = Migrate()

def create_app(config_class=Config):
    """
    Application Factory: crea y configura la instancia de la aplicación Flask.
    """
    app = Flask(__name__)

    # 1. Cargar configuración
    app.config.from_object(config_class)

    # 2. Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)

    # 3. Registrar Blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 4. (Opcional) Registrar comandos CLI
    # from .commands import register_commands
    # register_commands(app)

    # 5. (Opcional) Registrar un hook before_request para la autenticación
    @app.before_request
    def before_request_hook():
        # Aquí puedes poner lógica que se ejecute antes de cada request
        # Por ejemplo, la validación de IAP
        pass

    return app
```

### Ventajas de este Patrón

1.  **Testing**: Puedes crear múltiples instancias de la aplicación con diferentes configuraciones para tus pruebas. Por ejemplo, una instancia con una base de datos de prueba en memoria.
2.  **Configuraciones Múltiples**: Puedes pasar diferentes clases de configuración (`DevelopmentConfig`, `ProductionConfig`) a `create_app` para iniciar la aplicación en diferentes modos.
3.  **Evita Problemas de Importación Circular**: Al inicializar las extensiones dentro de la función, se evita la importación circular que puede ocurrir cuando tanto la app como las extensiones se definen globalmente.

## `config.py` - Gestión de la Configuración

El archivo `config.py` centraliza todas las variables de configuración.

```python
# config.py

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

class Config:
    """Configuración base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-secreta-muy-dificil'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Variables específicas de la app
    ENABLE_IAP = os.environ.get('ENABLE_IAP', 'false').lower() == 'true'

class ProductionConfig(Config):
    """Configuración de producción."""
    FLASK_ENV = 'production'
    DEBUG = False

class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    FLASK_ENV = 'development'
    DEBUG = True
```

En `app.py`, podrías detectar el entorno y usar la configuración adecuada:

```python
# En create_app()
env = app.config.get('FLASK_ENV')
if env == 'production':
    app.config.from_object('your_app.config.ProductionConfig')
else:
    app.config.from_object('your_app.config.DevelopmentConfig')
```

---

**Próximo paso:** [4. Modelo de Datos Multi-tenant](./04-multi-tenancy-model.md)
