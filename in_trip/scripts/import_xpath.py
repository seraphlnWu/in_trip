#coding=utf-8


from buzz.lib.store import mongo
from buzz.lib.http import get_domain

from admin.model.site import *
from admin.model import get_inc_id
from admin.lib.url_regex import regex_decoder

def main():
    rule = db.rule_new.find_one()
    for url_regex in rule['rules']:
        if regex_decoder(url_regex) == '^bbs\.auto\.ifeng\.com\/thread.*html':
            continue
        print "\033[91m" + regex_decoder(url_regex),
        yes = raw_input('default y:\033[0m') or 'y'
        if yes == 'y':
            domain = get_domain(rule['rules'][url_regex]['eg'][0])
            site = get_site_by_domain(domain)
            if not site:
                _id = get_inc_id(db.site)
                site = {'_id': _id, 'domain': domain, 'site_name': u"", 'url': rule['rules'][url_regex]['eg'][0], 'status': 0}
                db.site.insert(site)

            xpath_id =  get_inc_id(db.xpath)
            url_regex_id = get_inc_id(db.url_regex)

            xpath = {'_id': xpath_id, 'xpath': rule['rules'][url_regex]['xpath'], 'prop': rule['rules'][url_regex]['prop'], 'site_id': site['_id'], 'status': 0, 'eg': rule['rules'][url_regex]['eg'], 'url_regex_id': [url_regex_id, ]}
            db.xpath.insert(xpath)

            url_regex = {'_id': url_regex_id, 'status': 0, 'url_reg': url_regex, 'site_id': site['_id'], 'xpath_ids': [xpath_id, ]}
            db.url_regex.insert(url_regex)

if __name__ == '__main__':
    main()
