"""Run a disposable, authenticated STAR ballot on localhost (synthetic data only).

PYTHONPATH=. python scripts/star-rating/serve_demo.py
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pyweek.test_settings'
import django
from django.conf import settings
settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
settings.DEBUG = True
django.setup()
from django.core.management import call_command
from django.contrib.auth.models import User
from django.test import Client
from pyweek.challenge.models import Challenge, Poll, Option, Response
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from wsgiref.simple_server import make_server

call_command('migrate', verbosity=0)
challenge = Challenge.objects.create(number=42, title='PyWeek 42', start='2026-09-20', end='2026-09-27', is_rego_open=True)
user = User.objects.create_user(username='demo_voter')
poll = Poll.objects.create(challenge=challenge, title='Theme voting', description='<p>Which theme would you like to build a game around?</p>', is_open=True, is_hidden=False, is_ongoing=True, type=Poll.STAR_VOTE)
for text, value in [('A Little Further', 4), ('Borrowed Time', 2), ('Everything Connects', 5), ('Out of the Blue', None), ('Paper Trails', 0)]:
    option = Option.objects.create(poll=poll, text=text)
    if value is not None:
        Response.objects.create(poll=poll, option=option, user=user, value=value)
client = Client()
client.force_login(user)
application = StaticFilesHandler(get_wsgi_application())
def demo_app(environ, start_response):
    environ['HTTP_COOKIE'] = 'sessionid=' + client.cookies['sessionid'].value
    return application(environ, start_response)
print('Synthetic ballot: http://127.0.0.1:8766/p/1/', flush=True)
make_server('127.0.0.1', 8766, demo_app).serve_forever()
