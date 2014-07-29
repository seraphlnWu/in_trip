# coding=utf-8

import re
import time
import datetime
import traceback

from in_trip.lib.mq import MQ
from in_trip.lib.mail import mail
from in_trip.lib.http import HttpRequest, url_quote, curl
from in_trip.lib.consts import PAGE_TYPE, INDUSTRY, DEPTH_LIMIT, SEARCH_ENGINE

from admin.config.consts import RECORD_STATUS
from admin.model import Site, Feed, DealerFeed, get_keywords, get_feeds, parse_feed, PostFeed


def insert_feed_url(urls, method="GET", data=None, page_type=PAGE_TYPE.SEATCH_FEED_PAGE, depth=DEPTH_LIMIT):
    for url in urls:
        request = HttpRequest(url, method=method, data=data, page_type=page_type, depth=depth)
        MQ.push(request.domain, request)
        time.sleep(0.001)


def feed():
    keywords = get_keywords()

    """
    industry_ids = keywords.keys()
    if INDUSTRY['*'] not in industry_ids:
        industry_ids.append(INDUSTRY['*'])
    """

    feeds = get_feeds()

    for feed in feeds:
        urls = parse_feed(feed, keywords)
        print feed._id, len(urls)
        insert_feed_url(urls, page_type=feed.feed_type)


def sogou_feed():  # site search
    feed = Feed.get(16)
    sites = []
    for site in Site.find(prior_level=5):
        if site.domain == 'qq.com' or site.domain not in SEARCH_ENGINE:
            sites.append(site.domain)
    feed.kwargs['site'] = sites
    keywords = get_keywords()
    urls = parse_feed(feed, keywords)
    insert_feed_url(urls, page_type=feed.feed_type)


def site_feed():  # level:2
    urls = []
    for site in Site.find(prior_level=2):
        urls.append(site.url)

    insert_feed_url(urls, page_type=PAGE_TYPE.NORMAL_FEED_PAGE, depth=0)


def dealer_feed():
    urls = []
    for dealer_feed in DealerFeed.find():  # TODO: check project is available
        urls.append(dealer_feed.url)

    insert_feed_url(urls, page_type=PAGE_TYPE.NORMAL_FEED_PAGE)


def get_formhash(url, regex):
    try:
        search = curl(url)
    except:
        print url, 'connection error getting formhash'
        return None

    formhash = re.search(regex, search.utf8_source).group(1)
    return formhash


def search_id_feed():
    all_keywords = get_keywords()

    for post_feed in PostFeed.find():
        for industry_id in post_feed.industry_id:
            keywords = all_keywords.get(industry_id, [])
            try:
                formhash_regex = post_feed.formhash_regex
                formhash = get_formhash(post_feed.formhash_url, formhash_regex)
                if formhash is None:
                    continue

                for keyword in keywords:
                    post_feed.kwargs['topic'] = keyword
                    post_feed.kwargs['formhash'] = formhash
                    insert_feed_url([url_quote(post_feed.post_url % post_feed.kwargs, post_feed.charset)], post_feed.method)
            except AttributeError:
                print 'post_feed error for _id:%s %s' % (post_feed._id, traceback.format_exc().replace('\n', '$$'))
                continue


def wemedia_feed_360():
    def get_pages():
        url = "http://wemedia.so.com/media_list.html"
        resp = curl(url)
        source_html = resp.utf8_source
        p = re.compile('href="media_list_(\d+).html">末页</a>')
        max_value = 0
        max_value, =  p.findall(source_html)

        if max_value == 0:
            return []
        max_value = int(max_value)

        urls = []
        urls.append(url)
        for i in range(2, max_value + 1):
            urls.append("http://wemedia.so.com/media_list" + "_" + str(i) + ".html")
        return urls

    urls = get_pages()
    insert_feed_url(urls, page_type=PAGE_TYPE.NORMAL_FEED_PAGE, depth=1)


def baidu_baijia_feed():
    def get_pages():
        url = "http://baijia.baidu.com/?tn=listauthor"
        resp = curl(url)
        source_html = resp.utf8_source
        p = re.compile('href="(http://\w+\.baijia.baidu.com)/"')
        urls = p.findall(source_html)

        if urls == []:
            return []
        return urls

    urls = get_pages()
    insert_feed_url(urls, page_type=PAGE_TYPE.NORMAL_FEED_PAGE, depth=1)


def wemedia_feed_sogou():
    data = {}
    data['url_rule'] = ["http://weixin.sogou.com/weixin?query=%(topic)s&tsn=1&interation=&type=2&interV=kKIOkrELjbkRmLkElbkTkKIMkrELjboImLkEk74TkKIRmLkEk78TkKILkbELjboN_105333196&ie=utf8&page=%(page)s&p=40040100&dp=1&num=100"]

    data['site_id'] = 68
    data['charset'] = 'utf-8'
    data['feed_type'] = PAGE_TYPE.SEATCH_FEED_PAGE
    data['industry_id'] = [INDUSTRY['*']]
    data['describe'] = u"搜狗微信搜索"
    data['created_on'] = datetime.datetime.now()
    data['status'] = RECORD_STATUS.NORMAL
    data['kwargs'] = {"page": [1, 8]}
    feed = Feed(**data)
    keywords = get_keywords()
    urls = parse_feed(feed, keywords, page_range=(0, 8))
    insert_feed_url(urls, page_type=feed.feed_type)


def main():
    feed()
    search_id_feed()

    now = datetime.datetime.now()
    if now.hour % 2 == 0:
        sogou_feed()
        site_feed()
        dealer_feed()

    if now.hour % 12 == 0:
        wemedia_feed_360()
        wemedia_feed_sogou()
        baidu_baijia_feed()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        mail('no-reply@buzzmaster.com.cn', ['wangjian@admaster.com.cn', 'yangchao@admaster.com.cn', 'lidexin@admaster.com.cn'], 'insert feed encounter error', traceback.format_exc())
