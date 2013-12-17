"""
Tests playback functionality
"""

import unittest
import json
from datetime import datetime
from screener.util import bytes_to_int, bytes_to_str
from screener.app import ScreenServer
import klv

class TestPlayback(unittest.TestCase):
    """
    Playback tests
    """

    def setUp(self):
        self.s = ScreenServer()

    def test_status(self):
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(json.loads(bytes_to_str(v))['state'], 0)

    def test_play(self):
        msg = bytearray('\x00' * 15 + '\x00' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(bytes_to_int(v), 0)
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(json.loads(bytes_to_str(v))['state'], 1)

    def test_stop(self):
        msg = bytearray('\x00' * 15 + '\x00' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(bytes_to_int(v), 0)
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(json.loads(bytes_to_str(v))['state'], 1)
        msg = bytearray('\x00' * 15 + '\x01' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(bytes_to_int(v), 0)
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(json.loads(bytes_to_str(v))['state'], 0)

    def test_pause(self):
        msg = bytearray('\x00' * 15 + '\x00' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(bytes_to_int(v), 0)
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(json.loads(bytes_to_str(v))['state'], 1)
        msg = bytearray('\x00' * 15 + '\x05' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(bytes_to_int(v), 0)
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = klv.decode(self.s.process_klv(msg), 16)
        self.assertEqual(json.loads(bytes_to_str(v))['state'], 2)


if __name__ == '__main__':
    unittest.main()