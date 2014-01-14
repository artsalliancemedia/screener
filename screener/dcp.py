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

        print "\nDownload path: {0}\n".format(path)

        # Work out what we're dealing with, store this info on the object itself for easy access :)
        items, total_size = self.get_folder_info(self.ftp, path)
        print "Files:"
        for item in items:
            print item
        print "Total size: {0}".format(total_size)

#         self.ftp.cwd(path)
        # @todo: Finish off downloading the DCP files and storing them locally.

        print "\nLocal file path: {0}\n".format(local_path)

        local_paths = []
        server_paths = []

        progress_tracker = {
                "downloaded" : 0,
                "total_size" : total_size,
                "progress" : 0
                }

        print "Progress tracker:\n{0}".format(progress_tracker)

        for item in items:
            # local path stuff
            path_parts = item.split("/")
            localfilepath = "\\".join(path_parts[2:])
            local_paths.append(localfilepath)

            #server path stuff
            server_paths.append(item)

        to_parent_dir(self.ftp, path)

        for local, server in zip(local_paths, server_paths):
            if '\\' in local:
                check_directories_exist(local_path, local)
            if local[-4:] == '.mxf': #binary file
                print "{0} - binary".format(local)
                download_bin(self.ftp, progress_tracker, local_path, local, server)
            else:
                print "{0} - text".format(local)
                download_text(self.ftp, progress_tracker, local_path, local, server)

        """
        print "LOCAL FILE PATHS:"
        for item in items:
            # print "{0}{1}".format(local_path, item).replace("/", "\\")
            print item[-4:]
            path_parts = item.split("/")
            localfilepath = "\\".join(path_parts[2:])
            print localfilepath

        print "SERVER FILE PATHS:"
        for item in items:
            print item

        print "DOWNLOADING TEST"
        for item in items:
            path_parts = item.split("/")
            localfilepath = "\\".join(path_parts[2:])
            serverpath = item
            print "\ndownloading {0}\nto\n{1}\n".format(serverpath,
                    localfilepath)
        """

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
                self.items.append("{path}{filename}".format(path=current_path,
                    filename=parts[8]))
                self.total_size += int(parts[4])

        queue.put(path)
        current_path = ftp.pwd()
        print "CURRENT PATH: {0}".format(current_path)
        while not queue.empty():
            p = queue.get()
            # print "p: {0}".format(p)
            ftp.cwd(p)
            current_path = "{directory}{slash}".format(directory=ftp.pwd(),
                    slash="/")
            # replace forward slashes with backward slashes for Windows paths
            # current_path = current_path.replace("/", "\\")
            print "CURRENT PATH: {0}".format(current_path)
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

def check_directories_exist(local_path, localname):
    parts = localname.split("\\")
    path = ""
    for part in parts[:-1]:
        path += part
        path += "\\"
        print "Checking directory: {0}".format(os.path.join(local_path, path))
        if not os.path.isdir(os.path.join(local_path, path)):
            print "Making dir: {0}".format(os.path.join(local_path, path))
            os.mkdir(os.path.join(local_path, path))


def download_text(ftp, progress_tracker, local_path, localname, servername):
    '''Downloads text files from an FTP to the DCP directory.
    Uses write_download to keep track of how much has been downloaded.'''
    with open(os.path.join(local_path, localname), 'w') as f:
        ftp.retrlines('RETR {0}'.format(servername),
                write_download(progress_tracker, f))

    # @todo: Emit event that download is complete

def download_bin(ftp, progress_tracker, local_path, localname, servername):
    '''Downloads binary files from an FTP to the DCP directory but writes them to /dev/null (or NULL on win32).
    Uses write_download to keep track of how much has been downloaded.'''
    # pipe data to /dev/null
    
    with open(os.devnull, 'wb') as f:
        print "Attempting download - RETR {0}".format(servername[1:])
        ftp.retrbinary('RETR {0}'.format(servername[1:]),
                write_download(progress_tracker, f))
   

    # Write a dummy placeholder file
    with open(os.path.join(local_path, localname), 'w') as f:
        f.write('Dummy placeholder')

    # @todo: Emit event that download is complete

def write_download(progress_tracker, f):
    '''
    Provides a function for FTP.retrlines/retrbinary to call when processing a chunk. It uses the DCP's downloaded
    counter to keep track of how much of the DCP has been downloaded, alerting TMS of progress.
    '''
    def write_chunk(chunk, progress_tracker=progress_tracker, f=f):
        f.write(chunk)
        # print "length of chunk: {0}".format(len(chunk))
        progress_tracker["downloaded"] += len(chunk)
        # print "progress_tracker[downloaded]: {0}".format(progress_tracker["downloaded"])
        # print "writing chunk"
        old_progress = progress_tracker["progress"]
        # print "old_progress: {0}".format(old_progress)
        progress_tracker["progress"] = float(progress_tracker["downloaded"]) / progress_tracker["total_size"]
        # print "progress_tracker[progress]: {0}".format(progress_tracker["progress"])
        # print "progress_tracker[total_size]: {0}".format(progress_tracker["total_size"])

        # has the downloaded chuck caused the size downloaded to tick over a 1% threshold?
        # print floor(100 * progress_tracker["downloaded"]) - floor(100 * old_progress)
        if floor(100 * progress_tracker["progress"]) - floor(100 * old_progress) > 0:
            # @todo: Emit event with progress made
            logging.info('{0:.0%}'.format(progress_tracker["progress"]))

    return write_chunk
