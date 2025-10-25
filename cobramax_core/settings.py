"""
Django settings for cobramax_core project.
"""

import os
import dj_database_url
from pathlib import Path

# RUTA BASE DEL PROYECTO
BASE_DIR = Path(__file__).resolve().parent.parent

# CLAVE SECRETA (leer desde variable de entorno en producción)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-ltvkw+4+jzvy)8bv*#j2&a-86*h&4ss@)p3+vwg0f%^5exxx#w')

# MODO DEBUG (leer desde entorno): usar 'True' o 'False'
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['cobramax-core.onrender.com', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías externas
    'rest_framework',

    # Aplicaciones del proyecto
    'cobramax_core',
    'usuarios',
    'clientes',
    'cobranza',
    'zonas',
    'chatbot',
    'reportes',
    'notificaciones',
]


# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise: servir archivos estáticos eficientemente en producción
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # ← Este debe estar presente
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'cobramax_core.urls'

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cobramax_core.wsgi.application'

# CONFIGURACIÓN DE BASE DE DATOS (PostgreSQL)
# Configuración de la base de datos: preferir URL interna de Render si existe,
# luego DATABASE_URL (externa), y finalmente construir desde POSTGRES_*.
database_url = None
# Render puede exponer una URL interna para conexiones desde servicios en la misma VPC
database_url = os.environ.get('RENDER_INTERNAL_DATABASE_URL') or os.environ.get('DATABASE_URL')
if not database_url:
    # construir URL a partir de variables POSTGRES_* si existe
    pg_user = os.environ.get('POSTGRES_USER')
    pg_password = os.environ.get('POSTGRES_PASSWORD')
    pg_host = os.environ.get('POSTGRES_HOST')
    pg_port = os.environ.get('POSTGRES_PORT', '5432')
    pg_db = os.environ.get('POSTGRES_DB')
    if pg_user and pg_password and pg_host and pg_db:
        database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

# Si database_url está definido, usar dj_database_url para parsearla.
# Establecer conn_max_age para conexiones persistentes en producción.
if database_url:
    DATABASES = {
        'default': dj_database_url.config(default=database_url, conn_max_age=600)
    }
else:
    # Fallback a sqlite para entornos de desarrollo sin variables de BD
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# VALIDACIÓN DE CONTRASEÑAS
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# CONFIGURACIÓN DE IDIOMA Y ZONA HORARIA
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# ARCHIVOS ESTÁTICOS
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Uso de WhiteNoise para servir archivos estáticos en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Si la aplicación está detrás de un proxy (Render), permitir detectar HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CLAVE PRIMARIA POR DEFECTO
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CONFIGURACIÓN DE AUTENTICACIÓN
AUTH_USER_MODEL = 'usuarios.Usuario'

# REDIRECCIONES DE LOGIN / LOGOUT
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

# Email (por defecto consola en desarrollo)
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@cobramax.local')

# SMTP settings (se leen desde variables de entorno si están disponibles)
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587')) if os.environ.get('EMAIL_PORT') else None
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')


# Twilio / WhatsApp (usar variables de entorno en producción)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', '')

# Celery (broker/result backend)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

