from ftplib import FTP
import os, time, logging
from math import floor
from datetime import datetime
from hashlib import sha1, md5, sha224, sha256, sha384, sha512
import base64
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import Queue

from smpteparsers.dcp import DCP


def process_ingest_queue(queue, content_store, interval=1):
    logging.info('Starting ingest queue processing thread.')
    while 1:
        if not queue.empty():
            item = queue.get()

            logging.info('Downloading "{0}" from the ingest queue'.format(item['dcp_path']))
            with DCPDownloader(item['ftp_details']) as dcp_downloader:
                local_dcp_path, local_dcp_files = dcp_downloader.download(item['dcp_path'])

            logging.info('Parsing DCP "{0}"'.format(local_dcp_path))
            dcp = DCP(local_dcp_path)
            parse_dcp(local_dcp_path, local_dcp_files)

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

#         self.ftp.cwd(path)
        # @todo: Finish off downloading the DCP files and storing them locally.

        local_paths = []
        server_paths = []

        progress_tracker = {
                "downloaded" : 0,
                "total_size" : total_size,
                "progress" : 0
                }

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
                rightmost_slash = local.rfind("\\")
                directory_path = local[:rightmost_slash+1]
                print "directory_path: {0}".format(directory_path)
                if not os.path.isdir(os.path.join(local_path, directory_path)):
                    create_directories(local_path, local)
            if local[-4:] == '.mxf': #binary file
                download_bin(self.ftp, progress_tracker, local_path, local, server)
            else:
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

        logging.info("Finished getting folder info.")
        
        return local_path, local_paths

    def get_folder_info(self, ftp, path):
        """
        Aggregate the DCP folder contents so we know what we're dealing with.
        """
#         ftp.cwd(path)

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

def parse_dcp(local_dcp_path, local_dcp_files):
    """
    Establish and parse ASSETMAP and pkl files so we can verify downloads
    and check hashes
    """

    assetmap_path = ""
    pkl_path = ""

    assetmap_found = False
    pkl_found = False
    for filename in local_dcp_files:
        if "assetmap" in filename.lower():
            print "Found ASSETMAP file at: {0}".format(os.path.join(local_dcp_path, filename))
            assetmap_path = os.path.join(local_dcp_path, filename)
            assetmap_found = True
        elif "pkl.xml" in filename.lower():
            print "Found pkl.xml file at: {0}".format(os.path.join(local_dcp_path, filename))
            pkl_path = os.path.join(local_dcp_path, filename)
            pkl_found = True
        if assetmap_found and pkl_found:
            break

    # tree = ET.ElementTree(file=assetmap_path)
    tree = ET.parse(assetmap_path)
    root = tree.getroot()
    print "root: {0}".format(root.attrib)
    for elem in tree.getiterator():
        print elem.tag

    generate_hash(os.path.join(local_dcp_path, local_dcp_files[1]))


# Some util functions.

def generate_hash(local_path):
    """
    Work out the base64 encoded sha-1 hash of the file so we can compare
    integrity with hashes in pkl.xml file
    """
    chunk_size = 1048576 # 1mb
    file_sha1 = sha1()
    with open(r"{0}".format(local_path), "r") as f:
        chunk = f.read(chunk_size)
        file_sha1.update(chunk)
        while chunk:
            chunk = f.read(chunk_size)
            file_sha1.update(chunk)
    file_hash = file_sha1.digest()
    logging.info("Hash for {0}: {1}".format(local_path,
        base64.b64encode(file_hash)))
    return file_hash

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

def create_directories(local_path, localname):
    parts = localname.split("\\")
    path = ""
    for part in parts[:-1]:
        path += part
        path += "\\"
        if not os.path.isdir(os.path.join(local_path, path)):
            logging.info("Making dir: {0}".format(os.path.join(local_path, path)))
            os.mkdir(os.path.join(local_path, path))


def download_text(ftp, progress_tracker, local_path, localname, servername):
    '''Downloads text files from an FTP to the DCP directory.
    Uses write_download to keep track of how much has been downloaded.'''
    with open(os.path.join(local_path, localname), 'w') as f:
        logging.info("Starting download: {0}".format(servername))
        ftp.retrbinary('RETR {0}'.format(servername),
                write_download(progress_tracker, f))

    # @todo: Emit event that download is complete
    logging.info("Download of {0} complete.".format(servername))

def download_bin(ftp, progress_tracker, local_path, localname, servername):
    '''Downloads binary files from an FTP to the DCP directory but writes them to /dev/null (or NULL on win32).
    Uses write_download to keep track of how much has been downloaded.'''
    # pipe data to /dev/null
    
    with open(os.devnull, 'wb') as f:
        logging.info("Attempting download: {0}".format(servername))
        ftp.retrbinary('RETR {0}'.format(servername),
                write_download(progress_tracker, f))
   

    # Write a dummy placeholder file
    with open(os.path.join(local_path, localname), 'w') as f:
        f.write('Dummy placeholder')

    # @todo: Emit event that download is complete
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
            # @todo: Emit event with progress made
            logging.info('Download progress: {0:.0%}'.format(progress_tracker["progress"]))

    return write_chunk
