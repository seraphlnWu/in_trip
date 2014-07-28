# coding:utf-8

import re
import logging
import datetime

import lxml.html
from lxml.html import tostring
from .cleaners import normalize_spaces, clean_attributes, html_cleaner

logging.getLogger().setLevel(logging.DEBUG)

utf8_parser = lxml.html.HTMLParser(encoding='utf-8')


def build_dom(utf8_source):
    doc = lxml.html.document_fromstring(utf8_source, parser=utf8_parser)
    doc = html_cleaner.clean_html(doc)
    return doc


def js_re(src, pattern, flags, repl):
    return re.compile(pattern, flags).sub(src, repl.replace('$', '\\'))


def normalize_entities(cur_title):
    entities = {
        u'\u2014': '-',
        u'\u2013': '-',
        u'&mdash;': '-',
        u'&ndash;': '-',
        u'\u00A0': ' ',
        u'\u00AB': '"',
        u'\u00BB': '"',
        u'&quot;': '"',
    }
    for c, r in entities.iteritems():
        if c in cur_title:
            cur_title = cur_title.replace(c, r)
    return cur_title


def norm_title(title):
    return normalize_entities(normalize_spaces(title))


def get_title(doc):
    title = doc.find('.//title')
    if title is None or not title.text:
        return u'[no-title]'

    return norm_title(title.text)


def add_match(collection, text, orig):
    text = norm_title(text)
    if len(text) >= 5:
        if text.replace('"', '') in orig.replace('"', ''):
            collection.add(text)


def shorten_title(doc):
    title = doc.find('.//title')
    if title is not None and title.text:
        orig = title.text.strip()
        for delimiter in ['|', ' - ', ' :: ', ' / ', '_']:
            if delimiter in orig:
                parts = orig.split(delimiter)
                orig = parts[0]
                break
    else:
        orig = u""

    candidates = []
    for item in ['.//h1', './/h2', './/h3']:
        for e in list(doc.iterfind(item)):
            text = e.text_content().strip()  # http://www.xincheping.com/ExpertsBuy/11298/1.htm
            if text and (5 < len(text) <= 45):
                candidates.append(text)

        # if candidates: # http://blog.sina.com.cn/s/blog_d8f05d950101hi9a.html
        #    break

    for item in ['#title', '#head', '#heading', '#thread_subject', '.pageTitle', '.news_title', '.title', '.head', '.heading', '.contentheading', '.small_header_red', '#ArticleTit', '.artTitle']:
        for e in doc.cssselect(item):
            text = e.text_content().strip()
            if text and (5 < len(text) <= 45):
                candidates.append(text)

    if candidates:
        candidates = sorted(candidates, key=len, reverse=True)
        if orig:
            title = candidates[0]
            for candidate in candidates:
                if candidate in orig or orig in candidate:
                    title = candidate
                    break
        else:
            title = candidates[0]

    elif orig:
        title = orig
    else:
        title = u'[no-title]'

    return norm_title(title)


def get_body(doc):
    [elem.drop_tree() for elem in doc.xpath('.//script | .//link | .//style')]
    raw_html = unicode(tostring(doc.body or doc))
    cleaned = clean_attributes(raw_html)
    try:
        # BeautifulSoup(cleaned) #FIXME do we really need to try loading it?
        return cleaned
    except Exception:  # FIXME find the equivalent lxml error
        logging.error("cleansing broke html content: %s\n---------\n%s" % (raw_html, cleaned))
        return raw_html


def remove_ctrl_char(origin_str):
    # ctr_chars = [u'\x%02d' % i for i in range(0, 32)]
    ctr_chars = [u'\u0000', u'\u0001', u'\u0002', u'\u0003', u'\u0004', u'\u0005', u'\u0006', u'\u0007', u'\u0008', u'\u0009',
                 u'\u000a', u'\u000b', u'\u000c', u'\u000d', u'\u000e', u'\u000f', u'\u0010', u'\u0011', u'\u0012', u'\u0013',
                 u'\u0014', u'\u0015', u'\u0016', u'\u0017', u'\u0018', u'\u0019', u'\u001a', u'\u001b', u'\u001c', u'\u001d',
                 u'\u001e', u'\u001f']
    if not isinstance(origin_str, unicode):
        origin_str = unicode(origin_str)

    regex = re.compile(u'|'.join(ctr_chars))
    return regex.subn(u'', origin_str)[0]


def describe(node, depth=1):
    if not hasattr(node, 'tag'):
        return "[%s]" % type(node)
    name = node.tag
    if node.get('id', ''):
        name += '#' + node.get('id')
    if node.get('class', ''):
        name += '.' + node.get('class').replace(' ', '.')
    if name[:4] in ['div#', 'div.']:
        name = name[3:]
    if depth and node.getparent() is not None:
        return name + ' - ' + describe(node.getparent(), depth - 1)
    return name


def to_int(x):
    if not x:
        return None
    x = x.strip()
    if x.endswith('px'):
        return int(x[:-2])
    if x.endswith('em'):
        return int(x[:-2]) * 12
    return int(x)


def clean(text):
    text = re.sub('\s*\n\s*', '\n', text)
    text = re.sub('[ \t]{2,}', ' ', text)
    return text.strip()


def text_length(i):
    """remove space
    """
    return len(i.replace(' ', ''))


class Unparseable(ValueError):
    pass


def to_legal_datetime(match):
    date_kwargs = {}
    text = ''
    for key, value in match.groupdict().items():
        if key == 'text':
            text = value
        else:
            if value:
                date_kwargs[key] = int(value)

    now = datetime.datetime.now()
    if len(date_kwargs) == 1:
        if 'months' in date_kwargs:
            return now.replace(month=abs((now.month - date_kwargs['months']) % 12), microsecond=0)
        else:
            return now.replace(microsecond=0) - datetime.timedelta(**date_kwargs)
    elif len(date_kwargs) == 3 and 'month' not in date_kwargs:
        date_kwargs['year'] = now.year
        date_kwargs['month'] = now.month
    elif text == u'今天':
        result = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if len(date_kwargs):
            result += datetime.timedelta(**date_kwargs)
        return result

    elif text == u'昨天':
        result = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)
        if len(date_kwargs):
            result += datetime.timedelta(**date_kwargs)
        return result

    elif 'year' not in date_kwargs:
        date_kwargs['year'] = now.year
    elif date_kwargs['year'] < 100:  # two digit year
        date_kwargs['year'] += 2000

    try:
        result = datetime.datetime(**date_kwargs)
        if result > datetime.datetime.now():
            return None
    except ValueError:
        return None

    return result

SPACE_REGEX = re.compile(u"(\s|\xa0)+", re.U)
def remove_space(text):
    return SPACE_REGEX.subn(' ', text)[0]
