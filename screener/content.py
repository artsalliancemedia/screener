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
    logging.info("Starting startup scan thread.")
    if not os.path.isdir(ingest_path):
        return
    for root, dirs, files in os.walk(ingest_path):
        # TODO can this be done in a list comprehension (or similar)?
        for f in files:
            # Ignore binary files
            if f[-4:] == ".mxf":
                continue
            tree = ET.parse(os.path.join(root, f))
            if tree:
                tree_root = tree.getroot()
                tag = tree_root.tag[tree_root.tag.rfind("}")+1:]
                if tag == "CompositionPlaylist":
                    cpl_path = os.path.join(root, f)
                    cpl = CPL(cpl_path)
                    content_store.content[cpl.cpl_uuid] = cpl

class Content(object):

    def __init__(self):
        logging.info('Instantiating Content()')

        self.content = {}
        self.history = {}

        # TODO Move this path to a config file
        self.ingest_path = "C:\Users\crosie\Documents\GitHub\screener\screener\INGEST"
        self.startup_scan_thread = Thread(target=startup_cpl_scan,
                args=(self, self.ingest_path), name="StartupScan")
        self.startup_scan_thread.start()

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
        # TODO this is no longer technically correct since we now store cpls in
        # self.content, not dcps
        # How do we check if a dcp has already been ingested? Scan folders for
        # dcp_path?
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
        self.history[ingest_uuid] = (state, timestamp)
        logging.info("Ingest state updated: {0} - {1} - {2}".format(ingest_uuid,
            self.history[ingest_uuid][0], self.history[ingest_uuid][1]))

    def get_ingest_history(self, *args):
        return self.history

    # TODO add in response code?
    def clear_ingest_history(self, *args):
        self.history = {}

    def get_ingests_info(self, ingest_uuids, *args):
        return [self.ingest_queue[ingest_uuid] for ingest_uuid in ingest_uuids]

    def get_ingest_info(self, ingest_uuid, *args):
        return self.ingest_queue[ingest_uuid]
