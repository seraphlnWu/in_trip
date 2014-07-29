#coding=utf-8

import re
import csv
import time
import urlparse
from collections import deque
from lxml.html import tostring

from admin.lib.utils import curl
from in_trip.lib.http import get_domain
from readability.htmls import build_doc

xpath = {            
    'mtime.com': [(("//li[@class='ele_img_item pt25']/div[2]/p[2]/a/@href", ), 
                   ("//div[@class='pagenav tc mt20']/a/@href", ), 
                   ("//div[@id='blogInfoRegion']/h2/text()", "//div[@class='mt5']/span[1]/text()", "//div[@class='mt5']/span[2]/time/text()", "//div[@class='content']/p//text()")
                  ),
                  (("", ),
                   ("//div[@class='pagenav tc mt20']/a/@href", ), 
                   ("//a[@name='movietweetuser']/text()", "//span[@class='mt3 fl']/a/@entertime", "//dt[@class='normal']//text()"),
                  ),],
    'douban.com': [(("//div[@class='review-hd']/h3/a[2]/@href",),
                    ("//div[@id='paginator']/a[@class='next']/@href", ),
                    ("//div[@id='content']/h1/span/text()", "//div[@class='main-hd']/p/a[2]/span/text()", "//span[@class='main-meta']/text()", "//div[@id='link-report']/div/text()")
                   ),
                   (("", ),
                    ("//div[@id='paginator']/a/@href", ), 
                    ("//div[@class='comment']/h3/span[@class='comment-info']/a/text()", "//div[@class='comment']/h3/span[@class='comment-info']/span[2]/text()|//div[@class='comment']/h3/span[@class='comment-info']/span[1]/text()", "//div[@class='comment']/p/text()"),
                   ), ]
}

"""
def get_host(url, scheme=True):
    parse_result = urlparse.urlparse(url)
    host = parse_result.netloc
    if scheme:
        host = parse_result.scheme + '://' + host
    return host 
"""

def build_url(url, relative_paths):
    parse_result = urlparse.urlparse(url)
    host = parse_result.netloc
    path = parse_result.path
    scheme = parse_result.scheme
    host_with_scheme = scheme + "://" + host

    results = []
    for relative_path in relative_paths: 
        if relative_path.startswith('http'):
            results.append(relative_path)
            continue

        if relative_path.startswith('/'):
            complete_url = host_with_scheme + relative_path

        elif relative_path.startswith('?'):
            complete_url = host_with_scheme + path + relative_path

        elif relative_path[-2:] == './' or relative_path[-1] != '.':
            complete_url = host_with_scheme + path[:path.rfind('/') + 1] + relative_path

        results.append(complete_url)

    return results 

def split_page(domain, html_source, encode="utf-8"):
    doc = build_doc(html_source)
    if domain == 'mtime.com':
        sub_page_nodes = doc.xpath(".//div[@class='t_module']")
    elif domain == 'douban.com':
        sub_page_nodes = doc.xpath(".//div[@class='comment-item']")

    for sub_page_node in sub_page_nodes:
        html = u"""
            <html>
                <body>
                %s
                </body>
            </html>
        """ % tostring(sub_page_node).decode('utf-8')
        yield html.encode(encode)

def get_comments(source_url):
    queue = deque() 
    comments = []
    domain = get_domain(source_url)
    crawled_url = set()
    if domain == 'mtime.com':
        url = source_url + '/comment.html'
    elif domain == 'douban.com':
        url = source_url + "/reviews"
    queue.append(url)
    comment_urls = set() 
    while len(queue):
        url = queue.popleft()
        if url in crawled_url:
            continue
        print url
        html_source, _ = curl(url)
        if not html_source:
            time.sleep(2*60)
            continue
        time.sleep(1.2)
        crawled_url.add(url)
        doc = build_doc(html_source)
        pages = doc.xpath(xpath[domain][0][1][0]) 
        pages = build_url(url, pages)
        queue.extend(pages)
        comment_urls |= set(doc.xpath(xpath[domain][0][0][0]))
    for comment_url in comment_urls:
        print comment_url
        comment_source, _ = curl(comment_url)
        if not comment_source:
            time.sleep(2*60)
            continue
        time.sleep(1.2)
        doc = build_doc(comment_source)
        title = u' '.join(doc.xpath(xpath[domain][0][2][0]))
        author = u" ".join(doc.xpath(xpath[domain][0][2][1]))
        created_on = u' '.join(doc.xpath(xpath[domain][0][2][2]))
        content = u' '.join(doc.xpath(xpath[domain][0][2][3]))
        #comments.append((title, author, created_on, content))
        yield (title, author, created_on, content)
    if domain == 'mtime.com':
        url = source_url + '/newshortcomment.html'
    elif domain == 'douban.com':
        url = source_url + "/comments"
    queue.append(url)
    while len(queue):
        url = queue.popleft()
        if url in crawled_url:
            continue
        html_source, _ = curl(url)
        if not html_source:
            time.sleep(2*60)
            queue.appendleft(url)
            continue
        print url
        time.sleep(1.2)
        crawled_url.add(url)
        doc = build_doc(html_source)
        pages = doc.xpath(xpath[domain][0][1][0]) 
        pages = build_url(url, pages)
        queue.extend(pages)
        for page_source in split_page(domain, html_source):
            doc = build_doc(page_source)
            author = u' '.join(doc.xpath(xpath[domain][1][2][0]))
            created_on = u' '.join(doc.xpath(xpath[domain][1][2][1]))
            content = u' '.join(doc.xpath(xpath[domain][1][2][2]))
            #comments.append((u"", author, created_on, content))
            yield (u"", author, created_on, content)


if __name__ == '__main__':
    with open('commnet.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        for link in [u"http://movie.douban.com/subject/5422105/", u"http://movie.douban.com/subject/3412882/", u"http://movie.douban.com/subject/10726941/"]:
            writer.writerow([link.encode('gbk'), ])
            for comment in get_comments(link):
                writer.writerow(map(lambda x: isinstance(x, unicode) and re.sub(u'\s+|\xa0', ' ', x).encode('gbk', 'replace') or x, comment))
