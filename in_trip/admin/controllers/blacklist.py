#coding=utf-8

from json import dumps as json_dumps
from bottle import request, response

from in_trip.lib.store import mongo
from in_trip.lib.http import get_domain
from admin.config.consts import RECORD_STATUS

from admin.lib.utils import render
from admin.model import get_inc_id
from admin.lib.url_regex import regex_encoder, regex_decoder

@render('blacklist/index.html')
def index(page):
    page_count = 15
    keyword = (request.params.get('keyword') or '').decode('utf-8')
    records = []
    db = mongo.get_db()
    if keyword:
        domain = get_domain(keyword)
        site = db.site.find_one({'domain': domain, 'status': RECORD_STATUS.NORMAL})
        if site:
            blacklist = []
            for row in db.blacklist.find({'site_id': site['_id']}).sort('_id'):
                if row['status'] == RECORD_STATUS.NORMAL:
                    row['url_reg'] = regex_decoder(row['url_reg'])
                    blacklist.append(row)

            site['blacklist'] = blacklist
            records.append(site)
    else:
        filters = {'status': RECORD_STATUS.NORMAL, }
        records = []
        for site in db.site.find(filters).sort('_id').skip((page - 1) * page_count).limit(page_count):
            site['blacklist'] = []
            records.append(site)

    return {'sites': records, 'keyword': keyword, 'query': 'true' if keyword else 'false', 'page': page}

def add():
    data = get_form_data()
    data['site_id'] = int(request.forms.get('site_id'))
    db = mongo.get_db()
    _id = get_inc_id(db.blacklist)
    data['_id'] = _id
    data['status'] = RECORD_STATUS.NORMAL
    db.blacklist.insert(data)
    return {'status': True, 'msg': u""}

def get_form_data():
    data = {}
    data['url_reg'] = regex_encoder(request.forms.get('url_reg'))
    data['detail'] = request.forms.get('detail')
    return data

def j_get_blacklist():
    site_id = int(request.params.get('site_id'))
    response.content_type = "application/json"
    results = []
    db = mongo.get_db()
    for row in db.blacklist.find({'site_id': site_id, 'status': RECORD_STATUS.NORMAL}):
        if row:
            row['url_reg'] = regex_decoder(row['url_reg'])
        results.append(row)
    return json_dumps(results)

def j_get_black():
    _id = int(request.params.get('_id'))
    db = mongo.get_db()
    blacklist = db.blacklist.find_one({'_id': _id})
    if blacklist:
        blacklist['url_reg'] = regex_decoder(blacklist['url_reg'])
    return {'status': True, 'data': blacklist}

def update():
    data = get_form_data()
    _id = int(request.forms.get('_id'))
    db = mongo.get_db()
    db.blacklist.update({'_id': _id}, {'$set': data})
    return {'status': True, 'msg': u""}

def j_delete():
    _id = int(request.params.get('_id'))
    db = mongo.get_db()
    db.blacklist.update({'_id': _id}, {'$set': {'status': RECORD_STATUS.DELETED}});
    return {'status': True, 'msg': u""}

