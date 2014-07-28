#coding=utf-8

class RPCError(Exception):
    code = None
    message = None

    def to_dict(self):
        return {'code': self.code, 'message': self.message}

class RPCTimeout(RPCError):
    code = 1
    message = "timeout error"

class ServerError(RPCError):
    code = 2
    message = "server error"

class CMDNotFoundError(RPCError):
    code = 3
    message = "command not found error"
    def __init__(self, command_name):
        self.message += ": %s" % command_name

class ConnectionClosedError(RPCError):
    code = 6
    message = "server close connection error"
