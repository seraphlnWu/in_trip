#coding=utf-8

import os

from buzz.lib.arbiter import Arbiter
from buzz.lib.utils import parse_args

SPIDER = "buzz.lib.http:WebClient"

def main():
    args = parse_args()

    config_file = getattr(args, 'config')
    section = getattr(args, 'section') or "spider"
    if config_file:
        if config_file[0] != '/':
            config_file = os.path.join(os.getcwd(), os.path.abspath(config_file))

    Arbiter(SPIDER, config_file, section).run()

if __name__ == '__main__':
    main()
