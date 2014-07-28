#coding=utf-8

import re

from collections import OrderedDict

from buzz.lib.enum import Enum

HttpCode = Enum(OK=200,
                MOVED_PERMANENTLY=301,
                FOUND=302,
                SEE_OTHER=303,
                NOT_MODIFIED=304,
                TEMPORARY_REDIRECT=307,
                BAD_REQUEST=400,
                NOT_FOUND=404,
                ERROR=600) # crawl error

PAGE_TYPE = Enum(NORMAL_DETAIL_PAGE=1,
                 BBS_DETAIL_PAGE=1<<1,
                 ASK_DETAIL_PAGE=1<<2,
                 NORMAL_INDEX_PAGE=1<<8,
                 BBS_INDEX_PAGE=1<<9,
                 NORMAL_FEED_PAGE=1<<10,
                 SEATCH_FEED_PAGE=1<<11,
                 INDEX_PAGE=0xff00,
                 DETAIL_PAGE=0xff,
                 BBS_LIKE_PAGE=0x206,
                 FEED_PAGE=0xc00,
                 JS_PAGE=1<<16) # BBS_LIKE_PAGE = BBS_INDEX_PAGE | BBS_DETAIL_PAGE | ASK_DETAIL_PAGE

PAGE_TYPE_MAP = {
    PAGE_TYPE.NORMAL_DETAIL_PAGE: "normal_detail_page",
    PAGE_TYPE.BBS_DETAIL_PAGE: "bbs_detail_page",
    PAGE_TYPE.ASK_DETAIL_PAGE: "ask_detail_page",
    PAGE_TYPE.NORMAL_INDEX_PAGE: "normal_index_page",
    PAGE_TYPE.BBS_INDEX_PAGE: "bbs_index_page",
    PAGE_TYPE.NORMAL_FEED_PAGE: "normal_feed_page",
    PAGE_TYPE.SEATCH_FEED_PAGE: "search_feed_page",
    PAGE_TYPE.JS_PAGE: "js_page"
}

EXTRACTOR_QUEUE = "ExtractorQueue"
URL_IN_QUEUE_SET = "UrlInQueueSet"
DOWNLOAD_QUEUE = "DownloadQueue"

MAX_MISC_COUNT = 2 ** 24 - 1

DEFAULT = 0
# 性别
SEX = {
    DEFAULT: None,
    1 : u"男",
    2 : u"女",
    None: DEFAULT,
    u"男": 1,
    u"女": 2,
}


# site category

CATEGORY = {
    DEFAULT: None,
    1: u"新闻",
    2: u"博客",
    3: u"论坛",
    4: u"SNS",
    5: u"问答",
    6: u"电子报",
    None: DEFAULT,
    u"新闻": 1,
    u"博客": 2,
    u"论坛": 3,
    u"SNS" : 4,
    u"问答": 5,
    u"电子报": 6,
}

# site industry

INDUSTRY = OrderedDict([
    (u"*", 1000),
    (u"IT", 1),
    (u"电商资讯", 2),
    (u"房地产", 3),
    (u"服装", 4),
    (u"卫浴美容", 5),
    (u"家居装饰", 6),
    (u"教育", 7),
    (u"金融", 8),
    (u"旅游", 9),
    (u"零售购物", 10),
    (u"媒体", 11),
    (u"女性", 12),
    (u"汽车交通", 13),
    (u"餐饮", 14),
    (u"文化体育", 15),
    (u"数码通讯", 16),
    (u"医疗健康", 17),
    (u"游戏", 18),
    (u"母婴", 19),
    (u"其他", DEFAULT),

    (1000, u"*"),
    (1, u"IT"),
    (2, u"电商资讯"),
    (3, u"房地产"),
    (4, u"服装"),
    (5, u"卫浴美容"),
    (6, u"家居装饰"),
    (7, u"教育"),
    (8, u"金融"),
    (9, u"旅游"),
    (10, u"零售购物"),
    (11, u"媒体"),
    (12, u"女性"),
    (13, u"汽车交通"),
    (14, u"餐饮"),
    (15, u"文化体育"),
    (16, u"数码通讯"),
    (17, u"医疗健康"),
    (18, u"游戏"),
    (19, u"母婴"),
    (DEFAULT, u"其他"),
    ]
)

