import confluent_kafka
from gevent import monkey, get_hub, spawn
from gevent.event import AsyncResult
from gevent.threadpool import ThreadPoolExecutor
from random import randbytes
import time
import numpy
import os
import sys
import multiprocessing
monkey.patch_all(subprocess=False)
original_sleep = monkey.saved['time']['sleep']


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


class Stats(object):

    def __init__(self):
        self.messages = []

    def add(self, messages):
        self.messages.extend(messages)

    def print(self):
        latency = [m.get()[1] for m in self.messages]

        min_latency = numpy.min(latency) * 1000
        avg_latency = numpy.average(latency) * 1000
        percentile_latency = numpy.percentile(latency, 99.9) * 1000
        max_latency = numpy.max(latency) * 1000

        print(f"Latency - min: {min_latency:.2f} ms, "
              + f"avg: {avg_latency:.2f} ms,"
              + f" 99.9th percentile: {percentile_latency:.2f} ms,"
              + f" max: {max_latency:.2f} ms")
        self.messages = []


# From time to time it has to return control to
# the gevent loop to execute other things like
# produce requests.
# If you increment the modulo, latency increases because has very few CPU time
# to execute other things.
#
# In gevent it's better to execute CPU intensive code in a different
# native thread, with ThreadPoolExecutor, as suggested here:
# https://www.gevent.org/api/gevent.threadpool.html
# Set the CPU_INTENSIVE env variable to "tpe" to run it in
# a ThreadPoolExecutor.
#
# Even if using the TPE latency increases as only one thread can hold the
# GIL. Unpatched multiprocessing or C/C++ modules are better
# to execute CPU intensive code.
#
# Set the CPU_INTENSIVE env variable to "process" to run it
# in a subprocess. This way latency is reduced to the original value.
#
def cpu_intensive(sleep, q=None):
    i = 0
    try:
        while True:
            i = (i + 1) % 1000000
            if i == 0:
                sleep(0.001)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    if "BOOTSTRAP_SERVERS" not in os.environ:
        print("BOOTSTRAP_SERVERS env variable required")
        sys.exit(1)
    if "TOPIC" not in os.environ:
        print("TOPIC env variable required")
        sys.exit(1)

    bootstrap_servers = os.environ["BOOTSTRAP_SERVERS"]
    topic = os.environ["TOPIC"]
    linger_ms = os.environ.get("LINGER_MS", "10")

    N = int(os.environ.get("PRODUCE_RATE", "3000"))
    stats_interval = int(os.environ.get("STATS_INTERVAL", "10"))
    cpu_intensive_var = os.environ.get("CPU_INTENSIVE", "coroutine")

    # Run a CPU intensive process in different ways
    subprocess = None
    task = None
    tpe = ThreadPoolExecutor(max_workers=1)
    if cpu_intensive_var == "tpe":
        task = tpe.submit(cpu_intensive, original_sleep)
    elif cpu_intensive_var == "process":
        subprocess = multiprocessing.Process(target=cpu_intensive,
                                             args=(original_sleep,))
        subprocess.start()
    else:
        task = spawn(cpu_intensive, time.sleep)

    stats = Stats()
    producer = ProducerAdapter({"bootstrap.servers": bootstrap_servers,
                                "linger.ms": linger_ms})
    producer.start()

    try:
        # produce N messages per seconds
        seconds = 0
        while True:
            begin = time.time()
            messages = [producer.produce(topic, randbytes(1024))
                        for i in range(N)]
            stats.add(messages)
            sleep_for = max(0, 1 - (time.time() - begin))
            time.sleep(sleep_for)

            # every [stats_interval] seconds print the statistics
            # and start again
            seconds = (seconds + 1) % stats_interval
            if seconds == 0:
                stats.print()
    except KeyboardInterrupt:
        print("exiting")
