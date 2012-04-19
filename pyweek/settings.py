# Django settings for pyweek project.

DEBUG = False #or True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('Richard Jones', 'richard@pyweek.org'),
    ('Richard Jones', 'rjones@ekit-inc.com'),
)

MANAGERS = ADMINS

import socket
hostname = socket.gethostname()
DIARY_RSS_FILE_NEW = '/home/pyweek/media/rss/diaries.rss.new'
DIARY_RSS_FILE = '/home/pyweek/media/rss/diaries.rss'
if hostname == 'shiny':
    DATABASE_ENGINE = 'postgresql'
    DATABASE_NAME = 'rjones_pyweek'
    DATABASE_USER = 'rjones_pyweek'
    DATABASE_PASSWORD = 'NaDYNyt7'

    # Absolute path to the directory that holds media.
    # Example: "/home/media/media.lawrence.com/"
    MEDIA_ROOT = '/home2/rjones/webapps/media/dl/'
elif hostname == 'lucio-torres-ibook-g4.local':
    DATABASE_ENGINE = 'sqlite3'
    DATABASE_NAME = '/Users/lucio/tmp/pyweek-test.db'
    DATABASE_USER = ''
    DATABASE_PASSWORD = ''
    DIARY_RSS_FILE_NEW = '/Users/lucio/tmp/diaries.rss.new'
    DIARY_RSS_FILE = '/Users/lucio/tmp/diaries.rss'

    # Absolute path to the directory that holds media.
    # Example: "/home/media/media.lawrence.com/"
    MEDIA_ROOT = '/Users/lucio/src/pyweek/site/dl/'
    EMAIL_HOST = '192.168.1.10'
else:
    DATABASE_ENGINE = 'postgresql'
    DATABASE_NAME = 'rjones_pyweek'
    DATABASE_USER = 'rjones_pyweek'
    DATABASE_PASSWORD = open('/home/pyweek/database-password.txt',
        'r').read().strip()

    # Absolute path to the directory that holds media.
    # Example: "/home/media/media.lawrence.com/"
    MEDIA_ROOT = '/home/pyweek/media/dl/'

    PAGES_DIR = '/home/pyweek/lib/pyweek/challenge/media/'

if hostname == 'l-rjones':
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG

DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC' #America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = 'http://media.pyweek.org/dl/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = 'http://media.pyweek.org/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '7h+@gd=zdc=+2crk8s#1_$mh$l6&fn(8@n#g9@$g7p(==68=+5'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'pyweek.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/home/pyweek/lib/pyweek/challenge/templates',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
#    "django.core.context_processors.i18n",
    "pyweek.challenge.views.context.challenges",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    "pyweek.challenge",
)
