from ftplib import FTP
import os
import time
import xml.dom.minidom as dom
from base64 import b64encode, b64decode
from hashlib import sha1
from math import floor
from datetime import datetime
import logging





def process_ingest_queue(queue, interval=1):
    """
    The process running on a separate thread which loops every interval (default 1)
    and runs process_ingest_queue_item on each item it finds on the queue
    """
    logging.info('Starting ingest queue processing thread.')
    while 1:
        if not queue.empty():
            item = queue.get()
            process_ingest_queue_item(item)
            queue.task_done()
        time.sleep(interval)

def process_ingest_queue_item(item):
    """
    Takes FTP connection details and DCP path from queue items and instantiates a DCP object
    """
    connection_details = item['connection_details']
    dcp_path = item['dcp_path']
    logging.info('Processing {0} from the ingest queue'.format(dcp_path))
    dcp = DCP(dcp_path, connection_details)
    ### NEED A WAY FOR SCREENER TO KNOW IT NOW HAS THE DCP IN ITS CONTENT
    ### PERHAPS THE LIST_DCPS FN CAN CONSULT THE DCP_STORE

    
# Some XML functions to help pull text from DOM nodes.
#
def text_from_node(node):
    text = []
    for child in node.childNodes:
        if child.nodeType==child.TEXT_NODE:
            text.append(child.data)
    return ''.join(text)

def text_from_tag_name(context_node, tag_name):
    text = []
    nodelist = context_node.getElementsByTagName(tag_name)
    for node in nodelist:
        text.append(text_from_node(node))
    return ''.join(text)

def text_from_direct_child(node, tag_name):
    for child in node.childNodes:
        if child.nodeType==child.ELEMENT_NODE and child.tagName==tag_name:
            return text_from_node(child)


# Some functions to download files from the DCP FTP
#
def download_text(ftp, dcp, filename):
    '''Downloads text files from an FTP to the DCP directory.
    Uses write_and_track_progress to keep track of how much has been downloaded.'''
    with open(os.path.join(dcp.dir, filename), 'w') as f:
        ftp.retrlines('RETR {0}'.format(filename), write_and_track_progress(dcp, f))
    ###
    # Inform TMS the download is complete?

def download_bin(ftp, dcp, filename):
    '''Downloads binary files from an FTP to the DCP directory but writes them to /dev/null (or NULL on win32).
    Uses write_and_track_progress to keep track of how much has been downloaded.'''
    # pipe data to /dev/null
    with open(os.devnull, 'wb') as f:
        ftp.retrbinary('RETR {0}'.format(filename), write_and_track_progress(dcp, f))
    # write a dummy placeholder file
    with open(os.path.join(dcp.dir, filename), 'w') as f:
        f.write('Dummy placeholder')
    ###
    # Inform TMS the download is complete?

def write_and_track_progress(dcp, f):
    '''
    Provides a function for FTP.retrlines/retrbinary to call when processing a chunk. It uses the DCP's downloaded
    counter to keep track of how much of the DCP has been downloaded, alerting TMS of progress.
    '''
    def write_track_inner(chunk, dcp=dcp, f=f):
        f.write(chunk)
        dcp.downloaded += len(chunk)
        old_progress = dcp.progress
        dcp.progress = float(dcp.downloaded)/dcp.total_size
        # has the downloaded chuck caused the size downloaded to tick over a 1% threshold?
        if floor(100*dcp.progress)-floor(100*old_progress) > 0:
            # we need to inform TMS of the progress we have made
            logging.info('{0:.0%}'.format(dcp.progress))
            # print "THIS WOULD INFORM TMS THAT WE HAVE DOWNLOADED {0:.0%} OF THE DCP".format(dcp.progress)
    return write_track_inner


