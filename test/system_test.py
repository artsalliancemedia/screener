"""
Tests system functionality
"""

import unittest
from datetime import datetime

from screener.app import ScreenServer
from test import decode_rsp

class TestSystem(unittest.TestCase):
    """
    System tests
    """

    def setUp(self):
        self.s = ScreenServer()

    def test_system_time(self):
        msg = bytearray('\x00' * 15 + '\x03' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertTrue(datetime.fromtimestamp(v))

if __name__ == '__main__':
    unittest.main()