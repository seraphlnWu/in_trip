#coding=utf-8

import os
os.environ['GEVENT_RESOLVER'] = "ares" # use c-ares
import re
import time
import socket
import urllib
import hashlib
import logging
import traceback
import collections
from cookielib import http2time
from urlparse import urlparse, ParseResult

import tldextract
from requests import Session, exceptions

import chardet
from charlockholmes import detect

from buzz.lib.mq import MQ
from buzz.lib.config import Config
from buzz.lib.compress import compress
from buzz.lib.log import setup_logging
from buzz.lib.pool import ConnectionPool
from buzz.lib.rpc.client import RPCClient
from buzz.lib.workers.coroutine_worker import CoroutineWorker
from buzz.lib.consts import TIMES_LIMIT, CRAWL_TIME_INTERVAL, URL_STATUS, HttpCode, PAGE_TYPE, EXTRACTOR_QUEUE, DEPTH_LIMIT

class UrlMixin(object):
    AVAIL_CACHE_VALUE = re.compile("max-age=(?P<seconds>\d+)")
    @property
    def no_schema(self):
        if not hasattr(self, '_no_schema'):
            self._no_schema = remove_schema(self.url)
        return self._no_schema

    @property
    def domain(self):
        if not hasattr(self, '_domain'):
            self._domain = get_domain(self.url)
        return self._domain

    def to_msgpack(self):
        return dict([(attr, value) for attr, value in self.__dict__.items() if not attr.startswith("_") and value is not None])

    @property
    def md5(self):
        if not hasattr(self, '_md5'):
            md5 = hashlib.md5(self.url)
            self._md5 = md5.hexdigest()

        return self._md5

    @property
    def cache_time(self): # seconds
        if not hasattr(self, '_cache_time'):
            cache_control = self.headers.get('Cache-Control', None)
            if not cache_control: # no cache-control
                self._cache_time = 0
            else:
                max_age = self.AVAIL_CACHE_VALUE.search(cache_control)
                if max_age:
                    self._cache_time = int(max_age.groupdict().get('seconds'))
                else:
                    self._cache_time = 0

        return self._cache_time

    def to_tyrant(self): # not include depth
        return (self.http_code, self.date, self.get_cache_info(),
                self.count, self.page_type, self.status)

    @property
    def refer(self):
        return self.headers.get("Referer", u'')

class HttpRequest(UrlMixin):
    def __init__(self, url, method="GET", http_code=None, date=None, headers=None, cookie=None,
                 data=None, count=0, depth=0, page_type=None, status=URL_STATUS.URL_NORMAL, prior_level=1):
        self.url = url
        self.http_code = http_code
        self.date = date
        self.headers = CaseInsensitiveDict(headers)
        self.cookie = cookie
        self.method = method
        self.count = count
        self.depth = depth
        self.page_type = page_type
        self.status = status
        self.prior_level = prior_level
        self.data = data # http post data

    def get_cache_info(self):
        data = []
        cache_headers = ['If-Modified-Since', 'If-None-Match']
        for header in cache_headers:
            value = self.headers.get(header, None)
            data.append(value)
        data.append(self.cache_time)

        return data

    def from_tyrant(self, r):
        cache_info = r[2]
        cache_info[2] = 'max-age=%d' % (cache_info[2] or 0)
        cache_headers = ['If-Modified-Since', 'If-None-Match', 'Cache-Control']
        headers = dict(zip(cache_headers, cache_info))
        self.http_code = r[0]
        self.date = r[1]
        self.count = r[3]
        self.page_type = r[4]
        self.status = r[5]
        self.headers.update(headers)

    def is_available(self):
        result = True
        if self.status == URL_STATUS.URL_DELETED:
            result = False
        elif self.count >= TIMES_LIMIT and self.page_type and self.page_type & PAGE_TYPE.DETAIL_PAGE:
            result = False
        elif self.depth > DEPTH_LIMIT and self.page_type and self.page_type & PAGE_TYPE.INDEX_PAGE:
            result = False
        else:
            if self.page_type is None or self.page_type & PAGE_TYPE.INDEX_PAGE: # TODO: remove None check
                time_interval = CRAWL_TIME_INTERVAL.INDEX_PAGE_INTERVAL
            else:
                time_interval = CRAWL_TIME_INTERVAL.DETAIL_PAGE_INTERVAL

            now = time.time()

            interval = max(self.cache_time, time_interval)
            if (self.date + interval) < now:
                result = True
            else:
                result = False

        return result