class DCP(object):
    
    def __init__(self, uuid, ftp_connection_details=None):
        logging.info('Instantiating DCP({0})'.format(uuid))
        self.uuid = uuid
        self.dir = os.path.join('dcp_store',uuid) ### TODO, make dcp_store configurable
        logging.info('DCP Store: {0}'.format(self.dir))
        self.total_size = 0
        self.downloaded = 0
        self.assets = {}
        self.cpls = {}

        # initialises the object based on whether ftp details were provided
        if ftp_connection_details:
            print ftp_connection_details
            logging.info('Initialising {0} using FTP details.'.format(self.uuid))
            self.progress = 0
            self.ftp_connection_details = ftp_connection_details
            # make a dir in the dcp store to put the dcp contents
            if not os.path.isdir(self.dir):
                os.mkdir(self.dir)
            self.download_and_parse()
        # if there is a folder already, attempt to initialise from already downloaded files
        elif os.path.isdir(self.dir):
            logging.info('DCP directory already exists for {0}, attempting to parse files.'.format(self.uuid))
            # initialise DCP from existing dir
            parse_exisiting_files()
        else:
            logging.info('Unable to construct DCP.')
            raise Exception('Unable to construct DCP, DCP not present.')

    def compute_total_size(self, ftp):
        '''Loops through FTP LISTing and counts the DCP's total size.'''

        if self.uuid in ftp.pwd():
            logging.info('Computing {0!r}\'s size.'.format(self))
            def count_filesize(dir_line):
                filesize = int(dir_line.split()[4])
                self.total_size += filesize
            ftp.retrlines('LIST', count_filesize)
            logging.info('{0!r}\'s size is {1}'.format(self, self.total_size))
        else:
            logging.error('Could not compute DCP size as not in DCP dir on FTP')

    def parse_exisiting_files(self):
        raise NotImplementedError

    def download_and_parse(self):
        '''
        Uses the connection_details to connect to the FTP server, downloads the common files then
        downloads and parses the other assets from the details in them.
        '''
        logging.info('Connecting to FTP')
        try:
            ftp = FTP(**self.ftp_connection_details)
        except Exception as err:
            logging.error('Could not connect to FTP')
            os.rmdir(os.path.join('dcp_store',self.uuid))
            logging.error(str(err))
            return False
        # change dir on the FTP
        try:
            ftp.cwd(self.uuid)
        except:
            logging.error('Error trying to change to dir {0} on FTP'.format(self.uuid))
            raise Exception('Dir {0} not present on {1}'.format(self.uuid, self.ftp_connection_details['host']))

        self.compute_total_size(ftp)
        download_text(ftp, self, 'VOLINDEX') # legacy, but counts toward download total!
        download_text(ftp, self, 'ASSETMAP')
        logging.info('Parsing assets')
        self.parse_and_download_assets(ftp)
        logging.info('Parsing CPLs')
        self.parse_cpls()

        ftp.quit()

    def parse_and_download_assets(self, ftp):
        '''
        Reads the DCP's ASSETMAP and packing list to parse info on all the contained assets
        storing them all in the DCP assets dictionary.
        '''
        # parse the ASSETMAP XML
        asset_map_dom = dom.parse(os.path.join(self.dir, 'ASSETMAP'))
        # pick out all the assets
        asset_nodes = asset_map_dom.getElementsByTagName('Asset')
        # acquire pkl and download file for parsing later
        pkl_node = asset_map_dom.getElementsByTagName('PackingList')[0].parentNode
        self.process_asset(pkl_node)
        self.pkl.download(ftp)
        # remove it from the asset_nodes as we do not need to process it further
        asset_nodes.remove(pkl_node)
        # process rest of nodes
        for asset_node in asset_nodes:
            self.process_asset(asset_node)
        # add extra info from the PKL
        logging.info('Parsing PKL for extra asset info.')
        pkl_dom = dom.parse(os.path.join(self.dir, self.pkl.filename))
        asset_nodes = pkl_dom.getElementsByTagName('Asset')
        for asset_node in asset_nodes:
            asset_id = text_from_tag_name(asset_node, 'Id')
            # Add hash and two types to asset
            self.assets[asset_id].hash = text_from_tag_name(asset_node, 'Hash')
            self.assets[asset_id].mime_type = text_from_tag_name(asset_node, 'Type').split(';')[0]
            self.assets[asset_id].asdcpKind = text_from_tag_name(asset_node, 'Type').split('=')[1]
        logging.info('DCP({0}) has {1} assets'.format(self.uuid, len(self.assets.items())))
        # now we can download all the assets
        for asset in self.assets.values():
            asset.download(ftp)        

    def process_asset(self, asset_node):
        asset_id = text_from_tag_name(asset_node, 'Id')
        is_pkl = bool(asset_node.getElementsByTagName('PackingList').length)
        # create asset objects from the nodes
        asset = Asset(self,
                      id=asset_id,
                      filename=text_from_tag_name(asset_node, 'Path'),
                      offset=int(text_from_tag_name(asset_node, 'Offset')),
                      size=int(text_from_tag_name(asset_node, 'Length')),
                      is_pkl=is_pkl)
        self.assets[asset_id] = asset
        if is_pkl:
            self.pkl = asset


    def parse_cpls(self):
        for cpl_asset in [a for a in self.assets.values() if (not a.is_pkl and a.asdcpKind==CPL)]:
            cpl = self.parse_cpl(cpl_asset)
            self.cpls[cpl.id] = cpl

    def parse_cpl(self, cpl_asset):
        '''
        Opens a given CPL asset, parses the XML to extract the playlist info and create a CPL object
        which is added to the DCP's CPL list.
        '''
        cpl_dom = dom.parse(os.path.join(self.dir, cpl_asset.filename))
        root = cpl_dom.getElementsByTagName('CompositionPlaylist')
        cpl_id = text_from_direct_child(root, 'Id')
        issue_date_string = text_from_direct_child(root, 'IssueDate')
        cpl = CPL(dcp=self,
                  asset=cpl_asset,
                  id=cpl_id,
                  metadata={'title': text_from_direct_child(root, 'ContentTitleText'),
                            'annotation': text_from_direct_child(root, 'AnnotationText'),
                            'issue_date': datetime.strptime(issue_date_string, "%Y-%m-%dT%H:%M:%S"),
                            'issuer': text_from_direct_child(root, 'Issuer'),
                            'creator': text_from_direct_child(root, 'Creator'),
                            'content_type': text_from_direct_child(root, 'ContentKind'),
                            'version_id': 'urn:uri:{0}_{1}'.format(cpl_id, issue_date_string),
                            'version_label': '{0}_{1}'.format(cpl_id, issue_date_string)})
        
        # fetch and parse reel info
        reels = root.getElementsByTagName('Reel')
        for reel_node in reels:
            reel_id = text_from_direct_child(reel_node, 'Id')
            
            # initialise the picture obj
            picture_node = reel_node.getElementsByTagName('MainPicture')[0]
            picture = Picture(cpl=cpl,
                              id=text_from_node(picture_node.getElementsByTagName('Id')),
                              edit_rate=text_from_node(picture_node.getElementsByTagName('EditRate')),
                              intrinsic_duration=text_from_node(picture_node.getElementsByTagName('IntrinsicDuration')),
                              entry_point=text_from_node(picture_node.getElementsByTagName('EntryPoint')),
                              duration=text_from_node(picture_node.getElementsByTagName('Duration')),
                              frame_rate=text_from_node(picture_node.getElementsByTagName('FrameRate')),
                              aspect_ratio=text_from_node(picture_node.getElementsByTagName('AspectRatio')),
                              annotation=text_from_node(picture_node.getElementsByTagName('AnnotationText')))
            
            # initialise the sound obj
            sound_node = reel_node.getElementsByTagName('MainSound')[0]
            sound = Sound(cpl=cpl,
                          id=text_from_node(sound_node.getElementsByTagName('Id')),
                          edit_rate=text_from_node(sound_node.getElementsByTagName('EditRate')),
                          intrinsic_duration=text_from_node(sound_node.getElementsByTagName('IntrinsicDuration')),
                          entry_point=text_from_node(sound_node.getElementsByTagName('EntryPoint')),
                          duration=text_from_node(sound_node.getElementsByTagName('Duration')),
                          annotation=text_from_node(sound_node.getElementsByTagName('AnnotationText')),
                          language=text_from_node(sound_node.getElementsByTagName('Language')))
            
            # finally initialise the reel
            reel = Reel(cpl=cpl,
                        id=reel_id,
                        picture=picture,
                        sound=sound)
            # and finally put the reel on the CPL reel_list
            cpl.reel_list.append(reel)
        return cpl

    def __repr__(self):
        return 'DCP({0})'.format(self.uuid)

