from ftplib import FTP
import os, time, logging
from math import floor
from datetime import datetime

import Queue

from smpteparsers.dcp import DCP


def process_ingest_queue(queue, content_store, interval=1):
    logging.info('Starting ingest queue processing thread.')
    while 1:
        if not queue.empty():
            item = queue.get()

            logging.info('Downloading "{0}" from the ingest queue'.format(item['dcp_path']))
            with DCPDownloader(item['ftp_details']) as dcp_downloader:
                local_dcp_path = dcp_downloader.download(item['dcp_path'])

            logging.info('Parsing DCP "{0}"'.format(local_dcp_path))
            dcp = DCP(local_dcp_path)

            queue.task_done()

        time.sleep(interval)

class DCPDownloader(object):
    def __init__(self, ftp_details):
        self.ftp_details = ftp_details

    def __enter__(self):
        logging.info('Connecting to FTP')
        
        ftp_mode = True if self.ftp_details['mode'] == 'passive' else False

        self.ftp = FTP()
        self.ftp.set_pasv(ftp_mode)
        self.ftp.connect(host=self.ftp_details['host'], port=(self.ftp_details['port'] or 21))

        if 'user' in self.ftp_details or 'passwd' in self.ftp_details:
            self.ftp.login(user=self.ftp_details['user'], passwd=self.ftp_details['passwd'])

        return self

    def __exit__(self, *args):
        self.ftp.quit()

    def download(self, path):
        local_path = ensure_local_path(path)

        # Work out what we're dealing with, store this info on the object itself for easy access :)
        items, total_size = self.get_folder_info(self.ftp, path)
        print items, total_size

#         self.ftp.cwd(path)
        # @todo: Finish off downloading the DCP files and storing them locally.

        to_parent_dir(self.ftp, path)

        print "Finished getting folder info.\nCurrent path on ftp server: {0}".format(self.ftp.pwd())
        
        return local_path

    def get_folder_info(self, ftp, path):
        """
        Recursively aggregate the DCP folder contents so we know what we're dealing with.
        """
        print path
#         ftp.cwd(path)

        # Not particularly happy about having to do it this way (saving to the object), but it'll work for now.
        self.items = []
        self.total_size = 0
        queue = Queue.Queue()

        def process_line(line):
            parts = line.split()
            print parts
 
            if parts[0][0] == 'd': # Checks the permission signature :)
                # Must be a directory, lets recurse.
                print "Found a directory: {0}".format(parts[8])
                queue.put(parts[8])
#                 ftp.retrlines('LIST', process_line)
#                 to_parent_dir(ftp, path)
#                 items, total_size = self.get_folder_info(ftp, parts[8])
#                 self.items.extend(items)
#                 self.total_size += total_size
            else:
                self.items.append(parts[8])
                self.total_size += int(parts[4])

        queue.put(path)
        while not queue.empty():
            p = queue.get()
            # print "p: {0}".format(p)
            ftp.cwd(p)
            ftp.retrlines('LIST', process_line)
            
        to_parent_dir(ftp, path)
        
        # print "RETURNING items: {items}\nTotal size: {total}".format(items=self.items, total=self.total_size)

        # print "current path: {0}".format(ftp.pwd())

        return self.items, self.total_size

# Some util functions.

def ensure_local_path(remote_path):
    # Just in case this is the first run, make sure we have the parent directory as well.
    dcp_store = os.path.join(os.path.dirname(__file__), u'dcp_store') ### TODO, make dcp_store configurable
    if not os.path.isdir(dcp_store):
        os.mkdir(dcp_store)

    local_path = os.path.join(dcp_store, remote_path)
    if not os.path.isdir(local_path):
        os.mkdir(local_path) # Ensure we have a directory to download to.

    return local_path

def to_parent_dir(ftp, path):
    for directory in path.split('/'):
        ftp.cwd('..') # Go back to where we started from so we don't get ourselves into a hole.

# Some functions to download files from the DCP FTP

def download_text(ftp, dcp, filename):
    '''Downloads text files from an FTP to the DCP directory.
    Uses write_download to keep track of how much has been downloaded.'''
    with open(os.path.join(dcp.dir, filename), 'w') as f:
        ftp.retrlines('RETR {0}'.format(filename), write_download(dcp, f))

    # @todo: Emit event that download is complete

def download_bin(ftp, dcp, filename):
    '''Downloads binary files from an FTP to the DCP directory but writes them to /dev/null (or NULL on win32).
    Uses write_download to keep track of how much has been downloaded.'''
    # pipe data to /dev/null
    with open(os.devnull, 'wb') as f:
        ftp.retrbinary('RETR {0}'.format(filename), write_download(dcp, f))

    # Write a dummy placeholder file
    with open(os.path.join(dcp.dir, filename), 'w') as f:
        f.write('Dummy placeholder')

    # @todo: Emit event that download is complete

def write_download(dcp, f):
    '''
    Provides a function for FTP.retrlines/retrbinary to call when processing a chunk. It uses the DCP's downloaded
    counter to keep track of how much of the DCP has been downloaded, alerting TMS of progress.
    '''
    def write_chunk(chunk, dcp=dcp, f=f):
        f.write(chunk)
        dcp.downloaded += len(chunk)
        old_progress = dcp.progress
        dcp.progress = float(dcp.downloaded) / dcp.total_size

        # has the downloaded chuck caused the size downloaded to tick over a 1% threshold?
        if floor(100 * dcp.progress) - floor(100 * old_progress) > 0:
            # @todo: Emit event with progress made
            logging.info('{0:.0%}'.format(dcp.progress))

    return write_chunk
