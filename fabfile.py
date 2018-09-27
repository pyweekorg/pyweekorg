import datetime
from fabric.api import env, run, put, get, local
from fabric.context_managers import cd, shell_env
from fabric.contrib.project import rsync_project

env.hosts = ['pyweek@pyweek.org:6185']


rsync_exclusions = [
    '*.pyc',
    '*.pyo',
    '__pycache__',
    '.git',
    'venv',
    'dumps',
    'db.sqlite3',
    'dev_settings.py',
    'source',
    'fabfile.py',
    'deploy'
]

PYTHON = "/home/pyweek/.local/bin/python"


def publish():
    run('mkdir -p www')
    rsync_project(local_dir='./', remote_dir='www/', exclude=rsync_exclusions)
    rsync_project(local_dir='./deploy/', remote_dir='www/')
    with cd('/home/pyweek/www/'):
        run('chmod 600 prod_settings.py')
        if run('test -x venv/bin/pip', quiet=True).failed:
            run('virtualenv --python={} venv'.format(PYTHON))
            run('venv/bin/python get-pip.py')

        # Symlink the media directory (containing uploads) into place
        if run('test -d media', quiet=True).failed:
            run('ls -s ../media')

        path = run('echo "${PATH}"', quiet=True)
        with shell_env(
                DJANGO_SETTINGS_MODULE='prod_settings',
                VIRTUAL_ENV='/home/pyweek/www/venv',
                PATH='/home/pyweek/www/venv/bin:' + path):
            run('pip install --upgrade setuptools distribute')
            run('pip install -r requirements.txt -r prod-requirements.txt')
            run('python manage.py collectstatic -v 0 -c --no-input')
            run('python manage.py migrate')
            run('./runserver.sh reload')
        run('crontab crontab.txt')


def pg_dump():
    """Create a PostgreSQL database dump and download it."""
    today = datetime.date.today()
    fname = '{today:%Y-%m-%d}-rjones_pyweek.sql.gz'.format(today=today)
    run('mkdir -p dumps')
    local('mkdir -p dumps')
    with cd('/home/pyweek/dumps'):
        run('PGUSER=rjones_pyweek pg_dump rjones_pyweek | gzip >' + fname)
        get(fname, local_path='dumps/' + fname)
