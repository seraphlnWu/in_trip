#coding=utf-8

'''
engine app;
to start the spider;
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

ENGINE = "in_trip.lib.engine:Engine"

def main():
    ''' main loop of engine '''
    args = parse_args()

    config_file = getattr(args, 'config')
    section = getattr(args, 'section') or "engine"
    if config_file:
        if config_file[0] != '/':
            config_file = join(getcwd(), abspath(config_file))

    Arbiter(ENGINE, config_file, section).run()

if __name__ == '__main__':
    main()
