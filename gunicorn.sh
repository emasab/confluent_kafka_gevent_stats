#!/bin/sh
TOPIC=${TOPIC:-test1}
BOOSTRAP_SERVERS=${BOOSTRAP_SERVERS:-localhost:9492}
python -m gunicorn \
    --env TOPIC=$TOPIC \
    --env BOOTSTRAP_SERVERS=$BOOSTRAP_SERVERS \
    -w 8 -k gevent 'gunicorn_gevent_kafka:create_app()'
