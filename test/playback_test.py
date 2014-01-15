"""
Tests playback functionality
"""

import unittest, json
from datetime import datetime

from screener.app import ScreenServer
from test import decode_rsp

class TestPlayback(unittest.TestCase):
    """
    Playback tests
    """

    def setUp(self):
        self.s = ScreenServer()

    def test_status_eject(self):
        # Check status starts at EJECT
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

    def test_play(self):
        # Send PLAY
        msg = bytearray('\x00' * 15 + '\x00' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)

        # Check status is PLAY
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 2)

    def test_stop(self):
        # Send PLAY
        msg = bytearray('\x00' * 15 + '\x00' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)

        # Check status is PLAY
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 2)

        # Send STOP
        msg = bytearray('\x00' * 15 + '\x01' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)

        # Check status is STOP
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 1)

    def test_pause(self):
        # Send PLAY
        msg = bytearray('\x00' * 15 + '\x00' + '\x00')
        k, v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)

        # Check status is PLAY
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 2)

        # Send PAUSE
        msg = bytearray('\x00' * 15 + '\x05' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)

        # Check status is PAUSE
        msg = bytearray('\x00' * 15 + '\x02' + '\x00')
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 3)


if __name__ == '__main__':
    unittest.main()