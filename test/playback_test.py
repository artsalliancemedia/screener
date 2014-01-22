import unittest, json
from datetime import datetime

from screener.app import ScreenServer
from test import encode_msg, decode_rsp

class TestPlaybackNoContentLoaded(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer()

    def test_status(self):
        # Check status starts at EJECT
        msg = encode_msg(0x02)
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

    def test_play(self):
        # Send PLAY
        msg = encode_msg(0x00)
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 3) # No CPL or playlist loaded

        # Check status is EJECT
        msg = encode_msg(0x02)
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

    def test_pause(self):
        # Send PAUSE
        msg = encode_msg(0x05)
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 3) # No CPL or playlist loaded

        # Check status is EJECT
        msg = encode_msg(0x02)
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

# class TestPlaybackCPLLoaded(unittest.TestCase):
#     def setUp(self):
#         self.s = ScreenServer()

#         # Ingest a CPL manually
        

#     def test_status(self):
#         # Check status starts at STOP
#         msg = encode_msg(0x02)
#         k,v = decode_rsp(self.s.process_klv(msg))
#         self.assertEqual(v['status'], 0)
#         self.assertEqual(v['state'], 1)

#     def test_play(self):
#         # Send PLAY
#         msg = encode_msg(0x00)
#         k,v = decode_rsp(self.s.process_klv(msg))
#         self.assertEqual(v['status'], 3) # No CPL or playlist loaded

#         # Check status is EJECT
#         msg = encode_msg(0x02)
#         k,v = decode_rsp(self.s.process_klv(msg))
#         self.assertEqual(v['status'], 0)
#         self.assertEqual(v['state'], 0)

#     # def test_stop(self):
#     #     # Send PLAY
#     #     msg = encode_msg(0x00)
#     #     k,v = decode_rsp(self.s.process_klv(msg))
#     #     self.assertEqual(v['status'], 0)

#     #     # Check status is PLAY
#     #     msg = encode_msg(0x02)
#     #     k,v = decode_rsp(self.s.process_klv(msg))
#     #     self.assertEqual(v['status'], 0)
#     #     self.assertEqual(v['state'], 2)

#     #     # Send STOP
#     #     msg = encode_msg(0x01)
#     #     k,v = decode_rsp(self.s.process_klv(msg))
#     #     self.assertEqual(v['status'], 0)

#     #     # Check status is STOP
#     #     msg = encode_msg(0x02)
#     #     k,v = decode_rsp(self.s.process_klv(msg))
#     #     self.assertEqual(v['status'], 0)
#     #     self.assertEqual(v['state'], 1)

#     def test_pause(self):
#         # Send PAUSE
#         msg = encode_msg(0x05)
#         k,v = decode_rsp(self.s.process_klv(msg))
#         self.assertEqual(v['status'], 3) # No CPL or playlist loaded

#         # Check status is EJECT
#         msg = bytearray(0x02)
#         k,v = decode_rsp(self.s.process_klv(msg))
#         self.assertEqual(v['status'], 0)
#         self.assertEqual(v['state'], 0)


if __name__ == '__main__':
    unittest.main()