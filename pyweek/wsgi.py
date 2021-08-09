import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyweek.settings")

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
from raven.contrib.django.middleware.wsgi import Sentry

django_app = get_wsgi_application()
sentrified_app = Sentry(django_app)


def application(environ, start_response):
    """Quick WSGI middleware to set host and scheme headers."""
    environ.update(
        HTTP_HOST='pyweek.org',
        HTTP_X_FORWARDED_PROTO='https',
    )
    return sentrified_app(environ, start_response)

