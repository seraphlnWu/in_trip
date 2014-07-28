# coding=utf-8

from collections import OrderedDict

from in_trip.lib.enum import Enum

from admin.config.config import ROOT

# record status
RECORD_STATUS = Enum(NORMAL=0, DELETED=1, PAUSE=2)

# download status
DOWNLOAD_STATUS = Enum(WAITING=0, PROCESSING=1, COMPLETED=2)

# user role
ROLE = Enum(ROOT=0, NORMAL=1, BLOCK=2)

# xapth多一个审核过程
XPATH_STATUS = Enum(AUDITED=0, PENDING=1, DELETE=2)

DUMP_FILE_PATH = ROOT + '/static/download/'
COLUMN_MAP = OrderedDict()
COLUMN_MAP['title'] = u"标题"
COLUMN_MAP['at'] = u"时间"
COLUMN_MAP['src'] = u"正文"
COLUMN_MAP['authr'] = u"作者"
COLUMN_MAP['views'] = u"浏览数"
COLUMN_MAP['ccnt'] = u"回复数"

SPECIAL_FIELD = [
    "url",
    "site_id",
    "url_regex",
    "main_block",
    "bbs_blocks",
    "title",
    "content",
    "pub_date",
    "pub_date_regex",
    "author",
    "author_regex",
    "view_count",
    "view_count_regex",
    "comment_count",
    "comment_count_regex",
    "page_type",
]
