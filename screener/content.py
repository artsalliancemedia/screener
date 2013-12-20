"""
Content management
"""
import json
from uuid import uuid4
from util import str_to_bytes

class Content(object):

    def __init__(self):
        # Set up some dummy content for testing
        self._content = [str(uuid4()) for i in xrange(10)]

    def get_cpl_uuids(self, *args):
        """
        Returns UUIDs of all content
        """
        return str_to_bytes(json.dumps(self._content))

    def get_cpls(self, cpl_uuids, *args):
        raise NotImplementedError

    def get_cpl(self, cpl_uuid, *args):
        raise NotImplementedError

    def ingest(self, connection_details, dcp_path, *args):
        """
        Ingest a DCP by pulling in the content from the FTP connection details supplied and the path to the individual DCP.
        """
        raise NotImplementedError

    def cancel_ingest(self, ingest_uuid, *args):
        raise NotImplementedError

    def get_ingest_history(self, *args):
        raise NotImplementedError

    def clear_ingest_history(self, *args):
        raise NotImplementedError

    def get_ingests_info(self, ingest_uuids, *args):
        raise NotImplementedError

    def get_ingest_info(self, ingest_uuid, *args):
        raise NotImplementedError
