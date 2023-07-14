# gevent usage with confluent_kafka

# Usage

## Start the docker compose cluster

```sh
docker-compose up -d
```

# Gevent only test

## Environment variables

### Required
* *BOOTSTRAP_SERVERS*
* *TOPIC*

### Optional
* *PRODUCE_RATE* in msgs/s
* *LINGER_MS*
* *STATS_INTERVAL* stats interval in seconds

Start the test with
```sh
python gevent_kafka.py
```


# Gunicorn gevent test

Start a gunicorn server

```sh
./gunicorn.sh
```

Run a k6 test
```sh
sudo snap install k6
k6 run constant-arr-rate.js
```

# Gunicorn gthread test

Start a gunicorn server with gthread

```sh
WORKER_CLASS=gthread ./gunicorn.sh
```

Run a k6 test
```sh
sudo snap install k6
k6 run constant-arr-rate.js
