"""
Content management
"""
import cfg
from uuid import uuid4
from util import str_to_bytes, bytes_to_str, IndexableQueue
from threading import Thread
import dcp
import logging

class Content(object):

    def __init__(self):
        logging.info('Instantiating Content()')
        # Set up some dummy content for testing
        self._content = [str(uuid4()) for i in xrange(10)]

        self.ingest_queue = IndexableQueue()
        self.ingest_thread = Thread(target=dcp.process_ingest_queue,
                                    args=(self.ingest_queue,),
                                    name='IngestQueue')
        self.ingest_thread.daemon = True
        self.ingest_thread.start()

    def get_cpl_uuids(self, *args):
        """
        Returns UUIDs of all content
        """
        return self._content

    def get_cpls(self, cpl_uuids, *args):
        raise NotImplementedError

    def get_cpl(self, cpl_uuid, *args):
        raise NotImplementedError

    def ingest(self, dcp_path, *args):
        """
        Ingest a DCP by pulling in the content from the FTP connection details supplied and the path to the individual DCP.
        """
        connection_details = {'host': cfg.ftp_host,
                              'user': cfg.ftp_username,
                              'passwd': cfg.ftp_password}
        if dcp_path not in self._content:
            logging.info('Adding DCP({0}) to the ingest queue'.format(dcp_path))
            queue_uuid =  self.ingest_queue.put({'connection_details':connection_details,
                                          'dcp_path':dcp_path})
            return queue_uuid
        else:
            logging.info('DCP{0} is already in the content store. It was not added to queue.')


    def cancel_ingest(self, ingest_uuid, *args):
        self.ingest_queue.remove( (ingest_uuid, self.ingest_queue[ingest_uuid]) )
        return True

    def get_ingest_history(self, *args):
        raise NotImplementedError

    def clear_ingest_history(self, *args):
        raise NotImplementedError

    def get_ingests_info(self, ingest_uuids, *args):
        return [self.ingest_queue[uuid] for uuid in ingest_uuids]

    def get_ingest_info(self, ingest_uuid, *args):
        return self.ingest_queue[ingest_uuid]
