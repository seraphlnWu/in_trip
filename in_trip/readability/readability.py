#!/usr/bin/env python
#coding=utf-8
import re
import sys
import copy
import logging
import datetime
import urlparse
from collections import defaultdict

from lxml.html import document_fromstring
from lxml.html import fragment_fromstring, HtmlElement
from lxml.etree import tostring, tounicode, ParserError, XMLSyntaxError

from .cleaners import html_cleaner, clean_attributes
from .htmls import (get_body, build_dom, get_title, shorten_title,
                   describe, text_length, Unparseable, to_legal_datetime, remove_space)

from buzz.lib.utils import first
from buzz.lib.http import url_quote
from buzz.lib.consts import PAGE_TYPE, DATE_REGEX

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

REGEXES = {
    'unlikelyCandidatesRe': re.compile('combx|comment|community|disqus|extra|foot|menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|popup|tweet|twitter|friend_link|relateSearch|scrol|adList|adarea|jibie|con_right|siderbarl|tie-quote|areaNav|address|cominfo|pro_condition|bread_nav'),
    'okMaybeItsACandidateRe': re.compile('and|article|body|column|main|shadow|result|conright fr|summary_about|car_xq', re.I),
    'positiveRe': re.compile('article|body|content|entry|hentry|main|page|pagination|post|blog|story|pzoom', re.I),
    'negativeRe': re.compile('combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget|Tzbjb-Article-QQ|main_tk', re.I),
    'divToPElementsRe': re.compile('<(a|blockquote|dl|div|img|ol|p|pre|table|ul|span|h1|h2)', re.I),
    'dateRe': re.compile('(?<!thanks_)time|date'),
    'dateAttrScoreRe': re.compile('post|article|pub|art'),
    'dateTextScoreRe': re.compile(u'发表|post|时间|日期'),
    'dateTextNegativeRe': re.compile(u'注 ?册|专访|促销|车展|采集|团购|活动|上市|采访|当地|生产|报价|被.*?编辑|上次访问|上次登录'),
    'commentCountRe': re.compile(u'评论|回复'),
    'viewCountRe': re.compile(u'(浏览|查看|阅读|人气|点击|参与)'),
    'miscCountNegativeRe': re.compile(u'(点击查看|查看.*?图|车友|参与互动|阅读全文|提交评论|查看全部|我要评论|关注人气|点击排行|关键词阅读|评论分析|相关阅读|查看更多)'),
    'authorRe': re.compile('author|auth|editor|user|owner|nick'),
    'authorReInHref': re.compile('uid|user'),
    'authorTextRe': re.compile(u'作者|来 ?源|我要评论|编辑|新闻类别|楼主'),
    'authorTextReFirst': re.compile(u'(作者|楼主)[:：\n]*(?P<author>.*?)([|\s类责编\u3000\u3002].*|$)'),
    'authorTextReSecond': re.compile(u'(来源|出处)[:：\n]*(?P<author>.*?)[|\s类责编\u3000\u3002].*'),
    'bbsBlockPositiveRe': re.compile('reply|comment|thread|post|js_linkItem|topic|Article', re.I),
    'bbsBlockNegativeRe': re.compile('right|left|rank|sider|mframe|subnav|hidden|adNone|content01|top|area|w950|hclc|mb8|ina_|chan_|w1000|arl-|s_li|wrp|Warp|nscon|text|mainwrap|articl|bGray|artical|row_black|border|conbox|panel|table_pics|wrapper|page|other|hot|navat|rec_box|mt10|box\d|ivy_art_yc|ajax|Detail_bind|lay1|share_detail_list|piece', re.I),
    'likelyBlock': re.compile("f_header|right_side_2", re.I),
    'unlikelyBlock': re.compile("MsoNormalTable|article_infos|price_container|p_content|articlecontent|moduleParagraph|contentText|jxs_twshbox|news_content|art_con|centerbox|rightkuan|dright|news_right|article_right|content_right|con_right|a_right|finnal_right|cnt_right|ina_news_main_right|main_right f_r|sohm_right|area_right|bottom|detail_right|art_rig|related|side|gallery|slide|photo|rank|head|info-detail-article|mutu-news|wd_setcar|box-center|postcontent_body|nry_zw|right_news|content_bit|partrig|contrgt|sina_keyword_ad_area2|ina_news_contents|ptb_right|post_\d+|share_detail_list", re.I),
    #'replaceBrsRe': re.compile('(<br[^>]*>[ \n\r\t]*){2,}',re.I),
    #'replaceFontsRe': re.compile('<(\/?)font[^>]*>',re.I),
    #'trimRe': re.compile('^\s+|\s+$/'),
    #'normalizeRe': re.compile('\s{2,}/'),
    #'killBreaksRe': re.compile('(<br\s*\/?>(\s|&nbsp;?)*){1,}/'),
    #'videoRe': re.compile('http:\/\/(www\.)?(youtube|vimeo)\.com', re.I),
    #skipFootnoteLink:      /^\s*(\[?[a-z0-9]{1,2}\]?|^|edit|citation needed)\s*$/i,
}

DIGITAL_REGEX = re.compile("(?P<count>(\d+,?\d*))")

DIGITAL_SUB = re.compile("\d{5,}|first")
PUNCTUATIONS = re.compile(ur"[^\u4E00-\u9FA5a-z]")

PAGE_REGEX = re.compile('page|pg|fanye|l_thread_info|bbs_CtrlArea|numb_post2', re.I)
FIRST_PAGE_TEXT = ['1', u'首页', u'第一页', '1 ...', '1...', u'«']

