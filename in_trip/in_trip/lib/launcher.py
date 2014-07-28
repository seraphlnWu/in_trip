#coding=utf-8

# This module start prefork module

from buzz.lib.arbiter import Arbiter
from buzz.lib.utils import import_app

class Launcher(object):
    def __init__(self, worker_uri, config_file, section):
        self.worker_uri = worker_uri
        self.config_file = config_file
        self.section = section

    @property
    def worker_class(self):
        return import_app(self.worker_uri)

    def run(self):
        Arbiter(self, self.worker_class, self.config_file, self.section).run()
