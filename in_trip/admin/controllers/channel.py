# coding=utf-8

from datetime import datetime

from json import dumps as json_dumps
from bottle import request, response

from buzz.lib.store import mongo
from buzz.lib.http import get_domain

from admin.lib.utils import render
from admin.model import get_inc_id, Channel
from admin.config.consts import RECORD_STATUS


@render('channel/index.html')
def index(page):
    page_count = 15
    keyword = (request.params.get('keyword') or '').decode('utf-8')
    records = []
    db = mongo.get_db()
    if keyword:
        domain = get_domain(keyword)
        site = db.site.find_one({'domain': domain, 'status': RECORD_STATUS.NORMAL})
        if site:
            channels = []
            for row in db.channel.find({'site_id': site['_id']}).sort('_id'):
                if row['status'] == RECORD_STATUS.NORMAL:
                    channels.append(row)

            site['channels'] = channels
            records.append(site)
    else:
        filters = {'status': RECORD_STATUS.NORMAL, }
        records = []
        for site in db.site.find(filters).sort('_id').skip((page - 1) * page_count).limit(page_count):
            site['channels'] = []
            records.append(site)

    return {'sites': records, 'keyword': keyword, 'query': 'true' if keyword else 'false', 'page': page}


def add():
    data = get_form_data()
    data['site_id'] = int(request.forms.get('site_id'))
    db = mongo.get_db()
    _id = get_inc_id(db.channel)
    data['_id'] = _id
    data['status'] = RECORD_STATUS.NORMAL
    data['created_on'] = datetime.now()
    db.channel.insert(data)
    return {'status': True, 'msg': u""}


def get_form_data():
    data = {}
    data['url'] = request.forms.get('url')
    data['channel_name'] = request.forms.get('channel_name')
    data['industry_id'] = int(request.forms.get('industry_id'))
    data['category_id'] = int(request.forms.get('category_id'))
    return data


def j_get_channels():
    site_id = int(request.params.get('site_id'))
    response.content_type = "application/json"
    results = []
    for row in Channel.find(site_id=site_id).sort('-_id'):
        row = row.to_mongo()
        row['created_on'] = row['created_on'].strftime('%Y-%m-%d %H:%M')
        results.append(row)
    return json_dumps(results)


def j_get_channel():
    _id = int(request.params.get('_id'))
    db = mongo.get_db()
    channel = db.channel.find_one({'_id': _id})
    channel['created_on'] = channel['created_on'].strftime('%Y-%m-%d %H:%M')
    return {'status': True, 'data': channel}


def update():
    data = get_form_data()
    _id = int(request.forms.get('_id'))
    db = mongo.get_db()
    db.channel.update({'_id': _id}, {'$set': data})
    return {'status': True, 'msg': u""}


def j_delete():
    _id = int(request.params.get('_id'))
    db = mongo.get_db()
    db.channel.update({'_id': _id}, {'$set': {'status': RECORD_STATUS.DELETED}})
    return {'status': True, 'msg': u""}
