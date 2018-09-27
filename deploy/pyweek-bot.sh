#!/bin/bash
echo "RUNNING PYWEEK BOT"
export DJANGO_SETTINGS_MODULE=prod_settings
cd www
. venv/bin/activate
python manage.py bot
