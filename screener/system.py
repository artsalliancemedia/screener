from time import time

from screener import rsp_codes

def system_time(*args):
    """
    Retrieve the system time

    Returns:
        The return status::

            0 -- Success

        Also the time in POSIX UTC format
    """

    rsp = rsp_codes[0]
    rsp['time'] = int(time())
    return rsp