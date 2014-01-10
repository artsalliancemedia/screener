'''
Settings for Screener
'''

import ConfigParser

config = ConfigParser.ConfigParser()
config.read('screener.cfg')

screener_host = config.get('server','host')
screener_port = config.getint('server','port')
