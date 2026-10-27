"""Settings for the local-only LinkScope demonstration."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY.strip():
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY before starting LinkScope.")

DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

INSTALLED_APPS = []
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "linkscope.urls"
WSGI_APPLICATION = "linkscope.wsgi.application"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
STATIC_ROOT = FRONTEND_DIR / "assets"
STATIC_URL = "/assets/"
WHITENOISE_STATIC_PREFIX = "/assets/"
# Unhashed bundles must revalidate, including after a workspace rebuild.
WHITENOISE_MAX_AGE = 0
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = False
