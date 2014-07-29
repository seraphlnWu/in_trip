#! /usr/bin/env python
# coding: utf-8

import zipfile
import datetime

from in_trip.lib.mq import MQ
from in_trip.lib.store import mongo
from admin.model import Download
from admin.config.config import ROOT
from admin.lib.topic import dump_topic
from in_trip.lib.consts import DOWNLOAD_QUEUE
from admin.config.consts import DOWNLOAD_STATUS


def download_task():
    while True:
        task_id = MQ.pop(DOWNLOAD_QUEUE)
        if task_id:
            now = datetime.datetime.now
            download = Download.find_one(_id=task_id)
            db = mongo.get_db()
            filename = ROOT + '/static/download/' + download.filename.encode('utf-8', 'ignore')
            with open(filename, 'w') as f:
                download.update(status=DOWNLOAD_STATUS.PROCESSING)
                print '%s Download task %s start...' % (now(), task_id)
                zip_file = zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED)
                for index, topic_id in enumerate(download.topic):
                    topic_dict = db.topic.find_one({'_id': topic_id})
                    tmp_file = dump_topic(download.start_time.strftime("%Y-%m-%d"), download.end_time.strftime("%Y-%m-%d"), topic_dict, download.need_comment)
                    arc_name = ['%s/%s-%s' % (download.filename[:-4], index + 1, topic_dict['main_key'])]
                    if topic_dict['and_keys']:
                        arc_name.append('and')
                        arc_name.extend(topic_dict['and_keys'][:5])
                    if topic_dict['or_keys']:
                        arc_name.append('or')
                        arc_name.extend(topic_dict['or_keys'][:5])
                    if topic_dict['not_keys']:
                        arc_name.append('not')
                        arc_name.extend(sum(topic_dict['not_keys'][:5], []))

                    arc_name = '-'.join(arc_name) + '.csv'
                    zip_file.writestr(arc_name, tmp_file)

                zip_file.close()

            download.update(status=DOWNLOAD_STATUS.COMPLETED)
            print '%s Download task %s finish...' % (now(), task_id)

        else:
            print '%s Nothing to download' % now()
            break

if __name__ == '__main__':
    download_task()
