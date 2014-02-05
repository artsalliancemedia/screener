"""
Utility functions
"""

from struct import pack, unpack
from Queue import Queue
from uuid import uuid4
import json, klv, os, sys


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

def decode_msg(msg, header_len=16):
    k, v = klv.decode(msg, header_len)
    decoded_val = json.loads(bytes_to_str(v)) if v else {}
    return k, decoded_val


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


def create_dirs(file_path):
    """
    Create the parent directories required for a file if they do not exist.
    """
    abs_path = os.path.abspath(file_path)

    try:
        os.makedirs(abs_path)
    except OSError:
        # Throws to here if the folder already exists, therefore we have no work to do :)
        pass

    return abs_path

def create_hard_link(hard_link_to, source_file):
    """
    Create a hardlink to a file. Should work on both Windows and Unix.
    """

    if sys.platform == 'win32':
        create_dirs(os.path.dirname(hard_link_to))

        from ctypes import windll
        from ctypes.wintypes import BOOLEAN, LPWSTR, DWORD, LPVOID
        CreateHardLink = windll.kernel32.CreateHardLinkW
        CreateHardLink.argtypes = (LPWSTR, LPWSTR, LPVOID,)
        CreateHardLink.restype = BOOLEAN

        if not CreateHardLink(hard_link_to, source_file, None):
            GetLastError = windll.kernel32.GetLastError
            GetLastError.argtypes = ()
            GetLastError.restype = DWORD

            error_dict = {
                    0: 'The operation completed successfully',
                    2: 'The system cannot find the file specified',
                    3: 'The system cannot find the path specified',
                    183: 'Cannot create a file when that file already exists',
                    1142: 'An attempt was made to create more links on a file than the file system supports'
            }

            error_key = GetLastError()
            if error_key in error_dict:
                error = error_dict[error_key]
            else:
                error = 'ErrorKey[%s] not in Error_dict, goto http http://msdn.microsoft.com/en-us/library/ms681382(VS.85).aspx for description '% error_key
            error = error + '|| to: |' + str(hard_link_to) + '| source: |' + str(source_file) + '|'
            raise Exception(error)
    else:
        os.link(source_file, hard_link_to)