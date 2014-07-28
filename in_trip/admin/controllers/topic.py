#coding=utf-8

import re
import csv
import zipfile
import time
from datetime import datetime, timedelta
from cStringIO import StringIO

from bottle import request, response, static_file, redirect

from in_trip.lib.mq import MQ
from in_trip.lib.store import mongo
from in_trip.lib.consts import DOWNLOAD_QUEUE

from admin.model import get_inc_id, Download
from admin.lib.utils import remove_empty, jsonify, render
from admin.config.consts import RECORD_STATUS, DOWNLOAD_STATUS, ROLE

@render('topic/index.html')
def index(page):
    page_count = 10
    keyword = (request.params.get('keyword') or '').decode('utf-8')
    project_id = int(request.params.get('project_id') or 0)
    topics = []
    db = mongo.get_db()
    filters = {'status': RECORD_STATUS.NORMAL}
    s = request.environ.get('beaker.session')
    role = s.get('role', None)
    project_ids = []
    if role is not None and role != ROLE.ROOT:
        user_id = s.get('user_id')
        project_li = db.project.find({'user_id': int(user_id), 'status': RECORD_STATUS.NORMAL})
        project_ids = [project['_id'] for project in project_li] if project_li else []
        filters['project_id'] = {'$in': project_ids}

    if project_id:
        if project_ids and project_id not in project_ids:
            # display nothing when a normal user searching a project without connection to him
            project_id = None

        project = db.project.find_one({'_id': project_id, 'status': RECORD_STATUS.NORMAL})
        if project:
            topic_ids = project['topic_ids']
            topic_ids.sort(reverse=True)
            for topic_id in topic_ids:
                topic = db.topic.find_one({'_id': topic_id})
                topic['project_name'] = project['name']
                topics.append(topic)

    elif keyword:
        filters['main_key'] = keyword
        projects = {} # for cache
        for topic in db.topic.find(filters).sort('_id'):
            _project_id = topic['project_id']
            if _project_id in projects:
                project = projects[_project_id]
            else:
                project = db.project.find_one({'_id': _project_id})
                projects[_project_id] = project

            topic['project_name'] = project['name']
            topics.append(topic)

    else:

        projects = {} # for cache
        for topic in db.topic.find(filters).sort('_id', -1).skip((page - 1) * page_count).limit(page_count):
            _project_id = topic['project_id']
            if _project_id in projects:
                project = projects[_project_id]
            else:
                project = db.project.find_one({'_id': _project_id})
                projects[_project_id] = project

            topic['project_name'] = project['name']
            topics.append(topic)

    return {'topics': topics, 'page': page, 'project_id': project_id, 'keyword': keyword}

@jsonify()
def get_topic(_id):
    db = mongo.get_db()
    topic = db.topic.find_one({'_id': _id})
    return {'status': True, 'topic': topic}

def dump(_id):
    start = datetime.strptime(request.params.get('start'), "%Y-%m-%d")
    end = datetime.strptime(request.params.get('end'), "%Y-%m-%d") + timedelta(hours=24) - timedelta(milliseconds=1)
    need_comment = int(request.params.get('need_comment'))

    db = mongo.get_db()
    topic = db.topic.find_one({'_id': _id})

    _id = get_inc_id(db.download)
    data = {
        "_id": _id,
        "status": DOWNLOAD_STATUS.WAITING,
        "start_time": start,
        "end_time": end,
        "created_on": datetime.now(),
        "topic": [topic['_id']],
        "project_id": [topic['project_id']],
        "filename": '%s-%s-%s-%s.zip' % (_id, topic['main_key'].replace(' ', '_'), start.date(), end.date()),
        "need_comment": need_comment,
    }
    download = Download(**data)
    download.save(autoincrement_id=False)
    MQ.push(DOWNLOAD_QUEUE, _id)
    return {'status': True}


def add():
    form_data = get_form_data()
    db = mongo.get_db()
    _id = get_inc_id(db.topic)
    form_data['_id'] = _id
    project_id = request.params.get('project_id')
    form_data['status'] = RECORD_STATUS.DELETED
    if project_id is not None:
        form_data['project_id'] = int(project_id)
        db.project.update({'_id': int(project_id)}, {'$addToSet': {'topic_ids': _id}})
        form_data['status'] = RECORD_STATUS.NORMAL

    form_data['created_on'] = datetime.now()
    db.topic.insert(form_data, w=1)
    return {'status': True, '_id': _id}

def update(_id):
    form_data = get_form_data()
    db = mongo.get_db()
    db.topic.update({'_id': _id}, {'$set': form_data})
    return {'status': True, '_id': _id}

def delete(_id):
    db = mongo.get_db()
    topic = db.topic.find_and_modify({'_id': _id}, {'$set': {'status': RECORD_STATUS.DELETED}})
    project_id = topic.get('project_id')
    if project_id is not None:
        project = db.project.find_one({'_id': project_id})
        topic_ids  = project.get('topic_ids') if project else []
        if topic_ids and _id in topic_ids:
            topic_ids.remove(_id)
            db.project.update({'_id': project_id}, {'$set': {'topic_ids': topic_ids}})

    return {'status': True, 'msg': u""}

def get_form_data():
    main_key = request.params.get('main_key')
    synonyms = request.params.getall('synonyms[]') or []
    and_keys = request.params.getall('and_keys[]') or []
    or_keys = request.params.getall('or_keys[]') or []
    not_keys = request.params.getall('not_keys[]') or []

    return {
            'main_key': main_key,
            'synonyms': remove_empty(synonyms),
            'and_keys': remove_empty(and_keys),
            'or_keys': remove_empty(or_keys),
            'not_keys': [not_key.split(';') for not_key in remove_empty(not_keys)],
    }


