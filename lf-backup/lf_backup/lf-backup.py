#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
#  backing up large files 

from lffunc import *
import sys, os, getpass, argparse, logging, json, functools, tempfile
from swiftclient.service import SwiftService

#constants
__app__ = "lf-backup"
__author__ = "?"
__company__ = "Fred Hutch, Seattle"

USERNAME = getpass.getuser()
OS = sys.platform

#variables
_default_global_options = {}

logger = logging.getLogger('SWG')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(os.path.join(tempfile.gettempdir(),"SwiftClientGUI.debug.txt"))
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.info('username: %s  temp: %s' % (USERNAME, tempfile.gettempdir()))

### main entry point 

def main():
    """ main entry point """
    moin()

def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='lf-backup ',
        description='a tool for backing up large files ' + \
            '(tar.gz, zip, etc)')
    parser.add_argument( '--debug', '-g', dest='debug', action='store_true', default=False,
        help="verbose output for all commands")
    parser.add_argument('--mailto', '-e', dest='mailto', action='store', default='', 
        help='send to this email address to notify of a new deployment.')

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    try:
        main()
    except KeyboardInterrupt:
        print('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
