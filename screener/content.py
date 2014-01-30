"""
Content management
"""
import logging
from uuid import uuid4
from threading import Thread

from screener.lib.util import IndexableQueue
from screener import dcp

from lib.util import QUEUED, INGESTING, INGESTED, CANCELLED

from smpteparsers.util import (get_element, get_element_text,
        get_element_iterator, get_namespace)
from smpteparsers.cpl import CPL

import datetime, os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def startup_cpl_scan(content_store, ingest_path):
    """
    Function which can be called at startup to scan the local INGEST 
    folder (if it exists) and parse any CPL files which have already 
    been downloaded.
    """
    if not os.path.isdir(os.path.abspath(ingest_path)):
        return
    for root, dirs, files in os.walk(ingest_path):
        # TODO can this be done in a list comprehension (or similar)?
        for f in files:
            # Ignore binary files
            if f.endswith('.mxf'):
                continue
            # TODO change to use regexp?
            tree = ET.parse(os.path.join(root, f))
            if tree:
                tree_root = tree.getroot()
                tag = tree_root.tag[tree_root.tag.rfind("}")+1:]
                if tag == "CompositionPlaylist":
                    cpl_path = os.path.join(root, f)
                    cpl = CPL(cpl_path)
                    content_store.content[cpl.cpl_uuid] = cpl
                    logging.info("Processed CPL: {0}".format(cpl.cpl_uuid))

class Content(object):

    def __init__(self):
        logging.info('Instantiating Content()')

        self.content = {}
        self.history = {}

        # TODO Move this path to a config file
        self.ingest_path = "screener\INGEST"
        # startup_cpl_scan(self, self.ingest_path)

        self.ingest_queue = IndexableQueue()

        self.ingest_thread = Thread(target=dcp.process_ingest_queue,
                args=(self.ingest_queue, self), name='IngestQueue')
        self.ingest_thread.daemon = True
        self.ingest_thread.start()

    def __getitem__(self, cpl_uuid):
        return self.content[cpl_uuid]

    def get_cpl_uuids(self, *args):
        """
        Returns UUIDs of all content
        """
        return self.content.keys()

    def get_cpls(self, cpl_uuids, *args):
        """
        Returns a list of CPLs
        """
        return [self.content[cpl_uuid] for cpl_uuid in cpl_uuids if cpl_uuid in self.content.keys()]

    def get_cpl(self, cpl_uuid, *args):
        """
        Return a CPL that has an Id matching cpl_uuid
        """
        return self.content[cpl_uuid]

    def ingest(self, connection_details, dcp_path, *args):
        """
        Ingest a DCP by pulling in the content from the FTP connection details supplied and the path to the individual DCP.
        """
        if dcp_path not in self.content.keys():
            logging.info('Adding DCP "{dcp_path}" to the ingest queue'.format(dcp_path=dcp_path))
            ingest_uuid = self.ingest_queue.put({'ftp_details': connection_details, 'dcp_path': dcp_path})
            
            self.update_ingest_history(ingest_uuid, QUEUED)

            return ingest_uuid

    # TODO add in response codes?
    # TODO cancel the ingest if it has already started (how?)
    def cancel_ingest(self, ingest_uuid, *args):
        # Since we're using IndexableQueue, we can't just use del x
        self.ingest_queue.cancel(ingest_uuid)
        self.update_ingest_history(ingest_uuid, CANCELLED)

    # TODO add in response codes?
    def update_ingest_history(self, ingest_uuid, state, *args):
        timestamp = datetime.datetime.now()
        
        if ingest_uuid not in self.history:
            self.history[ingest_uuid] = []

        self.history[ingest_uuid].append({"timestamp": timestamp, "state": state})
        logging.info("Ingest state updated: {0} - {1} - {2}".format(ingest_uuid,
            state, timestamp))

    def get_ingest_history(self, *args):
        return self.history

    # TODO add in response code?
    def clear_ingest_history(self, *args):
        self.history = {}

    def get_ingests_info(self, ingest_uuids, *args):
        return [self.ingest_queue[ingest_uuid] for ingest_uuid in ingest_uuids]

    def get_ingest_info(self, ingest_uuid, *args):
        return self.ingest_queue[ingest_uuid]

    """
    TODO Currently we don't store a link between the ingest uuid returned by
    the IndexableQueue and a cpl. Will need to create this relationship before
    we can delete ingests.
    """
    def delete_ingest(self, ingest_uuid, *args):
        raise NotImplementedError
