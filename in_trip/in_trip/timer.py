#coding=utf-8
'''
timer app;
used to scheduler tasks;
'''

import sys
from os import getcwd

from os.path import realpath, dirname, abspath, join
sys.path.insert(
    0,
    realpath(join(dirname(__file__), '../'))
)


from in_trip.lib.config import Config
from in_trip.lib.utils import parse_args
from in_trip.lib.timer import Timer

def main():
    '''main loop of timer'''
    args = parse_args()

    config_file = getattr(args, 'config')
    section = getattr(args, 'section') or "timer"
    if config_file:
        if config_file[0] != '/':
            config_file = join(getcwd(), abspath(config_file))

    Config.ACTUAL_CONFIG_FILE = config_file
    Config.SECTION_NAME = section
    Timer(Config()).run()

if __name__ == '__main__':
    main()
