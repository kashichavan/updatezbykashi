from pathlib import Path
import os
from datetime import timedelta

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security & Environment Settings
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true" or os.environ.get("DEBUG", "false").lower() == "true"

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-only-local-test-key-do-not-use-in-production"
    else:
        # Require strong secret key in production
        import secrets
        SECRET_KEY = secrets.token_urlsafe(64)

raw_hosts = os.environ.get("ALLOWED_HOSTS", "").strip()
if raw_hosts:
    ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(",") if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = [
        "kashiiupdatez.online",
        "www.kashiiupdatez.online",
        ".onrender.com",
        "localhost",
        "127.0.0.1",
    ]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'requirements',
    'debugger',
    'sqlsandbox',
    'blog',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=90),
    'ROTATE_REFRESH_TOKENS': True,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'requirements.middleware.RateLimitMiddleware',
    'requirements.middleware.SecurityHeadersMiddleware',
    'requirements.middleware.VisitorAnalyticsMiddleware',
]

ROOT_URLCONF = 'reqpulse.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ])
            ] if not DEBUG else [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'reqpulse.wsgi.application'
ASGI_APPLICATION = 'reqpulse.asgi.application'

# Database Configuration: PostgreSQL on Render or Local/Internal SQLite3
_db_url = os.environ.get("DATABASE_URL", "").strip()
if _db_url.startswith(("postgres://", "postgresql://")):
    try:
        import dj_database_url
        is_pooled = any(p in _db_url for p in ["pooler", "render", "vercel-storage", "neon.tech"])
        db_config = dj_database_url.config(
            default=_db_url,
            conn_max_age=0 if is_pooled else 300,
            conn_health_checks=True,
            ssl_require=True if "sslmode=require" in _db_url or "neon.tech" in _db_url or "vercel-storage" in _db_url else False,
        )
        db_config.setdefault("OPTIONS", {})
        db_config["OPTIONS"].update({
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        })
        if "pooler" in _db_url or "neon.tech" in _db_url:
            db_config["DISABLE_SERVER_SIDE_CURSORS"] = True
        DATABASES = {"default": db_config}
    except Exception:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
                "OPTIONS": {"timeout": 30},
            }
        }
elif os.environ.get("DB_ENGINE"):
    DATABASES = {"default": {
        "ENGINE": os.environ["DB_ENGINE"],
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                "timeout": 30,
            }
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization & Timezone Settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static & Media Files Configuration (WhiteNoise Enabled)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# WhiteNoise High-Performance Static Caching (1 year cache for production immutable assets)
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0
WHITENOISE_KEEP_ONLY_HASHED_FILES = False
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Enterprise Security & Hardening Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Session & Cookie Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 2592000  # 30 Days persistent login session
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
CSRF_COOKIE_HTTPONLY = False  # Allows standard frontend AJAX/Fetch to read CSRF token
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Security & Data Upload Protection
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# High-Performance Caching
if os.environ.get("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ["REDIS_URL"],
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "kashii-updatez-cache",
            "OPTIONS": {
                "MAX_ENTRIES": 500,
                "CULL_FREQUENCY": 2,
            }
        }
    }

LOGIN_URL = "/owner/"

CSRF_TRUSTED_ORIGINS = [
    "https://kashiiupdatez.online",
    "https://www.kashiiupdatez.online",
    "https://*.onrender.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

if os.environ.get("CSRF_TRUSTED_ORIGINS"):
    custom_origins = [origin.strip() for origin in os.environ["CSRF_TRUSTED_ORIGINS"].split(",") if origin.strip()]
    for origin in custom_origins:
        # Validate that wildcard origins like * are rejected
        if origin not in ("https://*", "http://*", "*"):
            CSRF_TRUSTED_ORIGINS.append(origin)

# Meta / Instagram Graph API Configuration (Loaded strictly from Environment)
META_APP_ID = os.environ.get('META_APP_ID', '')
META_APP_SECRET = os.environ.get('META_APP_SECRET', '')
INSTAGRAM_REDIRECT_URI = os.environ.get('INSTAGRAM_REDIRECT_URI', 'https://kashiiupdatez.online/instagram/oauth/callback/')
META_VERIFY_TOKEN = os.environ.get('META_VERIFY_TOKEN', '')

