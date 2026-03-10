# ─────────────────────────────────────────────────────────────
# ADD THESE TO THE BOTTOM OF YOUR agrosmart/settings.py
# ─────────────────────────────────────────────────────────────

import os
import dj_database_url

# ── Security ──────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

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

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── HTTPS in production ───────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE   = True
    CSRF_COOKIE_SECURE      = True
