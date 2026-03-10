"""
AgroSmart Malawi – Django Settings
Stage 2: SMS Advisory Bot Backend
"""

import dj_database_url
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config(
    'SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: v.split(','))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    # AgroSmart apps
    'crops',
    'sms_bot',
    'weather',
    'market',
    'accounts',
    'whatsapp_bot',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agrosmart.urls'

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
        ],
    },
}]

WSGI_APPLICATION = 'agrosmart.wsgi.application'

# ── DATABASE ─────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── CACHE / CELERY ────────────────────────────────────────────────────────────
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# ── REST FRAMEWORK ────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ── AFRICA'S TALKING (SMS) ────────────────────────────────────────────────────
AFRICAS_TALKING_USERNAME = config('AT_USERNAME', default='sandbox')
AFRICAS_TALKING_API_KEY = config('AT_API_KEY',  default='your-sandbox-api-key')
AFRICAS_TALKING_SHORTCODE = config('AT_SHORTCODE', default='AgroSmart')

# ── TWILIO (WHATSAPP) ─────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID',   default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN',     default='')
TWILIO_WHATSAPP_FROM = config(
    'TWILIO_WHATSAPP_FROM',  default='whatsapp:+14155238886')

# ── WEATHER API ───────────────────────────────────────────────────────────────
OPENWEATHER_API_KEY = config('OPENWEATHER_API_KEY', default='your-api-key')

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: v.split(',')
)

# ── STATIC / MEDIA ────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Blantyre'
USE_I18N = True
USE_TZ = True

# ── SMS BOT CONFIG ────────────────────────────────────────────────────────────
SMS_BOT = {
    'MAX_SMS_LENGTH': 160,
    'SESSION_TIMEOUT_MINUTES': 30,
    'DEFAULT_LANGUAGE': 'en',
    'SUPPORTED_LANGUAGES': ['en', 'ny'],   # English, Chichewa
    'RATE_LIMIT_PER_HOUR': 20,
}

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_FROM = config(
    'TWILIO_WHATSAPP_FROM', default='whatsapp:+14155238886')


# ─────────────────────────────────────────────────────────────
# ADD THESE TO THE BOTTOM OF YOUR agrosmart/settings.py
# ─────────────────────────────────────────────────────────────


# ── Security ──────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# ── Database (Railway gives us DATABASE_URL automatically) ────
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }

# ── Static files (WhiteNoise serves them without a CDN) ───────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← add after SecurityMiddleware
] + [m for m in MIDDLEWARE if m != 'django.middleware.security.SecurityMiddleware']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── HTTPS in production ───────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
