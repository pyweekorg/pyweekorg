#!/bin/bash

PROJDIR="/home/pyweek/src"
PORT=8765
PIDFILE="/home/pyweek/gunicorn.pid"
LOGFILE="/home/pyweek/gunicorn.log"
VENV="/home/pyweek/pyweek-virtual"

export DJANGO_LOCAL_SETTINGS=/home/pyweek/pyweek-local-settings.py


function stop () {
    if [ -f $PIDFILE ] ; then
        echo "Stopping gunicorn"
        kill $(cat $PIDFILE)
        rm -f "$PIDFILE"
    fi
}


function start () {
    cd $PROJDIR

    echo "Starting gunicorn"
    $VENV/bin/gunicorn --bind localhost:$PORT -w 4 --pid "$PIDFILE" --log-file "$LOGFILE" -D pyweek.wsgi:application
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
        sleep 1
        start
        ;;

    *)
        echo "Usage: runserver.sh start|stop|restart"
esac

