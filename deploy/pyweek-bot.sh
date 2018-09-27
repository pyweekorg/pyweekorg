#!/bin/bash
echo "RUNNING PYWEEK BOT"
source /home/pyweek/pyweek-virtual/bin/activate
export DJANGO_SETTINGS_MODULE=pyweek.settings
export DJANGO_LOCAL_SETTINGS=/home/pyweek/pyweek-local-settings.py
export PYTHONPATH=/home/pyweek/lib
django-admin.py bot
