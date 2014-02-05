from uuid import uuid4
from threading import Thread, RLock
import datetime, os, logging, time

from screener.lib.util import IndexableQueue, create_dirs
from screener.dcp import DCPDownloader, repackage_dcp
from screener import rsp_codes
from smpteparsers.dcp import DCP

QUEUED, INGESTING, INGESTED, CANCELLED = range(4)

class Content(object):

    def __init__(self, incoming_path=None, assets_path=None, ingest_path=None):
        logging.info('Instantiating Content()')

        self.content = {}
        self.content_lock = RLock()

        self.ingest_history = {}
        self.ingest_history_lock = RLock()

        self.incoming_path = incoming_path
        create_dirs(self.incoming_path)

        self.assets_path = assets_path
        create_dirs(self.assets_path)

        self.ingest_path = ingest_path
        create_dirs(self.ingest_path)

        self.ingest_queue = IndexableQueue()
        self.ingest_thread = Thread(target=self.process_ingests, name='ProcessIngests')
        self.ingest_thread.daemon = True
        self.ingest_thread.start()

        # Scan the ingest_path for existing content and load it into memory.
        if self.ingest_path is not None:
            for filename in os.listdir(self.ingest_path):
                dcp_path = os.path.join(self.ingest_path, filename)
                dcp = DCP(dcp_path)

                with self.content_lock:
                    for uuid, cpl in dcp.cpls.iteritems():
                        self.content[uuid] = cpl

    def process_ingests(self, interval=1):
        logging.info('Starting ingest queue processing thread.')
        while True:
            if not self.ingest_queue.empty():

                ingest_uuid, item = self.ingest_queue.get()
                self.update_ingest_history(ingest_uuid, INGESTING)

                logging.info('Downloading "{0}" from the ingest queue'.format(item['dcp_path']))
                with DCPDownloader(self.incoming_path, item['ftp_details']) as dcp_downloader:
                    local_dcp_path = dcp_downloader.download(item['dcp_path'])

                logging.info('Parsing DCP "{0}"'.format(local_dcp_path))
                incoming_dcp = DCP(local_dcp_path)

                # Now we have the DCP downloaded and parsed, but it could contain multiple CPLs so let's mirror
                # the TMS setup and repackage the DCP into multiple ones, one for each CPL.
                cpl_dcp_paths = repackage_dcp(incoming_dcp, assets_path=self.assets_path, ingest_path=self.ingest_path)
                repackaged_dcps = []
                for path in cpl_dcp_paths:
                    repackaged_dcps.append(DCP(path))

                # Finally add all CPLs to content store
                with self.content_lock:
                    for dcp in repackaged_dcps:
                        for uuid, cpl in dcp.cpls.iteritems():
                            self.content[uuid] = cpl

                self.update_ingest_history(ingest_uuid, INGESTED)

                # Release the task from the queue, we can move on, yay!
                self.ingest_queue.task_done()

            time.sleep(interval)

    def update_ingest_history(self, ingest_uuid, state):
        with self.ingest_history_lock:
            if ingest_uuid not in self.ingest_history:
                self.ingest_history[ingest_uuid] = []

            timestamp = datetime.datetime.now()
            self.ingest_history[ingest_uuid].append({"timestamp": timestamp, "state": state})

            logging.info("Ingest state updated: {0} - {1} - {2}".format(ingest_uuid, state, timestamp))

    def __getitem__(self, cpl_uuid):
        with self.content_lock:
            return self.content[cpl_uuid]

    def get_cpl_uuids(self):
        """
        Returns UUIDs of all content

        Returns:
            The return status::

                0 -- Success
        """
        with self.content_lock:
            rsp = rsp_codes[0]
            rsp["cpl_uuids"] = self.content.keys()
            return rsp

    def get_cpls(self, cpl_uuids):
        """
        Returns a list of CPLs

        Returns:
            The return status::

                0 -- Success
                1 -- CPL not found
        """
        with self.content_lock:
            cpl_uuids = self.content.keys() # Do this outside to avoid having to calculate this each time in the loop :)
            return [self.content[cpl_uuid] for cpl_uuid in cpl_uuids if cpl_uuid in cpl_uuids]

    def get_cpl(self, cpl_uuid):
        """
        Return a CPL that has an Id matching cpl_uuid

        Returns:
            The return status::

                0 -- Success
                1 -- CPL not found
        """
        with self.content_lock:
            try:
                cpl = self.content[cpl_uuid]
            except KeyError:
                return rsp_codes[1]

            rsp = rsp_codes[0]
            rsp["cpl"] = cpl
            return rsp

    def delete_cpl(self, cpl_uuid):
        """
        Attempts to delete a cpl given by cpl_uuid

        Args:
            cpl_uuid (string): The list of ingest_uuids to investigate

        Returns:
            The return status::

                0 -- Success
                1 -- CPL not found
        """
        raise NotImplementedError

    def ingest(self, connection_details, dcp_path):
        """
        Ingest a DCP by pulling in the content from the FTP connection details supplied and the path to the individual DCP.

        Returns:
            The return status::

                0 -- Success
        """
        logging.info('Adding DCP "{dcp_path}" to the ingest queue'.format(dcp_path=dcp_path))

        ingest_uuid = self.ingest_queue.put({
            'ftp_details': connection_details,
            'dcp_path': dcp_path
        })
        
        self.update_ingest_history(ingest_uuid, QUEUED)

        rsp = rsp_codes[0]
        rsp["ingest_uuid"] = ingest_uuid
        return rsp

    # TODO add in response codes?
    # TODO cancel the ingest if it has already started (how?)
    def cancel_ingest(self, ingest_uuid):
        raise NotImplementedError

        # Since we're using IndexableQueue, we can't just use del x
        self.ingest_queue.cancel(ingest_uuid)
        update_ingest_history(self.ingest_history, self.ingest_history_lock, ingest_uuid, CANCELLED)

    def get_ingest_history(self):
        """
        Returns the ingest history since it was last cleared or the server was restarted.

        Returns:
            The return status::

                0 -- Success
        """
        with self.ingest_history_lock:
            rsp = rsp_codes[0]
            rsp["history"] = self.ingest_history
            return rsp

    def clear_ingest_history(self):
        """
        Clears the ingest history

        Returns:
            The return status::

                0 -- Success
        """
        with self.ingest_history_lock:
            self.ingest_history = {}

        return rsp_codes[0]

    def get_ingests_info(self, ingest_uuids):
        """
        Returns information about a list of ingest_uuids

        Args:
            ingest_uuids (list): The list of ingest_uuids to investigate

        Returns:
            The return status::

                0 -- Success
                11 -- Ingest not found
        """

        try:
            ingests = [self.ingest_queue[ingest_uuid] for ingest_uuid in ingest_uuids]
        except KeyError:
            return rsp_codes[11]

        rsp = rsp_codes[0]
        rsp["ingests"] = ingests
        return rsp

    def get_ingest_info(self, ingest_uuid):
        """
        Returns information about a particular ingest

        Args:
            ingest_uuid (string): The ingest_uuid to investigate

        Returns:
            The return status::

                0 -- Success
                11 -- Ingest not found
        """

        try:
            ingest = self.ingest_queue[ingest_uuid]
        except KeyError:
            return rsp_codes[11]

        rsp = rsp_codes[0]
        rsp["ingest"] = ingest
        return rsp
