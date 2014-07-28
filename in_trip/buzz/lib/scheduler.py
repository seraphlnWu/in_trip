#coding=utf-8
#
# This module if used for schedule url
#
import time
import threading

from buzz.lib.consts import DEFAULT_GET_URL_COUNT, MIN_INTERVAL

class Scheduler(object):
    UPDATE_TIME_INTERVAL = {5: MIN_INTERVAL,
                            3: 4.5,
                            2: 5,
                            1: 7,
                            0: 7}

    def __init__(self):
        self.queues = []
        td = threading.Thread(target=self.update_queue_point)
        td.daemon = True # auto exit
        td.start()
        # self.td = td

    def schedule(self):
        for queue in self.queues:
            if not queue.tail():
                return queue.get()
        return None

    def update(self, schedulers):
        queues = []
        for prior_level, items in schedulers.iteritems():
            queue = Queue(items, prior_level)
            queues.append(queue)
        queues.sort(key=lambda x: x.priority, reverse=True) # order by priority desc
        self.queues = queues

    def update_queue_point(self):
        while 1:
            for queue in self.queues:
                if queue.tail() and time.time() > (self.UPDATE_TIME_INTERVAL[queue.priority] + queue.update_time):
                    queue.relocate()

            time.sleep(1.0) # 1 seconds


class Queue(object):
    """Synchronize Queue
    """
    def __init__(self, items, priority=0):
        self.priority = priority
        self.update_time = time.time()
        self.q = list(items)
        self._head = 0 # point to queue head
        self._lock = threading.Semaphore()

    def qsize(self):
        return len(self.q)

    def tail(self):
        result = True if self._head >= self.qsize() else False
        return result

    def empty(self):
        return True if self.qsize() else False

    def put(self, item):
        self._lock.acquire()
        self.q.append(item)
        self._lock.release()

    def get(self):
        self._lock.acquire()
        domain = self.q[self._head]
        self._head += 1
        self._lock.release()
        return domain

    def relocate(self, point=0):
        self._lock.acquire()
        self._head = point
        self.update_time = time.time()
        self._lock.release()

class UrlPool(object):
    def __init__(self, request_map, schedulers):
        self.empty_domains = []
        self.empty_domains_mutex = threading.Semaphore()
        self.request_map = request_map
        self.scheduler = Scheduler()
        self.scheduler.update(schedulers)
        self.cache = {}

    def append_urls(self, request_map, count=DEFAULT_GET_URL_COUNT):
        for domain, requests in request_map.iteritems():
            if domain in self.request_map:
                self.request_map[domain].extend(requests)
            else:
                self.request_map[domain] = requests

            if len(requests) < count:
                self.update_cache(domain)

    def get(self, timeout=0.05):
        delay = 0.0001 # 100 us
        endtime = time.time() + timeout
        while 1:
            domain = self.next_domain()
            if domain: # and domain in self.request_map and self.request_map[domain]:
                try:
                    url = self.request_map[domain].pop(0)
                    if url:
                        break
                except (KeyError, IndexError) as e:
                    self.put_empty_domain(domain)
            remaining = endtime - time.time()
            if remaining < 0:
                url = None
                break
            delay = min(delay, remaining)
            time.sleep(delay)

        return url

    def next_domain(self):
        """Return next available domain according to priority algorithm
        """
        return self.scheduler.schedule()

    def put_empty_domain(self, domain):
        self.empty_domains_mutex.acquire()
        if domain not in self.empty_domains:
            if self.cache.get(domain, 0) < time.time():
                self.empty_domains.append(domain)
        self.empty_domains_mutex.release()

    def pop_empty_domain(self, count=None):
        self.empty_domains_mutex.acquire()
        if not count:
            count = len(self.empty_domains)
        empty_domains = []
        while count and self.empty_domains:
            domain = self.empty_domains.pop(0)
            self.update_cache(domain, 2) # two seconds

            empty_domains.append(domain)
            count -= 1

        self.empty_domains_mutex.release()
        return empty_domains

    def update_scheduler(self, schedulers):
        self.scheduler.update(schedulers)

    def update_cache(self, domain, seconds=3*60):
        self.cache[domain] = time.time() + seconds

if __name__ == '__main__':
    import time
    from buzz.lib.rpc.client import RPCClient
    client = RPCClient("127.0.0.1:6262")
    sr = client.call('get_scheduler')
    r = client.call('get_urls', "*")
    if 'error' not in r:
        url_pool = UrlPool(r['result'], sr['result'])
        empty_domains = ['ifeng.com', 'sina.com.cn']
        r = client.call("get_urls", empty_domains)
        print r
        if 'error' not in r:
            url_pool.append_urls(r['result'])
        #time.sleep(60.0)
        # url_pool.scheduler.td.join()
