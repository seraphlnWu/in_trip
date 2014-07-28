# coding=utf-8

import re
import time
import logging
import hashlib
import operator
import urlparse
import datetime
import traceback

from summary.summarization import summary
from readability.readability import Document

from buzz.lib.mq import MQ
from buzz.lib.hbase import hb
from buzz.lib.utils import first
from buzz.lib.rpc import RPCClient
from buzz.lib.log import setup_logging
from buzz.lib.compress import decompress
from buzz.lib.emotion import get_emotion
from buzz.lib.serialize import deserialize
from buzz.lib.store import mongo, sqlstore
from buzz.lib.workers.sync import SyncWorker
from buzz.lib.compress import compress, decompress
from buzz.lib.http import HttpRequest, HttpResponse, get_domain, url_quote, remove_schema, format_url
from buzz.lib.consts import PAGE_TYPE, DEFAULT, PAGE_TYPE_MAP, SEARCH_ENGINE, DATE_REGEX, EXTRACTOR_QUEUE, HttpCode, DEPTH_LIMIT, MAX_MISC_COUNT

from admin.lib.url_regex import regex_decoder
from admin.config.consts import RECORD_STATUS
from admin.model import Site, Channel, Blacklist

TIANYA_RE = re.compile("^bbs\.tianya\.cn/post\-cars\-\d+\-1\.shtml")
URL_FILTER = re.compile(r"^(javascript:|mailto:|#|mms:).*|.*\.(pdf|jpg|gif|png)$")
BBS_USER_HOME_RE = re.compile('^bbs\.[^/]*\/home.*')
SO_WEMEDIA_RE = re.compile('^wemedia\.so\.com.*')
WENDA_RE = re.compile("^(wenwen|wenda|zhidao|tieba|\w+\.baijia).*")

DATE_LIMIT = datetime.datetime(2013, 1, 1)