class HttpResponse(UrlMixin):
    def __init__(self, url, http_code=None, raw_source=None, headers=None, count=1, depth=0,
                 page_type=None, status=URL_STATUS.URL_NORMAL, prior_level=1): # need prior_level and status?
        self.url = url
        self.http_code = http_code
        self.raw_source = raw_source
        self.headers = CaseInsensitiveDict(headers)
        self.count = count
        self.depth = depth
        self.page_type = page_type
        self.status = status
        self.prior_level = prior_level
        self._encoding = None

    def get_cache_info(self, data_format="dict"): #available value: dict, list
        cache_headers = ['Last-Modified', 'Etag'] # , 'Cache-Control']
        data = []
        for header in cache_headers:
            value = self.headers.get(header, None)
            data.append(value)

        data.append(self.cache_time)

        return data

    def is_cache_enable(self):
        return self.cache_time > 0

    @property
    def date(self):
        if not hasattr(self, '_date'):
            date_text = self.headers.get('date', None)
            if date_text:
                self._date = int(http2time(date_text) or time.time())
            else:
                self._date = int(time.time())

        return self._date

    def to_tyrant(self): # not include depth
        if self.http_code in (HttpCode.OK, HttpCode.MOVED_PERMANENTLY,
                              HttpCode.FOUND, HttpCode.SEE_OTHER, HttpCode.NOT_MODIFIED, HttpCode.ERROR):
            status = URL_STATUS.URL_NORMAL
        else:
            status = URL_STATUS.URL_DELETED # check page_type js_page?

        return (self.http_code, self.date, self.get_cache_info(),
                self.count, self.page_type, self.status)

    @property
    def encoding(self):
        if self._encoding is None:
            self._encoding = get_encoding(self.raw_source)

        return self._encoding

    @property
    def utf8_source(self):
        if not hasattr(self, '_utf8_source'):
            #if self.encoding != "utf-8":
            try:
                self._utf8_source = merge_space(self.raw_source.decode(self.encoding, 'ignore').encode('utf-8', 'replace'))
            except LookupError:
                raise LookupError("Unknown encoding %s in url:%s" % (self.encoding, self.url))
            #else:
            #    self._utf8_source = self.raw_source

            self._utf8_source = JS_COMMENT.sub("", self._utf8_source)
            if self.domain == 'qc188.com':
                self._utf8_source = PHP_CODE_RE.sub("", self._utf8_source)

            if self.domain == 'bianews.com':
                self._utf8_source = UNKNOWN_CHAR.sub("", self._utf8_source)

        return self._utf8_source

SPACE_REGEX = re.compile("(\s|\r\n|\xe3\x80\x80|\xc2\xa0)+")
def merge_space(utf8_source, space=True):
    # return SPACE_REGEX.subn('\\1', utf8_source)[0]
    if space:
        return SPACE_REGEX.subn(' ', utf8_source)[0]
    else:
        return SPACE_REGEX.subn('', utf8_source)[0]

PHP_CODE_RE = re.compile("<\?.*\?>", re.DOTALL)
JS_COMMENT = re.compile("/\*.*?\*/", re.DOTALL)
UNKNOWN_CHAR = re.compile("^\x00+")

CHARSET_RE = [re.compile("charset=(?P<charset>[^;\s]+)", flags=re.I),
              re.compile(r'<meta.*?charset=["\']?(?P<charset>.+?)["\'>]', flags=re.I)]

