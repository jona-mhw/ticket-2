import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

# Detectar entorno y cargar archivo .env correspondiente
environment = os.environ.get('ENVIRONMENT', 'local')

import logging as _logging
_config_logger = _logging.getLogger('config')

VALID_ENVIRONMENTS = ('local', 'qa', 'production')

if environment not in VALID_ENVIRONMENTS:
    _config_logger.warning(
        f"ENVIRONMENT='{environment}' no es un valor reconocido. "
        f"Valores válidos: {VALID_ENVIRONMENTS}. Comportándose como 'local'."
    )

if environment == 'local':
    # Desarrollo local: cargar .env.local
    env_file = os.path.join(basedir, '.env.local')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        _config_logger.info(f"[LOCAL] Loaded LOCAL environment from {env_file}")
elif environment == 'production':
    # Producción: cargar .env.production (solo configs no sensibles)
    env_file = os.path.join(basedir, '.env.production')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        _config_logger.info(f"[PROD] Loaded PRODUCTION environment from {env_file}")
elif environment == 'qa':
    env_file = os.path.join(basedir, '.env.qa')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        _config_logger.info(f"[QA] Loaded QA environment from {env_file}")

class Config:
    # Configuración de Flask
    ENVIRONMENT = environment
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if environment == 'production' and not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production environment!")
    if not SECRET_KEY:
        SECRET_KEY = 'dev-secret-key-change-in-production'

    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Base de datos
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("No DATABASE_URL set for the application. Please set it in your environment.")
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('ENABLE_SQL_LOGGING', 'False').lower() == 'true'
    
    # URLs y configuraciones generales
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Features flags
    SKIP_AUTH_FOR_TESTING = os.environ.get('SKIP_AUTH_FOR_TESTING', 'False').lower() == 'true'
    
    @classmethod
    def get_environment_info(cls):
        """Retorna información del entorno actual"""
        return {
            'environment': os.environ.get('ENVIRONMENT', 'unknown'),
            'flask_env': cls.FLASK_ENV,
            'debug': cls.FLASK_DEBUG,
            'database': 'PostgreSQL',
            'base_url': cls.BASE_URL
        }