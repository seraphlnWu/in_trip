#coding=utf-8

from admin.lib.url_regex import check_url_regex

from buzz.lib.http import curl
from buzz.lib.consts import HttpCode
from readability.readability import Document

def _validate(data, status=True, result=None):
    url = data['eg'][0]
    if not result:
        result = {'msg': u""}
    if len(data['xpath']) > 1:
        resp = curl(url)
        if not resp or resp.http_code != HttpCode.OK:
            status = False
            result['msg'] = u"页面抓取错误"
        else:
            data['_id'] = None
            doc = Document(resp, data['xpath'])

            check_list = {'title': 'short_title', 'src': 'text_content', 'authr': 'get_author', 'at': 'get_publish_date'}
            for key, method in check_list.items():
                if key in data['xpath']:
                    r = getattr(doc, method)()
                    if not r:
                        status = False
                        result[key] = u"no match"
                    else:
                        result[key] = r

            comment_count, view_count = doc.get_misc_count()
            if 'ccnt' in data['xpath']:
                result['ccnt'] = u'no match' if not comment_count else view_count
                if not comment_count:
                    status = False

            if 'views' in data['xpath']:
                result['veiws'] = u'no match' if not view_count else view_count
                if not view_count:
                    status = False

    return status, result
