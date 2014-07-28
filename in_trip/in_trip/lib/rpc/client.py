#encoding=utf-8

# Implement RPC client.
import errno
import select
import socket

from threading import Semaphore
from in_trip.lib.rpc.transport import Transport
from in_trip.lib.rpc.utils import build_request, build_response
from in_trip.lib.rpc.error import RPCTimeout, ConnectionClosedError

class RPCClient(object):
    def __init__(self, addr): # server addr
        self.addr = addr
        self._mutex = Semaphore()
        self._connected = False

    def connect(self):
        if "unix://" in self.addr:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            addr = self.addr[7:]
        else:
            host, port = self.addr.split(':')
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            addr = (host ,int(port))

        self.sock = Transport(sock)
        self.sock.connect(addr)
        self._connected = True

    def close(self):
        if hasattr(self, 'sock'):
            self.sock.close()
            self._connected = False

    def call(self, method, *args, **kwargs):
        timeout = kwargs.pop('timeout', None)
        data = build_request(method, args, kwargs)
        self._mutex.acquire()
        try:
            if not self._connected:
                 self.connect()

            sent = self.sock.send(data)
            if sent == -1:
                r = build_response(None, id=data['id'], error=ConnectionClosedError())
                self.close()
            else:
                if timeout is None:
                    r = self.sock.recv()
                else:
                    rest = select.select([self.sock, ], [], [], timeout) #TODO: check message id
                    if rest[0]:
                        r = self.sock.recv()
                    else:
                        r = build_response(None, id=data['id'], error=RPCTimeout())
                if not r:
                    self.close()
                    r = build_response(None, id=data['id'], error=ConnectionClosedError())
        except Exception as e:
            raise e
        finally:
            self._mutex.release()
        return r

    def batch_call(self):
        pass

if __name__ == '__main__':
    client = RPCClient("192.168.1.117:6262")
    print client.call("get_scheduler")
