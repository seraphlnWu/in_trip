#coding=utf-8

# This module implements timer for spider manipulating

import os
import time
import errno
import socket
import traceback
import threading
from cookielib import CookieJar # TODO: replace cookielib, because of it's inefficient.

from buzz.lib.pidfile import Pidfile
from buzz.lib.scheduler import UrlPool
from buzz.lib.rpc.error import RPCError
from buzz.lib.log import setup_file_logging
from buzz.lib.rpc import RPCServer, RPCClient
from buzz.lib.consts import SCHEDULER_INTERVAL
from buzz.lib.utils import daemonize, str2bool, set_process_owner, get_user_info

class Timer(RPCServer):

    def __init__(self, cfg):
        self.file_logger = setup_file_logging("timer", cfg.log_file)
        RPCServer.__init__(self, cfg, self.file_logger, ppid=None)
        if self.cfg.user:
            user = self.cfg.user.split(':')
            if len(user) <= 1:
                user[1] = user[0]
            self.uid, self.gid = get_user_info(*user[:2])
        else:
            # set as default
            self.uid, self.gid = os.getuid(), os.getgid()

    def setup(self):
        super(Timer, self).setup()
        self.engine_addr = self.cfg.engine_addr

        if isinstance(self.cfg.daemonize, basestring):
            self.daemonize = str2bool(self.cfg.daemonize)

        if self.cfg.pidfile is not None:
            self.pidfile = Pidfile(self.cfg.pidfile)
        else:
            self.pidfile = None

    def set_process_owner(self, uid, gid):
        try:
            set_process_owner(uid, gid)
        except OSError as e:
            if e.errno == errno.EPERM:
                self.file_logger.warning("Set proc username need sudo permission, use default user instead")
            else:
                raise e

    def init_process(self):
        self.set_process_owner(self.uid, self.gid)
        super(Timer, self).init_process()
        if self.daemonize:
            daemonize()

        if self.pidfile:
            self.pidfile.create(self.pid)
        self.rpc = RPCClient(self.engine_addr)
        self.init_pool()
        self._tds = []
        # get urls
        td = threading.Thread(target=self.get_urls)
        td.start()
        self._tds.append(td)
        # update scheduler
        td2 = threading.Thread(target=self.update_scheduler)
        td2.start()
        self._tds.append(td2)

    def stop(self):
        super(Timer, self).stop()
        self.rpc.close()
        for td in self._tds:
            td.join(0.2)

        if self.unix_socket:
            os.unlink(self.unix_socket)

    def init_pool(self): # init url pool
        sr = self.rpc.call('get_scheduler')
        r = self.rpc.call('get_urls', "*")
        if 'error' not in r:
            self.url_pool = UrlPool(r['result'], sr['result'])

    def cmd_get_url(self, timeout=0.05):
        """Get available url
        """
        request = self.url_pool.get(timeout=timeout)
        if not request:
            raise NoMoreUrlError()
        else:
            return request

    def get_urls(self): # request engine
        while self.alive:
            try:
                empty_domains = self.url_pool.pop_empty_domain(15)
                if empty_domains:
                    r = self.rpc.call("get_urls", empty_domains)
                    if 'error' not in r:
                        if r['result']:
                            self.url_pool.append_urls(r['result'])
                        else:
                            self.file_logger.warning("call rpc:get_urls faild")
                    else:
                        error = r['error']
                        self.file_logger.warning("call rpc:get_urls faild code: %d message: %s", error['code'], error['message'])
                time.sleep(0.1)
            except socket.error as e:
                time.sleep(1 * 60)
            except:
                self.file_logger.error(traceback.format_exc())


    def update_scheduler(self):
        while self.alive:
            time.sleep(SCHEDULER_INTERVAL) # reload every SCHEDULER_INTERVAL
            try:
                r = self.rpc.call("get_scheduler")
                if 'error' not in r: # TODO: wrap rpc response
                    self.url_pool.update_scheduler(r['result'])
                else:
                    error = r['error']
                    self.file_logger.warning("call rpc:get_scheduler faild code: %d message: %s", error['code'], error['message'])

            except socket.error as e:
                pass


class NoMoreUrlError(RPCError):
    code = 5
    message = "no more url"
    """
    def __init__(self, domain):
        self.message = self.message % domain
    """

if __name__ == '__main__':
    from buzz.lib.config import Config
    Config.SECTION_NAME = "timer"
    cfg = Config()
    Timer(Config()).run()