def get_encoding(source):
    res = detect(source)
    if res['type'] == 'binary':
        res = chardet.detect(source)
    elif res['confidence'] < 60 and res['encoding'].lower() == "big5":
        res['encoding'] = 'utf-8'

    if res['encoding'] == "ISO-8859-2":
        res['encoding'] = 'gbk'

    return res.get('encoding') or 'utf-8'

TLDEXTRACT_CACHE = os.path.join(Config().get("base_path"), ".tld_set")
tld_extractor = tldextract.TLDExtract(cache_file=TLDEXTRACT_CACHE, suffix_list_url=None)
def get_domain(url):
    result = tld_extractor(url)
    return result.domain + '.' + result.suffix if result else ""

SCHEMA = re.compile('^https?:\/\/')
def remove_schema(url):
    return SCHEMA.sub('', url)

def url_quote(url, encoding='utf-8'):
    if isinstance(url, unicode):
        url = urllib.quote(url.encode(encoding), '/:&?=')
    return url

BAIDU_ZHIDAO_RE = re.compile('\/question\/\d+\.html.*')
BAIDU_TIEBA_RE = re.compile('\/p\/\d+.*')
SOSO_QUESTION_RE = re.compile("\/z\/[qc]\d+\.htm.*")
WUBA_RE = re.compile('\/\w+\/\d+x\.shtml') # 58.com
TAOBAO_WENDA_RE = re.compile('\/thread\/detail/\d+\.htm')

def format_url(url):
    parse_result = urlparse(url)
    query = parse_result.query
    domain = get_domain(url)
    if parse_result.netloc == 'tieba.baidu.com':
        if BAIDU_TIEBA_RE.match(parse_result.path):
            querys = parse_qs(query)
            page = querys.get('pn') or 1
            query = join_qs({'pn': page})

    elif parse_result.netloc == 'zhidao.baidu.com':
        if BAIDU_ZHIDAO_RE.match(parse_result.path):
            query = ""


    elif parse_result.netloc == 'wenwen.sogou.com':
        querys = parse_qs(parse_result.query)
        'ch' in querys and querys.pop('ch')

        if SOSO_QUESTION_RE.match(parse_result.path):
            querys = {}

        query = join_qs(querys)

    elif domain == '58.com' and WUBA_RE.match(parse_result.path):
        query = ""

    elif parse_result.netloc == 'wenda.taobao.com' and TAOBAO_WENDA_RE.match(parse_result.path):
        querys = parse_qs(query)
        page = querys.get('pageNo') or 1
        query = join_qs({'pageNo': page})

    #if parse_result.query != query:
    parse_result = ParseResult(parse_result.scheme, parse_result.netloc,
                               parse_result.path, parse_result.params, query, '')

    return parse_result.geturl()

def parse_qs(qs, keep_blank_values=0, strict_parsing=0):
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r = {}
    for name_value in pairs:
        if not name_value and not strict_parsing:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError, "bad query field: %r" % (name_value,)
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            #name = unquote(nv[0].replace('+', ' '))
            #value = unquote(nv[1].replace('+', ' '))
            #r.append((name, value))
            r[nv[0]] = nv[1]


    return r

def join_qs(query):
    parts = []
    for name, value in query.iteritems():
        if isinstance(value, list):
            for v in value:
                parts.append("%s=%s" % (name, v))
        else:
            parts.append("%s=%s" % (name, value))

    return '&'.join(parts)

class CaseInsensitiveDict(collections.MutableMapping):
    """
    A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``collections.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    """
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, collections.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented

        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, dict(self.items()))

    def to_msgpack(self):
        return dict(self.lower_items())

