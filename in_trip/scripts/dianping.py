#coding=utf-8
import urllib
import json
import re
import base64
import copy
import pyquery
import zipfile
import csv
import requests
from buzz.youku.writer import XlsWriter
from os import system
from admin.lib.utils import curl
from readability.htmls import build_doc
from datetime import datetime
from time import sleep

rank_dict = {
        u'很差' : u'1 星',
        u'差'   : u'2 星',
        u'还行' : u'3 星',
        u'好'   : u'4 星',
        u'很好' : u'5 星',
}


def how_many_pages(total, count):
    if total < 0:
        return 0
    if total%count != 0:
        return (total/count) + 1
    else:
        return total/count

def get_review_page(url, page):
    review_url = url + '/review_more?pageno=%s'%page
    html_source, _= curl(review_url)
    if html_source:
        html_source = re.sub('\<br\s*\>|\<br/\>', ' ', html_source)
        unicode_source = html_source.decode('utf-8', 'ignore')
        doc = build_doc(unicode_source)
        comment_list = doc.xpath("//div[@class='J_brief-cont']/text()")
        time_list = doc.xpath("//span[@class='time']/text()")
        rank_list = map(lambda x:rank_dict[x], doc.xpath("//div[@class='user-info']/span[1]/@title"))
        user_list = doc.xpath("//p[@class='name']/a[@class='J_card']/text()")
        return zip(user_list, rank_list, time_list, comment_list)

def get_reviews(xlsfile, url):
    start = datetime(2000, 7, 1)
    end = datetime(2013, 8, 16)
    review_url = url + '/review_more?pageno=1'
    html_source, _= curl(review_url)
    if html_source:
        unicode_source = html_source.decode('utf-8', 'ignore')
        doc = build_doc(unicode_source)
        name = doc.xpath("//div[@class='info-name']/h2/a/text()")
        account = doc.xpath("//span[@class='active']/em[1]/text()")
        account = re.search('\d+', str(account))
        account = int(account.group(0)) if account else 0
        pages = how_many_pages(account, 20)
        xlsfile.append(name)
        for page in range(1, pages+1):
            too_old = False
            lines = get_review_page(url, page)
            for line in lines:
                time = re.findall('\d+', line[2])
                length = len(time)
                if length == 2 or length >3:
                    month = int(time[0])
                    day  = int(time[1])
                    year = 2013
                elif length ==3:
                    year = int('20'+time[0])
                    month = int(time[1])
                    day = int(time[2])

                comment_date = datetime(year, month, day)
                if comment_date<end:
                    if comment_date<start:
                        too_old = True
                        break

                    line = list(line)
                    line[2] = comment_date.date()
                    line.insert(0, name[0])
                    print line
                    print time
                    print year, month, day

                    xlsfile.append(line)

            sleep(2)

            if too_old:
                break

    xlsfile.append([' '])
    xlsfile.append([' '])

def run():
    urls = [] # add shop link list here
    xlsfile = XlsWriter(path='.', filename='starbucks')
    titles = [
            u'店名',
            u'昵称',
            u'评级',
            u'时间',
            u'内容',
    ]
    xlsfile.append(titles)
    for url in urls:
        get_reviews(xlsfile, url)

    xlsfile.close()

if __name__ == '__main__':
    #run()
    review_url = 'http://www.so.com/s?q=Azure+site:blogs.msdn.com&pn=4&j=0'
    html_source, _= curl(review_url)
    print html_source


