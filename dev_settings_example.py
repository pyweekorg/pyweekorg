from pyweek.settings import *

from os.path import join, dirname

def p(*path):
    return join(dirname(__file__), *path)


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = [
    ('Your Name', 'nobody@example.com'),
]

HOSTNAME = "localhost"
ALLOWED_HOSTS = ['.pyweek.org', 'localhost']
MEDIA_ROOT = p('media', 'dl')
MEDIA_URL = '/media/dl/'

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    p('pyweek', 'challenge', 'media'),
]

PAGES_DIR = p('pyweek', 'challenge', 'media')

DATABASES['default'] = dict(
    ENGINE = 'django.db.backends.postgresql_psycopg2',
    HOST = '172.17.0.2',
    NAME = 'pyweek',
    USER = 'pyweek',
    PASSWORD = 'hunter2',
)

SECRET_KEY = ';z{!:d:DK^Uf6}-R~HNn$+kv)c{9ILD}uWa&@nu#~uHI",5Zv{CMmC"z`WE|&I'


RECAPTCHA_PUBLIC_KEY = 'aaaa'
RECAPTCHA_PRIVATE_KEY = 'bbbb'