AUTHOR_TAG = ['span', 'em', 'strong', 'p', 'li', 'a', 'td', 'div', 'script']
MISC_COUNT_TAG = ['span', 'p', 'div', 'em', 'li', 'td', 'a', 'i', 'font']
NEGATIVE_BBS_TAGS = ('p', 'a', 'span', 'img', 'td', 'strong', 'b', 'i', 'center', 'h2', 'tbody')
BLOCK_TAGS = ['div', 'ul', 'li', 'table', 'tbody', 'tr', 'td', 'th', 'p', 'dl', 'dt', 'dd']
PUB_DATE_TAG = ['span', 'div', 'td', 'p', 'a', 'em', 'li', 'i', 'h2', 'h3', 'h4', 'h5', 'h6', 'cite', 'dt', 'dd', 'font', 'script', 'time', 'ul', 'center']

XPATH_HEAD = re.compile('^\(?\.?//?')


class Document:
    """Class to build a etree document out of html."""
    RETRY_LENGTH = 250
    MIN_TEXT_LENGTH = 60
    BBS_LEVEL_LIMIT = 12
    BBS_PAGE_BLOCK_LIMIT = 3
    TEXT_LENGTH_THRESHOLD = 25

    def __init__(self, response, **options):
        """Generate the document

        :param response: HttpResponse obj.

        kwargs:
            - attributes:
            - debug: output debug messages
            - min_text_length:
            - retry_length:
            - url: will allow adjusting links to be absolute

        """
        self.resp = response
        self.options = options

        self._dom = None
        self._page_type = None
        self.trans_html = None
        self.trans_flag = False
        self.other_page = None
        self._is_first_page = None

        self.special = self.options.get('special') or {}

    def title(self):
        return get_title(self.dom)

    def short_title(self):
        if not hasattr(self, 'post_title'):
            if self.special.get('title'):
                self.post_title = self.dom.xpath(self.special.get('title'))[0]
            else:
                self.post_title = shorten_title(self.dom)

        return self.post_title

    @property
    def page_type(self):
        if self._page_type is None:
            self._page_type = self.detect_page_type()
        return self._page_type

    @property
    def dom(self):
        if self._dom is None:
            try:
                self._dom = build_dom(self.resp.utf8_source)
            except (ParserError, XMLSyntaxError):
                self._main_block = None
        return self._dom

    def get_publish_date(self):
        if not hasattr(self, "pub_date"):
            dom = self.dom
            for elem in self.reverse_tags(dom, 'span'):  # trans some span to p
                if elem.text and len(elem.getchildren()) > 0:
                    span = fragment_fromstring('<span/>')
                    span.text = elem.text
                    elem.insert(0, span)
                    elem.tag = "p"
                    elem.text = None

            for elem in self.reverse_tags(dom, 'div'):  # trans some text in div to span
                if elem.text and len(elem.getchildren()) > 0:
                    span = fragment_fromstring('<span/>')
                    span.text = elem.text
                    elem.insert(0, span)

            self.pub_date = self._get_publish_date(dom)

        return self.pub_date

    def _get_publish_date(self, dom, comment=False):
        if self.special.get('pub_date'):
            date_text_li = dom.xpath(self.special.get('pub_date'))
            if len(date_text_li) > 0:
                if self.special.get('pub_date_regex'):
                    match = first(date_text_li, lambda x: re.search(self.special.get('pub_date_regex'), x))
                else:
                    match = first(date_text_li, lambda text: first(DATE_REGEX, lambda x: x.search(text)))

                if match:
                    return to_legal_datetime(match)

        date_regex = DATE_REGEX if comment else DATE_REGEX[:3]
        candidates = []
        for elem in self.tags(dom, *PUB_DATE_TAG):
            text = elem.text_content()
            data_field = elem.get('data-field', '')  # for baidu tieba
            text += elem.get('title', '')
            if data_field or (text and (8 <= text_length(text) <= 150)):
                score = 0
                text = data_field + text
                match = first(date_regex, key=lambda x: x.search(text))  # first or default
                if match:
                    attribute_text = '%s %s' % (elem.get('id', ''), elem.get('class', ''))
                    if len(attribute_text) > 1:
                        if REGEXES['dateRe'].search(attribute_text):
                            score += 20
                        if REGEXES['dateAttrScoreRe'].search(attribute_text):
                            score += 10

                    negative = REGEXES['dateTextNegativeRe'].search(text)
                    if negative and abs(match.start() - negative.end()) <= 4:
                        continue

                    author_match = REGEXES['authorTextRe'].search(text)
                    date_match = REGEXES['dateTextScoreRe'].search(text)
                    if author_match or (date_match and abs(date_match.start() - match.end()) < 6) or match.start() < len(data_field):
                        score += 30

                    result = to_legal_datetime(match)
                    if result is not None:
                        candidate = {'result': result, 'score': score}
                        candidates.append(candidate)
                    else:
                        continue

                if score >= 30:
                    break
        candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
        return candidates[0]['result'] if candidates else None

    def get_author(self):
        if not hasattr(self, 'author'):
            dom = self.dom
            self.author = self._get_author(dom)

        return self.author

    def _get_author(self, dom):
        if self.special.get('author'):
            text_li = dom.xpath(self.special.get('author'))
            if len(text_li) > 0:
                if self.special.get('author_regex'):
                    match = re.search(self.special.get('author_regex'), text_li[0])
                    if match:
                        return match.groupdict().get('author')
                else:
                    return text_li[0]

        candidates = []
        source = ''
        neighbour = 3
        for elem in self.tags(dom, *AUTHOR_TAG):
            text = elem.text_content()
            if elem.tag == 'div':
                match = REGEXES['authorRe'].search(elem.get('class', ''))
                if match:
                    return elem.text_content()

            if text and (2 < text_length(text) <= 50):
                score = 0
                if len(source) > 0:
                    if neighbour == 0:
                        return source
                    else:
                        neighbour -= 1
                for regex in ['authorTextReFirst', 'authorTextReSecond']:
                    match = REGEXES[regex].search(text) or REGEXES[regex].search(elem.getparent().text_content())
                    if match:
                        if regex == 'authorTextReSecond':
                            source = match.group('author')
                        else:
                            return match.group('author')

                attribute_text = '%s %s' % (elem.get('id', ''), elem.get('class', ''))
                if len(attribute_text) > 1:
                    score = 0
                    match = REGEXES['authorRe'].search(attribute_text)
                    if match:
                        score += 10
                        if 'nick' in attribute_text or 'name' in attribute_text:
                            score += 5
                        if not len(candidates):
                            score += 3
                        score += 2.0 / len(text)
                        candidates.append({'result': text, 'score': score})

        candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
        return candidates[0]['result'] if candidates else u""

    def get_misc_count(self):
        if not hasattr(self, "comment_count") and not hasattr(self, "view_count"):
            self.comment_count, self.view_count = None, None
            has_special = {}
            for i, key in enumerate(['view_count', 'comment_count']):
                if self.special.get(key):
                    has_special[key] = None
                    text_li = self.dom.xpath(self.special[key])
                    if len(text_li) > 0:
                        key_regex = key + '_regex'
                        if self.special.get(key_regex):
                            match = re.search(self.special.get(key_regex), text_li[0])
                            if match:
                                has_special[key] = int(match.groupdict().get(key))
                        else:
                            has_special[key] = int(text_li[0]) if text_li[0].isdigit() else None

            dom = self.dom
            comment_count = view_count = None
            for elem in self.tags(dom, *MISC_COUNT_TAG):
                text = elem.text_content()
                if text and (0 < text_length(text) <= 30):
                    text_len = len(text)
                    if text_len > 2:
                        comment_start = view_start = text_len
                        for index, re_key in enumerate(['commentCountRe', 'viewCountRe']):
                            search_result = REGEXES[re_key].search(text)
                            if search_result and not REGEXES['miscCountNegativeRe'].search(text):
                                if index == 0:
                                    comment_start = search_result.start()
                                else:
                                    view_start = search_result.start()

                        if view_start < text_len and comment_start < text_len:
                            match = first(DATE_REGEX[:3], key=lambda x: x.search(text))
                            need_exchange = False
                            if view_start < comment_start:
                                search_end = comment_start
                                first_start = view_start
                                second_start = comment_start
                            else:
                                search_end = view_start
                                first_start = comment_start
                                second_start = view_start
                                need_exchange = True

                            search_start = match.end() if match and match.end() < first_start else 0
                            for match in re.finditer(DIGITAL_REGEX, text[search_start:search_end]):
                                if match and abs(search_start + match.start() - first_start) < 10:
                                    count = int(match.groupdict().get('count').replace(',', ''))
                                    view_count = count
                                    search_start = match.end()

                            match = DIGITAL_REGEX.search(text[search_start:])
                            if match and abs(search_start + match.start() - second_start) < 10:
                                count = int(match.groupdict().get('count').replace(',', ''))
                                comment_count = count

                            if need_exchange:
                                view_count, comment_count = comment_count, view_count

                        elif view_start < text_len:
                            match = DIGITAL_REGEX.search(text[view_start:])
                            if match:
                                count = int(match.groupdict().get('count').replace(',', ''))
                                view_count = count

                        elif comment_start < text_len:
                            match = DIGITAL_REGEX.search(text[comment_start:])
                            if match:
                                count = int(match.groupdict().get('count').replace(',', ''))
                                comment_count = count

                if comment_count is not None and view_count is not None:
                    break

            self.view_count = has_special['view_count'] if 'view_count' in has_special else view_count
            self.comment_count = has_special['comment_count'] if 'comment_count' in has_special else comment_count

        return self.comment_count, self.view_count

    def text_content(self, page_type=PAGE_TYPE.NORMAL_DETAIL_PAGE):
        content = u"" if (page_type & PAGE_TYPE.BBS_DETAIL_PAGE) else self.main_post

        if page_type & PAGE_TYPE.BBS_LIKE_PAGE:
            bbs_content = []
            for block in self.bbs_comments:
                bbs_content.append(block['content'])
            content += u",".join(bbs_content)

        return remove_space(content)

    @property
    def main_post(self):
        if not hasattr(self, "_main_post"):
            if self.special.get('content'):
                _dom = self.remove_unlikely_candidates(copy.deepcopy(self.dom))
                return u' '.join(_dom.xpath(self.special.get('content')))
            else:
                if not self.trans_flag:
                    self.transform(html_partial=True)
                self._main_post = unicode(self.trans_html.text_content()) if self.trans_html is not None else u""

        return self._main_post

    def content(self):
        return get_body(self.dom)

    @property
    def main_block(self):
        if not hasattr(self, '_main_block'):
            if self.special.get('main_block'):
                main_block_xpath = self.special.get('main_block')
                try:
                    if XPATH_HEAD.match(main_block_xpath):
                        _main_block = self.dom.xpath(main_block_xpath)[0]
                    else:
                        _main_block = self.dom.cssselect(main_block_xpath)[0]

                    self._main_block = self.remove_unlikely_candidates(copy.deepcopy(_main_block))
                except IndexError:
                    self._main_block = None
            else:
                candidates = []
                for div in self.dom.xpath(".//body/*"):
                    attr = (div.get("class", "") or "") + ";" + (div.get('id') or "")
                    style = div.get("style", '').replace(' ', '')
                    if "display:none" not in style and "search_car" not in attr:
                        candidates.append((div, div.xpath("count(.//*)"), attr))

                candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
                if candidates:
                    if len(candidates) < 8:
                        main = copy.deepcopy(candidates[0][0])
                    else:
                        main = copy.deepcopy(self.dom.xpath('.//body')[0])

                    main = self.remove_unlikely_candidates(main)

                    MIN_LEN = max(self.options.get('min_text_length', self.TEXT_LENGTH_THRESHOLD), 45)
                    for elem in self.tags(main, 'a'):
                        text = elem.text_content()
                        if text_length(text) > MIN_LEN:
                            a = fragment_fromstring('<a/>')
                            a.set('href', elem.get('href') or "")
                            elem.append(a)
                            elem.tag = "p"

                    self._main_block = main
                else:  # js page
                    self._main_block = None

        return self._main_block

    def get_bbs_blocks_candidate(self):
        """Breadth-First-Search
        """
        node_queue = [(self.main_block, 0), ]
        while node_queue:
            node, level = node_queue.pop(0)
            childrens = node.getchildren()
            if len(childrens) >= self.BBS_PAGE_BLOCK_LIMIT:
                candidates = defaultdict(list)
                for order, children in enumerate(childrens):
                    possibility = False
                    tag = children.tag.lower()
                    if tag in NEGATIVE_BBS_TAGS:
                        pass
                    elif len(children.getchildren()) <= 0:
                        pass
                    elif tag == 'body' and children.tag.lower() == 'table':
                        # http://tibet.news.cn/gdbb/2013-05/15/c_132383342.htm
                        pass
                    else:
                        class_attr = children.get('class') or children.get('id') or ""
                        if REGEXES['bbsBlockPositiveRe'].search(class_attr) or not REGEXES['bbsBlockNegativeRe'].search(class_attr):
                            if (not class_attr and children.tag.lower() == "div") or class_attr in ('clear', 'clearfix'):
                                pass
                            else:
                                possibility = True

                    if possibility:
                        class_attr = DIGITAL_SUB.sub("", class_attr)
                        if len(class_attr) > 6:
                            class_attrs = first((' ', '-', '_'), lambda x: x in class_attr and class_attr.split(x), [class_attr, ])
                            if len(class_attrs) > 1:
                                class_attrs = sorted(class_attrs, key=len, reverse=True)[:3]
                                class_attrs = filter(lambda x: len(x) > 2 and x not in ('clear', 'clearfix', 'noborder'), class_attrs)
                        else:
                            class_attrs = [class_attr, ]
                        for index, attr in enumerate(class_attrs):
                            attr = "%s;%s_%d" % (children.tag.lower(), attr, index)
                            candidates[attr].append((children, order))

                candidates = filter(lambda y: 100 >= len(y[1]) >= self.BBS_PAGE_BLOCK_LIMIT,
                                    sorted(candidates.iteritems(), key=lambda x: len(x[1]), reverse=True))
                for candidate in candidates:
                    yield candidate

            for children in childrens:
                class_attr = children.get('class', "") + children.get('id', "") or ""
                if level < self.BBS_LEVEL_LIMIT and (REGEXES['likelyBlock'].search(class_attr) or
                                                not REGEXES['unlikelyBlock'].search(class_attr)):
                    node_queue.append((children, level + 1))

    @property
    def bbs_blocks(self):
        if not hasattr(self, '_bbs_blocks'):
            page_type = self.special.get('page_type')
            if page_type and not (page_type & PAGE_TYPE.BBS_LIKE_PAGE):
                self._bbs_blocks = None
            elif self.special.get("bbs_blocks"):
                bbs_blocks_xpath = self.special.get("bbs_blocks")
                if XPATH_HEAD.match(bbs_blocks_xpath):
                    self._bbs_blocks = self.dom.xpath(bbs_blocks_xpath)
                else:
                    self._bbs_blocks = self.main_block.cssselect(bbs_blocks_xpath)
            else:
                main_block_tag_count = max(self._get_block_tag_count(self.main_block), 1.0)
                main_block_len = max(text_length(PUNCTUATIONS.sub("", self.main_block.text_content())), 1.0)
                for candidate in self.get_bbs_blocks_candidate():
                    flag = False
                    orders = []
                    candidate_bbs_blocks = []
                    for block in candidate[1]:
                        orders.append(block[1])
                        candidate_bbs_blocks.append(block[0])
                    orders.sort()
                    max_interval = get_max_interval(orders)
                    if max_interval > 4:
                        continue
                    block_tag_density = (self._get_block_tag_count(candidate_bbs_blocks[0]) +
                                         self._get_block_tag_count(candidate_bbs_blocks[1]) * (len(candidate_bbs_blocks) - 1)) / main_block_tag_count
                    if block_tag_density >= 0.6:
                        flag = True
                    else:
                        text_len = 0.0
                        for n in candidate_bbs_blocks:
                            text_len += text_length(n.text_content())
                        text_dentisy = text_len / main_block_len
                        if text_dentisy > 0.65:
                            flag = True
                    if flag:
                        self._bbs_blocks = candidate_bbs_blocks
                        break
                else:
                    self._bbs_blocks = None

        return self._bbs_blocks

    def bbs_pub_date(self, block):
        return self._get_publish_date(block, comment=True)

    def bbs_text_content(self, block):
        block = self.remove_unlikely_candidates(copy.deepcopy(block))
        raw_content = block.text_content()
        start = 0
        end = len(raw_content)
        START_REGEX = [
            re.compile(u'发表于.{0,2}(\\d{4})(年|:|-|\/)(\\d{1,2})(月|:|-|\/)(\\d{1,2})(.{,4}?(\\d{1,2})(时|:)(\\d{1,2})((分|:)(\\d{1,2}))?)?'),
            re.compile(u'时间.{0,2}(\\d{4})(年|:|-|\/)(\\d{1,2})(月|:|-|\/)(\\d{1,2}).{,4}?(\\d{1,2})(时|:)(\\d{1,2})(分|:)(\\d{1,2})'),
            re.compile(u'只看该作者|只看楼主|只看该用户'),
            re.compile(u'倒序浏览'),
            re.compile(u'阅读模式'),
        ]
        END_REGEX = re.compile(u'回复本帖|回复本楼')
        for reg in START_REGEX:
            match = reg.search(raw_content, re.DOTALL)
            if match:
                start = max(start, match.end())

        match = END_REGEX.search(raw_content, re.DOTALL)
        if match and match.start > start:
            end = match.start()
        return unicode(raw_content[start:end])

    def bbs_author(self, block):
        return self._get_author(block)

    @property
    def bbs_comments(self):
        if not hasattr(self, '_bbs_comments') and self.bbs_blocks is not None:
            bbs_blocks = []
            for block in self.bbs_blocks:
                pub_date = self.bbs_pub_date(block)
                if pub_date is not None:
                    bbs_blocks.append({
                        'pub_date': pub_date,
                        'content': self.bbs_text_content(block),
                        'author': '',
                    })

            bbs_blocks.sort(key=lambda x: x['pub_date'])
            self._bbs_comments = bbs_blocks

        return getattr(self, '_bbs_comments', [])

    @property
    def is_first_page(self):
        if self._is_first_page is None:
            if self.other_page is None:
                self.get_other_page()

            self._is_first_page = self.other_page[0] == self.resp.url if self.other_page else False

        return self._is_first_page

    def get_first_page(self):
        if self.other_page is None:
            self.get_other_page()
        return self.other_page[0] if self.other_page else None

    def get_other_page(self):
        if self.other_page is None:
            self.other_page = [self.resp.url]
            base = self.dom.find('.//base')
            base_url = url_quote(base.get('href') if base is not None and base.get('href') else self.resp.url)
            for elem in self.dom.xpath('.//div'):
                attribute_text = '%s %s' % (elem.get('id', ''), elem.get('class', ''))
                if len(attribute_text) > 1 and PAGE_REGEX.search(attribute_text) and len(elem.text_content()) < 100:
                    for elem in elem.iterdescendants('a'):
                        href = elem.get('href')
                        if not href:
                            continue
                        href = url_quote(href.strip(), self.resp.encoding)
                        if href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('#'):
                            continue

                        if not href.startswith('http'):
                            href = urlparse.urljoin(base_url, href)

                        if elem.text in FIRST_PAGE_TEXT:
                            self.other_page[0] = href
                        else:
                            self.other_page.append(href)

        return self.other_page

    def transform(self, html_partial=False):
        try:
            ruthless = True
            while True:
                if ruthless:
                    html = self.main_block
                else:
                    html = self.remove_unlikely_candidates(copy.deepcopy(self.dom),
                                                           script=True, display=True, candidate=True)
                html = self.transform_misused_divs_into_paragraphs(html)
                candidates = self.score_paragraphs(html)
                best_candidate = self.select_best_candidate(candidates)
                if best_candidate:
                    article = self.get_article(
                        candidates, best_candidate, html_partial=html_partial)
                else:
                    if ruthless:
                        log.debug("ruthless removal did not work. ")
                        ruthless = False
                        self.debug(
                            ("ended up stripping too much - "
                             "going for a safer _parse"))
                        # try again
                        continue
                    else:
                        log.debug(
                            ("Ruthless and lenient parsing did not work. "
                             "Returning raw html"))
                        if html.tag.lower() == 'html':
                            article = html.xpath(".//body")[0]
                        else:
                            article = html
                html = self.sanitize(article, candidates)
                cleaned_article = self.get_clean_html(html)
                article_length = len(cleaned_article or '')
                retry_length = self.options.get(
                    'retry_length',
                    self.RETRY_LENGTH)
                of_acceptable_length = article_length >= retry_length
                if ruthless and not of_acceptable_length:
                    ruthless = False
                    # Loop through and try again.
                    continue
                else:
                    self.trans_flag = True
                    self.trans_html = html
                    return self.trans_html
        except StandardError, e:
            log.exception('error getting summary: ')
            raise Unparseable(str(e)), None, sys.exc_info()[2]

    def get_clean_html(self, dom):
        return clean_attributes(tounicode(dom))

    def summary(self, html_partial=False):
        """Generate the summary of the html docuemnt

        :param html_partial: return only the div of the document, don't wrap
        in html and body tags.

        """
        if not self.trans_flag:
            self.transform(html_partial=html_partial)
        return self.get_clean_html(self.trans_html)

    def get_article(self, candidates, best_candidate, html_partial=False):
        # Now that we have the top candidate, look through its siblings for
        # content that might also be related.
        # Things like preambles, content split by ads that we removed, etc.
        sibling_score_threshold = max([
            10,
            best_candidate['content_score'] * 0.2])
        # create a new html document with a html->body->div
        if html_partial:
            output = fragment_fromstring('<div/>')
        else:
            output = document_fromstring('<div/>')
        best_elem = best_candidate['elem']
        siblings = best_elem.getparent().getchildren() if best_elem.getparent() is not None else [best_elem]
        for sibling in siblings:
            # in lxml there no concept of simple text
            # if isinstance(sibling, NavigableString): continue
            append = False
            if sibling is best_elem:
                append = True
            else:
                sibling_key = sibling  # HashableElement(sibling)
                if sibling_key in candidates and \
                        candidates[sibling_key]['content_score'] >= sibling_score_threshold:
                    append = True
                else:
                    if sibling.tag == "p":
                        link_density = self.get_link_density(sibling)
                        node_content = sibling.text or ""
                        node_length = len(node_content)

                        if node_length > 80 and link_density < 0.25:
                            append = True
                        elif node_length <= 80 and link_density == 0 \
                                and re.search('\.( |$)', node_content):
                            append = True

            if append:
                # We don't want to append directly to output, but the div
                # in html->body->div
                if html_partial:
                    output.append(sibling)
                else:
                    output.getchildren()[0].getchildren()[0].append(sibling)
        if output is not None:
            output.append(best_elem)
        return output

    def select_best_candidate(self, candidates):
        sorted_candidates = sorted(candidates.values(), key=lambda x: x['content_score'], reverse=True)
        for candidate in sorted_candidates[:5]:
            elem = candidate['elem']
            self.debug("Top 5 : %6.3f %s" % (
                candidate['content_score'],
                describe(elem)))

        if len(sorted_candidates) == 0:
            return None

        best_candidate = sorted_candidates[0]
        return best_candidate

    def get_link_density(self, elem, remove_punctuations=False):
        link_length = 0
        for i in elem.findall(".//a"):
            link_length += text_length(i.text_content())
        if remove_punctuations:
            text = PUNCTUATIONS.sub("", elem.text_content())
        else:
            text = elem.text_content()
        total_length = text_length(text)

        return float(link_length) / max(total_length, 1)

    def _get_block_tag_count(self, elem):
        count = 0.0
        for block_tag in BLOCK_TAGS:
            count += len(elem.findall(".//%s" % block_tag))

        if elem.tag.lower() in BLOCK_TAGS:
            count += 1

        return count

    def detect_page_type(self):
        if self.special.get('page_type'):
            page_type = self.special.get('page_type')
        elif self.main_block is not None:
            if self.bbs_blocks:
                if len(self.bbs_blocks) >= self.BBS_PAGE_BLOCK_LIMIT:
                    block = self.bbs_blocks[self.BBS_PAGE_BLOCK_LIMIT - 1]
                else:
                    block = self.bbs_blocks[0]

                for a in self.tags(block, 'a'):
                    text = a.text and a.text.strip()
                    if text and len(text) < 10:
                        if text in (u'阅读', u'[阅读全文]'):
                            page_type = PAGE_TYPE.BBS_INDEX_PAGE
                            break
                        elif text in (u'回复', u'引用', u'发消息', u"回复本楼", u"回复本帖", u"回复楼主", u"使用道具卡", u"打赏", u"树型") or u"只看" in text:
                            page_type = PAGE_TYPE.BBS_DETAIL_PAGE
                            break
                else:
                    page_type = PAGE_TYPE.BBS_INDEX_PAGE
            else:
                if len(self.text_content()) >= self.MIN_TEXT_LENGTH:
                    page_type = PAGE_TYPE.NORMAL_DETAIL_PAGE
                else:
                    page_type = PAGE_TYPE.NORMAL_INDEX_PAGE

        else:
            page_type = PAGE_TYPE.JS_PAGE

        return page_type

    def score_paragraphs(self, html):
        if html is None:
            html = self.dom
        MIN_LEN = self.options.get(
            'min_text_length',
            self.TEXT_LENGTH_THRESHOLD)
        candidates = {}
        ordered = []
        for elem in self.tags(html, "p", "pre", "td", "span", "font"):
            parent_node = elem.getparent()
            if parent_node is None:
                continue
            grand_parent_node = parent_node.getparent()

            inner_text = elem.text_content() or ""
            inner_text_len = len(inner_text)

            # If this paragraph is less than 25 characters
            # don't even count it.
            if inner_text_len < MIN_LEN:
                continue

            if parent_node not in candidates:
                candidates[parent_node] = self.score_node(parent_node)
                ordered.append(parent_node)

            if grand_parent_node is not None and grand_parent_node not in candidates:
                candidates[grand_parent_node] = self.score_node(
                    grand_parent_node)
                ordered.append(grand_parent_node)

            content_score = 1
            content_score += len(inner_text.split(','))
            content_score += max((inner_text_len / 10), 3)
            #if elem not in candidates:
            #    candidates[elem] = self.score_node(elem)

            #WTF? candidates[elem]['content_score'] += content_score
            candidates[parent_node]['content_score'] += content_score
            if grand_parent_node is not None:
                candidates[grand_parent_node]['content_score'] += content_score / 2.0

        # Scale the final candidates score based on link density. Good content
        # should have a relatively small link density (5% or less) and be
        # mostly unaffected by this operation.
        for elem in ordered:
            candidate = candidates[elem]
            ld = self.get_link_density(elem)
            score = candidate['content_score']
            #self.debug("Candid: %6.3f %s link density %.3f -> %6.3f" % (
            #    score,
            #    describe(elem),
            #    ld,
            #    score * (1 - ld)))
            candidate['content_score'] *= (1 - ld)

        return candidates

    def class_weight(self, e):
        weight = 0
        if e.get('class', None):
            if REGEXES['negativeRe'].search(e.get('class')):
                weight -= 25

            if REGEXES['positiveRe'].search(e.get('class')):
                weight += 25

        if e.get('id', None):
            if REGEXES['negativeRe'].search(e.get('id')):
                weight -= 25

            if REGEXES['positiveRe'].search(e.get('id')):
                weight += 25

        return weight

    def score_node(self, elem):
        content_score = self.class_weight(elem)
        name = elem.tag.lower()
        if name == "div":
            content_score += 5
        elif name in ["pre", "td", "blockquote"]:
            content_score += 3
        elif name in ["address", "ol", "ul", "dl", "dd", "dt", "li", "form"]:
            content_score -= 3
        elif name in ["h1", "h2", "h3", "h4", "h5", "h6", "th"]:
            content_score -= 5
        return {
            'content_score': content_score,
            'elem': elem
        }

    def debug(self, *a):
        if self.options.get('debug', False):
            log.debug(*a)

    def remove_unlikely_candidates(self, html, script=True, display=True, candidate=True):
        if html is None:
            html = self.dom
        _kill = []
        for elem in html.iter():
            if not isinstance(elem, HtmlElement):
                _kill.append(elem)
            else:
                if script and elem.tag == 'script':
                    _kill.append(elem)

                if display:
                    style = (elem.get('style') or "").replace(' ', '')

                    if style and "display:none" in style and elem.tag.lower() != 'body':
                        _kill.append(elem)
                if candidate:
                    s = "%s %s" % (elem.get('class', ''), elem.get('id', ''))
                    if len(s) < 2:
                        continue

                    if REGEXES['unlikelyCandidatesRe'].search(s) and \
                            (not REGEXES['okMaybeItsACandidateRe'].search(s)) and elem.tag not in ['html', 'body']:
                        self.debug("Removing unlikely candidate - %s" % describe(elem))
                        _kill.append(elem)

        if _kill and _kill[0] == html:
            _kill.pop(0)

        _kill.reverse()  # start with innermost tags
        for elem in _kill:
            try:
                elem.drop_tree()
            except:
                pass

        return html

    def transform_misused_divs_into_paragraphs(self, doc):
        if doc is None:
            doc = self.dom
        for elem in self.tags(doc, 'div'):
            # transform <div>s that do not contain other block elements into
            # <p>s
            #FIXME: The current implementation ignores all descendants that
            # are not direct children of elem
            # This results in incorrect results in case there is an <img>
            # buried within an <a> for example
            if not REGEXES['divToPElementsRe'].search(
                    unicode(''.join(map(tostring, list(elem))))):
                #self.debug("Altering %s to p" % (describe(elem)))
                elem.tag = "p"
                #print "Fixed element "+describe(elem)
        for elem in self.tags(doc, 'div'):
            if elem.text and elem.text.strip():
                p = fragment_fromstring('<p/>')
                p.text = elem.text
                elem.text = None
                elem.insert(0, p)
                #print "Appended "+tounicode(p)+" to "+describe(elem)

            for pos, child in reversed(list(enumerate(elem))):
                if child.tail and child.tail.strip():
                    p = fragment_fromstring('<p/>')
                    p.text = child.tail
                    child.tail = None
                    elem.insert(pos + 1, p)
                    #print "Inserted "+tounicode(p)+" to "+describe(elem)
                if child.tag == 'br':
                    #print 'Dropped <br> at '+describe(elem)
                    child.drop_tree()

        return doc

    def tags(self, node, *tag_names):
        wrapper = fragment_fromstring('<wrapper/>')
        wrapper.append(node)
        for tag_name in tag_names:
            for e in wrapper.findall('.//%s' % tag_name):
                yield e

    def reverse_tags(self, node, *tag_names):
        for tag_name in tag_names:
            for e in reversed(node.findall('.//%s' % tag_name)):
                yield e

    def sanitize(self, node, candidates):
        MIN_LEN = self.options.get(
            'min_text_length',
            self.TEXT_LENGTH_THRESHOLD)
        for header in self.tags(node, "h1", "h2", "h3", "h4", "h5", "h6"):
            if self.class_weight(header) < 0 or self.get_link_density(header) > 0.33:
                header.drop_tree()

        allowed = {}
        # Conditionally clean <table>s, <ul>s, and <div>s
        for el in self.reverse_tags(node, "table", "ul", "div"):
            if el in allowed:
                continue
            weight = self.class_weight(el)
            if el in candidates:
                content_score = candidates[el]['content_score']
                #print '!',el, '-> %6.3f' % content_score
            else:
                content_score = 0
            tag = el.tag

            if weight + content_score < 0:
                self.debug(
                    "Cleaned %s with score %6.3f and weight %-3s" %
                    (describe(el), content_score, weight, ))
                el.drop_tree()
            elif el.text_content().count(",") < 10:
                counts = {}
                for kind in ['p', 'img', 'li', 'a', 'embed', 'input']:
                    counts[kind] = len(el.findall('.//%s' % kind))

                #counts["li"] -= 100

                # Count the text length excluding any surrounding whitespace
                content_length = text_length(el.text_content())
                link_density = self.get_link_density(el)
                parent_node = el.getparent()
                if parent_node is not None:
                    if parent_node in candidates:
                        content_score = candidates[parent_node]['content_score']
                    else:
                        content_score = 0
                #if parent_node is not None:
                    #pweight = self.class_weight(parent_node) + content_score
                    #pname = describe(parent_node)
                #else:
                    #pweight = 0
                    #pname = "no parent"
                to_remove = False
                reason = ""

                #if el.tag == 'div' and counts["img"] >= 1:
                #    continue
                #if counts["p"] and counts["img"] > counts["p"]:
                #    reason = "too many images (%s)" % counts["img"]
                #    to_remove = True
                if counts["li"] >= counts["p"]: # and tag != "ul" and tag != "ol":
                    reason = "more <li>s than <p>s"
                    to_remove = True
                elif counts["input"] > (counts["p"] / 2):
                    reason = "less than 3x <p>s than <input>s"
                    to_remove = True
                elif content_length < (MIN_LEN) and (counts["img"] == 0 or counts["img"] > 2):
                    reason = "too short content length %s without a single image" % content_length
                    to_remove = True
                elif weight < 25 and link_density > 0.3:
                    reason = "too many links %.3f for its weight %s" % (
                            link_density, weight)
                    to_remove = True
                elif weight >= 25 and link_density > 0.5:
                    reason = "too many links %.3f for its weight %s" % (
                        link_density, weight)
                    to_remove = True
                #elif (counts["embed"] == 1 and content_length < 75) or counts["embed"] > 1:
                elif counts["embed"] > 1 and content_length < 75:
                    reason = "<embed>s with too short content length, or too many <embed>s"
                    to_remove = True
