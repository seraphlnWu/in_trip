#coding=utf-8

import os

from buzz.lib.config import Config
from buzz.lib.utils import parse_args

def main():
    args = parse_args()

    config_file = getattr(args, 'config')
    section = getattr(args, 'section') or "timer"
    if config_file:
        if config_file[0] != '/':
            config_file = os.path.join(os.getcwd(), os.path.abspath(config_file))

    Config.ACTUAL_CONFIG_FILE = config_file
    Config.SECTION_NAME = section
    from buzz.lib.timer import Timer
    Timer(Config()).run()

if __name__ == '__main__':
    main()
