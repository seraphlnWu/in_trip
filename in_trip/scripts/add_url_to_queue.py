# -*- coding: utf-8 -*-

import time
import logging
import requests
import re

from urllib import quote
from itertools import product

from in_trip.utils.feed_db import put_url_item
from in_trip.lib.store import mongo
from admin.lib.utils import curl
from admin.model import get_feed_urls
from readability.htmls import build_doc
from in_trip.lib.http import get_domain

logger = logging.getLogger()

def load_feeds(feed_key, url_list, isindex=True):
    assert isinstance(url_list, list)

    url_item_list = map(lambda x: {
        "url"    : x,
        "isseed" : False,
        "isindex": False,
        "timestamp": time.time()
    }, url_list)
    logger.info("insert Feed_key:%s to redis" % feed_key)
    for url_item in url_item_list:
        put_url_item(feed_key, url_item, True)

if __name__ == '__main__':

    db = mongo.get_db()
    #feed_key = 'tieba_zghsy'
    #url_list = map(lambda (x, y):
    #     "http://tieba.baidu.com/f?ie=utf-8&kw=%s&tp=0&pn=%d" % (x, y),
    #     product(map(lambda x: quote(x.encode("utf-8")), [u"中国最强音", ]),  #u"湖南卫视"]),
    #     xrange(650, 6100, 50)))
    #
    #for url in url_list:
    #    print url
    #    html_source, _= curl(url)
    #    time.sleep(2)
    #    if html_source:
    #        unicode_source = html_source.decode('gbk', 'ignore')
    #        if u'你访问的贴子不存在' in unicode_source or u'你访问的贴子被隐藏' in unicode_source:
    #            print "ERROR:", row[0]
    #            continue
    #        doc = build_doc(unicode_source)
    #        links = ['http://tieba.baidu.com' + link for link in doc.xpath("//div[@class='threadlist_text threadlist_title j_th_tit  notStarList ']/a/@href")]
    #        load_feeds(feed_key, links)

    #keywords = [u'优势', u'申请', u'中欧', u'长江', 'MBA']

    #chasedream = requests.get('http://forum.chasedream.com/search.php?mod=forum')
    #formhash = re.search('name="formhash" value="(.*?)"', chasedream.text).group(1)
    #print formhash

    #sharewithu = requests.get('http://www.sharewithu.com/search.php')
    #elements=re.search('sId=(\d+)\&amp;ts=(\d+)\&amp;mySign=(.*?)\&q', sharewithu.text)
    #sId,ts,mySign=elements.group(1),elements.group(2),elements.group(3)
    #print sId,ts,mySign

    #for keyword in keywords:
    #    form_data = {
    #        'formhash':formhash,
    #        'srchtxt':keyword,
    #        'srchuname':'',
    #        'srchfilter':'all',
    #        'srchfrom':0,
    #        'before':'',
    #        'orderby':'dateline',
    #        'ascdesc':'desc',
    #        'srchfid[]':'all',
    #        'searchsubmit':'yes'
    #    }

    #    result = requests.post('http://forum.chasedream.com/search.php?mod=forum', data=form_data)
    #    try:
    #        searchid = re.search('searchid=(\d+)\&', result.url).group(1)
    #    except:
    #        print result.url
    #        continue

    #    url_list = map(lambda (x, y):'http://forum.chasedream.com/search.php?mod=forum&searchid=%d&orderby=dateline&ascdesc=desc&searchsubmit=yes&page=%d'%(x, y), product([int(searchid)], range(1, 11)))
    #    print url_list
    #    feed_key = 'chasedream_search'
    #    load_feeds(feed_key, url_list)
    #    time.sleep(15)

    #url='http://so.sharewithu.com/f/search?sId=%s&ts=%s&mySign=%s&extFids=&qs=txt.adv.a&q=%%s&author=&searchLevel=3&orderField=posted&timeLength=0&threadScope=all&orderType=desc&page=%%d'%(sId, ts, mySign)
    #url_list = map(lambda (keyword, page):url%(keyword, page), product(map(lambda x: quote(x.encode("utf-8")), keywords), range(1, 11)))
    #print url_list
    #feed_key = 'sharewithu_search'
    #load_feeds(feed_key, url_list)

    ##webgame duowan
    #project_id = 29
    #project = db.project.find_one({'_id':project_id})
    #topic_ids = project['topic_ids']
    #keywords = [db.topic.find_one({'_id':topic_id})['main_key'] for topic_id in topic_ids]

    #duowan = requests.get('http://bbs.duowan.com/search.php?mod=forum')
    #formhash = re.search('name="formhash" value="(.*?)"', duowan.text).group(1)
    #print formhash
    #domain = 'duowan.com'

    #for keyword in keywords:
    #    form_data = {
    #        'formhash':formhash,
    #        'srchtxt':keyword,
    #        'srchuname':'',
    #        'srchfilter':'all',
    #        'srchfrom':0,
    #        'before':'',
    #        'orderby':'dateline',
    #        'ascdesc':'desc',
    #        'srchfid[]':'all',
    #        'searchsubmit':'yes'
    #    }

    #    result = requests.post('http://bbs.duowan.com/search.php?mod=forum', data=form_data)
    #    try:
    #        searchid = re.search('searchid=(\d+)\&', result.text).group(1)
    #        print searchid
    #    except:
    #        print result.url
    #        raise
    #        continue

    #    url_list = map(lambda (x, y):'http://bbs.duowan.com/search.php?mod=forum&searchid=%s&orderby=dateline&ascdesc=desc&searchsubmit=yes&page=%s'%(x, y), product([int(searchid)], range(1, 87)))
    #    print url_list
    #    load_feeds(domain, url_list)
    #    time.sleep(15)

    #project_id = 25 # 露得清
    #project = db.project.find_one({'_id':project_id})
    #topic_ids = project['topic_ids']
    #keywords = []
    #for topic_id in topic_ids:
    #    topic = db.topic.find_one({'_id': topic_id})
    #    keywords.append(topic['main_key'])

    #for keyword in keywords:
    #    origin = keyword
    #    keyword = quote(origin.encode("utf-8"))

    #    # 55bbs
    #    url = "http://bbs.55bbs.com/my_search.php?q=%s&searchsubmit=yes" % keyword
    #    html_source, _ = curl(url)
    #    if html_source:
    #        unicode_source = html_source.decode('gbk', 'ignore')
    #        bbs55 = build_doc(unicode_source)
    #        search_url = bbs55.xpath("//div[@class='box message']/p[2]/a/@href")
    #        search_url =  search_url[0].split('q=')[0]+'q=%s'% keyword
    #        source = requests.get(search_url)
    #        elements = re.search('sId=(\d+)\&ts=(\d+)\&mySign=(.*?)\&', source.text)
    #        sId,ts,mySign=elements.group(1),elements.group(2),elements.group(3)
    #        final_url = 'http://search.discuz.qq.com/f/search?q=%%s&sId=%s&ts=%s&mySign=%s&searchLevel=3&menu=1&qs=txt.tsort.a&orderField=posted&orderType=desc&page=%%s'%(sId, ts, mySign)

    #        url_list = map(lambda x:final_url%(keyword, x), range(1, 11))
    #        print url_list
    #        load_feeds('55bbs.com', url_list)

    #    # onlylady
    #    keyword = quote(origin.encode("gb2312"))
    #    url = 'http://so.onlylady.com/index.php?idx=7&wd=%s&ordertype=1&page=%s'
    #    url_list = map(lambda x:url%(keyword, x), range(1, 60))
    #    print url_list
    #    load_feeds('onlylady.com', url_list)

    #    # pclady
    #    keyword = quote(origin.encode("gb2312"))
    #    url = 'http://ks.pclady.com.cn/lady_cms.jsp?q=%s&sort=input_date-long%%3Adesc&pageNo=%s'
    #    url_list = map(lambda x:url%(keyword, x), range(1, 10))
    #    print url_list
    #    load_feeds('pclady.com.cn', url_list)

    #    url = 'http://ks.pclady.com.cn/lady_bbs.jsp?q=%s&sort=time&pageNo=%s'
    #    url_list = map(lambda x:url%(keyword, x), range(1, 20))
    #    print url_list
    #    load_feeds('pclady.com.cn', url_list)

    #    # yoka
    #    keyword = quote(origin.encode("gbk"))
    #    url = 'http://search.yoka.com/s.php?wd=%s&page=%s&si=yoka.com&lm=180'
    #    url_list = map(lambda x:url%(keyword, x), range(1, 77))
    #    print url_list
    #    load_feeds('yoka.com', url_list)

    #    # ellechina
    #    keyword = quote(origin.encode("utf-8"))
    #    url = 'http://www.ellechina.com/se=%s-pn-%s.shtml'
    #    url_list = map(lambda x:url%(keyword, x), range(1, 30))
    #    print url_list
    #    load_feeds('ellechina.com', url_list)

    #    #lady8844
        #lady8844 = requests.get('http://bbs.lady8844.com/search.php')
        #formhash = re.search('name="formhash" value="(.*?)"', lady8844.text).group(1)
        #print formhash
        #form_data = {
        #    'formhash':formhash,
        #    'srchtxt':origin,
        #    'srchtype':'title',
        #    'searchsubmit':'true',
        #    'st':'on',
        #    'srchuname':'',
        #    'srchfilter':'all',
        #    'srchfrom':0,
        #    'before':'',
        #    'orderby':'lastpost',
        #    'ascdesc':'desc',
        #    'srchfid[]':'all'
        #}

        #result = requests.post('http://bbs.lady8844.com/search.php', data=form_data)
        #try:
        #    searchid = re.search('searchid=(\d+)\&', result.url).group(1)
        #    print searchid
        #except:
        #    print result.url
        #    raise
        #    continue
        #url = 'http://bbs.lady8844.com/search.php?searchid=%s&orderby=lastpost&ascdesc=desc&searchsubmit=yes&page=%d'
        #url_list = map(lambda x:url%(searchid, x), range(1, 20))
        #print url_list
        #load_feeds('lady8844.com', url_list)

        #time.sleep(15)