class Extractor(SyncWorker):

    """Extract page content
    """
    LOGGER_NAME = "extractor"

    def __init__(self, cfg, file_logger=None, ppid=None, sockets=None):
        SyncWorker.__init__(self, cfg, file_logger, ppid)
        setup_logging(self.cfg.ACTUAL_CONFIG_FILE or self.cfg.DEFAULT_CONFIG_FILE)
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.load_channel_blacklist_special()

    def setup(self):
        super(Extractor, self).setup()
        self.engine_addr = self.cfg.engine_addr

    def init_process(self):
        super(Extractor, self).init_process()
        self.rpc = RPCClient(self.engine_addr)

    def stop(self):
        super(Extractor, self).stop()
        self.rpc.close()

    def load_channel_blacklist_special(self):
        cache = {}
        self.channel = {}
        self.blacklist = {}
        self.specials = {}
        for channel in Channel.find():
            site_id = channel.site_id
            if site_id not in cache:
                site = Site.get(site_id)
                cache[site_id] = site
            else:
                site = cache[site_id]

            if site.domain in self.channel:
                self.channel[site.domain].append(channel)
            else:
                self.channel[site.domain] = [channel, ]

        for domain, channels in self.channel.items():
            self.channel[domain] = sorted(channels, key=lambda x: len(x.url), reverse=True)

        for blacklist in Blacklist.find():
            site_id = blacklist.site_id
            if site_id not in cache:
                site = Site.get(site_id)
                cache[site_id] = site
            else:
                site = cache[site_id]

            url_reg = re.compile(regex_decoder(blacklist.url_reg), re.I)
            if site.domain in self.blacklist:
                self.blacklist[site.domain].append(url_reg)
            else:
                self.blacklist[site.domain] = [url_reg, ]

        cursor = sqlstore.get_cursor(dict_format=True)
        sql = "select * from special where status=%s"
        cursor.execute(sql, (RECORD_STATUS.NORMAL, ))
        for special in cursor.fetchall():
            domain = get_domain(special['url'])
            special['url_regex'] = re.compile(special['url_regex'])
            if domain in self.specials:
                self.specials[domain].append(special)
            else:
                self.specials[domain] = [special, ]

    def handle_request(self):
        """\
        Get task from rabbitmq and extract
        """
        msg = MQ.pop(EXTRACTOR_QUEUE)
        if not msg:
            time.sleep(0.5)
            return
        resp = HttpResponse(**msg)
        if resp.http_code == HttpCode.OK:
            resp.raw_source = decompress(resp.raw_source)
            specials = self.specials.get(resp.domain)
            if specials:
                special = first(specials, lambda x: x['url_regex'].match(resp.no_schema) and x or None)
            else:
                special = None
            doc = Document(resp, special=special)
            if doc.dom and doc.main_block:
                extract_result = self.extract(doc)
                first_page_url = extract_result.save()
                if first_page_url is not None:
                    self.logger.warning("Put first page url %s for url:%s", first_page_url, resp.url)
                    self.put_urls([first_page_url], resp.url, resp.depth - 1)
                else:
                    self.put_urls(extract_result.urls, resp.url, resp.depth + 1)
            else:
                self.logger.warning("url: %s main_block is None", resp.url)

        if resp.page_type is None or not (resp.page_type & PAGE_TYPE.FEED_PAGE):
            if resp.http_code == HttpCode.OK:
                resp.page_type = doc.page_type
            resp.raw_source = None  # don't need raw_source
            r = self.rpc.call("update_url", resp)
            if 'error' in r:
                error = r['error']
                self.file_logger.error("call rpc:update_url faild code: %d message: %s, url: %s", error['code'], error['message'], resp.url)

    def put_urls(self, urls, refer, depth=1):
        if urls:
            r = self.rpc.call('put_urls', urls, refer, depth)
            if 'error' in r:
                error = r['error']
                self.file_logger.error("call rpc:put_urls faild code: %d message: %s", error['code'], error['message'])

    def extract(self, doc):
        if doc.resp.depth <= DEPTH_LIMIT:  # three level
            url_links = self.extract_urls(doc)
        elif doc.resp.depth <= (DEPTH_LIMIT + 1) and doc.page_type & (PAGE_TYPE.BBS_DETAIL_PAGE | PAGE_TYPE.ASK_DETAIL_PAGE):
            url_links = doc.get_other_page()
        else:
            url_links = []

        if url_links:
            url_links = self.url_filter(doc, url_links)

        if doc.page_type & PAGE_TYPE.DETAIL_PAGE:
            try:
                comment_count, view_count = doc.get_misc_count()
                if doc.page_type & PAGE_TYPE.BBS_DETAIL_PAGE and doc.is_first_page and comment_count is None and view_count is None:
                    self.logger.warning("BBS with comment_count: %s and view_count: %s url:%s", comment_count, view_count, doc.resp.url)

                bbs_blocks = []
                bbs = True if doc.page_type & PAGE_TYPE.BBS_LIKE_PAGE else False
                if bbs and doc.bbs_blocks is not None:
                    bbs_blocks = doc.bbs_comments

                extract_result = ExtractResult(self.logger, self.channel, doc,
                                               doc.short_title(), doc.get_publish_date(),
                                               doc.text_content(doc.page_type), doc.get_author(), comment_count,
                                               view_count, urls=url_links, bbs_blocks=bbs_blocks, main_post=doc.main_post)
            except Exception as e:
                self.logger.warning("Readability Exception %s, url:%s", e, doc.resp.url)  # can remove
                return ExtractResult(self.logger, self.channel, doc, urls=url_links)
        else:
            extract_result = ExtractResult(self.logger, self.channel, doc, urls=url_links)

        self.logger.info("Extract url:%s with page_type:%s", doc.resp.url, PAGE_TYPE_MAP[doc.page_type])
        return extract_result

    def extract_urls(self, doc):
        base = doc.dom.find('.//base')
        base_url = url_quote(base.get('href') if base is not None and base.get('href') else doc.resp.url)

        url_links = []
        blocks = doc.bbs_blocks or [doc.main_block, ]

        for block in blocks:
            for link in block.xpath('.//a'):
                href = link.get('href')
                if not href:
                    continue
                href = url_quote(href.strip(), doc.resp.encoding)
                if URL_FILTER.match(href):
                    continue

                if href.startswith('http'):
                    url_links.append(href)
                else:
                    url_links.append(urlparse.urljoin(base_url, href))  # add cache

        return url_links

    def url_filter(self, doc, url_links):
        url_links = list(set(url_links))
        site_domain = doc.resp.domain
        white_urls = []
        if site_domain == 'so.com' and SO_WEMEDIA_RE.match(doc.resp.no_schema):
            for url in url_links:
                if get_domain(url) != 'so.com' or SO_WEMEDIA_RE.match(remove_schema(url)):
                    white_urls.append(url)
        else:
            if WENDA_RE.match(doc.resp.no_schema):
                operation = operator.eq
            elif site_domain in SEARCH_ENGINE:
                operation = operator.ne
            else:
                operation = operator.eq

            blacklist = self.blacklist.get(site_domain, [])
            blacklist.append(BBS_USER_HOME_RE)
            #if blacklist:
            for url in url_links:
                if operation(get_domain(url), site_domain):
                    no_schema_url = remove_schema(url)
                    match = first(blacklist, lambda x: x.search(no_schema_url))
                    if not match:
                        white_urls.append(format_url(url))
            #else:
            #    white_urls = filter(lambda x: operation(get_domain(x), site_domain), url_links)

        return list(set(white_urls))


