#coding=utf-8
import re
import csv
import time
import datetime

import pymongo
import psycopg2

MONGODB_DB_NAME = 'sandbox_mongo_buzz'

def main():
    keywords = [u'中国最强音', ]
    start = datetime.datetime(2013, 5, 1)
    end = datetime.datetime(2013, 6, 1)
    conn = pymongo.Connection('192.168.1.117')
    db = conn[MONGODB_DB_NAME]

    conn = psycopg2.connect(user="postgres", database="sandbox_pg16_buzz", host="116.213.213.117", password="postgres")
    with open('%s.csv' % keywords[0], 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(map(lambda x:x.encode('gbk'), [u"url", u"时间", u"摘要", u"情感分析"]))
        for keyword in keywords:
            cursor = conn.cursor()
      	    table_name = u"%s_20130501" % keyword
            sql = "select * from %s " % table_name + """ where create_at >= %s and create_at < %s order by create_at;"""
            cursor.execute(sql, (start, end))
            for row in cursor.fetchall():
                print row[0]
                line = map(lambda x: re.sub(u'\s+|\xa0', ' ', x.decode('utf-8')).encode('gbk', 'ignore') if isinstance(x, basestring) else x, row[1:])
                writer.writerow(line)
            cursor.close()
            time.sleep(5)
            for row in db.tmp_content.find({'vklst': [keyword, ], 'cat': {'$gte': start, '$lt': end}}):
            	print row['_id']
                for key, value in row.iteritems():
                    if isinstance(value, unicode): 
                        row[key] = re.sub(u'\s+|\xa0', ' ', value).encode('gbk', 'ignore')
                writer.writerow([row['url'], row['cat'], row['brief'], row['pan']])

if __name__ == '__main__':
    main()
