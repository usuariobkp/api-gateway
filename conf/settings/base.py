"""
Django settings for sample project.

Generated by 'django-admin startproject' using Django 2.0.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import environ
from elasticsearch_dsl.connections import connections

env = environ.Env(DEBUG=(bool, False),) # set default values and casting

# SETTINGS_DIR = /conf/settings
SETTINGS_DIR = environ.Path(__file__) - 1
environ.Env.read_env(SETTINGS_DIR('.env'))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# ROOT_DIR = /
BASE_DIR = SETTINGS_DIR - 2


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'tihf+p+1gxjd)z&sq(v)h2=nm1)%6e(jl%&wpfo(oc^@nx@m4r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG') # False if not in os.environ
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

VENDOR_APPS = [
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',

    "django_rq",
    'django_filters',
    'axes',
    'admin_honeypot',
    'solo.apps.SoloAppConfig',
]

LOCAL_APPS = [
    'api_management.apps.common',
    'api_management.apps.analytics',
    'api_management.apps.api_registry',
]

INSTALLED_APPS += VENDOR_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'conf.urls'


def export_vars(_):
    data = {
        'PROJECT_VERSION': env('PROJECT_VERSION', default='local')
    }
    return data


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'conf.settings.base.export_vars',
            ],
        },
    },
]

WSGI_APPLICATION = 'conf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR('db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Argentina/Buenos_Aires'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
# Do not use a dir inside the project in production environments
MEDIA_ROOT = env('MEDIA_ROOT', default=BASE_DIR('/media/'))
MEDIA_URL = '/media/'
STATIC_ROOT = (BASE_DIR - 1)('static')
STATIC_URL = '/static/'

SITE_ID = 1

REDIS_HOST = env('REDIS_HOST', default='localhost')
REDIS_PORT = 6379

RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },

    'create_model': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },

    'generate_analytics': {
        'HOST': env('REDIS_HOST', default='localhost'),
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },

    'generate_indicators_csv': {
        'HOST': env('REDIS_HOST', default='localhost'),
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },

    'compress_csv_files': {
        'HOST': env('REDIS_HOST', default='localhost'),
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },
}

KONG_TRAFFIC_URL = ""
KONG_ADMIN_URL = ""

URLS_PREFIX = 'management'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'axes_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

AXES_CACHE = 'axes_cache'
HTTPLOG2_ENDPOINT = ""

SESSION_COOKIE_NAME = 'mgmtsessionid'

RQ_SHOW_ADMIN_LINK = True

AXES_FAILURE_LIMIT = 10

ELASTIC_SEARCH_HOST = env('ELASTIC_SEARCH_HOST', default='localhost')

connections.create_connection(hosts=[ELASTIC_SEARCH_HOST])
