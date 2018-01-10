import logging
import os

import config_parser

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

DB_CONFIG_PATH = "dbconfig.json"

dbconf = None
try:
    dbconf = config_parser.parse(os.path.join(__location__, DB_CONFIG_PATH))
except IOError, FileNotFoundError:
    logging.warning("Missing database configuration ({0})".format(DB_CONFIG_PATH))
