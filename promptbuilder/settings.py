"""
Django settings for the EduPrompt Studio project.

The Studio is embedded as a tool inside PROODOS (module M8). It stores nothing
that the teacher writes: no database rows, no sessions, no analytics.
"""
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# The secret key comes only from the environment. There is no built-in
# fallback. Local development (DEBUG) and the test runner get a random,
# per-process key; a production process without a key refuses to start.
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    _running_tests = len(sys.argv) > 1 and sys.argv[1] == 'test'
    if DEBUG or _running_tests:
        SECRET_KEY = get_random_secret_key()
    else:
        raise ImproperlyConfigured(
            'The SECRET_KEY environment variable is not set. Set it to a long '
            'random value before starting the application.'
        )

# Language of the user interface served by this deployment. It selects the
# in-app notice (generator/notices.py). Override with the UI_LANGUAGE env var.
UI_LANGUAGE = os.environ.get('UI_LANGUAGE', 'en')

# Embedding: the Studio may be framed only by itself and by PROODOS. The
# origins are space-separated in the FRAME_ANCESTORS environment variable.
# 'self' is always allowed and is added by the middleware.
FRAME_ANCESTORS = os.environ.get(
    'FRAME_ANCESTORS',
    'https://proodoseduai.com https://www.proodoseduai.com',
).split()

# The app is loaded in a cross-site iframe, so the remaining cookie (the CSRF
# cookie) must be SameSite=None and Secure.
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',
    '.up.railway.app',
]
CSRF_TRUSTED_ORIGINS = [
    'https://eduprompt-studio-production.up.railway.app',
    'https://*.railway.app',
    'https://*.up.railway.app',
]

# Application definition. No admin, no sessions, no messages: nothing is
# stored per visitor.
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'generator',
]

MIDDLEWARE = [
    # First, so that the framing policy is also applied to static files
    # answered early by WhiteNoise.
    'generator.middleware.FrameAncestorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

ROOT_URLCONF = 'promptbuilder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'promptbuilder.wsgi.application'

# Database. The application writes nothing to it; it exists only because the
# framework and the retained (unused) legacy models need a schema.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Gemini API Key - uses environment variable for security
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
