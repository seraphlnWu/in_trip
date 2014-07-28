# coding=utf-8

import time
import pymongo
import itertools

from buzz.lib.store import mongo
from buzz.lib.http import url_quote
from buzz.lib.consts import INDUSTRY, PAGE_TYPE

from admin.config.consts import XPATH_STATUS, RECORD_STATUS


def get_inc_id(collection_obj):
    if not isinstance(collection_obj, pymongo.collection.Collection):
        raise ValueError()
    db = mongo.get_db()
    inc_id = db.counter.find_and_modify(query={'_id': collection_obj.name}, update={"$inc": {"seq": 1}}, new=True,
                                        upsert=True).get("seq")
    return inc_id if inc_id is not None else 1


class ModelBase(object):
    fields = []
    __collection_name__ = ""

    def __init__(self, **kwargs):
        self._check_input(kwargs)
        for column, value in kwargs.items():
            setattr(self, column, value)
        self._connection = None

    def __getattr__(self, attr):
        if attr in self.fields:
            return None  # if not set is None
        else:
            raise AttributeError("Model doesn't have attribure %s" % attr)

    @property
    def last_id(self):
        return get_inc_id(self.collection)

    @property
    def collection(self):
        if self._connection is None:
            self._connection = self.__class__.get_collection()

        return self._connection

    @classmethod
    def get_collection(cls):
        return mongo.get_db()[cls.__collection_name__]

    @classmethod
    def find(cls, status=RECORD_STATUS.NORMAL, ignore_status=False, **kwargs):
        if not ignore_status:
            kwargs['status'] = status
        return QuerySet(cls).query(kwargs)

    @classmethod
    def find_one(cls, **kwargs):
        return QuerySet(cls).query(kwargs).first()

    @classmethod
    def get(cls, _id):
        return cls.find_one(_id=_id)

    def _check_input(self, input):
        for column, value in input.items():
            if column not in self.fields:
                raise ColumnNotExistError("%s doesn't have column:%s" % (self.__collection_name__, column))

    @property
    def _object_key(self):
        _id = getattr(self, "_id")
        if _id:
            query_params = {"_id": _id}
        else:
            query_params = self.to_mongo()
        return query_params

    def to_mongo(self):
        result = {}
        for field in self.fields:
            if hasattr(self, field):
                result[field] = getattr(self, field, None)
        return result

    def update(self, multi=True, upsert=False, safe=True, op="$set", **kwargs):
        operators = ['$set', '$unset', '$inc', '$pop', '$push', '$addToSet', '$pullAll']
        if op in operators:
            self.collection.update(self._object_key, {"$set": kwargs})
        else:
            OperatorNotRecognizeError("%s operator not recognized.", op)

    def update_one(self, multi=False, upsert=False, op="$set", **kwargs):
        self.update(multi=multi, upsert=upsert, op=op, **kwargs)

    def find_and_modify(self, upsert=False, sort=None, op="$set", new=True, **kwargs):
        query = self._object_key
        record = self.collection.find_and_modify(query, {op: kwargs}, upsert, sort, new=new)
        for column, value in record.items():
            setattr(self, column, value)

    def save(self, autoincrement_id=True):
        if autoincrement_id:
            self._id = self.last_id
        write_options = self.to_mongo()
        self.collection.insert(write_options)

    def delete(self, status=RECORD_STATUS.DELETED):
        self.update(status=status)


class QuerySet(object):

    def __init__(self, model_class):
        self.model_class = model_class
        self._collection = model_class.get_collection()
        self._iter = False
        self._cursor = None
        self._query = None
        self._ordering = None
        self._skip = None
        self._limit = None

    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = self._collection.find(self._query)
            if self._ordering:
                self._cursor.sort(self._ordering)

            if self._skip:
                self._cursor.skip(self._skip)

            if self._limit:
                self._cursor.limit(self._limit)
        return self._cursor

    def __getitem__(self, key):
        """Support slicing syntax.
        """
        if isinstance(key, slice):
            self._skip, self._limit = key.start, key.stop
        elif isinstance(key, int):
            return self._build_obj(self.cursor[key])

    def __len__(self):
        return self.count()

    def __iter__(self):
        self.rewind()
        return self

    def rewind(self):
        self._iter = False
        self.cursor.rewind()

    def next(self):
        self._iter = True
        try:
            if self._limit == 0:
                raise StopIteration()
            return self._build_obj(self.cursor.next())

        except StopIteration as e:
            self.rewind()
            raise e

    def _build_obj(self, row):
        if row is None:
            return None
        else:
            return self.model_class(**row)

    def query(self, qeury_statement):
        if self._query is None:
            self._query = qeury_statement

        return self

    def sort(self, *keys):
        key_list = []
        for key in keys:
            if not key:
                continue
            direction = pymongo.ASCENDING
            if key[0] == '-':
                direction = pymongo.DESCENDING
            if key[0] in ('-', '+'):
                key = key[1:]
            key_list.append((key, direction))

        self._ordering = key_list
        return self

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def first(self):
        try:
            result = self[0]
        except:
            result = None

        return result

    def count(self):
        if self._limit == 0:
            return 0
        return self.cursor.count(with_limit_and_skip=True)


