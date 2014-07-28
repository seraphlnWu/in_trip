#coding=utf-8
#分析tieba数据分布

import sys

from admin.lib.utils import curl
from readability.htmls import build_doc

XPATH="//a[@id='tab_forumname']/@href|//div[@class='star_info']/a[1]/@href"

def main():
    with open("stat.log", 'w') as f:
        for line in sys.stdin:
            url = line.rstrip('\n')
            html_source, _ = curl(url)  
            if not html_source:
                print "ERROR:", url
                continue
            unicode_source = html_source.decode('gbk')
            if u'你访问的贴子不存在' in unicode_source or u'你访问的贴子被隐藏' in unicode_source:
                print "ERROR:", url
                continue
            else:
                print url

            doc = build_doc(html_source)
            tie_ba = doc.xpath(XPATH)
            f.write(tie_ba[0] + '\n')
        

if __name__ == '__main__':
    main()
