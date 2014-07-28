#encoding=utf-8

import errno
import socket
import struct
import msgpack
import logging
import traceback

#BUF_SIZE = 4 * 1024 # 4k

class Transport(object):
    def __init__(self, stream, encoding="utf-8", logger=logging.getLogger()):
        self._stream = stream
        self._packer = msgpack.Packer(encoding=encoding, default=lambda x: x.to_msgpack())
        self._unpacker = msgpack.Unpacker(encoding=None)
        self.logger = logger

    def _recv(self, length):
        #TODO: timeout
        msg = ""
        while length:
            try:
                chuck = self._stream.recv(length)
                if not chuck:
                    return None
            except socket.error as e:
                if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    continue

                if e.errno in (errno.EBADF, errno.ECONNRESET):
                    return None

                raise e
            length -= len(chuck)
            msg += chuck

        return msg

    def recv(self): # callback: msg handler
        header = self._recv(4)
        if header:
            length, = struct.unpack('<i', header)
            data = self._recv(length)

            self._unpacker.feed(data)
            return self._unpacker.unpack()
        else:
            return None

    def send(self, data):
        data = self._packer.pack(data)
        msg = struct.pack("<i%ds" % len(data), len(data), data)
        r = length = len(msg)
        while length:
            try:
                sent = self._stream.send(msg)
            except socket.error as e:
                if e.args[0] in (errno.EAGAIN, errno.ECONNABORTED,
                                 errno.EWOULDBLOCK):
                    continue
                else:
                    self.logger.error(traceback.format_exc())
                    return -1
            length -= sent
            msg = msg[sent:]

        return r

    def connect(self, addr):
        self._stream.connect(addr)

    def fileno(self):
        return self._stream.fileno()

    def close(self):
        self._stream.close()
