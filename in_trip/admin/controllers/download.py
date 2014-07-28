#coding=utf-8
import os
import pymongo

from bottle import request, response, static_file, redirect

from in_trip.lib.store import mongo
from admin.config.consts import RECORD_STATUS, DUMP_FILE_PATH, ROLE
from admin.lib.utils import render
# from admin.lib.download_task import execute_task

@render('download/index.html')
def index(page):
    page_count = 15
    db = mongo.get_db()
    filters = {}
    s = request.environ.get('beaker.session')
    role = s.get('role', None)
    if role is not None and role != ROLE.ROOT:
        user_id = s.get('user_id')
        project_li = db.project.find({'user_id': int(user_id)})
        project_id = [[project['_id']] for project in project_li] if project_li else [[]]
        filters['project_id'] = {'$in': project_id}

    records = [row for row in db.download.find(filters).sort('_id', pymongo.DESCENDING).skip((page - 1) * page_count).limit(page_count)]
    return {'tasks': records, 'page': page}

def file(filename):
    return static_file(filename, root=DUMP_FILE_PATH)

# def is_topic_exsit():
#     topic = request.params.get('topic')
#     project = request.params.get('project')
#     db = mongo.get_db()
#     topic_id = db.topic.find_one({'main_key':topic})
#     if not topic_id:
#         return {'status':False}
#     topic_id = topic_id.get('_id')
#
#     project = db.project.find_one({'name':project})
#     if not project:
#         return {'status':False}
#     if topic_id in project.get('topic_ids'):
#         return {'status':True}
#     return {'status':False}
#
# def download(_id):
#     db = mongo.get_db()
#     download_task =  db.download_task.find_one({'_id':_id})
#     download_filename = download_task.get('filename',"").encode('utf-8')
#     return static_file(download_filename,DUMP_FILE_PATH,download=download_filename)
#
# def check_complete(_id):
#     db = mongo.get_db()
#     download_task = db.download_list.find_one({'_id':_id})
#     if download_task.get('complete',False):
#         return {'status':True}
#     else:
#         return {'status':False}
#
# def execute():
#     execute_task()
