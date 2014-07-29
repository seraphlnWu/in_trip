from rq import Queue,Worker,get_failed_queue
from redis import Redis
from in_trip.store_data.utils import REDIS_HOST
from admin.lib.store import db
#from pymongo import Connection
import youku
import time

#db = Connection('127.0.0.1')['buzz_master']
res = Redis(REDIS_HOST)

q_get = Queue('get',connection=res,default_timeout=-1)
q_update = Queue('update',connection=res,default_timeout=-1)
q_new = Queue('new',connection=res,default_timeout=-1)
q_retry = Queue('retry',connection=res,default_timeout=-1)

#update_worker = Worker(q_update,connection=res)
#new_worker = Worker(q_new,connection=res)

def update_all(timeout):
    for item in db.youku_video.find():
        #print "waiting....."
        if item.get('video_id') in [job.args[0] for job in q_update.jobs]: continue
        q_update.enqueue(youku.update_comment,item.get('video_id'))
    time.sleep(timeout*60)
    q_update.enqueue(update_all,timeout)

def get_new_url():
    url = res.blpop('new_url')
    #print url
    q_get.enqueue(youku.get_comments,[url[1],])
    q_new.enqueue(get_new_url)

def retry():
    while True:
        failed_queue = get_failed_queue(res)
        #print failed_queue
        for job in failed_queue.jobs:
            #print job.func_name
            if job.func_name == "youku.get_comments":
                #print "retry once......"
                func_arg = job.args[0]                
                q_get.enqueue(youku.get_comments_by_another_way,func_arg)
                failed_queue.remove(job)
            elif job.func_name == "youku.update_comment":
                func_arg = job.args[0]
                q_update.enqueue(youku.update_comment_by_another_way,func_arg)
                failed_queue.remove(job)
            else:      
                failed_queue.requeue(job.get_id())
        time.sleep(10)

if __name__ == '__main__':
    #time_plan(1)
    #update_all()
    pass