class Asset(object):
    '''
    A DCP asset object. Contains basic info about the asset from the ASSETMAP.
    When the PKL is consulted, more info can be added such as file hash etc.
    '''
    def __init__(self, dcp, id, filename, offset, size, is_pkl):
        self.dcp = dcp
        self.id = id
        self.filename = filename
        self.offset = offset
        self.size = size
        self.is_pkl = is_pkl

    def is_downloaded(self):
        '''
        .. py:function:: is_downloaded()

        Returns boolean of whether the asset has 
        '''
        return os.path.exists(os.path.join(self.dcp.dir, self.filename))

    def download(self, ftp_conn):
        logging.info('Downloading {0!r}'.format(self))
        if self.is_pkl:
            download_text(ftp_conn, self.dcp, self.filename)
        elif not self.is_downloaded():
            if self.mime_type.startswith('text'):
                download_text(ftp_conn, self.dcp, self.filename)
            elif self.mime_type.startswith('application'):
                download_bin(ftp_conn, self.dcp, self.filename)
        else:
            print '{0!r} already downloaded.'.format(self)

    def __repr__(self):
        if hasattr(self,'asdcpKind'):
            return 'Asset-{0}({1})'.format(self.asdcpKind, self.id.split(':')[2])
        else:
            return 'Asset({0})'.format(self.id.split(':')[2])
        

