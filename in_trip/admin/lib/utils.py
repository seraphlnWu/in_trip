#coding=utf-8
import re
import gzip
import json
import datetime
import urllib, urllib2
from functools import wraps
from StringIO import StringIO

from bottle import response, mako_view

from in_trip.lib.store import mongo
from in_trip.lib.http import get_domain
from admin.lib import webhelper as h


def curl(url):
    quoted_url = urllib.quote(url, '/:&?=')
    quoted_url = url
    domain = get_domain(url)
    request = urllib2.Request(url=quoted_url)

    request.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.52 Safari/537.17")
    request.add_header("Accept", "text/html")
    request.add_header('Accept-Language', 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3')
    request.add_header("Accept-Encoding", 'gzip')
    try:
        resp = urllib2.urlopen(request, timeout=10)
        if "Content-Encoding" in resp.info():
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            html_content = f.read()
        else:
            html_content = resp.read()

    except (urllib2.URLError, Exception) as e:
        return (None, None)
    else:
        return (html_content, dict(resp.info()))

def remove_empty(data):
    """
    remove list empty str
    """
    data = filter(lambda x: x != '' and x != ' ', data)

    for i, element in enumerate(data):
        if hasattr(element, '__iter__') and not isinstance(element, (str, unicode)):
            data[i] = filter(lambda x: x != '' and x != ' ', element)

    return data

FULL_TIME_FORMAT =  "%Y-%m-%d %H:%M:%S"

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(FULL_TIME_FORMAT)
        else:
            return super(self.__class__, self).default(obj)

def jsonify(encoder=DateTimeEncoder):
    def _(func):
        @wraps(func)
        def serialize(*args, **kwargs):
            result = func(*args, **kwargs)
            response.content_type = "application/json"
            return json.dumps(result, cls=encoder)

        return serialize

    return _

def render(page_path):
    return mako_view(page_path, h=h, output_encoding="utf8")
