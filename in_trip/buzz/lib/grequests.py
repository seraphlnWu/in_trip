#coding=utf-8

import gevent
from gevent import monkey
# Monkey-patch.
monkey.patch_all()

#__all__ = ['AsyncRequest', 'curl']


def curl(url, pool=None, stream=False, **kwargs):
    """Sends the request object using the specified pool. If a pool isn't
    specified this method blocks. Pools are useful because you can specify size
    and can hence limit concurrency."""
    r = get(url, callback=handle_response, **kwargs)
    if pool != None:
        pool.spawn(r.send, stream=stream)
    else:
        gevent.spawn(r.send, stream=stream)

def handle_response(request, **kwargs):