class ExtractResult(object):

    def __init__(self, logger, channel, doc, title=None, pub_date=None,
                 content=None, author=None, comment_count=None, view_count=None,
                 industry_id=DEFAULT, channel_name=None, category_id=DEFAULT, urls=None, bbs_blocks=None, main_post=None):
        self.logger = logger
        self.channel = channel
        self.doc = doc
        self.resp = doc.resp
        self.title = title[:150] if title else None
        if isinstance(pub_date, basestring):
            self.pub_date = None
            self.logger.info("Date time error url: %s value:'%s'", self.resp.url, pub_date)
        else:
            self.pub_date = pub_date
        self.content = content if content else None
        self.industry_id = industry_id
        self.channel_name = channel_name[:12] if channel_name else None
        self.category_id = category_id
        self.author = author[:12] if author else None
        self.comment_count = comment_count & MAX_MISC_COUNT if comment_count is not None else None
        self.view_count = view_count & MAX_MISC_COUNT if view_count is not None else None
        self.urls = urls
        self.bbs_blocks = bbs_blocks
        self.main_post = main_post

    def save_source(self):
        # detail page insert to hbase
        # self.logger.info("Insert url:%s to hbase", self.resp.url)
        hb.put(self.resp.md5, {"url": self.resp.url,
                               "source": self.resp.utf8_source})

    #@profile
    def save(self):
        if not (self.doc.page_type & PAGE_TYPE.DETAIL_PAGE):
            return  # index page, js page

        self.save_source()
        domain = self.resp.domain
        url = self.resp.url
        channel = first(self.channel.get(domain, []), lambda x: x.url in url and x or None)
        if channel:
            self.industry_id = channel.industry_id
            self.channel_name = channel.channel_name
            self.category_id = channel.category_id
        else:
            self.logger.error("No matched channel url:%s", self.resp.url)

        first_page_url = self.doc.get_first_page()
        first_page_md5 = HttpRequest(first_page_url).md5
        need_save_article = True
        if self.doc.page_type & PAGE_TYPE.BBS_DETAIL_PAGE and self.bbs_blocks:
            if self.doc.is_first_page:  # BBS first page
                main_post = self.bbs_blocks[0]
                self.bbs_blocks = self.bbs_blocks[1:]
                self.author = main_post['author']
                self.main_post = main_post['content']
                if not (self.resp.domain == "tianya.cn" and TIANYA_RE.match(self.resp.no_schema)):
                    self.pub_date = main_post['pub_date']
            else:
                # won't save following pages in article table
                need_save_article = False

        article_id = self.save_article() if need_save_article else None  # BBS first page, QA main post, normal detail page

        if self.bbs_blocks:  # handle comments
            cursor = sqlstore.get_cursor()  # TODO: check count
            if self.doc.is_first_page:
                if article_id is not None:
                    last_time = self.pub_date
                    count = 0
                else:
                    # BBS first page without keywords matched
                    return
            else:
                # BBS following page
                cursor.execute("select id, pub_date from article where url_md5=%s;", (first_page_md5, ))
                result = cursor.fetchone()
                if result:
                    article_id, last_time = result
                    count = 0
                else:
                    # can't find first_page in MySQL, put its url to spider queue
                    return first_page_url

            cursor.execute("select article_id, pub_date, count(id) from comment where url_md5=%s order by id desc limit 1;", (self.resp.md5, ))
            result = cursor.fetchone()
            if result[0] is not None:
                article_id, last_time, count = result

            self.save_comments(article_id, last_time, count)

    def save_comments(self, article_id, last_time, count):
        cursor = sqlstore.get_cursor()  # TODO: check count
        try:
            for block in self.bbs_blocks[count:]:
                if block['pub_date']:
                    if block['pub_date'] >= last_time:
                        cursor.execute("insert into comment values(null, %s, %s, %s, %s, default, %s, %s, %s, %s);",
                                       (article_id, self.resp.url[:250], self.resp.md5,
                                        DEFAULT, block['pub_date'], block['author'], block['content'], RECORD_STATUS.NORMAL))
                else:
                    self.logger.warning("No comment pub_date for url:%s", self.resp.url)
        except:
            self.logger.warning("Save comment error for url:%s %s", self.resp.url, traceback.format_exc())
        finally:
            cursor.connection.commit()

    def save_article(self):
        article = Article(self.logger, self.category_id, self.channel_name, self.resp.url,
                          self.resp.md5, self.title, self.pub_date, self.author, self.content,
                          self.comment_count, self.view_count, self.industry_id, self.doc.page_type, self.main_post)

        return article.save()

