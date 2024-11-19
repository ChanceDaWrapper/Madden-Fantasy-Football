from pathlib import Path
import os
import django_fantasy.settings


BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings
SECRET_KEY = 'paihwegpiahfaoiuhfawnegpahwopiughplkshdpofh23oiufth2348t8yh34iwhtgh98hg3ih4g98h34wifghe8hf98ehwfg098qah498gh3we4ugh930849wegh34nweagp8he'  # Use env variable in production
DEBUG = os.getenv('DEBUG', 'False') == 'False'

ALLOWED_HOSTS = [
    '*'
]

# Application definition
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pages.apps.PagesConfig",
    "teams.apps.TeamsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhitenoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

MIDDLEWARE += [
    "django.middleware.security.SecurityMiddleware",  # Already included
    "whitenoise.middleware.WhiteNoiseMiddleware",     # Static file serving
]


ROOT_URLCONF = "django_fantasy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "django_fantasy.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files settings
STATIC_URL = 'static/'

# For development
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Directory for your project's static files
]

STATIC_DIRS = [os.path.join(BASE_DIR, '/static')]
# For production (collectstatic output)
STATIC_ROOT = os.path.join(BASE_DIR,  "staticfiles")  # Where `collectstatic` will place files

# Command to run in production to collect static files
# python manage.py collectstatic


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0  # Explicitly disable HSTS in development
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False



{
    "version": 2,
    "builds": [
        { "src": "django_fantasy/wsgi.py", "use": "@vercel/python" }
    ],
    "routes": [
        { "src": "/static/(.*)", "dest": "/static/$1" },
        { "src": "/(.*)", "dest": "django_fantasy/wsgi.py" }
    ]
}