#common search engine list
SEARCH_ENGINE = ('so.com', 'sogou.com', 'cheyisou.com', 'qq.com', 'soso.com', 'baidu.com', 'sowm.cn')

# crawler depth limit and times limit
DEPTH_LIMIT = 2 # start from zero
TIMES_LIMIT = 3

DEFAULT_GET_URL_COUNT = 5
# crawler time interval
CRAWL_TIME_INTERVAL = Enum(INDEX_PAGE_INTERVAL=2 * 60 * 60,
                           DETAIL_PAGE_INTERVAL=12 * 60 * 60)

#url status
URL_STATUS = Enum(URL_NORMAL=0,
                  URL_IN_QUEUE=1,
                  URL_DELETED=2)

MIN_INTERVAL = 4
SCHEDULER_INTERVAL = 10 * 60.0  # seconds

#date regex
DATE_REGEX = (
    re.compile(u'(?P<year>\\d{4})(年|:|-|\/)(?P<month>\\d{1,2})(月|:|-|\/)(?P<day>\\d{1,2}).{,4}?(?P<hour>\\d{1,2})(时|:)(?P<minute>\\d{1,2})(分|:)(?P<second>\\d{1,2})', re.UNICODE),
    re.compile(u'(?P<year>\\d{4})(年|:|-|\/|\.)(?P<month>\\d{1,2})(月|:|-|\/|\.)(?P<day>\\d{1,2}).{,4}?(?P<hour>\\d{1,2})(时|:)(?P<minute>\\d{1,2})', re.UNICODE),
    re.compile(u'(?P<year>\\d{4})(年|:|-|\/|\.)(?P<month>\\d{1,2})(月|:|-|\/|\.)(?P<day>\\d{1,2})', re.UNICODE),
    re.compile(u'(?P<year>\\d{2})(年|:|-|\/|\.)(?P<month>\\d{1,2})(月|:|-|\/|\.)(?P<day>\\d{1,2}).{,4}?(?P<hour>\\d{1,2})(时|:)(?P<minute>\\d{1,2})', re.UNICODE),
    re.compile(u'(?P<month>\\d{1,2})(月|:|-|\/|\.)(?P<day>\\d{1,2}).{,4}?(?P<hour>\\d{1,2})(时|:)(?P<minute>\\d{1,2})', re.UNICODE),
    re.compile(u'(?P<days>\\d{1,2}).{,2}?天前', re.UNICODE),
    re.compile(u'(?P<hours>\\d{1,2}).{,2}?小时前', re.UNICODE),
    re.compile(u'(?P<minutes>\\d{1,2}).{,2}?分钟前', re.UNICODE),
    re.compile(u'(?P<seconds>\\d{1,2}).{,2}?秒钟前', re.UNICODE),
    re.compile(u'(?P<text>今天|昨天) ?((?P<hours>\\d{1,2}):(?P<minutes>\\d{1,2}))?', re.UNICODE),
    re.compile(u'(?P<hour>\\d+):(?P<minute>\\d+) / (?P<day>\\d+)', re.UNICODE),
    re.compile(u'(?P<months>\\d{1,2}).{,2}?months 之前', re.UNICODE),
)

SO_SITE_DOMAIN = re.compile("site(:|%3A)(?P<domain>[^&+%]*)")

if __name__ == '__main__':
    print PAGE_TYPE.NORMAL_FEED_PAGE | PAGE_TYPE.SEATCH_FEED_PAGE == PAGE_TYPE.FEED_PAGE
