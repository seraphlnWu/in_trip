#coding=utf-8

import time

import redis
import MySQLdb
from pymongo import MongoClient

from buzz.lib.config import Config
from buzz.lib.utils import parse_db_str

class MongoConnection(object):
    """\
    Wrap mongo client for lazy connect.
    """
    def __init__(self, host, port, db, max_pool_size=10):
        self.host = host
        self.port = port
        self.db = db
        self.max_pool_size = max_pool_size
        self._conn = None

    def _get_connection(self):
        if self._conn is None:
            self._conn = MongoClient(self.host, self.port, max_pool_size=self.max_pool_size)
        return self._conn

    def get_db(self, db_name=None):
        if not db_name:
            db_name = self.db
        conn = self._get_connection()
        return conn[db_name]

    def close(self):
        self._conn.close()

class SQLStore(object):
    """
    Wrap mysql connection.
    """

    TIMEOUT_INTERVAL = 6 * 3600

    def __init__(self, **kwargs):
        kwargs['charset'] = 'utf8'
        self._con_str = kwargs
        self._conn = None
        self.timeout = None

    def get_cursor(self, dict_format=False):
        if self.is_expire():
            self.close()
            self._connect()
        if dict_format:
            cursor = self._conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        else:
            cursor = self._conn.cursor()
        return cursor

    def _connect(self):
        self._conn = MySQLdb.connect(**self._con_str)
        self.timeout = time.time() + self.TIMEOUT_INTERVAL
        return self._conn

    def is_expire(self):
        return self.timeout is None or self.timeout < time.time()

    def close(self):
        if self._conn:
            self._conn.close()


config = Config()
addr = config.get('mongo', 'main')
mongo = MongoConnection(**parse_db_str(addr))

mysql_addr = config.get('mysql', 'main')
sqlstore = SQLStore(**parse_db_str(mysql_addr))

if __name__ == '__main__':
    print "mongo:", parse_db_str(addr)
    print "mysql:", parse_db_str(mysql_addr)
