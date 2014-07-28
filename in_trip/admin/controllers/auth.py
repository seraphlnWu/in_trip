# coding=utf-8
import os
import hashlib
import datetime
import pymongo

from bottle import request, redirect

from buzz.lib.store import mongo
from admin.model import Auth
from admin.lib.utils import render
from admin.config.consts import RECORD_STATUS, DUMP_FILE_PATH, ROLE


@render('auth/index.html')
def index(page):
    page_count = 15
    keyword = (request.params.get('keyword') or '').decode('utf-8')
    if not keyword:
        records = [row for row in Auth.find().sort('_id').skip((page - 1) * page_count).limit(page_count)]
    else:
        records = []
        user = Auth.find_one(mail=keyword, status=RECORD_STATUS.NORMAL)
        if user:
            records.append(user)

    return {'records': records, 'keyword': keyword, 'page': page}


def login():
    mail = request.forms.get('mail')
    password = request.forms.get('password')
    user = Auth.find_one(mail=mail)
    status = False
    msg = u'邮箱或密码错误'
    if user and hashlib.sha1(password + user.salt).hexdigest() == user.password:
        if user.role == ROLE.BLOCK:
            msg = u'账号已过期，请联系管理员修改'
        elif user.end_date < datetime.datetime.now():
            msg = u'账号已过期，请联系管理员修改'
            user.update(role=ROLE.BLOCK)
        else:
            s = request.environ.get('beaker.session')
            s['mail'] = mail
            s['role'] = user.role
            s['user_id'] = user._id
            s.save()
            status = True

    return {'status': status, 'msg': msg}


def logout():
    s = request.environ.get('beaker.session')
    s.delete()
    return


def add():
    data = get_form_data()
    if data['password']:
        if data['password'] != data['confirm']:
            return {'status': False, 'msg': u"两次输入的密码不一致"}
        else:
            data['salt'] = os.urandom(4).encode('hex')
            data['password'] = hashlib.sha1(data['password'] + data['salt']).hexdigest()
    else:
        data.pop('password')

    data.pop('confirm')
    data['created_on'] = datetime.datetime.now()
    data['status'] = RECORD_STATUS.NORMAL
    user = Auth(**data)
    user.save()
    return {'status': True, 'msg': u""}


def update():
    _id = int(request.forms.pop('_id'))
    data = get_form_data()
    if data['password']:
        if data['password'] != data['confirm']:
            return {'status': False, 'msg': u"两次输入的密码不一致"}
        else:
            data['salt'] = os.urandom(4).encode('hex')
            data['password'] = hashlib.sha1(data['password'] + data['salt']).hexdigest()
    else:
        data.pop('password')

    data.pop('confirm')
    user = Auth(_id=_id)
    user.update(**data)
    return {'status': True, 'msg': u""}


def j_delete():
    _id = int(request.params.get('_id'))
    user = Auth(_id=_id)
    user.update(status=RECORD_STATUS.DELETED)
    return {'status': True, 'msg': u""}


def j_get_user(_id):
    user = Auth.find_one(_id=_id)
    user = user.to_mongo()
    user.pop('created_on')
    user['end_date'] = user['end_date'].strftime('%Y-%m-%d')
    return {'status': True, 'user': user}


def get_form_data():
    data = {}
    data['mail'] = request.forms.get('mail')
    data['password'] = request.forms.get('password')
    data['confirm'] = request.forms.get('confirm')
    data['role'] = int(request.forms.get('role'))
    data['company'] = request.forms.get('company')
    data['end_date'] = datetime.datetime.strptime(request.forms.get('end_date'), '%Y-%m-%d')
    return data

if __name__ == '__main__':
    data = {}
    # data['mail'] = 'yangchao.cs@gmail.com'
    # data['salt'] = os.urandom(4).encode('hex')
    # data['password'] = hashlib.sha1('19870810' + data['salt']).hexdigest()
    # data['created_on'] = datetime.datetime.now()
    # data['role'] = 0
    # data['company'] = 'AdMaster'
    # data['end_date'] = datetime.datetime(2015, 1, 1)
    # data['status'] = 0
    user = Auth.find_one(mail='yangchao.cs@gmail.com')
    print hashlib.sha1('19870810' + user.salt).hexdigest() == user.password
