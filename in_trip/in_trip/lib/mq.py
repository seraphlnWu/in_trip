#coding=utf-8

# this is a message queue base on redis

import time

import redis

from buzz.lib.config import Config
from buzz.lib.utils import parse_db_str
from buzz.lib.serialize import serialize, deserialize

class MessageQueue(object):

    def __init__(self, host, port):
        self._conn = redis.Redis(connection_pool=redis.BlockingConnectionPool(max_connections=15, host=host, port=port))

    def push(self, queue, msg):
        self._conn.rpush(queue, serialize(msg))

    def pop(self, queue):
        msg = self._conn.lpop(queue)
        return deserialize(msg) if msg else msg

    def popright(self, queue):
        msg = self._conn.rpop(queue)
        return deserialize(msg) if msg else msg

    def delete(self, queue):
        self._conn.delete(queue)

    def sismember(self, queue, value):
        return self._conn.sismember(queue, value)

    def sadd(self, queue, value):
        return self._conn.sadd(queue, value)

    def srem(self, queue, value):
        return self._conn.srem(queue, value)

    def qsize(self, queue):
        if 'Set' in queue:
            return self._conn.scard(queue)
        else:
            return self._conn.llen(queue)

addr = Config().get("rd", "main")
MQ = MessageQueue(**parse_db_str(addr))

if __name__ == '__main__':
    print MQ.qsize("gzmama.com")
