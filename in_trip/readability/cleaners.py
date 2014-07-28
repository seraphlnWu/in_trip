# strip out a set of nuisance html attributes that can mess up rendering in RSS feeds
import re
from lxml.html.clean import Cleaner

bad_attrs = ['width', 'height', 'style', '[-a-z]*color', 'background[-a-z]*', 'on*']
single_quoted = "'[^']+'"
double_quoted = '"[^"]+"'
non_space = '[^ "\'>]+'
htmlstrip = re.compile("<" # open
    "([^>]+) " # prefix
    "(?:%s) *" % ('|'.join(bad_attrs),) + # undesirable attributes
    '= *(?:%s|%s|%s)' % (non_space, single_quoted, double_quoted) + # value
    "([^>]*)"  # postfix
    ">"        # end
, re.I)

def clean_attributes(html):
    while htmlstrip.search(html):
        html = htmlstrip.sub('<\\1\\2>', html)
    return html

def normalize_spaces(s):
    if not s: return ''
    """replace any sequence of whitespace
    characters with a single space"""
    return ' '.join(s.split())

html_cleaner = Cleaner(scripts=False, javascript=False, comments=True,
    style=False, links=True, meta=False, add_nofollow=False, page_structure=False,
    processing_instructions=True, embedded=False,
    frames=True, forms=False, annoying_tags=False, remove_tags=['wbr', ],
    remove_unknown_tags=False, safe_attrs_only=False, kill_tags=['select', 'style'])
