# 2. Manejo de Dependencias

La gestión de dependencias es crucial para la reproducibilidad y la seguridad.

## Archivo `requirements.txt`

Todas las dependencias de Python deben estar listadas en un archivo `requirements.txt` en la raíz del proyecto. Es una buena práctica "pinear" las versiones para asegurar que los despliegues sean consistentes.

### Dependencias Esenciales del Framework

Este es un ejemplo de `requirements.txt` basado en el proyecto "Ticket Home":

```
# Flask y extensiones
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
Flask-Login==0.6.3
gunicorn==22.0.0

# Base de datos
psycopg2-binary

# Autenticación IAP
PyJWT==2.8.0
cryptography
requests

# Utilidades
python-dotenv
python-dateutil
pytz

# Para exportar a Excel/PDF (opcional)
reportlab
openpyxl
xlsxwriter
```

### ¿Por Qué Pinear Versiones?

-   **Reproducibilidad**: Asegura que la misma versión de cada librería se use en desarrollo, QA y producción, evitando sorpresas.
-   **Seguridad**: Previene que se instale automáticamente una nueva versión de una dependencia que podría introducir un bug o una vulnerabilidad.
-   **Estabilidad**: Evita que cambios incompatibles en una librería rompan tu aplicación.

### Mantener las Dependencias Actualizadas

Periódicamente, debes revisar y actualizar las dependencias para recibir parches de seguridad y mejoras. Herramientas como `pip-review` o `dependabot` de GitHub pueden ayudar a automatizar este proceso.

## Entorno Virtual

Siempre desarrolla en un entorno virtual para aislar las dependencias de tu proyecto de las del sistema.

```bash
# Crear un entorno virtual
python -m venv .venv

# Activar el entorno virtual
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate

# Instalar las dependencias
pip install -r requirements.txt
```

Asegúrate de añadir `.venv` a tu archivo `.gitignore`.

---

**Próximo paso:** [3. El Patrón de Application Factory](./03-flask-app-factory.md)
