#encoding=utf-8

# This is a constant hash wrap for pytyrant.PyTyrant

from pyrant import Tyrant
from hash_ring import HashRing

from buzz.lib.config import Config
from buzz.lib.pool import ConnectionPool
from buzz.lib.serialize import serialize, deserialize

class PyTyrant(object):
    def __init__(self, nodes):
        self.nodes = nodes
        self.hash_ring = HashRing(nodes)
        self.server_mapping = {}
        self.connection()

    def connection(self): # create conection and set server_mapping attribute
        for node in self.nodes:
            host, port = node.split(":")
            self.server_mapping[node] = ConnectionPool(Tyrant,
                                                       (host, int(port)),
                                                       kwargs={'literal':True},
                                                       max_size=30)

    def _get_node(self, key):
        return self.hash_ring.get_node(key)

    def _get_server(self, key):
        node = self._get_node(key)
        return self.server_mapping[node].get(), node

    def _release_server(self, node, server):
        self.server_mapping[node].release(server)

    def get(self, key):
        server, node = self._get_server(key)
        r = server.get(key)
        if r:
            r = deserialize(r)
        self._release_server(node, server)
        return r

    def mget(self, klst):
        node_mapping = {}
        for key in klst:
            node = self._get_node(key)
            if node in node_mapping:
                node_mapping[node].append(key)
            else:
                node_mapping[node] = [key, ]

        for node, keys in node_mapping.iteritems():
            server = self.server_mapping[node].get()
            for result in server.multi_get(keys):
                yield deserialize(result)
            self._release_server(node, server)


    def set(self, key, value):
        value = serialize(value)
        server, node = self._get_server(key)
        # r = server.multi_set([(key, value), ]) # 127 copies?
        server[key] = value
        self._release_server(node, server)
        return 0

    def vsize(self, key):
        server, node = self._get_server(key)
        size = server.get_size(key)
        self._release_server(node, server)
        return size

    def size(self):
        """Get the size of the database
        """
        for node in self.nodes:
            server = self.server_mapping[node].get()
            size = server.size()
            self._release_server(node, server)
            yield (node, size)

    def delete(self, key):
        server, node = self._get_server(key)
        server.multi_del([key, ])
        self._release_server(node, server)

addrs = Config().get('tyrant', 'main').split(',') # comma separate multi addrs
tyrant = PyTyrant(addrs)


if __name__ == '__main__':
    import time
    from buzz.lib.http import HttpRequest

    request = HttpRequest("http://search.tianya.cn/bbs?q=%E8%8B%AF%E4%B8%99%E9%85%AE%E5%B0%BF%E7%97%87&pn=1&s=4")
    start = time.time()
    print tyrant.get(request.md5)
    print time.time() - start