class WebClient(CoroutineWorker):

    LOGGER_NAME = "spider"

    def __init__(self, cfg, file_logger=None, max_redirects=3, ppid=None, **kwargs):
        super(WebClient, self).__init__(cfg, file_logger, ppid)

        #: Associated ``Session``
        self.session = kwargs.pop('session', None)
        if self.session is None:
            self.session = Session()

        """
        callback = kwargs.pop('callback', None)
        if callback:
            kwargs['hooks'] = {'response': callback}
        """

        self.session.max_redirects = max_redirects

        if 'timeout' not in kwargs:
            kwargs['timeout'] = 1.5

        #: The rest arguments for ``Session.request``
        self.kwargs = kwargs

    def setup(self):
        super(WebClient, self).setup()
        self.timer_addr = self.cfg.timer_addr

    def init_process(self):
        super(WebClient, self).init_process()
        setup_logging(self.cfg.ACTUAL_CONFIG_FILE or self.cfg.DEFAULT_CONFIG_FILE)
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.rpcs = ConnectionPool(RPCClient, (self.timer_addr, ), max_size=self.max_greenlets)

    def stop(self):
        super(WebClient, self).stop()
        self.rpcs.disconnect()

    def get_response(self, request):
        """
        Prepares request based on parameter passed to constructor and optional ``kwargs```.
        Then sends request and saves response to :attr:`response`

        :returns: ``Response``
        """
        request.headers = default_headers(request.headers) # add default headers
        start = time.time()
        try:
            resp =  self.session.request(request.method, request.url,
                                         data=request.data, headers=request.headers, **self.kwargs)

        except exceptions.Timeout as e:
            self.logger.error("Crawl url:%s connect timeout", request.url)
            resp = None
        except exceptions.TooManyRedirects as e:
            self.logger.error("Crawl url:%s redirect more than 3 times", request.url)
            resp = None
        except exceptions.ConnectionError as e:
            self.logger.error("Crawl url:%s connect error", request.url)
            resp = None
        except socket.timeout as e:
            self.logger.error("Crawl url:%s recv timetout", request.url)
            resp = None
        except:
            self.logger.error("Crawl url:%s exception: %s", request.url, traceback.format_exc())
            resp = None

        if not resp:
            response = HttpResponse(request.url, HttpCode.ERROR, None, None,
                                    request.count + 1, page_type=request.page_type, status=URL_STATUS.URL_NORMAL, prior_level=request.prior_level)
        else:
            response = HttpResponse(request.url, resp.status_code, resp.content, resp.headers,
                                    request.count + 1, request.depth, request.page_type, URL_STATUS.URL_NORMAL, request.prior_level)
            self.logger.info("Crawl url:%s %d takes %.3f seconds, refer:%s, depth:%d", request.url, response.http_code, (time.time() - start), request.refer, request.depth)
        return response

    def handle_request(self):
        rpc = self.rpcs.get()
        r = rpc.call("get_url")
        self.rpcs.release(rpc)
        if 'error' not in r:
            request = HttpRequest(**r['result'])
            response = self.get_response(request)
            if response.http_code == HttpCode.OK:
                response.raw_source = compress(response.raw_source)
            MQ.push(EXTRACTOR_QUEUE, response)
        else:
            time.sleep(0.5)
            self.file_logger.warning("call rpc:get_url faild code:%d reason:%s", r['error']['code'], r['error']['message'])

def default_headers(headers):
    if headers is None:
        headers = CaseInsensitiveDict()

    if 'User-Agent' not in headers:
        headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.52 Safari/537.17"

    if 'Accept' not in headers:
        headers['Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    if 'Accept-Encoding' not in headers:
        headers['Accept-Encoding'] = "gzip,deflate"

    if 'Accept-Language' not in headers:
        headers['Accept-Language'] = "zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3"

    if 'Connection' not in headers:
        headers['Connection'] = "keep-alive"

    headers['Cache-Control'] = "max-age=0"

    return headers

web_client = None

def curl(url, method="GET"):
    global web_client
    if web_client is None:
        Config.SECTION_NAME = "spider"
        web_client = WebClient(Config())
        web_client.logger = logging.getLogger()

    request = HttpRequest(url, method=method)
    return web_client.get_response(request)

if __name__ == '__main__':
    Config.SECTION_NAME = "spider"
    web_client = WebClient(Config())
    web_client.logger = logging.getLogger()
    r = MQ.pop("gzmama.com")
    print r
    request = HttpRequest(**r)
    response = web_client.get_response(request)
    print response.raw_source