class CPL(object):
    def __init__(self, dcp, asset, id, reel_list=[], rating_list=[], metadata={}):
        self.dcp = dcp
        self.asset = asset
        self.id = id
        self.reel_list = reel_list
        self.rating_list = rating_list
        self.metadata = metadata

    def __repr__(self):
        return 'CPL-{0}({1})'.format(self.metadata['content_type'][:3],
                                     self.metadata['title'])


class Reel(object):
    def __init__(self, cpl, id, picture, sound):
        self.cpl = cpl
        self.id = id
        self.picture = picture
        self.sound = sound

    def __repr__(self):
        return 'Reel({0})'.format(self.id.split(':')[2])


class Picture(object):
    def __init__(self, cpl, id, edit_rate, intrinsic_duration, entry_point,
                 duration, frame_rate, aspect_ratio, annotation=None):
        self.cpl = cpl
        self.id = id
        self.asset = self.cpl.dcp.assets[self.id]
        self.edit_rate = tuple(edit_rate.split(' '))
        self.intrinsic_duration = int(intrinsic_duration)
        self.entry_point = int(entry_point)
        self.duration = int(duration)
        self.frame_rate = tuple(frame_rate.split(' '))
        self.aspect_ratio = float(aspect_ratio)
        self.annotation = annotation

    def __repr__(self):
        return 'Picture({0})'.format(self.id.split(':')[2])
    

class Sound(object):
    def __init__(self, cpl, id, edit_rate, intrinsic_duration, entry_point,
                 duration, annotation=None, language=None):
        self.cpl = cpl
        self.id = id
        self.asset = self.cpl.dcp.assets[self.id]
        self.annotation = annotation
        self.edit_rate = tuple(edit_rate.split(' '))
        self.intrinsic_duration = int(intrinsic_duration)
        self.entry_point = int(entry_point)
        self.duration = int(duration)
        self.language = language

    def __repr__(self):
        return 'Sound({0})'.format(self.id.split(':')[2])
        
