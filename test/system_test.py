"""
Tests system functionality
"""

import unittest
from datetime import datetime
import klv
from screener.util import bytes_to_int
from screener.app import ScreenServer

class TestSystem(unittest.TestCase):
    """
    System tests
    """

    def setUp(self):
        self.s = ScreenServer()

    def test_system_time(self):
        msg = bytearray('\x00' * 15 + '\x03' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertTrue(datetime.fromtimestamp(bytes_to_int(v)))

if __name__ == '__main__':
    unittest.main()