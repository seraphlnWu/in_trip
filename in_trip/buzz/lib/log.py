#coding=utf-8
import os
import socket
import logging
from logging.config import fileConfig

from buzz.lib.pool import ConnectionPool

class ScribeHandler(logging.Handler):
    def __init__(self, host, port):
        from buzz.lib.scribe_client import ScribeClient
        logging.Handler.__init__(self) # for python 2.6 compatibility
        if not isinstance(port, int):
            port = int(port)
        self.client_pool = ConnectionPool(ScribeClient, (host, port), max_size=5)
        self.hostname = socket.gethostname()

    def emit(self, record):
        try:
            # TODO: searialize record
            record.hostname = self.hostname
            client = self.client_pool.get()
            client.log(self.format(record), record.name)
            self.client_pool.release(client)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self.client_pool.close()
        logging.Handler.close(self)

class Utf8Logger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None):
        if args:
            args = tuple([arg.encode('utf-8') if isinstance(arg, unicode) else arg for arg in args])
        logging.Logger._log(self, level, msg, args, exc_info, extra)

def setup_logging(conf_file_name):
    logging.setLoggerClass(Utf8Logger)
    fileConfig(conf_file_name, dict(__file__=conf_file_name, here=os.path.dirname(conf_file_name)), disable_existing_loggers=0)

DEFAULT_FORMAT = '[%(asctime)s] %(levelname)s "%(message)s"'

def setup_file_logging(logger_name, file_name, level=logging.INFO, log_format=DEFAULT_FORMAT, propagate=0):
    logger = logging.getLogger(None if logger_name == "root" else logger_name)
    logger.propagate = propagate
    logger.setLevel(level)
    fh = logging.FileHandler(file_name)
    fh.setLevel(level)
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger
