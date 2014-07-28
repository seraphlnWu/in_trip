#coding=utf-8

import time

import pymongo
from cPickle import dumps as pickle_dumps

from buzz.lib.store import rd, pg, mongo
from buzz.lib.http import get_domain

MONGODB_DB_NAME = 'sandbox_mongo_buzz'

def main1():
    conn = pymongo.Connection('192.168.1.117')
    db = conn[MONGODB_DB_NAME]

    con = rd.get_connection()
    for row in db.tmp_content.find().sort('_id').limit(100):
        #print row['_id']
        print row['url']
    """
        item = {
            "url"    : row['url'],
            "isseed" : False,
            "isindex": False,
            "timestamp": time.time()}
        domain = get_domain(row['url'])
        con.lpush(domain, pickle_dumps(item))
    """

def main():
    con = rd.get_connection()
    db = mongo.get_db()
    keywords = []
    for topic in db.topic.find({'status': RECORD_STATUS.NORMAL}):
        keywords.append(topic['main_key'])
        keywords.extend(topic['synonyms'])
    #self.keywords = [keyword.encode('utf-8') for keyword in keywords]
    conn = psycopg2.connect(user="postgres", database="sandbox_pg16_buzz", host="116.213.213.117", password="postgres")
    cursor = conn.get_cursor()
    for keyword in keywords:
        try:
            table_name = u"%s_20130601"
            sql = "select url from %s " % table_name + " order by article_id;"
            cursor.execute(sql)
            for row in cursor.fetchall():
                url, = row
                print url
                item = {
                    "url"    : url,
                    "isseed" : False,
                    "isindex": False,
                    "timestamp": time.time()}
                domain = get_domain(row['url'])
                con.lpush(domain, pickle_dumps(item))
        except e:
            print e
        
if __name__ == '__main__':
    main()
