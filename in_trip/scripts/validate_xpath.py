#coding=utf-8
import sys
import urlparse

from buzz.utils import feed_db
from buzz.lib.http import get_domain, curl
from admin.lib.url_regex import regex_decoder, regex_match
from readability.readability import build_doc
from admin.lib.store import db
from admin.config.consts import RECORD_STATUS
from admin.lib.xpath import _validate

def main():
    feeds = feed_db.get_feeds()   
    feed_urls = []
    cache = {}
    for feed in feeds:
        if 'domain' in feed:
            feed_urls.append('http://' + feed['domain'])
    regex_url_map = {}
    for feed_url in feed_urls:
        print feed_url,
        #if get_matched_regex(feed_url):
        #    print >> sys.stderr, 'Unmatched URL: ' + feed_url
        parse_result = urlparse.urlparse(feed_url)
        prefix = parse_result.scheme + '://' + parse_result.netloc
        site_domain = get_domain(feed_url)
        same_domain_urls = set()
        content, _ = curl(feed_url)
        if content:
            doc = build_doc(content)
            for node in doc.findall('.//a'):
                href = node.get('href')
                if not href:
                    continue
                if href.startswith('/'):
                    base = doc.find('.//base')
                    if base and base.get('href'):
                        href = base.get('href') + href.encode('utf-8')
                    else:
                        href = prefix + href 
                    same_domain_urls.add(href)
                elif href.startswith('.'):
                    print >> sys.stderr, "Bad URL:" + href.encode('utf-8')
                elif get_domain(href) == site_domain:
                    same_domain_urls.add(href)
        else:
            # log error feed
            print >> sys.stderr, "FEED ERROR:" + feed_url

        for url in same_domain_urls:
            regex, xpath_ids = get_matched_regex(url)
            if regex and xpath_ids:
                xpaths = []
                for xpath_id in xpath_ids:
                    if xpath_id in cache:
                        xpath = cache[xpath_id]
                    else:
                        xpath = db.xpath.find_one({'_id': xpath_id})
                        cache[xpath['_id']] = xpath
                    xpaths.append(xpath)

                if regex in regex_url_map:
                    regex_url_map[regex]['urls'].append(url)
                else:
                    regex_url_map[regex] = {'urls': [url, ], 'xpaths': xpaths} 
            else:
                print >> sys.stderr, "Unmatched URL:" + url.encode('utf-8')

    for regex in regex_url_map:
        urls = regex_url_map[regex]['urls']
        if not urls:
            continue
        xpaths = regex_url_map[regex]['xpaths']
        #for url in urls:
        for i in range(0, 6):
            status = False
            for xpath in xpaths:
                xpath['eg'] = urls[i:i+1]
                if not xpath['eg']:
                    continue
                status, result = _validate(xpath)
                if status:
                    break
            if not status and len(urls) > i:
                print >> sys.stderr, "Extrace ERROR URL:" + urls[i]


REGEX = [] 

def get_matched_regex(url):
    if not REGEX:
        for regex in db.url_regex.find({'status': RECORD_STATUS.NORMAL}):
            if 'xpath_ids' not in regex or not regex['xpath_ids']:
                continue
            REGEX.append(
                    (
                        regex_decoder(regex['url_reg']), 
                        [regex_decoder(white_reg) for white_reg in regex.get('white_reg_list', [])], 
                        [regex_decoder(black_reg) for black_reg in regex.get('black_reg_list', [])], 
                        regex['xpath_ids']
                    )
                ) 

    for i, regex in enumerate(REGEX):
        if regex_match(url, regex[0], regex[1], regex[2]):
            return regex[0], regex[3]

    return None, None


if __name__ == '__main__':
    main()

