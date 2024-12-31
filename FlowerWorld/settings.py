"""
Django settings for FlowerWorld project.

Generated by 'django-admin startproject' using Django 5.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import environ
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env()

PORT = os.environ.get("PORT", 8000)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'flowers',
    'order',
    'user',
    'payment',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
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

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_HEADERS = [
    'Authorization',
    'Content-Type',
    'X-Requested-With',
]

CSRF_TRUSTED_ORIGINS = ['https://flowerworld-modified.onrender.com', 'https://*.127.0.0.1']

ROOT_URLCONF = 'FlowerWorld.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'FlowerWorld.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# AUTH_USER_MODEL = 'user.Account'

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env("EMAIL")
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")

# SSLCOMMERZ Configuration
# SSLCOMMERZ = {
#     'STORE_ID': env("STORID"),
#     'STORE_PASSWORD': env("STORE_PASS"),
#     'IS_SANDBOX': True,  # Set False for production
#     'SUCCESS_URL': 'https://flowerworld-modified.onrender.com/api/payment/success/',
#     'FAIL_URL': 'https://flowerworld-modified.onrender.com/api/payment/fail/',
#     'CANCEL_URL': 'https://flowerworld-modified.onrender.com/api/payment/cancel/',
#     'IPN_URL': 'https://flowerworld-modified.onrender.com/api/payment/ipn/',
# }

SSLCOMMERZ = {
    'STORE_ID': 'goswa675fa7e179b51',
    'STORE_PASSWORD': 'goswa675fa7e179b51@ssl',
    'IS_SANDBOX': True,  # Set False for production
    # 'SUCCESS_URL': 'http://127.0.0.1:8000/api/payment/success/',
    # 'FAIL_URL': 'http://127.0.0.1:8000/api/payment/fail/',
    # 'CANCEL_URL': 'http://127.0.0.1:8000/api/payment/cancel/',
    # 'IPN_URL': 'http://127.0.0.1:8000/api/payment/ipn/',
    'SUCCESS_URL': 'https://flowerworld-modified.onrender.com/api/payment/success/',
    'FAIL_URL': 'https://flowerworld-modified.onrender.com/api/payment/fail/',
    'CANCEL_URL': 'https://flowerworld-modified.onrender.com/api/payment/cancel/',
    'IPN_URL': 'https://flowerworld-modified.onrender.com/api/payment/ipn/',
}

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}