# 5. Integración con IAP

La integración con IAP en Flask implica validar un token JWT (JSON Web Token) que IAP añade a las cabeceras de cada solicitud. Este token contiene la identidad del usuario autenticado.

## `auth_iap.py` - El Validador de JWT

Crea un archivo `auth_iap.py` para encapsular la lógica de validación. Esto mantiene tu código de autenticación limpio y separado.

```python
# auth_iap.py

import requests
from flask import request
import jwt

# URLs de claves públicas de Google para verificar el token
IAP_PUBLIC_KEY_URL = 'https://www.gstatic.com/iap/verify/public_key'

# Metadata de GCP necesaria para validar la audiencia del token
METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email'
METADATA_HEADERS = {'Metadata-Flavor': 'Google'}

def get_iap_user_email():
    """
    Valida el token JWT de IAP y devuelve el email del usuario.
    """
    # 1. Obtener el token de la cabecera
    iap_jwt = request.headers.get('X-Goog-IAP-JWT-Assertion')
    if not iap_jwt:
        # Si no hay token, no es una solicitud de IAP
        return None

    try:
        # 2. Obtener las claves públicas de Google
        keys = requests.get(IAP_PUBLIC_KEY_URL).json()

        # 3. Obtener la audiencia esperada (ID del servicio de backend)
        # Esta es una forma dinámica de obtenerlo desde el entorno de Cloud Run
        # audience = f'/projects/[PROJECT_NUMBER]/apps/[PROJECT_ID]'
        # Es más robusto obtenerlo de forma dinámica si es posible o configurarlo como env var.
        # Para este ejemplo, lo dejaremos como un placeholder.
        # Necesitarás obtener el PROJECT_NUMBER y PROJECT_ID de tu GCP.
        expected_audience = '/projects/YOUR_PROJECT_NUMBER/apps/YOUR_PROJECT_ID'


        # 4. Decodificar y validar el token
        decoded_token = jwt.decode(
            iap_jwt,
            keys,
            algorithms=['ES256'],
            audience=expected_audience
        )

        # 5. Devolver el email y el ID de usuario
        return decoded_token.get('email'), decoded_token.get('sub')

    except (requests.exceptions.RequestException, jwt.PyJWTError) as e:
        print(f"Error al validar el token IAP: {e}")
        return None, None
```

**Importante:** Necesitarás reemplazar `YOUR_PROJECT_NUMBER` y `YOUR_PROJECT_ID` con los valores correspondientes de tu proyecto GCP. Puedes encontrarlos en la consola de GCP.

## Hook `before_request` para Autenticación Automática

Usa el decorador `@app.before_request` en `app.py` para ejecutar la validación de IAP antes de cada solicitud y gestionar la sesión del usuario.

```python
# app.py en la función create_app

from .auth_iap import get_iap_user_email
from .models import User, db
from flask_login import login_user, current_user
from flask import request, redirect, url_for

# ...

@app.before_request
def check_authentication():
    # Ignorar rutas públicas como /login, /static, etc.
    if request.path.startswith('/static') or request.endpoint in ['auth.login', 'auth.logout']:
        return

    # Si el usuario ya tiene una sesión activa, continuar
    if current_user.is_authenticated:
        return

    # Si IAP está habilitado, intentar autenticar con IAP
    if app.config.get('ENABLE_IAP'):
        email, _ = get_iap_user_email()
        if email:
            # Buscar o crear el usuario en la base de datos
            user = User.query.filter_by(email=email).first()
            if not user:
                # Lógica para crear un nuevo usuario si es necesario
                # user = User(email=email, ...)
                # db.session.add(user)
                # db.session.commit()
                pass # O mostrar una página de "acceso denegado"

            if user and user.is_active:
                login_user(user) # Iniciar sesión con Flask-Login
                return

    # Si todo falla, redirigir a la página de login o mostrar no autorizado
    return redirect(url_for('auth.login'))
```

Esta configuración crea un sistema de autenticación híbrido:
-   En producción (con IAP), los usuarios son autenticados automáticamente.
-   En desarrollo local (sin IAP), los usuarios pueden usar un formulario de login tradicional.

---

**Has completado la configuración de la aplicación.**

**Próximo paso:** [Guía de Diseño y Estética](../design/01-look-and-feel.md)
