#coding=utf-8

import time
from datetime import datetime, timedelta
from bottle import request, response, static_file, redirect

from buzz.lib.mq import MQ
from buzz.lib.store import mongo
from buzz.lib.consts import DOWNLOAD_QUEUE

from admin.model import get_inc_id, Download, Auth
from admin.lib.utils import remove_empty, jsonify, render
from admin.config.consts import RECORD_STATUS, DOWNLOAD_STATUS, ROLE

DATE_TIME_FORMAT = '%Y-%m-%d'


@render('project/index.html')
def index(page):
    projects = []
    db = mongo.get_db()
    keyword = (request.params.get('keyword') or '').decode('utf-8')
    filters = {'status': RECORD_STATUS.NORMAL}
    s = request.environ.get('beaker.session')
    role = s.get('role', None)
    if role is not None and role != ROLE.ROOT:
        filters['user_id'] = s['user_id']

    if not keyword:
        page_count = 10
        for project in db.project.find(filters).sort('_id', -1).skip((page - 1) * page_count).limit(page_count):
            projects.append(project)
    else:
        filters['name'] = keyword
        project = db.project.find_one(filters)
        if project:
            projects.append(project)

    for project in projects:
        for i, time_stamp in enumerate(project['effective_time']):
            user = Auth.get(_id=project['user_id'])
            project['mail'] = user.mail if user is not None else None
            if isinstance(time_stamp, (int, float)):
                project['effective_time'][i] = time.strftime(DATE_TIME_FORMAT, time.localtime(int(time_stamp)))
    return {'projects': projects, 'keyword': keyword, 'page': page}


def add():
    data = get_form_data()
    db = mongo.get_db()
    mail = data.pop('mail')
    user = Auth.find_one(mail=mail)
    status = False
    msg = ''
    _id = -1

    if user is None:
        msg = u'关联用户不存在'
    else:
        _id = get_inc_id(db.project)
        data['_id'] = _id
        data['status'] = RECORD_STATUS.NORMAL
        data['created_on'] = datetime.now()
        data['user_id'] = user._id

        db.project.insert(data)
        topic_ids = data['topic_ids']
        for topic_id in topic_ids:
            db.topic.update({'_id': topic_id}, {'$set': {'project_id': _id, 'status': RECORD_STATUS.NORMAL}})
        status = True

    return {'status': status, '_id': _id, 'msg': msg}

@jsonify()
def get_project(_id):
    db = mongo.get_db()
    project = db.project.find_one({'_id': _id})
    project['mail'] = Auth.get(project['user_id']).mail
    topic_ids = project['topic_ids']
    topics = []
    #for topic_id in topic_ids:
    #    topic = db.topic.find_one({'_id': topic_id})
    #    topics.append(topic)

    return {'status': True, 'project': project, 'topics': topics}

def update(_id):
    data = get_form_data()
    data.pop('topic_ids')
    db = mongo.get_db()

    user = Auth.find_one(mail=data.pop('mail'))
    status = False
    msg = ''

    if user is None:
        msg = u'关联用户不存在'
    else:
        data['user_id'] = user._id
        db.project.update({'_id': _id}, {'$set': data})
        status = True

#    topic_ids = data['topic_ids']
#    for topic_id in topic_ids:
#        db.topic.update({'_id': topic_id}, {'$set': {'project_id': _id, 'status': RECORD_STATUS.NORMAL}})

    return {'status': status, 'msg': msg}

def delete(_id):
    db = mongo.get_db()
    project = db.project.find_and_modify({'_id': _id}, {'$set': {'status': RECORD_STATUS.DELETED}})
    topic_ids = project['topic_ids']

    for topic_id in topic_ids:
        db.topic.update({'_id': topic_id}, {'$set': {'status': RECORD_STATUS.DELETED}})

    return {'status': True, 'msg': u""}


def dump(_id):
    start = datetime.strptime(request.params.get('start'), "%Y-%m-%d")
    end = datetime.strptime(request.params.get('end'), "%Y-%m-%d") + timedelta(hours=24) - timedelta(milliseconds=1)
    need_comment = int(request.params.get('need_comment'))

    db = mongo.get_db()
    project = db.project.find_one({'_id': _id})
    _id = get_inc_id(db.download)
    data = {
        "_id": _id,
        "status": DOWNLOAD_STATUS.WAITING,
        "start_time": start,
        "end_time": end,
        "created_on": datetime.now(),
        "topic": project['topic_ids'],
        "project_id": [project['_id']],
        "filename": '%s-%s-%s-%s.zip' % (_id, project['name'].replace(' ', '_'), start.date(), end.date()),
        "need_comment": need_comment,
    }
    download = Download(**data)
    download.save(autoincrement_id=False)
    MQ.push(DOWNLOAD_QUEUE, _id)
    status = True

    return {'status': status}


def get_form_data():
    proj_name = request.params.get('name')
    mail = request.params.get('mail')
    industry_id = int(request.params.get('industry'))
    start = request.params.get('start')
    end = request.params.get('end')
    topic_ids = request.params.get('topic_ids') # separate by space
    white_list = request.params.get('white_list')
    black_list = request.params.get('black_list')
    regex = int(request.params.get('regex') or 0)
    return {'name': proj_name,
            'mail': mail,
            'industry_id': industry_id,
            'effective_time': [int(time.mktime(time.strptime(start, DATE_TIME_FORMAT))),
                int(time.mktime(time.strptime(end, DATE_TIME_FORMAT)))
                ],
            'white_list': white_list.split('\r\n') if white_list else [],
            'black_list': black_list.split('\r\n') if black_list else [],
            'regex': regex,
            'topic_ids': list(set([int(topic_id) for topic_id in remove_empty(topic_ids.split(' '))] if topic_ids else []))
            }


