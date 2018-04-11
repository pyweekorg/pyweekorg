Pyweek.org website
==================

This website runs the pyweek.org challenge.


Developing
----------

Database
''''''''

The production site runs against a PostgreSQL database. You can run one of
these using Docker for development purposes::

    docker run --name pyweek-postgresql postgres:latest

Environment
'''''''''''

How to set up a PyWeek-like site:

1. Create a virtualenv
2. Install ``requirements.txt`` and ``requirements-dev.txt``
3. Create a local settings file pointed to by an environment variable named
   ``DJANGO_LOCAL_SETTINGS``. You will need to set the ``MEDIA_*`` and
   ``STATIC_*`` variables, and add database configuration etc.

Collect the static files::

    DJANGO_LOCAL_SETTINGS=path/to/pyweek-local-settings.py python -m pyweek.manage collectstatic

(Alternatively set up `static url patterns
<https://docs.djangoproject.com/en/2.0/howto/static-files/#serving-static-files-during-development>`_).

Running a server
''''''''''''''''

To run the dev server, use::

    PYTHONPATH=. DJANGO_LOCAL_SETTINGS=dev_settings.py django-admin.py runserver --settings=pyweek.settings
