"""
Django settings – Plateforme Avances Sociales OCP
Compatible : Local (MySQL) + Production Render (PostgreSQL)
"""
import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SÉCURITÉ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-ocp-avances-2025-changez-absolument-en-production'
)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLICATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps projet
    'accounts',
    'agents',
    'events',
    'demandes',
    'dashboard',
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MIDDLEWARE — WhiteNoise en 2ème position (obligatoire)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← Render : fichiers statiques
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'accounts.context_processors.notifications_count',
        ],
    },
}]

WSGI_APPLICATION = 'core.wsgi.application'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASE DE DONNÉES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Render fournit DATABASE_URL automatiquement → PostgreSQL
# En local (pas de DATABASE_URL) → MySQL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # ── Production Render (PostgreSQL) ────────────────────
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # ── Développement local (MySQL) ────────────────────────
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'ocp_avances_db',
            'USER': 'root',
            'PASSWORD': '',         # ← Ton mot de passe MySQL local
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTH_USER_MODEL     = 'accounts.CustomUser'
LOGIN_URL           = '/accounts/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EMAIL SMTP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Les valeurs sont lues depuis les variables d'environnement
# (définies dans Render Dashboard → Environment)
# En local, utilise EMAIL_BACKEND console pour tester sans Gmail.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)
# Pour tester en local sans envoyer de vrais emails, définis :
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER',     '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f'OCP Avances RH <{EMAIL_HOST_USER}>'
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERNATIONALISATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Casablanca'
USE_I18N      = True
USE_TZ        = True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FICHIERS STATIQUES — WhiteNoise pour Render
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SESSION_COOKIE_AGE           = 28800   # 8 heures
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MESSAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'secondary',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'danger',
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SÉCURITÉ PRODUCTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if not DEBUG:
    SECURE_PROXY_SSL_HEADER      = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT          = True
    SESSION_COOKIE_SECURE        = True
    CSRF_COOKIE_SECURE           = True
    SECURE_HSTS_SECONDS          = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True