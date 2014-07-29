# coding=utf-8
import urllib
import json
import re
import base64
from in_trip.lib.store import mongo
import copy
import pyquery
import datetime
from writer import XlsWriter
from os import system

YOUKU_URL = re.compile('^http://.*?\.youku\.com/.*?/id_(.*?)\.html')
url_video_comment_another_way = "http://comments.youku.com/comments/~ajax/vpcommentContent.html"
EverPage_another_way = '30'
db = mongo.get_db()


def how_many_pages(total, count):
    if total < 0:
        return 0
    if total % count != 0:
        return (total / count) + 1
    else:
        return total / count


def get_by_another_way(video_id, page):
    comment = {}
    print page
    url_request = url_video_comment_another_way + \
        "?__ap={%22videoid%22:%22" + video_id + \
        "%22,%22sid%22:593271619,%22page%22:" + str(page) + "}"
    print url_request
    res = json.loads(urllib.urlopen(url_request).read())
    comment['total'] = res['totalSize'].replace(',', '')
    comment['page'] = page
    comment['count'] = EverPage_another_way
    comment['video_id'] = video_id
    title = re.search('title=(.*?)\&', res['con']).group(1)
    tmp = []
    b = pyquery.PyQuery(res['con'])
    length = len(b('.text'))
    for i in range(length):
        tmp_comment = {}
        try:
            tmp_comment['content'] = b('.text')[i].text_content()
        except Exception, e:
            print 'content missing'
            tmp_comment['content'] = ''

        try:
            tmp_comment['id'] = b('.text')[i].getchildren()[0].attrib['id'].split('_')[1]
        except Exception, e:
            print 'id missing'
            tmp_comment['id'] = ''

        try:
            tmp_comment['user'] = {
                'id': b('.text')[i].attrib['name'].split('_')[1],
                'name': b('.bar')[i].getchildren()[0].text,
                'link': b('.bar')[i].getchildren()[0].attrib['href']
            }
        except Exception, e:
            print 'user missing'
            tmp_comment['user'] = {
                'id': '',
                'name': '',
                'link': ''
            }

        try:
            tmp_comment['published'] = str(
                datetime.datetime.fromtimestamp(int(tmp_comment['id'][0:8], 16))).split('.')[0]
        except Exception, e:
            print 'published missing'
            print i
            print str(e)
            tmp_comment['published'] = ''

        try:
            tmp_comment['source'] = {
                'link': b('.via')[i].getchildren()[0].getchildren()[0].attrib['href'],
                'name': b('.via')[i].getchildren()[0].getchildren()[0].text
            }
        except Exception, e:
            print 'source missing'
            print i
            print str(e)
            tmp_comment['source'] = {'link': '', 'name': ''}

        tmp.append(tmp_comment)

    comment['comments'] = tmp
    return comment, title


def get_comment_by_another_way(video_id, url):
    total = 0
    comment = {}
    response, title = get_by_another_way(video_id, 2)
    if response:
        total = response.get('total')
        print 'total', total
        comment = response
        del comment['page']
        del comment['count']
        comment['comments'] = []
        for index in range(1, how_many_pages(int(total), int(EverPage_another_way)) + 1):
            reponse, title = get_by_another_way(video_id, index)
            comment['comments'].extend(reponse['comments'])

        for each_comment in comment['comments']:
            data = copy.deepcopy(each_comment)
            data['video_id'] = video_id
            db.youku_comment.update(
                {'id': data['id']}, {'$set': data}, upsert=True)
    comment_data = copy.deepcopy(comment)
    comment_ids = [item['id'] for item in comment_data['comments']]
    comment_data['comments'] = list(set(comment_ids))
    comment_data['url'] = base64.encodestring(url)
    comment_data['real_total'] = db.youku_comment.find(
        {'video_id': video_id}).count()
    comment_data['title'] = title
    db.youku_video.update(
        {'video_id': comment_data['video_id']}, {'$set': comment_data}, upsert=True)
    return comment


def update_comment_by_another_way(video_id):
    comment = db.youku_video.find_one({'video_id': video_id})
    response = get_by_another_way(video_id, 1)
    count = int(response.get('total')) - int(comment.get('total')) + 200
    comment['total'] = response.get('total')
    if count <= 0:
        return False
    else:
        for index in range(1, how_many_pages(count, int(EverPage_another_way)) + 1):
            reponse = get_by_another_way(video_id, index)
            for each_comment in reponse['comments']:
                data = copy.deepcopy(each_comment)
                data['video_id'] = video_id
                if db.youku_comment.find_one({'id': data['id']}) == None:
                    db.youku_comment.insert(data, safe=True)
                    comment['comments'].append(data['id'])
        db.youku_video.update({'video_id': video_id}, {
                              '$set': {'total': comment['total'], 'real_total': db.youku_comment.find({'video_id': video_id}).count(), 'comments': comment['comments']}}, safe=True)
        return True


def get_video_ids(urls):
    video_ids = {}
    for url in urls:
        res = YOUKU_URL.match(url)
        if res:
            video_ids[res.groups()[0]] = url
    return video_ids


def get_comments_by_another_way(urls):
    print "call me .........."
    video_ids = get_video_ids(urls)
    print video_ids, len(video_ids)
    for video_id in video_ids:
        get_comment_by_another_way(video_id, video_ids[video_id])


def dump_report(video_id, FILE_ENCOIDNG='gbk'):
    titles = [
        u"user",
        u"published",
        u"content",
        u"source"
    ]
    data = db.youku_comment.find({'video_id': video_id})
    video = db.youku_video.find_one({'video_id': video_id})
    xlsfile = XlsWriter(path='.', filename=video['title'])
    xlsfile.append(titles)
    for d in data:
        try:
            xlsfile.append([
                d['user']['name'],
                d['published'],
                d['content'].lstrip(),
                d['source']['name']
            ])
        except Exception, e:
            print str(e)
            print d['id']
    xlsfile.close()


def dump_reports(video_ids):
    for id in video_ids:
        print id
        dump_report(id)
    system('tar cvf report.tar --remove-files *.xls')
    return True


def run():
    urls = ['http://v.youku.com/v_show/id_XNjIxMjgwNzE2.html']
    get_comments_by_another_way(urls)
    video_ids = get_video_ids(urls)
    dump_reports(video_ids)

if __name__ == '__main__':
    run()
