#coding=utf-8
import sys

import sys
import socket
import time
import scribe

from scribe import scribe
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

import logging
import time

LOG_FORMAT = "[%(asctime)s]-%(hostname)s %(levelname)s %(message)s" 

class ScribeHandler(logging.Handler):
    def __init__(self, host, port):
        super(self.__class__, self).__init__()
        if not isinstance(port, int):
            port = int(port)
        self.client = ScribeClient(host, port)
        self.hostname = socket.gethostname()

    def emit(self, record):
        try:
            # TODO: searialize record
            record.hostname = self.hostname
            self.client.log(self.format(record), record.name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self.client.close()
        logging.Handler.close(self)

class ScribeClient(object):
    def __init__(self, host, port):
        self.host = host 
        self.port = port 
        self.retry_peorid = 5 # 5秒后重新尝试
        self.retry_times = 3  # 每次尝试连接的次数
        self.retry_time = None
        self.client = None

        self.make_connection()
        #self.try_make_connection()

    def make_connection(self):
        self.sock = TSocket.TSocket(host=self.host, port=self.port)
        transport = TTransport.TFramedTransport(self.sock)
        protocol = TBinaryProtocol.TBinaryProtocol(trans=transport, strictRead=False, strictWrite=False)
        self.sock.open()
        self.client = scribe.Client(iprot=protocol, oprot=protocol)

    def try_make_connection(self):
        """
        Try to make a connection
        """
        now = time.time()
        if self.retry_time and now < self.retry_time: # 在5秒内不再重新连接
            return
        else:
            retry_times = 0
            while retry_times < self.retry_times and self.client is None:
                retry_times += 1
                self.make_connection()

            if self.client is None:
                self.retry_time = now + self.retry_peorid        

    def log(self, msg, category):
        if self.client is None:
            self.try_make_connection()

        if self.client:
            try:
                log_entry = scribe.LogEntry(category=category, message=msg)
                self.client.Log(messages=[log_entry, ])
            except socket.error:
                self.sock.close()
                self.clinet = None
                raise ConnectScribedERROR()
        else:
            raise ConnectScribedERROR()

    def close(self):
        self.sock.close()
        self.clinet = None

class ConnectScribedERROR(Exception):
    pass

def setup_logger():
    for logger_name in ['parser', 'spider']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        hdlr = ScribeHandler('127.0.0.1', 1463)
        fmt = logging.Formatter(LOG_FORMAT)
        hdlr.setFormatter(fmt)
        logger.addHandler(hdlr)


def main():
    parser_logger = logging.getLogger('parser')
    spider_logger = logging.getLogger('spider')

    parser_logger.info('this is parser')
    spider_logger.info('this is spider')

if __name__ == '__main__':
    setup_logger()
    while True:
        main()
