#coding=utf-8

import time
import threading
from collections import deque

from admin.model import Site

from in_trip.lib.mq import MQ
from in_trip.lib.rpc import RPCServer
from in_trip.lib.tyrant import tyrant
from in_trip.lib.http import HttpRequest, HttpResponse
from in_trip.lib.consts import (SCHEDULER_INTERVAL,
                             DEFAULT_GET_URL_COUNT, URL_IN_QUEUE_SET)

class Engine(RPCServer):

    def init_process(self):
        super(Engine, self).init_process()
        self._tds = []
        td = threading.Thread(target=self.load_scheduler)
        td.start()
        self._tds.append(td)
        self._put_urls = deque()
        for i in xrange(0, 3):
            td2 = threading.Thread(target=self.put_urls)
            td2.start()
            self._tds.append(td2)

        td3 = threading.Thread(target=self.log_urls_len)
        td3.start()
        self._tds.append(td3)


    def log_urls_len(self):
        while self.alive:
            time.sleep(30.0)
            self.file_logger.info("engine:%d put urls len: %7d", self.pid, len(self._put_urls))

    def stop(self):
        super(Engine, self).stop()
        for td in self._tds:
            td.join(0.2)

    def load_scheduler(self):
        while self.alive:
            scheduler = {}
            sites = {}
            for site in Site.find().sort('_id'): # load available site
                if site.prior_level in scheduler:
                    scheduler[site.prior_level].append(site)
                else:
                    scheduler[site.prior_level] = [site, ]
                sites[site.domain] = site
            self._sites = sites
            self._scheduler = scheduler
            time.sleep(SCHEDULER_INTERVAL)

    def cmd_get_scheduler(self): # return prior_level, domain map
        _scheduler = {}
        for prior_level, sites in self._scheduler.iteritems():
            _scheduler[prior_level] = [site.domain for site in sites]

        return _scheduler

    def cmd_get_urls(self, domains, count=DEFAULT_GET_URL_COUNT):
        if domains == '*':
            # domains = self._sites.keys()[:15] # random 15?
            domains = [site.domain for site in self._scheduler[5]] # top level sites
            count = 1

        elif isinstance(domains, basestring):
            domains = [domains, ]

        request_map = {}
        for domain in domains:
            c = count
            request_map[domain] = []
            while c:
                request = MQ.pop(domain)
                if request:
                    request_map[domain].append(request) #TODO: construct HttpRequest obj
                    c -= 1
                else: # if no more urls return actual count urls
                    break

        return request_map

    def cmd_update_url(self, response):
        #for r in responses:
        resp = HttpResponse(**response)
        MQ.srem(URL_IN_QUEUE_SET, resp.md5)
        tyrant.set(resp.md5, resp.to_tyrant())

    def cmd_put_urls(self, url_links, refer=None, depth=0):
        headers = {"Referer": refer} if refer else None
        for url_link in url_links:
            request = HttpRequest(url_link, depth=depth, headers=headers)
            # request.prior_level = self._sites[request.domain].prior_level
            if request.domain not in self._sites:
                self.file_logger.warning("site:%s not exists", request.domain)
            self._put_urls.append(request)

    def put_urls(self):
        while self.alive:
            while len(self._put_urls):
                request =  self._put_urls.popleft()
                if MQ.sismember(URL_IN_QUEUE_SET, request.md5):
                    continue
                r = tyrant.get(request.md5)
                if r:
                    request.from_tyrant(r)

                    if request.is_available():
                        MQ.sadd(URL_IN_QUEUE_SET, request.md5)
                        MQ.push(request.domain, request)
                else:
                    # first time
                    MQ.sadd(URL_IN_QUEUE_SET, request.md5)
                    MQ.push(request.domain, request)

            time.sleep(0.001)

        return None

if __name__ == '__main__':
    from in_trip.lib.config import Config
    Config.SECTION_NAME = "engine"
    Engine(Config()).run()
