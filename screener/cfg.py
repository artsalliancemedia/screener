'''
# Settings for the Screener server
[server]
# leave blank for all hostnames
host=
port=9500


# Settings for the FTP server hosting the DCPs
[ftp]
host=
port=21
username=
password=

'''

import ConfigParser

config = ConfigParser.ConfigParser()
config.read('screener.cfg')

screener_host = config.get('server','host')
screener_port = config.getint('server','port')
ftp_host = config.get('ftp','host')
ftp_username = config.get('ftp','username')
ftp_password = config.get('ftp','password')

