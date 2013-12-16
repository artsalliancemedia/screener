"""
System time
"""
from time import time
from util import int_to_bytes

def system_time(*args):
    """
    Retrieve and encode the system time in POSIX UTC format
    """
    return int_to_bytes(int(time()))