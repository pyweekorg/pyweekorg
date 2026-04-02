#!/bin/bash

PROJDIR="/home/pyweek/www"
PORT=8765
PIDFILE="/home/pyweek/www/gunicorn.pid"
LOGFILE="/home/pyweek/www/gunicorn.log"
ACCESS_LOGFILE="/home/pyweek/www/access.log"
VENV="/home/pyweek/www/venv"

export DJANGO_SETTINGS_MODULE=prod_settings


function stop () {
    if [ -f $PIDFILE ] ; then
        echo "Stopping gunicorn"
        kill $(cat $PIDFILE)
        rm -f "$PIDFILE"
    fi
}

function reload () {
    if [ -f $PIDFILE ] ; then
        echo "Reloading gunicorn"
        kill -HUP $(cat $PIDFILE)
    else
        start
    fi
}


function start () {
    cd $PROJDIR

    echo "Starting gunicorn"
    $VENV/bin/gunicorn --bind localhost:$PORT \
	    -w 3 --threads 20 \
	    --max-requests 600 --max-requests-jitter 100 \
	    --pid "$PIDFILE" --log-file "$LOGFILE" \
	    -D pyweek.wsgi:application \
	    --access-logfile "$ACCESS_LOGFILE"
}

case $1 in
    stop)
        stop
        ;;

    start)
        start
        ;;

    restart)
        stop
        sleep 5
        start
        ;;

    reload)
        reload
        ;;

    *)
        echo "Usage: runserver.sh start|stop|restart|reload"
esac

