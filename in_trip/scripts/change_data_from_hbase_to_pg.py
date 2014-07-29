#coding=utf-8
import time
import cPickle

from in_trip.store_data.views import pg_db,conn

import logging
logger = logging.getLogger('parser')

def creat_table():
    sql_str = '''
            create table "tmp_hbase_to_pg"( 
                data text,
                timestamp float(24)
            )
    '''
    pg_db.execute(sql_str)
    conn.commit()

def insert_data(o_dict, default_value):
    data =cPickle.dumps({
        'o_dict' : o_dict,
        'default_value' : default_value
        })
    sql_str = '''
        insert into tmp_hbase_to_pg
        (data,timestamp) 
        values
        (%s,%s);
    '''
    try:
        pg_db.execute(sql_str,(data,time.time()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error('insert to pg error: %s', e)


def get_data_all():
    sql_str = '''
    select * from tmp_hbase_to_pg;
    '''
    pg_db.execute(sql_str)
    print pg_db.fetchall()

def get_data(offset,limit=1000):
    sql_str = '''
    select * from tmp_hbase_to_pg limit(%s) offset(%s);
    '''
    pg_db.execute(sql_str,(limit,offset))
    return pg_db.fetchall()

def insert_into_hbase():
    from in_trip.store_data.hbase.run import insert_data as hbase_insert
    offset = 0
    limit = 1000
    while True:
        res_list = get_data(offset,limit)
        if not res_list:
            break
        offset = offset + limit
        for item in res_list:
            tmp_data = cPickle.loads(item[0])
            hbase_insert(tmp_data['o_dict'],tmp_data['default_value'])
    return True

if __name__ == "__main__":
    creat_table()
    print "success!"