class Article(object):

    def __init__(self, logger, category_id, channel_name, url, url_md5, title,
                 pub_date, author, content, comment_count, view_count, industry_id, page_type, main_post):
        self.logger = logger
        self.category_id = category_id
        self.channel_name = channel_name
        self.url = url
        self.url_md5 = url_md5
        self.title = title
        self.pub_date = pub_date
        self.author = author
        self.content = content
        self.comment_count = comment_count
        self.view_count = view_count
        self.industry_id = industry_id
        self.page_type = page_type
        self.main_post = main_post

    def is_exist(self):
        cursor = sqlstore.get_cursor()  # TODO: check count
        cursor.execute("select id, content_md5 from article where url_md5=%s;", (self.url_md5, ))
        result = cursor.fetchone()
        cursor.close()
        if result:
            self.article_id, self.old_content_md5 = result

            return True
        else:
            return False

    def is_changed(self):
        return self.old_content_md5 != self.content_md5

    def save(self):
        # check essential columns
        columns = []
        for column in ['title', 'pub_date', 'content']:
            if not getattr(self, column, None):
                columns.append(column)
        if columns:
            self.logger.warning("url:%s extractresult not contails all essential columns:%s.", self.url, ','.join(columns))
            return

        if self.keywords and self.pub_date >= DATE_LIMIT:
            article_exist = self.is_exist()
            if article_exist:
                article_id = self.article_id
                if self.is_changed():
                    cursor = sqlstore.get_cursor()  # TODO: check count
                    self.logger.info("url:%s content changed.", self.url)
                    cursor.execute("update article "
                                   "set title=%s, pub_date=%s, author=%s, word_count=%s, comment_count=%s, view_count=%s, content_md5=%s "
                                   "where id=%s;", (self.title, self.pub_date, self.author, len(self.main_post),
                                                    self.comment_count, self.view_count, self.content_md5, article_id))
                    cursor.execute("update article_matched_keywords set pub_date=%s where article_id=%s;", (self.pub_date, article_id))
                    cursor.connection.commit()
                    cursor.close()
            else:
                cursor = sqlstore.get_cursor()  # TODO: check count
                cursor.execute("insert into article values(null, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, default, %s, %s, %s, %s);",
                               (self.category_id, self.channel_name, self.url[:250], self.title, self.pub_date, self.author,
                                self.comment_count, self.view_count, '', len(self.content), self.industry_id, self.url_md5,
                                self.content_md5, self.page_type, RECORD_STATUS.NORMAL))

                article_id = cursor.lastrowid
                cursor.execute("insert into article_content values(%s, %s);", (article_id,
                                                                               compress(self.main_post.encode('utf-8'))))
                cursor.connection.commit()
                cursor.close()

            self.save_keywords(article_id, article_exist)
            return article_id

    def save_keywords(self, article_id, exist=False):
        cursor = sqlstore.get_cursor()
        if exist:
            old_matched_keywords = {}
            cursor.execute("select id, keyword from article_matched_keywords where article_id=%s;", (article_id, ))  # id used for remove
            for matched_id, keyword in cursor.fetchall():
                old_matched_keywords[keyword] = matched_id

            unmatched_keywords = set(old_matched_keywords.keys()) - set(self.keywords)
            # unchange keyword need to change emotion?
            if unmatched_keywords:
                for keyword in unmatched_keywords:
                    cursor.execute("update article_matched_keywords "
                                   "set status=%s where id=%s", (RECORD_STATUS.DELETED, old_matched_keywords[keyword]))

            keywords = set(self.keywords) - set(old_matched_keywords.keys())  # new matched
        else:
            keywords = self.keywords

        text = (self.title + self.content).lower()
        for keyword in keywords:
            if keyword == '':
                continue

            brief = self.get_brief(text, keyword)
            emotion = self.get_emotion(text, keyword)
            cursor.execute("insert into article_matched_keywords "
                           "values(null, %s, %s, %s, %s, %s, %s);", (article_id, self.pub_date,
                                                                     keyword, emotion, brief, RECORD_STATUS.NORMAL))

        cursor.connection.commit()
        cursor.close()

    @property
    def content_md5(self):
        if not hasattr(self, "_content_md5"):
            md5 = hashlib.md5()
            text = self.title + self.content + self.pub_date.strftime('%Y-%m-%d %H:%M:%S')
            if self.author:
                text += self.author
            if self.comment_count:
                text += str(self.comment_count)
            if self.view_count:
                text += str(self.view_count)
            md5.update(text.encode('utf-8'))
            self._content_md5 = md5.hexdigest()

        return self._content_md5

    def get_emotion(self, text, keyword):  # 情感分析
        start = time.time()
        emotion = get_emotion(text, keyword)
        self.logger.info("Get emotion takes %.3f seconds" % (time.time() - start))
        return emotion

    def get_brief(self, text, keyword):
        summary_text = summary(text, keyword, 1, 145)
        if not summary_text:
            self.logger.warning("Brief empty url:%s, keyword:%s", self.url, keyword)
            brief = u""
        else:
            brief = re.sub(u'\s+|\xa0', '', summary_text[0])
            try:
                index = brief.index(keyword)
                length = len(keyword)
                if index + length < 150:
                    brief = brief[:150]
                else:
                    brief = brief[index - 75:index + 75]
            except ValueError:
                brief = brief[:150]

        return brief

    @property
    def keywords(self):
        from buzz.lib.search import multi_pattern_search  # uwsgi memory problem
        if not hasattr(self, "_keywords"):
            self._keywords = multi_pattern_search.match(self.title + self.content)

        return self._keywords


if __name__ == '__main__':
    import sys
    import logging
    from buzz.lib.http import curl
    from buzz.lib.config import Config
    from buzz.lib.consts import HttpCode
    Config.SECTION_NAME = "extractor"
    extractor = Extractor(Config())
    extractor.logger = logging.getLogger()
    # extractor.init_process()
    # extractor.handle_request()
    extractor.run()
    """
    while True:
        url = raw_input("Url: ")
        try:
            request = HttpRequest(url)
            html_source = hb.get(request.md5)[1]
            resp = HttpResponse(url, HttpCode.OK, html_source, None)
        except:
            resp = curl(url)
        if resp:
            specials = extractor.specials.get(resp.domain)
            if specials:
                special = first(specials, lambda x: x['url_regex'].match(resp.no_schema) and x or None)
            else:
                special = None
            doc = Document(resp, special=special)
            extract_result = extractor.extract(doc)
            if doc.page_type & PAGE_TYPE.DETAIL_PAGE:
                print extract_result.title, 'tt', extract_result.content, extract_result.pub_date, extract_result.comment_count, extract_result.view_count
                extract_result.save()
            else:
                print extract_result.urls, len(extract_result.urls)
                extract_result.save()
        else:
            print "get page error"
    """