class Project(ModelBase):
    fields = ['_id', 'name', 'effective_time', 'industry_id', 'topic_ids', 'created_on', 'user_id', 'black_list', 'white_list', 'regex', 'status']
    __collection_name__ = "project"


class Topic(ModelBase):
    fields = ['_id', 'main_key', 'synonyms', 'and_keys', 'or_keys', 'not_keys', 'project_id', 'created_on', 'status']
    __collection_name__ = 'topic'


class Site(ModelBase):
    fields = ['_id', 'domain', 'site_name', 'url', 'prior_level', 'industry_id', 'status']
    __collection_name__ = 'site'

    @classmethod
    def get_by_domain(cls, domain):
        return cls.find_one(domain=domain, status=RECORD_STATUS.NORMAL)


class Feed(ModelBase):
    fields = ['_id', 'site_id', 'url_rule', 'kwargs', 'charset', 'feed_type', 'industry_id', 'describe', 'created_on', 'status']
    __collection_name__ = 'feed'


class DealerFeed(ModelBase):
    fields = ['_id', 'url', 'keyword', 'created_on', 'site_id', 'status']
    __collection_name__ = 'dealer_feed'


class Xpath(ModelBase):
    fields = ['_id', 'eg', 'prop', 'site_id', 'status', 'url_regex_id', 'xpath']
    __collection_name__ = 'xpath'

    @classmethod
    def get_by_site_id(cls, site_id):
        return [row for row in cls.find(site_id=site_id, status={"$lt": XPATH_STATUS.DELETE}).sort('_id')]


class UrlRegex(ModelBase):
    fields = ['_id', 'status', 'url_reg', 'site_id', 'xpath_ids']
    __collection_name__ = 'url_regex'


class Channel(ModelBase):
    fields = ['_id', 'category_id', 'channel_name', 'industry_id', 'site_id', 'status', 'url', 'created_on']
    __collection_name__ = 'channel'


class Blacklist(ModelBase):
    fields = ['_id', 'status', 'site_id', 'detail', 'url_reg']
    __collection_name__ = 'blacklist'


class PostFeed(ModelBase):
    fields = ['_id', 'status', 'site_id', 'industry_id', 'charset', 'created_on', 'formhash_regex', 'formhash_url', 'post_url', 'kwargs', 'method']
    __collection_name__ = 'postfeed'


class Download(ModelBase):
    fields = ['_id', 'status', 'start_time', 'end_time', 'topic', 'project_id', 'created_on', 'filename', 'need_comment']
    __collection_name__ = 'download'


class Auth(ModelBase):
    fields = ['_id', 'status', 'role', 'mail', 'password', 'salt', 'company', 'end_date', 'created_on']
    __collection_name__ = 'auth'


class ColumnNotExistError(Exception):
    pass


class OperatorNotRecognizeError(Exception):
    pass


def get_keywords():
    keywords = {}
    current_time = time.time()
    for project in Project.find():
        start, end = project.effective_time
        if start < current_time < end:
            for topic in Topic.find(project_id=project._id):
                if project.industry_id in keywords:
                    keywords[project.industry_id].append(topic.main_key)
                    keywords[project.industry_id].extend(topic.synonyms)
                else:
                    keywords[project.industry_id] = topic.synonyms
                    keywords[project.industry_id].append(topic.main_key)
    return keywords


def get_feeds():
    feeds = []
    for feed in Feed.find().sort('_id'):
        feeds.append(feed)
    return feeds


def parse_feed(feed, keywords, page_range=(0, 1)):
    url_rule = feed.url_rule[0] if page_range[0] <= 1 else feed.url_rule[-1]
    if feed.feed_type == PAGE_TYPE.NORMAL_FEED_PAGE:
        urls = [url_rule, ]
    else:
        kwargs = feed.kwargs
        for key, value in kwargs.iteritems():
            if isinstance(value[0], int) and len(value) <= 4:
                if key == 'page':
                    if len(page_range) == 2:
                        start, end = page_range
                        end = value[3] if len(value) == 4 and value[3] > end else end
                        kwargs[key] = range(*value[:3])[start: end]
                    else:
                        start = page_range[0]
                        kwargs[key] = range(*value[:3])[start:]
                else:
                    kwargs[key] = range(*value)

        if feed.industry_id and '%(topic)s' in url_rule:
            _keywords = []
            if INDUSTRY['*'] in feed.industry_id:
                for k in keywords.values():
                    _keywords.extend(k)
            else:
                for industry_id in feed.industry_id:
                    _keywords.extend(keywords.get(industry_id, []))

                _keywords.extend(keywords.get(INDUSTRY['*'], []))  # * project
            _keywords = list(set(_keywords))
            kwargs['topic'] = _keywords

        for key, value in kwargs.iteritems():
            kwargs[key] = [url_quote(x, feed.charset or "utf-8") for x in value]

        args = [dict(zip(kwargs.iterkeys(), value)) for value in itertools.product(*kwargs.itervalues())]
        urls = [str(url_rule % arg) for arg in args]

    return urls

if __name__ == '__main__':
    n = Feed.get(30)
    keywords = get_keywords()
    print keywords
    urls = parse_feed(n, keywords)
    print len(urls), urls
