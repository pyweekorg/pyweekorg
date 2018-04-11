#!/bin/bash
source /home/pyweek/pyweek-virtual/bin/activate
export DJANGO_SETTINGS_MODULE=pyweek.settings
export DJANGO_LOCAL_SETTINGS=/home/pyweek/pyweek-local-settings.py
export PYTHONPATH=/home/pyweek/lib
cd /home/pyweek/lib/pyweek
python manage.py $*
