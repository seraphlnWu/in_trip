#coding=utf-8
import os
import os.path
import zipfile
import datetime,time

from cStringIO import StringIO

from buzz.lib.store import mongo
from admin.model import get_inc_id
from admin.lib.topic import dump_topic
from buzz.store_data.QueueService import DownloadQ
from admin.config.consts import RECORD_STATUS,DOWNLOAD_STATUS,DUMP_FILE_PATH

def add_task(start,end,project_id,topic_id,dump_type):
    db = mongo.get_db()
    _id = get_inc_id(db.download_list)
    data = {}
    data['_id'] = _id
    data['start'] = start
    data['end'] = end
    data['project_id'] = project_id
    data['topic_id'] = topic_id
    data['type'] = dump_type
    data['create_time'] = datetime.datetime.now()
    data['complete'] = DOWNLOAD_STATUS.WAIT
    data['status'] = RECORD_STATUS.NORMAL
    db.download_task.insert(data,safe=True)
    DownloadQ.put(data)
    return {'status':True}

def execute_task():
    if DownloadQ.empty():
        return False
    dump_data = DownloadQ.get()
    db = mongo.get_db()
    db.download_task.update({'_id':dump_data['_id']},{'$set':{'complete':DOWNLOAD_STATUS.START}},safe=True)
    if dump_data['type'] == 'topic_dump':
        content,file_name = dump_topic_file(dump_data['start'],dump_data['end'],dump_data['topic_id'])
    else:
        content,file_name = dump_project_file(dump_data['start'],dump_data['end'],dump_data['project_id'])

    if not os.path.exists(DUMP_FILE_PATH):
        os.makedirs(DUMP_FILE_PATH)

    file_path = (DUMP_FILE_PATH+file_name).encode('utf-8')
    open(file_path,'wb').write(content)
    db.download_task.update({'_id':dump_data['_id']},{'$set':{'complete':DOWNLOAD_STATUS.COMPLETE,'filename':file_name}},safe=True)
    return True

def dump_topic_file(start,end,topic_id):
    db = mongo.get_db()
    topic = db.topic.find_one({'_id': topic_id,'status':RECORD_STATUS.NORMAL})
    project = db.project.find_one({'_id': topic['project_id']})
    key = '%s_%s' % (project['name'], topic['main_key'])
    tmp_file, size = dump_topic(start, end, key)
    file_obj = StringIO()
    zip_file = zipfile.ZipFile(file_obj, 'w', zipfile.ZIP_DEFLATED)
    zip_file.writestr(topic['main_key'] + '.csv', tmp_file.getvalue())
    zip_file.close()
    file_name = '%s-%s-%s.zip' % (topic['main_key'],start,end)
    content = file_obj.getvalue()
    return content,file_name

def dump_project_file(start,end,project_id):
    db = mongo.get_db()
    project = db.project.find_one({'_id':project_id,'status':RECORD_STATUS.NORMAL})
    topics = [db.topic.find_one({'_id':topic_id}) for topic_id in project['topic_ids']]
    file_obj = StringIO()
    zip_file = zipfile.ZipFile(file_obj, 'w', zipfile.ZIP_DEFLATED)
    for topic in topics:
        key = '%s_%s' % (project['name'], topic['main_key'])
        tmp_file, _ = dump_topic(start, end, key)
        arc_name = '%s-%s-%s/%s.csv' % (project['name'], start,end, topic['main_key'])
        zip_file.writestr(arc_name, tmp_file.getvalue())
    zip_file.close()
    file_name = "%s-%s-%s.zip" % (project['name'], start,end)

    content = file_obj.getvalue()
    return content,file_name

if __name__ == "__main__":
    while True:
        try:
            if not execute_task():
                time.sleep(10)
        except Exception,e:
            print (e)


