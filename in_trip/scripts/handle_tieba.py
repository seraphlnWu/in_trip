#coding=utf-8
import re
import csv
import time
import codecs
from datetime import datetime
import urlparse

MONGODB_DB_NAME = 'sandbox_mongo_buzz'

from admin.lib.utils import curl
from readability.htmls import build_doc

def get_url_with_qs(url):
    parse_result = urlparse.urlparse(url)
    return '%s://%s%s' % (parse_result.scheme, parse_result.netloc, parse_result.path)

def main():
    start=datetime(2013, 06, 16)
    end=datetime(2013, 06, 17)
    f = open('stat-0616.csv', 'w') # 新产生的文件名, 最终发给顾问得
    f2 = codecs.open(u'中国最强音.csv', 'r', 'gbk') # 由query_from_pg.py生成的文件名
    writer = csv.writer(f)
    parsed_set =  {}
    for line in f2:
        row = line.split(',')
        print row[1], row[0]
        if 'tieba' not in row[0]:
            continue
        topic_url = get_url_with_qs(row[0])
        if topic_url not in parsed_set:
            html_source, _= curl(topic_url)
            if html_source:
                unicode_source = html_source.decode('gbk', 'ignore')
                if u'你访问的贴子不存在' in unicode_source or u'你访问的贴子被隐藏' in unicode_source:
                    print "ERROR:", row[0] 
                    continue
                doc = build_doc(unicode_source)
                title = doc.xpath("//h1//text()") 
                if "#" in row[0]:
                    title = u"[回复]" + title[0] if len(title)>0 else ''
                else:
                    title = title[0] if len(title)>0 else ''

                comment_num = doc.xpath("//span[@id='comment_num']/text()|(//li[@class='l_reply_num'])[3]/span/text()")
                comment_count=comment_num[0] if len(comment_num)>0 else 0

                at_xpath = "//div[contains(@class,'l_post')]//@data-field"
                regex = re.compile(u'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2}).*?(?P<hour>\d{1,2}).*?(?P<minute>\d{1,2})')
                at = doc.xpath(at_xpath)
                matched = regex.search(str(at))
                kwargs = {}
                if matched:
                    for key, value in matched.groupdict().items():
                        if value:
                            kwargs[key] = int(value)
                    at_str = datetime(**kwargs).strftime("%Y-%m-%d %H:%M:%S") 
                else:
                    at_str=''

                line = [topic_url, title[4:], at_str, comment_count]
                line = [column.encode('gbk') if isinstance(column, unicode) else column for column in line]
                #line=map(lambda x: re.sub(u'\s+|\xa0', ' ', x.decode('utf-8')).encode('gbk', 'ignore') if isinstance(x, basestring) else x, line)
                parsed_set[topic_url] = {'title': title, 'comment_count': comment_count} 
                
                at_time=datetime.strptime(at_str, "%Y-%m-%d %H:%M:%S")
                if start<= at_time < end:
                    writer.writerow(line)
            time.sleep(3) 

        if topic_url in parsed_set:
            title = parsed_set[topic_url]['title']
            comment_count = parsed_set[topic_url]['comment_count']
            line = [row[0], title, row[1], comment_count]
            line = [column.encode('utf-8') if isinstance(column, unicode) else column for column in line]

            at_time=datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            if start<= at_time < end:
                writer.writerow(line)

    f.close()
    f2.close()

if __name__ == '__main__':
    main()
