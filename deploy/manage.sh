#!/bin/bash
ROOT=/home/pyweek/www
VENV=${ROOT}/venv
PYTHON=${VENV}/bin/python
DJANGO_ADMIN=${VENV}/bin/django-admin
DJANGO_SETTINGS_MODULE=prod_settings PYTHONPATH=${ROOT} ${DJANGO_ADMIN} "$@"
