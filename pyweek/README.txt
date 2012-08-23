How to set up a PyWeek-like site:

1. install requirements.txt
2. either use pyweek/*.py as your site's configuration or somehow merge it with
   your own.
3. create a local settings file pointed to by DJANGO_LOCAL_SETTINGS
   - most notably you will need to set the MEDIA_* and STATIC_* variables, and
     the database etc.

Collect the static files:

DJANGO_LOCAL_SETTINGS=path/to/pyweek-local-settings.py python -m pyweek.manage collectstatic