#                if el.tag == 'div' and counts['img'] >= 1 and to_remove:
#                    imgs = el.findall('.//img')
#                    valid_img = False
#                    self.debug(tounicode(el))
#                    for img in imgs:
#
#                        height = img.get('height')
#                        text_length = img.get('text_length')
#                        self.debug ("height %s text_length %s" %(repr(height), repr(text_length)))
#                        if to_int(height) >= 100 or to_int(text_length) >= 100:
#                            valid_img = True
#                            self.debug("valid image" + tounicode(img))
#                            break
#                    if valid_img:
#                        to_remove = False
#                        self.debug("Allowing %s" %el.text_content())
#                        for desnode in self.tags(el, "table", "ul", "div"):
#                            allowed[desnode] = True

                    #find x non empty preceding and succeeding siblings
                else:
                    i, j = 0, 0
                    x = 1
                    siblings = []
                    for sib in el.itersiblings():
                        #self.debug(sib.text_content())
                        sib_content_length = text_length(sib.text_content())
                        if sib_content_length:
                            i += 1
                            siblings.append(sib_content_length)
                            #if i == x:
                            #    break
                    for sib in el.itersiblings(preceding=True):
                        #self.debug(sib.text_content())
                        sib_content_length = text_length(sib.text_content())
                        if sib_content_length:
                            j += 1
                            siblings.append(sib_content_length)
                            #if j == x:
                            #    break
                    #self.debug(str(siblings))
                    if siblings and sum(siblings) > 1000:
                        to_remove = False
                        self.debug("Allowing %s" % describe(el))
                        for desnode in self.tags(el, "table", "ul", "div"):
                            allowed[desnode] = True

                if to_remove:
                    self.debug(
                        "Cleaned %6.3f %s with weight %s cause it has %s." %
                        (content_score, describe(el), weight, reason))
                    #print tounicode(el)
                    #self.debug("pname %s pweight %.3f" %(pname, pweight))
                    el.drop_tree()

        for el in ([node] + [n for n in node.iter()]):
            if not self.options.get('attributes', None):
                #el.attrib = {} #FIXME:Checkout the effects of disabling this
                pass
        return node
        #self.trans_html = node
        #return self.get_clean_html(self.trans_html)


