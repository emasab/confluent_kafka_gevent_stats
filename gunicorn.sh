#!/bin/sh
TOPIC=${TOPIC:-test1}
BOOSTRAP_SERVERS=${BOOSTRAP_SERVERS:-localhost:9492}
WORKER_CLASS=${WORKER_CLASS:-gevent}

if [ $WORKER_CLASS = "gevent" ]; then
python -m gunicorn \
    --env TOPIC=$TOPIC \
    --env BOOTSTRAP_SERVERS=$BOOSTRAP_SERVERS \
    -w 1 -k gevent 'gunicorn_gevent_kafka:create_app()'
elif [ $WORKER_CLASS = "gthread" ]; then
python -m gunicorn \
    --env TOPIC=$TOPIC \
    --env BOOTSTRAP_SERVERS=$BOOSTRAP_SERVERS \
    -w 1 -k gthread --threads 5 'gunicorn_gthread_kafka:create_app()'
fi
