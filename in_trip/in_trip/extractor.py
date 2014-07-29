#coding=utf-8

import os

from in_trip.lib.arbiter import Arbiter
from in_trip.lib.utils import parse_args

EXTRACTOR = "buzz.lib.extractor:Extractor"

def main():
    args = parse_args()
    config_file = getattr(args, 'config')
    section = getattr(args, 'section') or "extractor"
    if config_file:
        if config_file[0] != '/':
            config_file = os.path.join(os.getcwd(), os.path.abspath(config_file))

    Arbiter(EXTRACTOR, config_file, section).run()

if __name__ == '__main__':
    main()
