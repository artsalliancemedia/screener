from ftplib import FTP
from math import floor
from datetime import datetime
import Queue, shutil, os, logging

from screener.lib.util import create_dirs, create_hard_link

class DCPDownloader(object):
    def __init__(self, incoming_path, ftp_details):
        self.incoming_path = incoming_path
        self.ftp_details = ftp_details

        create_dirs(self.incoming_path)

    def __enter__(self):
        logging.info('Connecting to FTP')

        # Stupid API only take a boolean instead of an enum value!
        ftp_mode = (self.ftp_details.get('mode', 'passive') == 'passive')

        self.ftp = FTP()
        self.ftp.set_pasv(ftp_mode)
        self.ftp.connect(host=self.ftp_details['host'], port=(self.ftp_details['port'] or 21))

        if 'user' in self.ftp_details or 'passwd' in self.ftp_details:
            self.ftp.login(user=self.ftp_details['user'], passwd=self.ftp_details['passwd'])

        return self

    def __exit__(self, *args):
        self.ftp.quit()

    def download(self, path):
        download_path = os.path.join(self.incoming_path, path)
        create_dirs(download_path)

        # Work out what we're dealing with, store this info on the object itself for easy access :)
        items, total_size = self.get_folder_info(self.ftp, path)

        local_paths = []
        server_paths = []

        progress_tracker = {
            "downloaded": 0,
            "total_size": total_size,
            "progress": 0
        }

        for item in items:
            path_parts = item.split("/")
            localfilepath = "\\".join(path_parts[2:])
            local_paths.append(localfilepath)

            server_paths.append(item)

        to_parent_dir(self.ftp, path)

        """
        Code which calls functions to download files from the ftp server.
        This can be commented out when testing if the files have already been downloaded.
        """
        for local_path, server_path in zip(local_paths, server_paths):
            dirname = os.path.dirname(local_path)
            if dirname is not None:
                full_download_path = os.path.join(download_path, dirname)
                if not os.path.isdir(full_download_path):
                    create_dirs(full_download_path)

            if local_path.endswith('.mxf'): # binary file
                download_bin(self.ftp, progress_tracker, download_path, local_path, server_path)
            else:
                download_text(self.ftp, progress_tracker, download_path, local_path, server_path)

        logging.info("Finished getting folder info.")
        
        return download_path

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
                self.items.append("{path}{filename}".format(path=current_path, filename=parts[8]))
                self.total_size += int(parts[4])

        queue.put(path)
        current_path = ftp.pwd()
        while not queue.empty():
            p = queue.get()
            ftp.cwd(p)
            current_path = "{directory}{slash}".format(directory=ftp.pwd(), slash="/")
            ftp.retrlines('LIST', process_line)
            
        to_parent_dir(ftp, path)
        
        return self.items, self.total_size

# Some util functions.

def to_parent_dir(ftp, path):
    for directory in path.split('/'):
        ftp.cwd('..') # Go back to where we started from so we don't get ourselves into a hole.

# Some functions to download files from the DCP FTP

def download_text(ftp, progress_tracker, folder_path, filename, servername):
    '''
    Downloads text files from an FTP to the DCP directory.
    '''
    with open(os.path.join(folder_path, filename), 'w') as f:
        logging.info("Starting download: {0}".format(servername))
        ftp.retrbinary('RETR {0}'.format(servername), write_download(progress_tracker, f))

    logging.info("Download of {0} complete.".format(servername))

def download_bin(ftp, progress_tracker, folder_path, filename, servername):
    '''
    Downloads binary files from an FTP to the DCP directory but writes them to /dev/null (or NULL on win32).
    '''
    # Write a dummy placeholder file
    with open(os.path.join(folder_path, filename), 'w') as f:
        f.write('Dummy placeholder')

    # Pipe data to /dev/null
    with open(os.devnull, 'wb') as f:
        logging.info("Starting download: {0}".format(servername))
        ftp.retrbinary('RETR {0}'.format(servername), write_download(progress_tracker, f))


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



class RepackageDCPError(Exception):
    pass

def repackage_dcp(dcp, assets_path, ingest_path):
    """
    Split out each cpl into it's own respective dcp but utilise a hard linking structure
    so we don't duplicate disk space.

    @todo: Work out what to do with existing CPL's that have already been ingested successfully, currently
    this function will fall over in this scenario!
    @todo: Add in support for copying over the VOLINDEX
    """
    cpl_dcp_paths = []

    for uuid, cpl in dcp.cpls.iteritems():

        # First off make sure we have a folder to add in the hard links to.
        cpl_ingest_path = os.path.join(ingest_path, uuid)
        create_dirs(cpl_ingest_path)

        # Add the ingested path for re-parsing later.
        cpl_dcp_paths.append(cpl_ingest_path)

        for asset_uuid, asset in cpl.assets.iteritems():
            original_asset_path = os.path.join(dcp.path, asset.path)

            # Store each asset, named as it's uuid in the assets_path directory.
            asset_storage_path = os.path.join(assets_path, '{0}.mxf'.format(asset_uuid))

            if not os.path.isfile(asset_storage_path):
                os.rename(original_asset_path, asset_storage_path)
            else:
                # Already this file there, remove the temporary copy!
                os.unlink(original_asset_path)

            # Finally add in the hard links.
            asset_link_path = os.path.join(cpl_ingest_path, '{0}.{1}'.format(asset_uuid, asset.ext()))
            if not os.path.isfile(asset_link_path):
                create_hard_link(asset_link_path, asset_storage_path)

            # Write the new path to the assetmap ready for repackaging it later.
            dcp.assetmap[asset_uuid].path = os.path.join('{0}.{1}'.format(asset_uuid, asset.ext()))

        # We have all the picture/sound/subtitle assets linked up, not onto the metadata
        os.rename(cpl.path, os.path.join(cpl_ingest_path, 'cpl.xml'))
        dcp.assetmap[cpl.id].path = 'cpl.xml'

        shutil.copyfile(dcp.pkl.path, os.path.join(cpl_ingest_path, 'pkl.xml'))
        dcp.assetmap[dcp.pkl.id].path = 'pkl.xml'

        # Finally repackage the assetmap with the new file paths and write it in the new place.
        repackaged_assetmap_path = os.path.join(cpl_ingest_path, 'assetmap.xml')
        with open(repackaged_assetmap_path, 'w') as f:
            f.write(unicode(dcp.assetmap))

    # Finally clean up the incoming DCP path.
    shutil.rmtree(dcp.path)

    return cpl_dcp_paths
