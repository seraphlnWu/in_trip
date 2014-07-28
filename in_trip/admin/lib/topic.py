# coding=utf-8
import re
import csv
import zipfile

from datetime import datetime
from cStringIO import StringIO

from buzz.lib.utils import parse_db_str
from buzz.lib.compress import decompress
from buzz.lib.store import SQLStore, mongo
from buzz.lib.consts import CATEGORY, PAGE_TYPE

sqlstore = SQLStore(**parse_db_str("mysql://buzz:f0b5e7@192.168.1.194/buzz_master"))


def dump_topic(start, end, topic, need_comment=0, FILE_ENCOIDNG='gbk'):
    from buzz.lib.search import MultiPatternSearch
    and_keys = [and_key.lower() for and_key in topic['and_keys']]
    or_keys = [or_key.lower() for or_key in topic['or_keys']]
    not_keys = [not_key.lower() for not_key in sum(topic['not_keys'], [])]

    if and_keys or or_keys or not_keys:
        multi_search = MultiPatternSearch(and_keys + or_keys + not_keys)
    else:
        multi_search = None

    titles = [
        u"关键词",
        u"分类",
        u"域",
        u"链接地址",
        u"主题",
        u"发表时间",
        #u"作者昵称",
        u"评论数",
        u"浏览量",
        #u"行业",
        u"性别",
        u"地域",
        u"摘要",
        u"情感分析",
    ]

    emotion_dict = {
        None: u"无",
        1: u"正面",
        0: u"中性",
        -1: u"负面"
    }

    tmp_file = StringIO()
    writer = csv.writer(tmp_file)
    writer.writerow(map(lambda x: x.encode(FILE_ENCOIDNG, 'ignore'), titles))

    key_li = [topic['main_key']] + topic['synonyms']
    processed_url_md5 = set()
    for i, key in enumerate(key_li):
        key = key.lower()
        table_name = "article_matched_keywords"
        sql = "select article_id, pub_date, emotion, brief from %s " % table_name + """ force index(pub_date_keyword) where keyword = %s and pub_date >= %s and pub_date <= %s and status=0 order by pub_date;"""
        cursor = sqlstore.get_cursor()
        cursor.execute(sql, (key, start, end))

        table_name = "article"
        for id, pub_date, emotion, brief in cursor.fetchall():
            sql = "select category_id,channel_name,url,title,\
                        comment_count,view_count,url_md5,page_type from %s " % table_name + """ where id = %s;"""

            cursor.execute(sql, (id, ))
            article = cursor.fetchone()
            if article:
                article = list(article)
                title = article[3]
                url_md5 = article.pop(-2)
                if url_md5 in processed_url_md5:
                    continue
                else:
                    processed_url_md5.add(url_md5)

                if multi_search is not None:
                    sql = "select content from article_content where article_id = %s;"
                    cursor.execute(sql, (id, ))
                    article_content = cursor.fetchone()
                    if article_content is None:
                        continue

                    content, = article_content
                    content = title + unicode(decompress(content), 'utf-8')
                    result = set(multi_search.match(content))

                    if not_keys:
                        skip = False
                        for sublist in topic['not_keys']:
                            if not (set([sub_key.lower() for sub_key in sublist]) - result):
                                skip = True
                                break

                        if skip:
                            continue

                    if and_keys and (set(and_keys) - result):
                        continue

                    if or_keys and not (set(or_keys) & result):
                        continue

                page_type = article.pop(-1)
                article[0] = CATEGORY[article[0]]
                article.insert(0, key_li[i])
                article.insert(5, pub_date)
                article.extend([
                    None,  # sex
                    None,  # zone
                    brief,
                    emotion_dict[emotion] if emotion in emotion_dict else emotion
                ])
                writer.writerow(map(lambda x: re.sub(u'\s+|\xa0', ' ', x).encode(FILE_ENCOIDNG, 'ignore') if isinstance(x, basestring) else x, article))
                if need_comment and page_type & PAGE_TYPE.BBS_LIKE_PAGE:
                    sql = "select url,pub_date,content from comment where article_id = %s;"
                    cursor.execute(sql, (id, ))
                    comment_li = cursor.fetchall()
                    if comment_li:
                        comment_li = sorted(comment_li, key=lambda x: x[1])
                        for url, pub_date, content in comment_li:
                            row = (key_li[i], u"回复", article[2], url, article[4], pub_date) + (None, ) * 4 + (content, )
                            writer.writerow(map(lambda x: re.sub(u'\s+|\xa0', ' ', x).encode(FILE_ENCOIDNG, 'ignore') if isinstance(x, basestring) else x, row))

    cursor.connection.commit()
    result = tmp_file.getvalue()
    tmp_file.close()
    return result

if __name__ == '__main__':
    key = u'奔驰'
    start = datetime(2013, 3, 1)
    end = datetime(2013, 9, 30)

    db = mongo.get_db()
    topic = db.topic.find_one({'_id': 26})
    synonyms = topic['synonyms']
    project = db.project.find_one({'_id': topic['project_id']})

    zip_file = zipfile.ZipFile(u'奥迪-2013-03-01-2013-09-30.zip', 'w')
    tmp_file, _ = dump_topic(start, end, topic['main_key'])
    arc_name = '%s-%s-%s/%s.csv' % (topic['main_key'], start.date(), end.date(), topic['main_key'])
    zip_file.writestr(arc_name, tmp_file.getvalue())

    for synonym in synonyms:
        tmp_file, _ = dump_topic(start, end, synonym)
        arc_name = '%s-%s-%s/%s.csv' % (topic['main_key'], start.date(), end.date(), synonym)
        zip_file.writestr(arc_name, tmp_file.getvalue())

    zip_file.close()
