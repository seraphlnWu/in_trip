#coding=utf-8

import datetime
from bottle import request, response

from in_trip.lib.http import get_domain
from in_trip.lib.consts import INDUSTRY, PAGE_TYPE

from admin.lib.utils import render, jsonify
from admin.config.consts import RECORD_STATUS
from admin.model import Feed, Site, parse_feed

FULL_TIME_FORMAT = "%Y-%m-%d %H:%M"
@render('feeds/index.html')
def index(page):
    page_count = 15
    keyword = (request.params.get('keyword') or "").decode('utf-8')
    records = []
    if keyword:
        if keyword in INDUSTRY:
            records = [row for row in Feed.find(industry_id=INDUSTRY[keyword], ignore_status=True)]
        elif keyword.isdigit():
            feed = Feed.get(_id=int(keyword))
            records = [feed] if feed is not None else []
        else:
            domain = get_domain(keyword)
            site = Site.get_by_domain(domain)
            if site:
                records = [row for row in Feed.find(site_id=site._id, ignore_status=True).sort('_id')]
    else:
        records = [row for row in Feed.find(ignore_status=True).sort('_id').skip((page - 1) * page_count).limit(page_count)]
    return {'feeds': records, 'page': page, "keyword":keyword, "feed_type": PAGE_TYPE}

def add():
    data = get_from_data()

    #TODO:关联site
    feed = Feed(**data)
    feed.save()
    return {'status': True, 'msg': u""}

def update():
    data = get_from_data()
    _id = int(request.forms.get('_id'))
    feed = Feed(_id=_id)
    feed.update(**data)
    return {'status': True, 'msg': u""}


def get_from_data():
    data = {}
    url_rule = request.forms.get('url_rule')
    data['url_rule'] = [u.strip() for u in url_rule.split('\r\n')]
    domain_name = get_domain(data['url_rule'][0])
    site = Site.get_by_domain(domain_name)
    prior_level = int(request.forms.get('prior_level'))
    if site is None:
        site_data = {'domain': domain_name, 'url': data['url_rule'][0], 'site_name': '', 'status': RECORD_STATUS.NORMAL, 'prior_level': prior_level}
        site = Site(**site_data)
        site.save()
    elif site.prior_level != prior_level:
        site.update(prior_level=prior_level)

    data['site_id'] = site._id
    data['charset'] = request.forms.get('charset') or 'utf-8'
    data['feed_type'] = int(request.forms.get('feed_type'))
    industry_id_li = request.forms.getall('industry')
    data['industry_id'] = [int(id) for id in industry_id_li]
    data['describe']=request.forms.get('describe') or ""
    data['created_on'] = datetime.datetime.now()
    data['status'] = RECORD_STATUS.NORMAL
    kwargs_len = (len(request.forms.items()) - 6)/2
    kwargs = {}
    for index in range(kwargs_len):
        name = request.forms.get("field"+str(index)+"_name")
        value = request.forms.get("field"+str(index)+"_value").split(",")
        for i in range(len(value)):
            try:
                value[i] = int(value[i])
            except:
                break
        kwargs[name] = value

    # data['delay'] = float(request.forms.get('delay'))
    # data['prior_level'] = int(request.forms.get('prior_level'))
    # data['handler'] = request.forms.get('handler')
    # data['uptime'] = int(request.params.get('uptime') or 300)
    # data['cookie'] = request.forms.get('cookie') or None
    data['kwargs'] = kwargs

    return data

@jsonify()
def j_get_feed():
    _id = request.params.get('_id')
    msg = u""
    if _id:
        feed = Feed.get(int(_id))
        site = Site.get(feed.site_id)
        if site:
            feed = feed.to_mongo()
            feed['prior_level'] = site.prior_level
            return {'status': True, 'data': feed}

        msg = u"种子对应网站不存在，请先添加网站"

    return {'status': False, 'msg': msg}

def j_op():
    _id = int(request.params.get('_id'))
    feed = Feed.get(_id)
    if feed.status == RECORD_STATUS.NORMAL:
        status = RECORD_STATUS.DELETED
    else:
        status = RECORD_STATUS.NORMAL
    feed.update(status=status)
    return {'status': True, 'msg': u""}

def j_test_feed():
    data = get_from_data()
    feed = Feed(**data)
    keywords = {INDUSTRY[u"*"]: [u"测试", ], }
    try:
        urls = parse_feed(feed, keywords)
        result = {'status': True, 'data': urls[0]}
    except Exception as e:
        result = {'status': False, 'msg': str(type(e))}

    return result
