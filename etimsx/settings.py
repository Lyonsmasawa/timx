"""
Django settings for etimsx project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import logging.config
import environ
import os
from pathlib import Path

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()  # Load from .env file

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Define log directory
LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)  # Ensure the directory is created

# SECURITY WARNING: keep the secret key secret!
SECRET_KEY = env("SECRET_KEY", default="django-insecure-key")
ENCRYPTION_SECRET_KEY = env(
    "ENCRYPTION_SECRET_KEY", default="5WjRuOGuaxo-OSNlvL3eKKWmK5KBCYHzpIJjFxi9mZk=")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True)

# Allowed hosts

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "etimsx.herokuapp.com",
                 "*.ngrok-free.app", "4524-217-199-146-205.ngrok-free.app", "34.60.172.27"]
# ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "etimsx.herokuapp.com", "*.ngrok-free.app", "https://4524-217-199-146-205.ngrok-free.app"])

# VSCU Configuration
VSCU_TIN = env("VSCU_TIN", default="P0000000K")
VSCU_BRANCH_ID = env("VSCU_BRANCH_ID", default="00")
VSCU_DEVICE_SERIAL = env("VSCU_DEVICE_SERIAL", default="Interactive00")
VSCU_CMC_KEY = env("VSCU_CMC_KEY")

# API Configuration
API_BASE_URL = env(
    "API_BASE_URL", default="http://localhost:8088")

VSCU_API_BASE_URL = env(
    "API_BASE_URL", default="http://localhost:8088")

# Installed apps
INSTALLED_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'django_celery_beat',
    'django_celery_results',
    'api_tracker',
    'device',
    'jazzmin',
    'dal',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_select2',
    'crispy_forms',
    'accounts',
    'commons',
    'organization',
    'transaction',
    'item_movement',
    'customer',
    'item',
    'sales_items',
    'purchases',
    'imports',
    'corsheaders',
    'bootstrap5',
    "crispy_bootstrap5",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

# Middleware settings
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'  # Allow same-origin iframes

ROOT_URLCONF = 'etimsx.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'etimsx.wsgi.application'

# Celery Configuration
# CELERT_BROKER_URL ='pyamqp://guest@localhost//'
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default="amqp://admin:mysecurepassword@rabbitmq:5672/")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = "Africa/Nairobi"
CELERY_RESULT_BACKEND = 'django-db'


# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': env("DB_ENGINE", default="django.db.backends.sqlite3"),
#         'NAME': env("DB_NAME", default=BASE_DIR / "db.sqlite3"),
#         'USER': env("DB_USER", default=""),
#         'PASSWORD': env("DB_PASSWORD", default=""),
#         'HOST': env("DB_HOST", default=""),
#         'PORT': env("DB_PORT", default=""),
#     }
# }

# CORS settings
# CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
#     "http://localhost:3000",
#     "http://localhost:3001",
#     "http://localhost:3002"
# ])

CORS_ALLOWED_ORIGINS = [
    "https://4524-217-199-146-205.ngrok-free.app",
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:8000",  # Django itself
    "http://34.60.172.27:8001",
    "https://etimsx.herokuapp.com",  # Heroku app
]

CSRF_TRUSTED_ORIGINS = [
    "https://4524-217-199-146-205.ngrok-free.app",
    "http://34.60.172.27"
]

CORS_ALLOW_ALL_ORIGINS = True  # Allow requests from any domain
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "content-type",
    "authorization",
    "x-requested-with",
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Email settings
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="lyonsmasawa@gmail.com")

# Authentication settings
LOGIN_URL = env("LOGIN_URL", default="/accounts/login/")
LOGIN_REDIRECT_URL = env("LOGIN_REDIRECT_URL", default="/api/organization/")
LOGOUT_REDIRECT_URL = env("LOGOUT_REDIRECT_URL", default="/accounts/login/")

# Static and Media files
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
        },
        "simple": {
            "format": "[%(levelname)s] %(message)s"
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/vscu_api.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": [],
            "level": "DEBUG",
            "propagate": True,
        },
        "celery": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "vscu_api": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_DEMO_CONFIG = {
    "tin": "DEMO123456789",
    "branch_id": "00",
    "device_serial_number": "DEMO-DEVICE-001",
    "device_id": "DEMO-DEVICE-ID",
    "control_unit_id": "DEMO-CU-ID",
    "internal_key": "DEMO-INTERNAL-KEY",
    "sign_key": "DEMO-SIGN-KEY",
    "communication_key": "DEMO-COMM-KEY",
}

JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Etimsx Admin",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "Etimsx",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "Etimsx",

    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": "books/img/logo.png",

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": None,

    # Logo to use for login form in dark themes (defaults to login_logo)
    "login_logo_dark": None,

    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,

    # Welcome text on the login screen
    "welcome_sign": "Welcome to the etimsx",

    # Copyright on the footer
    "copyright": "Etimsx Ltd",

    # List of model admins to search from the search bar, search bar omitted if excluded
    # If you want to use a single search field you dont need to use a list, you can use a simple string
    "search_model": ["auth.User", "auth.Group"],

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    ############
    # Top Menu #
    ############

    # Links to put along the top menu
    "topmenu_links": [

        # Url that gets reversed (Permissions can be added)
        {"name": "Home",  "url": "admin:index",
            "permissions": ["auth.view_user"]},

        # external url that opens in a new window (Permissions can be added)
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues",
            "new_window": True},

        # model admin to link to (Permissions checked against model)
        {"model": "auth.User"},

        # App with dropdown menu to all its models pages (Permissions checked against models)
        {"app": "books"},
    ],

    #############
    # User Menu #
    #############

    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues",
            "new_window": True},
        {"model": "auth.user"}
    ],

    #############
    # Side Menu #
    #############

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": True,

    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],

    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],

    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": ["auth", "books", "books.author", "books.book"],

    # Custom links to append to app groups, keyed on app name
    "custom_links": {
        "books": [{
            "name": "Make Messages",
            "url": "make_messages",
            "icon": "fas fa-comments",
            "permissions": ["books.view_book"]
        }]
    },

    # Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,

    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
    "use_google_fonts_cdn": True,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,

    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    # Add a language dropdown into the admin
    # "language_chooser": True,
}
