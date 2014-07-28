#coding
# This module encapsulate underling communication between node .
# Implement RPC server.
import os
import sys
import errno
import socket
import select
import signal
import traceback

from buzz.lib.serialize import serialize
from buzz.lib.rpc.transport import Transport
from buzz.lib.workers.coroutine_worker import CoroutineWorker
from buzz.lib.rpc.utils import build_response, parse_request_args
from buzz.lib.rpc.error import RPCError, CMDNotFoundError, ServerError

class RPCServer(CoroutineWorker):
    def handle_request(self, sock=None, client=None, addr=None):
        transport = Transport(client, logger=self.file_logger)
        results = []
        request = transport.recv()
        if request:
            id = request['id']
            try:
                method_name = request['method']
                args, kwargs = parse_request_args(request['params'])
                result = self.call_method(method_name, args, kwargs)
                resp = build_response(result, id)
            except RPCError as e:
                resp = build_response(None, id=id, error=e)
            except Exception as e:
                self.file_logger.error(traceback.format_exc())
                resp = build_response(None, id=id, error=ServerError())
            return transport.send(resp)
        else: # client closed
            return -1

    def call_method(self, name, args, kwargs):
        self.file_logger.debug("call method %s", name)
        method = self.find_method(name)
        if not method:
            raise CMDNotFoundError(name)
        else:
            return method(*args, **kwargs)

    def find_method(self, method):
        if not hasattr(self, 'methods'):
            self.methods = self.get_all_method()
        return self.methods.get(method)

    def get_all_method(self):
        methods = {}
        for attr in dir(self):
            if attr.startswith('cmd_') and callable(getattr(self, attr)):
                methods[attr[4:]] = getattr(self, attr)

        return methods
