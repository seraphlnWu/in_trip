#coding=utf-8

import pymongo
from bottle import request, response
from functools import partial

from buzz.lib.store import mongo
from buzz.lib.http import get_domain
from buzz.lib.consts import INDUSTRY

from admin.lib.utils import render
from admin.model import get_inc_id
from admin.model import Site, Xpath, Channel, UrlRegex
from admin.config.consts import RECORD_STATUS, XPATH_STATUS

site_find = partial(Site.find, status={'$ne': RECORD_STATUS.DELETED})
site_find_one = partial(Site.find_one, status={'$ne': RECORD_STATUS.DELETED})

@render('site/index.html')
def index(page):
    page_count = 15
    keyword = (request.params.get('keyword') or '').decode('utf-8')
    if not keyword:
        sites = [row for row in site_find().sort('_id').skip((page - 1) * page_count).limit(page_count)]
    else:
        if keyword in INDUSTRY:
            sites = [site for site in site_find(industry_id=INDUSTRY[keyword])]
        else:
            sites = []
            domain = get_domain(keyword)
            site = site_find_one(domain=domain)
            if site:
                sites.append(site)
    return {'sites': sites, 'keyword': keyword, 'page': page}

def add():
    url = request.forms.get('url')
    site_name = request.forms.get('site_name')
    prior_level = int(request.forms.get('prior_level') or 1)
    industry_id = int(request.forms.get('industry_id'))
    domain = get_domain(url)
    site = site_find_one(domain=domain)
    if site:
        status = False
    else:
        data = {'domain': domain, 'url': url, 'site_name': site_name, 'prior_level': prior_level, 'industry_id': industry_id, 'status': RECORD_STATUS.NORMAL}
        site = Site(**data)
        site.save()
        status = True
    return {'status': status, 'msg': u""}

def update():
    _id = int(request.forms.pop('_id'))
    url = request.forms.get('url')
    site_name = request.forms.get('site_name')
    prior_level = int(request.forms.get('prior_level') or 1)
    industry_id = int(request.forms.get('industry_id'))
    data = {'domain': get_domain(url), 'url': url, 'site_name': site_name, 'prior_level': prior_level, 'industry_id': industry_id}
    site = Site(_id=_id)
    site.update(**data)
    return {'status': True, 'domain': data['domain']}

def j_delete():
    _id = int(request.params.get('_id'))
    site=Site(_id=_id)
    site.update(status=RECORD_STATUS.DELETED)
    # xpath = Xpath(site_id=_id)
    # xpath.update(status=XPATH_STATUS.DELETED)
    # url_regex = UrlRegex(site_id=_id)
    # xpath.update(RECORD_STATUS.DELETED)
    channel = Channel(site_id=_id)
    channel.update(RECORD_STATUS.DELETED)
    return {'status': True, 'msg': u""}

def j_get_site(_id):
    site = Site.get(_id)
    site = site.to_mongo()
    #site['industry'] = INDUSTRY[site['industry_id']]
    return {'status': True, 'site': site}

def j_op():
    _id = int(request.params.get('_id'))
    print "here"
    site = Site.get(_id)
    if site.status == RECORD_STATUS.NORMAL:
        status = RECORD_STATUS.PAUSE
    else:
        status = RECORD_STATUS.NORMAL
    site.update(status=status)
    return {'status': True, 'msg': u""}
