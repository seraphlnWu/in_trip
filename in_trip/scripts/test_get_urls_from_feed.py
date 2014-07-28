#coding=utf-8
import urllib
from pymongo import Connection
from buzz.configurations import FEEDS_DB_HOST
from admin.model import get_feed_urls

conn = Connection(FEEDS_DB_HOST)
db = conn.buzz_master

def get_urls(_id):
    urls = set()
    #project_id = db.topic.find_one({'_id':_id}).get('project_id')
    #project = db.project.find_one({'_id':project_id})
    feed = db.feed.find_one({'_id':_id})
    #if project.get('industry') in feed.get('industry',[]):
        #if feed.get('feed_urls',{}).get('field',{}).get('topic',None):
        #main_key = urllib.quote(db.topic.find_one({'_id':_id}).get('main_key').encode(feed['charset']))
    tmp_urls = get_feed_urls(feed)
    for url in tmp_urls:
        #if main_key in url:
        urls.add(url)

    return urls

if __name__ == "__main__":
    # 1~205
    print get_urls(18)
