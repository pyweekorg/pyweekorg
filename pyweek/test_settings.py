"""Django settings for running automated tests."""

from __future__ import annotations

import os
from pathlib import Path

from pyweek.settings import *  # noqa: F403,F401

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "test-secret-key")
PAGES_DIR = str(BASE_DIR / "pyweek" / "challenge" / "media")
MEDIA_ROOT = os.environ.get("PYWEEK_MEDIA_ROOT", str(BASE_DIR / "test-media"))
MEDIA_URL = "/media/dl/"
STATIC_URL = "/static/"
STATICFILES_DIRS = [str(BASE_DIR / "pyweek" / "challenge" / "media")]

RECAPTCHA_PUBLIC_KEY = "test-public"
RECAPTCHA_PRIVATE_KEY = "test-private"

if os.environ.get("POSTGRES_DB"):
    DATABASES["default"] = {  # noqa: F405
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
    }
else:
    DATABASES["default"] = {  # noqa: F405
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
