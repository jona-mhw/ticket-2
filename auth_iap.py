from flask import request, current_app, flash
from flask_login import login_user
from models import User, db, LoginAudit, Superuser, ROLE_ADMIN 
import jwt
import requests
import os

class IAPAuthenticator:
    """Handles Google Cloud IAP authentication and JWT validation."""

    def __init__(self, gcp_project_number=None, backend_service_id=None):
        self.gcp_project_number = gcp_project_number
        self.backend_service_id = backend_service_id
        self.expected_audience = f"/projects/{self.gcp_project_number}/global/backendServices/{self.backend_service_id}" if gcp_project_number and backend_service_id else None
        self.google_certs_url = "https://www.gstatic.com/iap/verify/public_key"
        self.certs = {}

    def is_iap_request(self):
        """Check if the request seems to come from IAP."""
        return 'X-Goog-IAP-JWT-Assertion' in request.headers

    def get_user_email(self):
        """Extracts user email from IAP header, an empty string if not available."""
        return request.headers.get('X-Goog-Authenticated-User-Email', '').replace('accounts.google.com:', '')

    def _get_google_public_keys(self):
        """Fetch and cache Google's public keys for IAP JWT validation."""
        if not self.certs:
            try:
                response = requests.get(self.google_certs_url)
                response.raise_for_status()
                self.certs = response.json()
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"Failed to fetch Google IAP public keys: {e}")
                return None
        return self.certs

    def _validate_jwt(self, iap_jwt):
        """Validate the IAP JWT assertion."""
        try:
            unverified_claims = jwt.decode(iap_jwt, options={"verify_signature": False})
            current_app.logger.info(f"IAP JWT unverified claims: {unverified_claims}")
        except Exception as e:
            current_app.logger.error(f"Could not decode unverified JWT: {e}")

        public_keys = self._get_google_public_keys()
        if not public_keys:
            return None, "No se pudieron obtener las claves públicas de Google."

        try:
            kid = jwt.get_unverified_header(iap_jwt).get('kid')
            if not kid or kid not in public_keys:
                return None, "Clave pública (kid) no encontrada en el JWT o en las claves de Google."

            key = public_keys[kid]
            decoded_jwt = jwt.decode(
                iap_jwt,
                key,
                algorithms=['ES256'],
                audience=self.expected_audience
            )
            return decoded_jwt, "JWT validado correctamente."
        except jwt.ExpiredSignatureError:
            return None, "El token JWT ha expirado."
        except jwt.InvalidAudienceError:
            return None, "Audiencia del JWT inválida."
        except Exception as e:
            current_app.logger.error(f"Error de validación JWT: {e}")
            return None, f"Error general de validación JWT: {e}"
            
    def authenticate_user(self):
        """Authenticate user based on IAP headers and logs them in."""
        if not self.is_iap_request():
            return None, "No es una solicitud IAP."

        # En Producción/QA (environment != local), es OBLIGATORIO validar el JWT
        environment = os.environ.get('ENVIRONMENT', 'local')
        iap_jwt = request.headers.get('X-Goog-IAP-JWT-Assertion')

        if environment != 'local':
            if not iap_jwt:
                current_app.logger.error("CRITICAL: Intento de acceso sin JWT en ambiente productivo.")
                return False, "Acceso denegado: Falta token de seguridad."

            if not self.expected_audience:
                current_app.logger.error("CRITICAL: IAP mal configurado. Faltan GCP_PROJECT_NUMBER o BACKEND_SERVICE_ID.")
                return False, "Error de configuración del servidor de autenticación."

            # Validación estricta del JWT
            decoded_jwt, validation_message = self._validate_jwt(iap_jwt)
            if not decoded_jwt:
                current_app.logger.error(f"CRITICAL: JWT de IAP inválido: {validation_message}")
                return False, f"Acceso denegado: Token de seguridad inválido. {validation_message}"

            # Obtener email del JWT validado
            email = decoded_jwt.get('email')
            current_app.logger.info(f"JWT validado correctamente. Usuario: {email}")

        else:
            # En local (DEV), permitimos fallback a header simple si no hay JWT (para facilitar pruebas con Postman/Curl)
            # O si hay JWT y audience configurado, también lo validamos.
            if iap_jwt and self.expected_audience:
                decoded_jwt, validation_message = self._validate_jwt(iap_jwt)
                if decoded_jwt:
                    email = decoded_jwt.get('email')
                else:
                    email = self.get_user_email() # Fallback a header
            else:
                email = self.get_user_email()

            if not email:
                return None, "No se encontró el email del usuario."

        # Normalize email
        email = email.lower().strip()
        current_app.logger.info(f"Usuario autenticado por IAP: {email}")

        # Buscar el usuario en la base de datos
        # IMPORTANTE: Verificar si existe más de un usuario con el mismo email (prevenir múltiples roles)
        users_with_email = User.query.filter_by(email=email).all()

        if len(users_with_email) > 1:
            current_app.logger.error(f"CONFLICTO: El email {email} tiene {len(users_with_email)} usuarios asociados con diferentes roles.")
            return False, f"Error de configuración: Tu email ({email}) está asociado a múltiples cuentas. Contacta al administrador."

        user = users_with_email[0] if users_with_email else None

        if user and user.is_active:
            # Usuario existe y está activo → login automático
            login_user(user)
            # Marcar en la sesión que este usuario entró por IAP
            from flask import session
            session['auth_type'] = 'iap'
            session['iap_email'] = email
            current_app.logger.info(f"Login automático exitoso para {email}")
            
            # Registrar auditoría de login
            try:
                audit_log = LoginAudit(
                    user_id=user.id,
                    username=user.username,
                    clinic_id=user.clinic_id,
                    ip_address=request.remote_addr
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Error al registrar auditoría de login IAP: {str(e)}")
                db.session.rollback()
            
            return True, f"Inicio de sesión automático exitoso para {email}."
        elif user:
            # Usuario existe pero está inactivo → denegar acceso
            current_app.logger.warning(f"Usuario {email} está inactivo")
            return False, f"La cuenta para {email} está inactiva."
        else:
            # Usuario NO existe en BD. Verifiquemos si es un superusuario para crearlo automáticamente.
            from models import db, Superuser, ROLE_ADMIN

            is_su = Superuser.query.filter_by(email=email).first()

            if is_su:
                current_app.logger.info(f"El email {email} es de un superusuario. Creando cuenta de usuario...")
                
                # Crear un nombre de usuario único a partir del email
                username = email.split('@')[0].replace('.', '_').replace('-', '_')
                counter = 1
                base_username = username
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}_{counter}"
                    counter += 1

                new_user = User(
                    email=email,
                    username=username,
                    role=ROLE_ADMIN,
                    password='iap_user_placeholder', # Contraseña no usada para login IAP
                    clinic_id=None, # Superusuarios no tienen clínica
                    is_active=True
                )
                db.session.add(new_user)
                db.session.commit()
                
                current_app.logger.info(f"Usuario {username} creado para el superusuario {email}.")
                
                # Loguear al nuevo usuario
                login_user(new_user)
                from flask import session
                session['auth_type'] = 'iap'
                session['iap_email'] = email
                
                # Registrar auditoría de login para el nuevo superusuario
                try:
                    audit_log = LoginAudit(
                        user_id=new_user.id,
                        username=new_user.username,
                        clinic_id=new_user.clinic_id,
                        ip_address=request.remote_addr
                    )
                    db.session.add(audit_log)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f"Error al registrar auditoría de login para nuevo superusuario: {str(e)}")
                    db.session.rollback()
                
                return True, f"Cuenta de superusuario creada y sesión iniciada para {email}."

            else:
                # Usuario NO existe en BD y NO es superusuario → denegar acceso
                current_app.logger.warning(f"Acceso denegado para {email}. No existe en BD y no es superusuario.")
                return False, f"Tu cuenta ({email}) no está registrada en la aplicación y no es una cuenta de superusuario."


