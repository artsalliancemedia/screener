"""
Content management
"""
import logging
from uuid import uuid4
from threading import Thread

from screener.lib.util import IndexableQueue
from screener import dcp

class Content(object):

    def __init__(self):
        logging.info('Instantiating Content()')

        self.content = {}
        self.ingest_queue = IndexableQueue()

        self.ingest_thread = Thread(target=dcp.process_ingest_queue,
                args=(self.ingest_queue, self), name='IngestQueue')
        self.ingest_thread.daemon = True
        self.ingest_thread.start()

    def __getitem__(self, k):
        return self.content[k]

    def get_cpl_uuids(self, *args):
        """
        Returns UUIDs of all content
        """
        cpl_uuids = []
        for dcp in self.content.itervalues():
            cpl_uuids.extend(dcp.cpls.keys())
        
        return cpl_uuids

    def get_cpls(self, cpl_uuids, *args):
        """
        Returns a list of CPLs
        """
        cpl_dict = {}
        for dcp in self.content.itervalues():
            for cpl_id, cpl in dcp.cpls.iteritems():
                cpl_dict[cpl_id] = cpl
        
        cpls = []
        for cpl_uuid in cpl_uuids:
            try:
                cpls.append(cpl_dict[cpl_uuid])
            except KeyError:
                logging.info("get_cpls(): key not found ({0})".format(cpl_uuid))
        return cpls

    def get_cpl(self, cpl_uuid, *args):
        """
        Return a CPL that has an Id matching cpl_uuid
        """
        for dcp in self.content.itervalues():
            for cpl_id, cpl in dcp.cpls.iteritems():
                if cpl_id == cpl_uuid:
                    return cpl

    def ingest(self, connection_details, dcp_path, *args):
        """
        Ingest a DCP by pulling in the content from the FTP connection details supplied and the path to the individual DCP.
        """
        if dcp_path not in self.content.keys():
            logging.info('Adding DCP "{dcp_path}" to the ingest queue'.format(dcp_path=dcp_path))
            ingest_uuid = self.ingest_queue.put({'ftp_details': connection_details, 'dcp_path': dcp_path})

            return ingest_uuid

    def cancel_ingest(self, ingest_uuid, *args):
        del self.ingest_queue[ingest_uuid]

    def get_ingest_history(self, *args):
        raise NotImplementedError

    def clear_ingest_history(self, *args):
        raise NotImplementedError

    def get_ingests_info(self, ingest_uuids, *args):
        return [self.ingest_queue[ingest_uuid] for ingest_uuid in ingest_uuids]

    def get_ingest_info(self, ingest_uuid, *args):
        return self.ingest_queue[ingest_uuid]
