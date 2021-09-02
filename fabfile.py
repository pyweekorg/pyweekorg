import datetime
from fabric.api import env, run, put, get, local
from fabric.context_managers import cd, shell_env
from fabric.contrib.project import rsync_project

env.hosts = ['pyweek@pyweek.org']


rsync_exclusions = [
    '*.pyc',
    '*.pyo',
    '*.swp',
    '__pycache__',
    '.git',
    'venv*',
    '.venv*',
    '.mypy_cache',
    '/media',
    'dumps',
    'db.sqlite3',
    'dev_settings.py',
    'source',
    'fabfile.py',
    '/deploy',
    'deadmigrations',
    'out',
    'stubs'
]

PYTHON = "/usr/bin/python3.9"


def publish():
    """Redeploy the site."""
    run('mkdir -p www logs')
    rsync_project(local_dir='./', remote_dir='www/', exclude=rsync_exclusions)
    rsync_project(local_dir='./deploy/', remote_dir='www/')
    with cd('/home/pyweek/www/'):
        run('chmod 600 prod_settings.py')
        if run('test -x venv/bin/pip', quiet=True).failed:
            run('{} -m venv venv'.format(PYTHON))

        path = run('echo "${PATH}"', quiet=True)
        with shell_env(
                DJANGO_SETTINGS_MODULE='prod_settings',
                VIRTUAL_ENV='/home/pyweek/www/venv',
                PATH='/home/pyweek/www/venv/bin:' + path,
                PYTHONPATH='/home/pyweek/www/'):
            run('pip install -r requirements.txt -r requirements-prod.txt')
            run('django-admin collectstatic -v 0 -c --no-input')
            run('django-admin migrate')
            run('./runserver.sh reload')
        run('crontab crontab.txt')


def quick_publish():
    """Redeploy very minor code/template changes."""
    rsync_project(local_dir='./', remote_dir='www/', exclude=rsync_exclusions)
    with cd('/home/pyweek/www/'):
        path = run('echo "${PATH}"', quiet=True)
        with shell_env(
                DJANGO_SETTINGS_MODULE='prod_settings',
                VIRTUAL_ENV='/home/pyweek/www/venv',
                PATH='/home/pyweek/www/venv/bin:' + path):
            run('python manage.py collectstatic -v 0 -c --no-input')
            run('./runserver.sh reload')


def pg_dump():
    """Create a PostgreSQL database dump and download it."""
    today = datetime.date.today()
    fname = '{today:%Y-%m-%d}-rjones_pyweek.sql.gz'.format(today=today)
    run('mkdir -p dumps')
    local('mkdir -p dumps')
    with cd('/home/pyweek/dumps'):
        run('PGUSER=rjones_pyweek pg_dump rjones_pyweek | gzip >' + fname)
        get(fname, local_path='dumps/' + fname)
