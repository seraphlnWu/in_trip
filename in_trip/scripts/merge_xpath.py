#coding=utf-8

import re

from buzz.lib.http import get_domain
from buzz.lib.store import mongo, get_mongo_connection
from admin.config.consts import XPATH_STATUS

from admin.model.site import *
from admin.model import get_inc_id
from admin.lib.url_regex import regex_decoder, check_url_regex

def main():
    db_tmp = get_mongo_connection(db_name="buzz_test")
    print db.name, db.host
    print db_tmp.name, db_tmp.host
    for xpath in db_tmp.xpath.find({'status': {'$ne': XPATH_STATUS.DELETE}}):
        print xpath['eg'][0]
        new_id = get_inc_id(db.xpath)
        xpath['_id'] = new_id
        domain = get_domain(xpath['eg'][0])
        site = get_site_by_domain(domain)
        if 'url_reg' in xpath:
            url_regex = xpath.pop('url_reg')
            print url_regex
        continue
        if not site:
            _id = get_inc_id(db.site)
            site = {'_id': _id, 'domain': domain, 'site_name': u"", 'url': xpath['eg'][0], 'status': 0}
            #db.site.insert(site)

        xpath['site_id'] = site['_id']
        insert = True
        for row in db.url_regex.find({'site_id': site['_id'], 'status': 0}):
            url_regex = re.compile(regex_decoder(row['url_reg']))
            if url_regex.match(xpath['eg'][0]):
                yes = raw_input('insert, default y?:\033[0m') or 'y'
                if yes != 'y':
                    insert = False

        if insert:
            pass
            #db.xpath.insert(xpath)

if __name__ == '__main__':
    main()
