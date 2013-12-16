"""
Content management
"""
import json
from uuid import uuid4
from util import str_to_bytes

class Content(object):

    def __init__(self):
        self._content = [str(uuid4()) for i in xrange(10)]

    def uuids(self, *args):
        """
        Returns UUIDs of all content
        """
        return str_to_bytes(json.dumps(self._content))