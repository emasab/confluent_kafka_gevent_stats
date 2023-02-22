import confluent_kafka
from gevent import get_hub
from gevent.event import AsyncResult
from gevent.threadpool import ThreadPoolExecutor
from random import randbytes
import time
import os
import sys


class ProducerAdapter(object):

    def __init__(self, configs):
        self._stopped = False
        self._producer = confluent_kafka.Producer(configs)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._loop = get_hub().loop

    def start(self):
        self._poll_task = self._executor.submit(self._poll_loop)

    def stop(self):
        self._stopped = True
        self._poll_task.result()

    def _poll_loop(self):
        while not self._stopped:
            self._producer.poll(0.1)
        self._producer.flush()

    def produce(self, topic, message):
        result = AsyncResult()
        start = time.time()

        def on_delivery_gevent(err, msg):
            diff = time.time() - start
            if err:
                result.set_exception(err)
            else:
                result.set_result((msg, diff))

        def on_delivery(err, msg):
            self._loop.run_callback_threadsafe(on_delivery_gevent, err, msg)

        self._producer.produce(topic, message, on_delivery=on_delivery)
        return result


class App(object):

    def create_producer(self):
        if "BOOTSTRAP_SERVERS" not in os.environ:
            print("BOOTSTRAP_SERVERS env variable required")
            sys.exit(1)
        if "TOPIC" not in os.environ:
            print("TOPIC env variable required")
            sys.exit(1)

        bootstrap_servers = os.environ["BOOTSTRAP_SERVERS"]
        linger_ms = os.environ.get("LINGER_MS", "0")
        max_inflight_per_connection = os.environ.get("MAX_INFLIGHT", "1")

        producer = ProducerAdapter({"bootstrap.servers": bootstrap_servers,
                                    "max.in.flight.requests.per.connection": max_inflight_per_connection,
                                    "linger.ms": linger_ms})
        return producer


    def __init__(self):
        self.topic = os.environ["TOPIC"]
        self.producer = self.create_producer()
        self.producer.start()

    def __call__(self, environ, start_response):
        _, latency = self.producer.produce(self.topic, randbytes(1024)).get()
        data = f"Message sent, latency: {latency * 1000:0.2f} ms\n"
        start_response("200 OK", [
            ("Content-Type", "text/plain; utf-8"),
            ("Content-Length", str(len(data)))
        ])
        return iter([data.encode("utf-8")])


def create_app():
    return App()
