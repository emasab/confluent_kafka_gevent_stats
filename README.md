# gevent usage with confluent_kafka

# Usage

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
