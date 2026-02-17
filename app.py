import logging
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect  # Import CSRFProtect
from dotenv import load_dotenv
import os
import pytz

load_dotenv()  # Carga las variables de entorno desde .env

from config import Config
from models import db, User
from commands import register_commands
from auth_iap import hybrid_auth, init_iap_auth

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Initialize CSRF Protection
    csrf = CSRFProtect(app)

    # Database initialization is now handled by Flask commands.

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize IAP Authentication
    init_iap_auth(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.tickets import tickets_bp
    from routes.admin import admin_bp
    from routes.visualizador import visualizador_bp
    from routes.exports import exports_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(visualizador_bp, url_prefix='/visualizador')
    app.register_blueprint(exports_bp, url_prefix='/export')

    # Middleware para proteger endpoints
    @app.before_request
    def before_request_auth():
        """
        Middleware de autenticación con separación por ambiente.

        Política:
        - DEV: Híbrido (IAP + Login tradicional)
        - QA/PROD: Solo IAP (Login tradicional deshabilitado)

        Implementado como parte de v1.9.2 Security Hardening.
        """
        # Endpoints públicos que no requieren autenticación
        public_endpoints = [
            'auth.login',
            'auth.logout',
            'auth.demo_login',
            'auth.unauthorized',
            'static'
        ]

        # Permitir acceso a endpoints públicos
        if request.endpoint in public_endpoints:
            return None

        # Si el usuario ya está autenticado (sesión Flask-Login), permitir acceso
        if current_user.is_authenticated:
            return None

        # Intentar autenticación con IAP si está habilitado
        if hybrid_auth.is_iap_request():
            # IAP está activo, intentar autenticar
            # Nota: authenticate_request() retorna (bool, str) y ya hace login_user() internamente
            success, message = hybrid_auth.authenticate_request()
            if success:
                # Usuario ya autenticado por authenticate_request()
                return None

        # El usuario no está autenticado
        # Verificar política de autenticación según ambiente
        environment = os.environ.get('ENVIRONMENT', 'local')
        enable_demo_login = os.environ.get('ENABLE_DEMO_LOGIN', 'false').lower() == 'true'

        if enable_demo_login:
            # DEV: Permitir login tradicional como fallback
            return redirect(url_for('auth.login'))
        else:
            # QA/PROD: Solo SSO, mostrar error 403
            return render_template('unauthorized.html',
                email=None,
                message=f"Acceso denegado. Solo autenticación SSO permitida en {environment.upper()}."
            ), 403

    @app.context_processor
    def inject_version():
        return dict(app_version=os.environ.get("APP_VERSION", "local"))

    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('tickets.nursing_board'))
        return redirect(url_for('auth.login'))

    # Timezone filter
    @app.template_filter('datetime_local')
    def datetime_local_filter(dt, fmt='%d/%m/%Y %H:%M'):
        if not dt:
            return 'N/A'
        local_tz = pytz.timezone('America/Santiago')
        local_dt = dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_dt.strftime(fmt)

    # Error handlers
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f'Error 500: {e}', exc_info=True)
        return render_template('errors/500.html'), 500

    # Security headers middleware
    @app.after_request
    def set_security_headers(response):
        """
        Agregar headers de seguridad a todas las respuestas HTTP.
        Protege contra: clickjacking, SSL stripping, XSS, MIME sniffing.

        Implementado como parte de v1.9.2 Security Hardening.

        NOTA: Solo se aplican en ambientes de producción/QA.
              En ambiente local se omiten para facilitar desarrollo.
        """

        # Detectar ambiente
        environment = os.environ.get('ENVIRONMENT', 'local')

        # Solo aplicar headers de seguridad en ambientes NO locales
        if environment == 'local':
            # En desarrollo local, no aplicar headers restrictivos
            return response

        # --- HEADERS DE SEGURIDAD (solo QA/PROD) ---

        # Prevenir clickjacking - no permitir iframe de este sitio
        response.headers['X-Frame-Options'] = 'DENY'

        # HSTS - Forzar HTTPS por 1 año (solo en producción y QA)
        if environment in ['production', 'qa']:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )

        # Prevenir MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Control de Referrer - no enviar URL completa a externos
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy
        # NOTA: unsafe-inline y unsafe-eval son necesarios para charts/dashboards
        # CDNs permitidos: Bootstrap, jQuery, DataTables, Chart.js, Font Awesome, Tailwind, Alpine.js
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdn.tailwindcss.com code.jquery.com cdn.datatables.net cdnjs.cloudflare.com unpkg.com",
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com cdnjs.cloudflare.com cdn.datatables.net",
            "img-src 'self' data: https:",
            "font-src 'self' data: fonts.gstatic.com cdnjs.cloudflare.com",
            "connect-src 'self' cdn.datatables.net cdn.jsdelivr.net",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

        # Permissions Policy (limitar APIs del navegador)
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), payment=()'
        )

        return response

    return app

app = create_app()
register_commands(app)

if __name__ == '__main__':
    # Fix for Issue #76: Debug Mode Habilitado en Entry Point
    debug_mode = Config.FLASK_DEBUG
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
