import gevent
import gevent.monkey
from gevent.threading import _DummyThread
gevent.monkey.patch_all()
import confluent_kafka
from concurrent.futures import Future
import time
import os
import sys
import time
import json
import logging
from uuid import uuid4
from gevent.threadpool import ThreadPool
loop = gevent.get_hub().loop
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

class ProducerAdapter(object):

    def __init__(self, configs):
        self._stopped = False
        self._producer = confluent_kafka.Producer(configs)
        self._executor = ThreadPool(maxsize=1)
        self._loop_f = self._poll_loop

    def start(self):
        self._poll_task = self._executor.spawn(self._loop_f)

    def stop(self):
        self._stopped = True
        self._poll_task.result()

    def _poll_loop(self):
        while not self._stopped:
            self._producer.poll(0)
            time.sleep(0.1)
        self._producer.flush()

    def produce(self, topic, message, key=None):
        result = Future()
        start = time.time()

        def on_delivery(err, msg):
            diff = time.time() - start
            if err:
                result.set_exception(err)
            else:
                result.set_result((msg, diff))

        self._producer.produce(topic=topic, key=key, value=message, on_delivery=on_delivery)
        return result

def _stats_cb(stats_str):
    stats = json.loads(stats_str)
    print(stats)

def _stats_cb1(data):
    loop.run_callback_threadsafe(_stats_cb, data)

class Logger:
    def _log_in_gevent(self, args):
        logger.log(*args)

    def log(self, *args):
        loop.run_callback(self._log_in_gevent, args)

def create_producer():
    if "BOOTSTRAP_SERVERS" not in os.environ:
        print("BOOTSTRAP_SERVERS env variable required")
        sys.exit(1)
    if "TOPIC" not in os.environ:
        print("TOPIC env variable required")
        sys.exit(1)

    bootstrap_servers = os.environ["BOOTSTRAP_SERVERS"]

    producer = ProducerAdapter({
        "bootstrap.servers": bootstrap_servers,
        "statistics.interval.ms": 1000,
        #"stats_cb": _stats_cb1,
        "logger": Logger(),
        "debug": "all"
    })
    return producer

producer = create_producer()
producer.start()

class ChronoPublisher:
    def __init__(self, topic, *args, **kwargs):
        global producer
        self.producer = producer
        self.topic = topic

    def publish_events(self, events):
        ret = []
        for event in events:
            ret.append(self.producer.produce(self.topic, event[1], event[0]))
        return ret

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self,*args, **kwargs):
        pass



class chrono_mc_service:
    @staticmethod
    def request_context():
        return chrono_mc_service()

    def __enter__(self, *args, **kwargs):
        pass

    def __exit__(self,*args, **kwargs):
        pass

def get_random_partition_key():
    return str(uuid4())

def construct_ChronoMCIntegrationTestEvent(execution_time, random_id):
    return str(uuid4())

STREAM_NAME = os.environ["TOPIC"]

class ChronoMCProducerIntegrationTestTask:
    producer_sleep = 0
    event_load = 10000

    def run(self):
        # type: () -> None
        ids = [str(uuid4()) for _ in range(self.event_load)]
        self.write_to_s3(ids)

        with chrono_mc_service.request_context():
            publishing_start_time = time.time()
            with ChronoPublisher(STREAM_NAME, send_async=True) as p:

                for random_id in ids:
                    start_time = time.time()
                    p.publish_events(
                        [
                            (
                                get_random_partition_key(),
                                construct_ChronoMCIntegrationTestEvent(
                                    execution_time=None,
                                    random_id=random_id,
                                ),
                            )
                        ]
                    )
                    single_event_emission = time.time() - start_time
                    time.sleep(self.producer_sleep)

        total_job_time = time.time() - publishing_start_time
        actual_throughput = float(self.event_load) / total_job_time

    def write_to_s3(self, ids):
        # type: (List[str]) -> None
        # chrono_mc_service.file_storage.put_file(
        #     namespace=NAMESPACE, keyname=self.produced_write_path, data=json.dumps(ids)
        # )
        pass

if __name__ == "__main__":
    runner = ChronoMCProducerIntegrationTestTask()
    while True:
        runner.run()
        print("run completed")
        time.sleep(1)
