"""
Django settings for python_puzzle (Local Development)
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings (🔴 Change these in production!)
SECRET_KEY = 'django-insecure-que5$_!$+z_mhe60o(swcskzjm7-b8mh-goawfg=f^11hr8r3g'
# Development only
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Application definition
INSTALLED_APPS = [
    'puzzle',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'whitenoise',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # Compression middleware
]

# Security Headers (Development compatible)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

ROOT_URLCONF = 'python_puzzle.urls'
WSGI_APPLICATION = 'python_puzzle.wsgi.application'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'TIMEOUT': 20,  # Add query timeout
    }
}

# Cache Configuration (Optimized)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 300,  # 5 minutes
        'KEY_PREFIX': 'puzzle_dev',  # Namespace keys
        'OPTIONS': {
            'no_delay': True,
            'ignore_exc': True,
            'max_pool_size': 8,  # Increased connection pool
            'use_pooling': True
        }
    }
}

# Static Files Configuration (Optimized)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "puzzle/static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_MAX_AGE = 86400  # 1 day cache for static files
WHITENOISE_USE_FINDERS = True

# Template Configuration
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
            'debug': DEBUG,
        },
    },
]

# Authentication Configuration
AUTHENTICATION_BACKENDS = [
    'puzzle.backends.EmailUsernameAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'puzzle:daily_puzzle'
LOGOUT_REDIRECT_URL = 'puzzle:home'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Security (Development settings)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # 🔴 True in production
CSRF_COOKIE_SECURE = False    # 🔴 True in production
SECURE_SSL_REDIRECT = False   # 🔴 True in production

# Site Configuration
SITE_ID = 1

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'puzzle.backends.EmailUsernameAuthBackend',
    'django.contrib.auth.backends.ModelBackend'  # Required for staff
]
# Custom Settings
PUZZLE_CACHE_TIMEOUT = 300  # 5 minutes
MAX_ATTEMPTS_PER_PUZZLE = 10
