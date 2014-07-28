# coding=utf-8

# keyword match based on  Aho-Corasick algorithm
import ahocorasick

from admin.config.consts import RECORD_STATUS

from in_trip.lib.store import mongo


class MultiPatternSearch(object):
    def __init__(self, keywords=None, ignorecase=True):
        if not keywords:
            keywords = self.load_keywords(keywords)
        self.ignorecase = ignorecase
        if self.ignorecase:
            self.keywords = [keyword.lower().encode('utf-8') for keyword in keywords]
        else:
            self.keywords = keywords

        self.build_tree()

    def load_keywords(self, keywords=None):
        # include all keywords even if outdate
        keywords = []
        db = mongo.get_db()
        for topic in db.topic.find({'status': RECORD_STATUS.NORMAL}):
            keywords.append(topic['main_key'])
            keywords.extend(topic['synonyms'])

        return list(set(keywords))


    def build_tree(self):
        tree = ahocorasick.KeywordTree()
        for keyword in self.keywords:
            tree.add(keyword)
        tree.make()
        self.tree = tree

    def match(self, text):
        if self.ignorecase:
            text = text.lower()
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        keywords = set()
        for match in self.tree.findall(text, allow_overlaps=1):
            start, end = match[:2]
            keywords.add(text[start:end])

        keywords = [keyword.decode('utf-8') for keyword in keywords]  # use unicode
        return keywords

multi_pattern_search = MultiPatternSearch()

if __name__ == '__main__':
    for x in multi_pattern_search.match(u"中国最强音》是湖南卫视2013年第二季主推的大型励志音乐类真人秀节目。节目主打零门槛参与，不限年龄不限性别，只要坚持梦想，热爱音乐的个人或者组合，知名歌手或者草根歌手都可以申请参与。节目在挖掘有潜质，声音优质的歌手同时，也关注他们在生活中对待音乐的态度。节目首次尝试全新的歌手选拔方式，打造中国的草根音乐联赛hEllo, Hello"):
        print x
