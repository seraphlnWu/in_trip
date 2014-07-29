#coding=utf-8
import time
import socket

from scribe import Scribe
from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport, TSocket

class ScribeClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.retry_period = 5 # 5秒后重新尝试
        self.retry_times = 2  # 每次尝试连接的次数
        self.retry_time = None
        self.client = None

        self.make_connection()
        #self.try_make_connection()

    def make_connection(self):
        self.sock = TSocket.TSocket(host=self.host, port=self.port)
        transport = TTransport.TFramedTransport(self.sock)
        protocol = TBinaryProtocol.TBinaryProtocol(trans=transport, strictRead=False, strictWrite=False)
        #self.sock.open()
        self.client = scribe.Client(iprot=protocol)
        transport.open()

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
                self.retry_time = now + self.retry_period

    def log(self, msg, category):
        if self.client is None:
            self.try_make_connection()

        if self.client:
            try:
                log_entry = scribe.LogEntry(category=category, message=msg)
                self.client.Log(messages=[log_entry, ])
            except (socket.error, TTransport.TTransportException) as e:
                self.sock.close()
                self.clinet = None
        else:
            raise ConnectScribedERROR()

    def close(self):
        self.sock.close()
        self.clinet = None

class ConnectScribedERROR(Exception):
    pass
