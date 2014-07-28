#! /usr/bin/env python
# coding: utf-8

import time
import socket
import datetime
from pygtail import Pygtail
from collections import defaultdict

from buzz.lib.http import get_domain as _get_domain

MAPPING = {
    'spider': 'takes',
    'extractor': 'emotion'
}


def graphite(prefix='spider'):
    count = defaultdict(int)
    filename = '/data1/scribe/%s/%s-%s_0000' % (prefix, prefix, datetime.datetime.now().strftime('%Y-%m-%d'))
    for line in Pygtail(filename):
        if MAPPING[prefix] in line:
            domain = get_domain(line)
            count[domain] += 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 2003))
    for domain, amount in count.iteritems():
        sock.send("%s.%s.amount %s %s\n" % (prefix, domain, amount, int(time.time())))
    sock.close()


def get_domain(line):
    url = line.split('//')[1].split()[0]
    return _get_domain(url)

if __name__ == '__main__':
    pass
