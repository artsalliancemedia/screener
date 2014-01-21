"""
Utility functions
"""

from struct import pack, unpack
from Queue import Queue
from uuid import uuid4
import json, klv

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


def encode_msg(handler_key, **kwargs):
    '''
    Takes json serialisable python objects and constructs a SMTPE compliant KLV message.
    '''
    # See SMPTE ST-336-2007 for details on the header format
    key = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 8) + [handler_key]
    if kwargs:
        value = json.dumps(kwargs)
        msg = klv.encode(key, value)
    else:
        msg = bytearray(key + [0x00]) # 0 length, 0 message

    return msg

def decode_rsp(rsp, header_len=16):
    k, v = klv.decode(rsp, header_len)
    return k, json.loads(bytes_to_str(v))


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
            return next(item[1] for item in self.queue if item[0] == uuid)

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        self.queue.append((str(uuid4()), item))

    def _get(self):
        return self.queue.pop(0)[1]

    def put(self, item, **kwargs):
        super(IndexableQueue, self).put(item, **kwargs)

        # return the uuid
        return next(qitem[0] for qitem in self.queue if qitem[1] == item)

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
