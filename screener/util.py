"""
Utility functions
"""

from struct import pack, unpack

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