class HybridAuthenticator:
    """Manages switching between IAP and traditional form-based authentication."""

    def __init__(self):
        self.iap_auth = None
        self.enable_iap = False
        self.enable_demo_login = True  # Por defecto, permitir login demo

    def init_app(self, app):
        self.enable_iap = os.environ.get('ENABLE_IAP', 'false').lower() == 'true'
        self.enable_demo_login = os.environ.get('ENABLE_DEMO_LOGIN', 'true').lower() == 'true'

        if self.enable_iap:
            # GCP_PROJECT_NUMBER y BACKEND_SERVICE_ID son opcionales
            # Solo se necesitan si quieres validar el JWT (no implementado por ahora)
            gcp_project_number = os.environ.get('GCP_PROJECT_NUMBER')
            backend_service_id = os.environ.get('BACKEND_SERVICE_ID')

            self.iap_auth = IAPAuthenticator(gcp_project_number, backend_service_id)
            if gcp_project_number and backend_service_id:
                app.logger.info("Autenticación IAP HABILITADA con validación de JWT (modo seguro).")
            else:
                app.logger.warning("⚠️ Autenticación IAP HABILITADA sin validación de JWT. Configure GCP_PROJECT_NUMBER y BACKEND_SERVICE_ID para modo seguro.")
        else:
            app.logger.info("Autenticación IAP DESHABILITADA (usando modo local/tradicional).")

        if self.enable_demo_login:
            app.logger.info("Login DEMO/Tradicional HABILITADO.")
        else:
            app.logger.info("Login DEMO/Tradicional DESHABILITADO (solo acceso por IAP).")
            
    def authenticate_request(self):
        """Middleware-like function to perform authentication for the current request."""
        # Only attempt IAP auth if it's enabled and looks like an IAP request
        if self.enable_iap and self.iap_auth and self.iap_auth.is_iap_request():
            return self.iap_auth.authenticate_user()
        
        # If IAP is not enabled or it's not an IAP request, do nothing and let standard login handle it.
        return None, "Autenticación IAP no aplica a esta solicitud."

    def get_current_user_email(self):
        """Helper to get user email from IAP header if available."""
        if self.enable_iap and self.iap_auth:
            return self.iap_auth.get_user_email()
        return None

    def is_iap_request(self):
        """Checks if IAP is enabled and if the current request is from IAP."""
        return self.enable_iap and self.iap_auth and self.iap_auth.is_iap_request()

# Singleton instance
hybrid_auth = HybridAuthenticator()

def init_iap_auth(app):
    """Initializes the IAP authenticator."""
    hybrid_auth.init_app(app)
