#encoding=utf-8

import happybase

from buzz.lib.config import Config
from buzz.lib.store import parse_db_str
from buzz.lib.compress import compress, decompress

class HbaseClient(object):
    """\
    Wrap happybase Connection
    """
    def __init__(self, host, port, db, table_prefix=None,
                 autoconnect=None, compat="0.90", transport="buffered"):
        self.host = host
        self.port = port
        self.table_name = db
        self.table_prefix = table_prefix
        self.autoconnect = autoconnect
        self.compat = compat
        self.transport = transport
        self.conn = None

    def _setup_conn(self):
        if self.conn is None:
            self.conn = happybase.Connection(
                host=self.host,
                port=self.port,
                table_prefix=self.table_prefix,
                autoconnect=self.autoconnect,
                compat=self.compat,
                transport=self.transport
            )
            self.conn.open()

    def close(self):
        self.conn.close()

    def get_table(self):
        if self.conn is None:
            self._setup_conn()
        return self.conn.table(self.table_name)

    def put(self, key, data):
        """
        :params key: url_md5,
        :params data:
        format : {
            "url": url,
            "source": source # utf-8 encoded
        }
        """
        if self.conn is None:
            self._setup_conn()
        table = self.get_table()
        table.put(key, {"bz:url": data['url'],
                                "src:html": compress(data['source'])})
                                #"src:encoding": data['encoding']})

    def get(self, url_md5):
        if self.conn is None:
            self._setup_conn()
        table = self.get_table()
        columns = ['bz:url', 'src:html']
        row = table.row(url_md5, columns=columns)
        return row[columns[0]], decompress(row[columns[1]])

    def tables(self):
        if self.conn is None:
            self._setup_conn()
        return self.conn.tables()

    def delete(self, key):
        if self.conn is None:
            self._setup_conn()

        table = self.get_table()
        return table.delete(key)

    def scan(self):
        table = self.get_table()
        for row in table.scan():
            yield row

config = Config()
hb_addr = config.get('hb', 'main')
hb = HbaseClient(**parse_db_str(hb_addr))

if __name__ == '__main__':
    print hb.scan().next()
