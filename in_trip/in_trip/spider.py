#coding=utf-8

'''
spider app;
to start spiders clients;
'''

import sys
from os import getcwd

from os.path import realpath, dirname, abspath, join
sys.path.insert(
    0,
    realpath(join(dirname(__file__), '../'))
)


from in_trip.lib.arbiter import Arbiter
from in_trip.lib.utils import parse_args

SPIDER = "in_trip.lib.http:WebClient"

def main():
    ''' main loop of spider '''
    args = parse_args()

    config_file = getattr(args, 'config')
    section = getattr(args, 'section') or "spider"
    if config_file:
        if config_file[0] != '/':
            config_file = join(getcwd(), abspath(config_file))

    Arbiter(SPIDER, config_file, section).run()

if __name__ == '__main__':
    main()
