import argparse
from tbot.utils.config_parser import ConfigParser
from broker import Broker
import logging
import sys
import time

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Constants config_file=None
SETTINGS_FILE = './settings.yaml'

# command line argument handler
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--settings", help="pass in a tbot settings yaml")
args = parser.parse_args()

# set up based on config file
config_parser = ConfigParser(SETTINGS_FILE)
config = config_parser.init_config()

broker = Broker(config['strategies'])
broker.broker()
