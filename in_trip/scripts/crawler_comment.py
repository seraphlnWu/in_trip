#coding=utf-8

import re
import csv
import sys
import os.path
import urlparse
import hashlib
from collections import deque

from admin.lib.utils import curl, get_domain
from readability.htmls import build_doc

crawed_urls = set()

def main():
    for file_name in  sys.argv[1:]:
        print file_name
        f = open(file_name, 'r')
        f2 = open('new-1/' + os.path.basename(file_name), 'w')
        writer = csv.writer(f2)
        for line in f:
            url = line.decode('gbk').split(',')[2]
            f2.write(line)

            if 'bbs' not in url:
                continue

            page_urls = deque([url, ]) 
            comments = []
        
            while len(page_urls):
                page = page_urls.popleft() 
                _comments, _pages = get_comments(page)
                page_urls.extend(_pages)
                comments += _comments

            for comment in comments:
                text = comment.title()
                if isinstance(text, str):
                    text = text.decode('utf-8')
                text = re.sub(u'\s+|\xa0', ' ', text)
                if text in (u'', u' '):
                    continue
                writer.writerow(['', text.encode('gbk', 'replace')])

        f.close()
        f2.close()
    
def get_comments(url):
    xpaths = {
            '21cn.com': [("//td[@class='t_f']/text()",), ("//div[@class='pg']//a/@href", )],
            '55bbs.com': [("//div[@class='t_msgfont']/text()", ), ("//div[@class='pages']//a/@href", )],
            #'lirenn.55bbs.com': [("//dd[@class='clearfix']//p/text()", ), ],
            'lady8844.com': [("//td[@class='t_msgfont']/text()",), ("//div[@class='pages']//a/@href", )],
            'onlylady.com': [("//td[@class='t_f']/text()",), ("//div[@class='pg']//a/@href", )],
            'pclady.com.cn': [("//div[@class='replyBody']/text()", ), ("//div[@class='pager']//a/@href", )],
            'yoka.com': [("//td[@class='con_content']/text()", ), ("//dl[@class='bbs_Page']/dt//a/@href", )], # ajax 
        }

    domain = get_domain(url)
    parse_result = urlparse.urlparse(url)
    page_urls = []
    prefix = parse_result.scheme + '://' + parse_result.netloc
    if domain not in xpaths:
        return [], []
    if (domain == '55bbs.com' and 'liren' in url) or url in crawed_urls:
        return [], page_urls
    xpath = xpaths[domain]
    html_source, _ = curl(url)
    if not html_source:
        return [], []
    print domain, url
    crawed_urls.add(url)
    doc = build_doc(html_source)
    comments = doc.xpath(xpath[0][0])
    pages = doc.xpath(xpath[1][0])
    for page in pages:
        if page.startswith('/'):
            page = prefix + page
        if not page.startswith('http'):
            page = prefix + '/' + page

        if page not in crawed_urls:
            page_urls.append(page)

    return comments, page_urls

if __name__ == '__main__':
    main()  
