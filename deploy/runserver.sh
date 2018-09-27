#!/bin/bash

PROJDIR="/home/pyweek/www"
#PORT=8765
PORT=8766
PIDFILE="/home/pyweek/www/gunicorn.pid"
LOGFILE="/home/pyweek/www/gunicorn.log"
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
    fi
}


function start () {
    cd $PROJDIR

    echo "Starting gunicorn"
    $VENV/bin/gunicorn --bind localhost:$PORT -w 20 --timeout 300 --pid "$PIDFILE" --log-file "$LOGFILE" -D pyweek.wsgi:application
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

