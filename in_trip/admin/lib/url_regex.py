#coding=utf-8
import re
from binascii import b2a_base64, a2b_base64

from in_trip.lib.store import mongo
from in_trip.lib.http import remove_schema

from admin.config.consts import XPATH_STATUS, RECORD_STATUS

def check_url_regex(site_id, url_regex, status=True, result=None):
    try:
        if url_regex:
            regex = re.compile(url_regex)
            db = mongo.get_db()
            for row in db.xpath.find({'site_id': site_id, 'status': {'$ne': XPATH_STATUS.DELETE}}):
                for url_eg in row['eg']:
                    url_eg = remove_schema(url_eg)
                    if regex.match(url_eg):
                        status = False
                        result = {u'url正则匹配': url_eg}
    except:
        status = False
        result[u'url正则匹配'] = u'正则表达式错误'

    return status, result

def _regex_coder(url_regexs, method):
    if isinstance(url_regexs, (str, unicode)):
        return method(url_regexs)
    else:
        return [method(url_regex) for url_regex in url_regexs]

def regex_encoder(url_regexs):
    return _regex_coder(url_regexs, b2a_base64)

def regex_decoder(url_regexs):
    return _regex_coder(url_regexs, a2b_base64)

def regex_match(eg, url_reg, white_reg_list, black_reg_list):
    if eg.startswith('http'):
        eg = remove_schema(eg)
    regex = re.compile(url_reg)
    white_reg_list = [re.compile(white_reg) for white_reg in white_reg_list if white_reg]
    black_reg_list = [re.compile(black_reg) for black_reg in black_reg_list if black_reg]
    if regex.match(eg):
        for white_reg in white_reg_list:
            if white_reg.match(eg):
                return True

        for black_reg in black_reg_list:
            if black_reg.match(eg):
                return False

        return True
    else:
        return False