class HashableElement():
    def __init__(self, node):
        self.node = node
        self._path = None

    def _get_path(self):
        if self._path is None:
            reverse_path = []
            node = self.node
            while node is not None:
                node_id = (node.tag, tuple(node.attrib.items()), node.text)
                reverse_path.append(node_id)
                node = node.getparent()
            self._path = tuple(reverse_path)
        return self._path
    path = property(_get_path)

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        return self.path == other.path

    def __getattr__(self, tag):
        return getattr(self.node, tag)


def get_max_interval(iteror):
    iteror = iter(iteror)
    max_interval = 0
    start = next(iteror)
    for index in iteror:
        interval = index - start
        if interval > max_interval:
            max_interval = interval
        start = index
    return max_interval
# http://auto.china.com/dongtai/jj/11031465/20130930/18072729.html


def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog: [options] [file]")
    parser.add_option('-v', '--verbose', action='store_true')
    parser.add_option('-u', '--url', default=None, help="use URL instead of a local file")
    (options, args) = parser.parse_args()

    if not (len(args) == 1 or options.url):
        parser.print_help()
        sys.exit(1)

    file = None
    if options.url:
        import urllib
        file = urllib.urlopen(options.url)
    else:
        file = open(args[0], 'rt')
    enc = sys.__stdout__.encoding or 'utf-8'
    try:
        print Document(
            file.read(), debug=options.verbose,
            url=options.url).summary().encode(enc, 'replace')
    finally:
        file.close()


def search(date_str):
    for regex in DATE_REGEX:
        match = regex.search(date_str)
        if match:
            print match.groupdict()

if __name__ == '__main__':
    main()
