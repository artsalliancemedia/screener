from ftplib import FTP
import os, time, logging
from math import floor
from datetime import datetime
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import Queue

from smpteparsers.dcp import DCP

from lib.util import INGESTING, INGESTED, CANCELLED

def process_ingest_queue(queue, content_store, interval=1):
    logging.info('Starting ingest queue processing thread.')
    while 1:
        if not queue.empty():

            item = queue.get()
            ingest_uuid = item[0]

            dcp_path = item[1]['dcp_path']

            content_store.update_ingest_history(ingest_uuid, INGESTING)

            logging.info('Downloading "{0}" from the ingest queue'.format(dcp_path))
            with DCPDownloader(item[1]['ftp_details']) as dcp_downloader:
                local_dcp_path = dcp_downloader.download(dcp_path)

            logging.info('Parsing DCP "{0}"'.format(local_dcp_path))
            dcp = DCP(local_dcp_path)

            # Add all CPLs to content store
            for cpl in dcp.cpls.itervalues():
                content_store.content[cpl.cpl_uuid] = cpl
            
            content_store.update_ingest_history(ingest_uuid, INGESTED)

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

        local_paths = []
        server_paths = []

        progress_tracker = {
                "downloaded" : 0,
                "total_size" : total_size,
                "progress" : 0
                }

        for item in items:
            path_parts = item.split("/")
            localfilepath = "\\".join(path_parts[2:])
            local_paths.append(localfilepath)

            server_paths.append(item)

        to_parent_dir(self.ftp, path)

        """
        Code which calls functions to download files from the ftp server.
        This can be commented out when testing if the files have already been
        downloaded.
        """
        for local, server in zip(local_paths, server_paths):
            if '\\' in local:
                rightmost_slash = local.rfind("\\")
                directory_path = local[:rightmost_slash+1]
                print "directory_path: {0}".format(directory_path)
                if not os.path.isdir(os.path.join(local_path, directory_path)):
                    create_directories(local_path, local)
            if local.endswith('.mxf'): #binary file
                download_bin(self.ftp, progress_tracker, local_path, local, server)
            else:
                download_text(self.ftp, progress_tracker, local_path, local, server)

        logging.info("Finished getting folder info.")
        
        return local_path

    def get_folder_info(self, ftp, path):
        """
        Aggregate the DCP folder contents so we know what we're dealing with.
        """

        # Not particularly happy about having to do it this way (saving to the object), but it'll work for now.
        self.items = []
        self.total_size = 0
        queue = Queue.Queue()

        def process_line(line):
            parts = line.split()
 
            if parts[0][0] == 'd': # Checks the permission signature :)
                queue.put(parts[8])
            else:
                self.items.append("{path}{filename}".format(path=current_path,
                    filename=parts[8]))
                self.total_size += int(parts[4])

        queue.put(path)
        current_path = ftp.pwd()
        while not queue.empty():
            p = queue.get()
            ftp.cwd(p)
            current_path = "{directory}{slash}".format(directory=ftp.pwd(),
                    slash="/")
            ftp.retrlines('LIST', process_line)
            
        to_parent_dir(ftp, path)
        
        return self.items, self.total_size

# Some util functions.

def ensure_local_path(remote_path):
    # Just in case this is the first run, make sure we have the parent directory as well.
    # TODO, make dcp_store configurable
    dcp_store = os.path.join(os.path.dirname(__file__), u'ASSET') 
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

def create_directories(local_path, localname):
    parts = localname.split("\\")
    path = ""
    for part in parts[:-1]:
        path += part
        path += "\\"
        if not os.path.isdir(os.path.join(local_path, path)):
            logging.info("Creating dir: {0}".format(os.path.join(local_path, path)))
            os.mkdir(os.path.join(local_path, path))

def download_text(ftp, progress_tracker, local_path, localname, servername):
    '''Downloads text files from an FTP to the DCP directory.
    Uses write_download to keep track of how much has been downloaded.'''
    with open(os.path.join(local_path, localname), 'w') as f:
        logging.info("Starting download: {0}".format(servername))
        ftp.retrbinary('RETR {0}'.format(servername),
                write_download(progress_tracker, f))

    logging.info("Download of {0} complete.".format(servername))

def download_bin(ftp, progress_tracker, local_path, localname, servername):
    '''Downloads binary files from an FTP to the DCP directory but writes them to /dev/null (or NULL on win32).
    Uses write_download to keep track of how much has been downloaded.'''
    # pipe data to /dev/null
    
    with open(os.devnull, 'wb') as f:
        logging.info("Starting download: {0}".format(servername))
        ftp.retrbinary('RETR {0}'.format(servername),
                write_download(progress_tracker, f))

    # Write a dummy placeholder file
    with open(os.path.join(local_path, localname), 'w') as f:
        f.write('Dummy placeholder')

    logging.info("Download of {0} complete.".format(servername))

def write_download(progress_tracker, f):
    '''
    Provides a function for FTP.retrlines/retrbinary to call when processing a chunk. It uses the DCP's downloaded
    counter to keep track of how much of the DCP has been downloaded, alerting TMS of progress.
    '''
    def write_chunk(chunk, progress_tracker=progress_tracker, f=f):
        f.write(chunk)
        progress_tracker["downloaded"] += len(chunk)
        old_progress = progress_tracker["progress"]
        progress_tracker["progress"] = float(progress_tracker["downloaded"]) / progress_tracker["total_size"]

        if floor(100 * progress_tracker["progress"]) - floor(100 * old_progress) > 0:
            logging.info('Download progress: {0:.0%}'.format(progress_tracker["progress"]))

    return write_chunk
