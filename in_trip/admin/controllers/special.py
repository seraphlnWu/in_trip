# coding=utf-8

import re
import MySQLdb

from json import dumps as json_dumps
from bottle import request, response

from in_trip.lib.store import sqlstore, mongo
from in_trip.lib.http import get_domain, remove_schema
from admin.config.consts import RECORD_STATUS, SPECIAL_FIELD

from admin.lib.utils import render
from admin.model import get_inc_id


@render('special/index.html')
def index(page):
    page_count = 15
    keyword = (request.params.get('keyword') or '').decode('utf-8')
    records = []
    cursor = sqlstore.get_cursor(dict_format=True)
    db = mongo.get_db()
    if keyword:
        domain = get_domain(keyword)
        site = db.site.find_one({'domain': domain, 'status': RECORD_STATUS.NORMAL})
        if site:
            special = []
            cursor.execute('select id, url, site_id, url_regex from special where site_id=%s AND status=%s', (site['_id'], RECORD_STATUS.NORMAL))
            for row in cursor.fetchall():
                special.append(row)

            site['special'] = special
            records.append(site)
    else:
        filters = {'status': RECORD_STATUS.NORMAL, }
        records = []
        for site in db.site.find(filters).sort('_id').skip((page - 1) * page_count).limit(page_count):
            site['special'] = []
            records.append(site)

    cursor.close()

    return {'sites': records, 'keyword': keyword, 'query': 'true' if keyword else 'false', 'page': page}


def validate_regex(data):
    regex = re.compile(data['url_regex'])
    url = remove_schema(data['url'])
    return True if regex.match(url) else False


def add():
    data = get_form_data()
    status = validate_regex(data)
    if status:
        cursor = sqlstore.get_cursor()
        cursor.execute("insert into special values(null, %s, %s, default, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                       tuple(data[key] for key in SPECIAL_FIELD) + (RECORD_STATUS.NORMAL, ))
        cursor.connection.commit()
        cursor.close()

    return {'status': data, 'msg': u""}


def get_form_data():
    data = {}
    for key in SPECIAL_FIELD:
        data[key] = request.forms.get(key)

    if data['site_id'].isdigit():
        data['site_id'] = int(data['site_id'])
    return data


def j_get_speciallist():
    site_id = int(request.params.get('site_id'))
    response.content_type = "application/json"
    special = []
    cursor = sqlstore.get_cursor()
    cursor.execute('select id, url, site_id, url_regex from special where site_id=%s AND status=%s order by id;', (site_id, RECORD_STATUS.NORMAL))
    for row in cursor.fetchall():
        id, url, site_id, url_regex = row
        special.append({'_id': id, 'url': url, 'site_id': site_id, 'url_regex': url_regex})

    cursor.close()
    return json_dumps(special)


def j_get_special():
    _id = int(request.params.get('_id'))
    cursor = sqlstore.get_cursor()
    sql = 'select %s from special where id=%s AND status=%s' % (','.join(SPECIAL_FIELD), _id, RECORD_STATUS.NORMAL)
    cursor.execute(sql)
    data = cursor.fetchone()
    special = {}
    if data:
        for i, key in enumerate(SPECIAL_FIELD):
            special[key] = data[i]

    cursor.close()
    return {'status': True, 'data': special}


def update():
    data = get_form_data()
    status = validate_regex(data)
    if status:
        _id = int(request.forms.get('_id'))
        cursor = sqlstore.get_cursor()
        set_field = ["%s='%s'" % (key, MySQLdb.escape_string(data[key])) for key in SPECIAL_FIELD if key != 'site_id']
        sql = 'update special set %s where id=%s;' % (', '.join(set_field), _id)
        cursor.execute(sql)
        cursor.connection.commit()
        cursor.close()
    return {'status': status, 'msg': u""}


def j_delete():
    _id = int(request.params.get('_id'))
    cursor = sqlstore.get_cursor()
    cursor.execute('update special set status=%s where id=%s', (RECORD_STATUS.DELETED, _id))
    cursor.connection.commit()
    cursor.close()
    return {'status': True, 'msg': u""}
