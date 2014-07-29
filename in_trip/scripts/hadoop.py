#coding=utf-8
# This script used to load map-reduce result to extractor queue

import sys

from in_trip.lib.mq import MQ
from in_trip.lib.hbase import hb
from in_trip.lib.http import HttpResponse
from in_trip.lib.compress import compress
from in_trip.lib.consts import EXTRACTOR_QUEUE, HttpCode, PAGE_TYPE, DEPTH_LIMIT

def main():
    for line in sys.stdin:
        md5 = line.rstrip()
        url, html_source = hb.get(md5)
        print md5, url
        response = HttpResponse(url, HttpCode.OK, compress(html_source), depth=DEPTH_LIMIT+3, page_type=PAGE_TYPE.FEED_PAGE)
        MQ.push(EXTRACTOR_QUEUE, response)

if __name__ == '__main__':
    main()
