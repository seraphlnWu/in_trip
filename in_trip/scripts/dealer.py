#coding=utf-8
"""
爬取dealer促销信息首页
"""
import re
import urlparse
import datetime
import itertools

from readability import Document
from buzz.lib.http import url_quote, get_domain, curl

from admin.model import DealerFeed, Topic

url_rule = "http://www.so.com/s?q=%(topic)s+site%%3A%(site)s&pn=%(page)s&j=0&ls=0&src=srp_paging&fr=tab_news"

SITES =[
    (28, "dealer.bitauto.com", "news_0.html"),
    (94, "dealer.autohome.com.cn", "newslist.html"),
    (22, "price.pcauto.com.cn", "news.html"),
]

DEALER_PATH = re.compile("^/\d+/?$")
ALPHA_CHAR = re.compile('^[a-z]+$', re.I)

def main(project_id):
    for topic in Topic.find(project_id=project_id, status=0):
        keyword = topic.main_key
        if not ALPHA_CHAR.match(keyword) and DealerFeed.find(keyword=keyword).count() <= 0:
            print keyword
            kwargs = {"topic": [keyword, ], "page": range(1, 26)}
            for site_id, site, postfix in SITES:
                kwargs['site'] = [site, ]
                for key,value in kwargs.iteritems():
                    kwargs[key] = [url_quote(x, "utf-8") for x in value]

                args = [dict(zip(kwargs.iterkeys(), value)) for value in itertools.product(*kwargs.itervalues())]
                urls = [url_rule % arg for arg in args]
                dealer_urls = set()
                for url in urls:
                    print url
                    resp = curl(url)
                    url_links = extract_urls(resp)
                    dealer_urls |= set(url_links)

                for dealer_url in dealer_urls:
                    parse_result = urlparse.urlparse(dealer_url)
                    if DEALER_PATH.match(parse_result.path):
                        dealer_url = urlparse.urljoin(dealer_url, postfix)
                        dealer_feed = DealerFeed(url=dealer_url, keyword=keyword, site_id=site_id, created_on = datetime.datetime.now(), status=0)
                        dealer_feed.save()

def extract_urls(resp):
    url_links = []
    doc = Document(resp, special=None)
    base = doc.dom.find('.//base')
    base_url = url_quote(base.get('href') if base is not None and base.get('href') else doc.resp.url)
    blocks = doc.bbs_blocks or [doc.main_block, ]
    for block in blocks:
        for link in block.xpath('.//a'):
            href = link.get('href')
            if not href:
                continue
            href = url_quote(href.strip(), doc.resp.encoding)
            if href.startswith('http'):
                url_links.append(href)
            else:
                url_links.append(urlparse.urljoin(base_url, href))  # add cache

    url_links = list(set(url_links))
    site_domain = resp.domain
    white_urls = filter(lambda x: get_domain(x) != site_domain, url_links)

    return white_urls

if __name__ == '__main__':
    main(72)
