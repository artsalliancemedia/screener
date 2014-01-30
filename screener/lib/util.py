"""
Utility functions
"""

from struct import pack, unpack
from Queue import Queue
from uuid import uuid4

import os

QUEUED, INGESTING, INGESTED, CANCELLED = range(4)

def int_to_bytes(num):
    """
    Transforms an unsigned int a big endian byte array
    """
    return bytearray(pack('>I', num))

def bytes_to_int(bytes):
    """
    Transforms a big endian byte array to an int
    """
    return unpack('>I', str(bytes))[0]

def str_to_bytes(txt):
    """
    Transforms a string into a byte array
    """
    return bytearray(txt)

def bytes_to_str(bytes):
    """
    Transforms a byte array into a string
    """
    return str(bytes)

def create_directories(full_path):
    try:
        os.makedirs(full_path)
    except WindowsError:
        pass

def ensure_local_path(local_path, remote_path):
    # Just in case this is the first run, make sure we have the parent directory as well.
    # TODO, make dcp_store configurable
    dcp_store = os.path.join(local_path, u'ASSET') 
    if not os.path.isdir(dcp_store):
        os.mkdir(dcp_store)

    local_path = os.path.join(dcp_store, remote_path)
    if not os.path.isdir(local_path):
        os.mkdir(local_path) # Ensure we have a directory to download to.

    return local_path

class IndexableQueue(Queue, object):
    '''
    Variant of Queue that returns queue item uuid on put() and allows reference to that item by its uuid.
    The queue backend is a list of tuples instead of a deque, index 0 is the uuid, index 1 is the item.
    [(item0_uuid, item0), (item1_uuid, item1), (item2_uuid, item2), ...]
    
    This is slightly better than an OrderedDict because we'll be consuming in a queue-like fashion primarily
    and only doing a seek on the odd occasion so this implementation is better in my opinion.
    '''
    def __getitem__(self, uuid):
        with self.mutex:
            try:
                return next(item[1] for item in self.queue if item[0] == uuid)
            except StopIteration:
                return None

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        self.queue.append((str(uuid4()), item))

    def _get(self):
        return self.queue.pop(0)[1]

    def get(self):
        return self.queue.pop(0)

    def put(self, item, **kwargs):
        super(IndexableQueue, self).put(item, **kwargs)

        # return the uuid
        return next(qitem[0] for qitem in self.queue if qitem[1] == item)

    def get_ingest_uuid(self):
        return self.queue[0][0]

    def cancel(self, uuid):
        self.queue = [qitem for qitem in self.queue if qitem[0] != uuid]

def synchronized(lock):
    """
    Synchronization decorator; provide thread-safe locking on a function
    http://code.activestate.com/recipes/465057/
    """
    def wrap(f):
        def synchronize(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return synchronize
    return wrap
