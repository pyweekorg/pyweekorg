#!/bin/bash
ROOT=/home/pyweek/www
PYTHON=${ROOT}/venv/bin/python
MANAGE_PY=${ROOT}/manage.py
DJANGO_SETTINGS_MODULE=prod_settings ${PYTHON} ${MANAGE_PY} "$@"
