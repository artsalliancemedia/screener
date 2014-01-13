#!/usr/bin/evn python
#
# Configuration options for Screener

import logging, os.path

from screener.lib import config as c

config_file = c.OptionStr('app', 'config_file', os.path.join(os.path.dirname(__file__), 'screener.cfg'), False, False)
screener_host = c.OptionStr('app', 'host', '0.0.0.0', description='The listen address for Screener. It will listen on all available network addresses if set to 0.0.0.0')
screener_port = c.OptionNum('app', 'port', 9500, description='The port that the Screener socket listens on.')
