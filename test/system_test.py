import unittest
from datetime import datetime

from screener.app import ScreenServer
from test import encode_msg, decode_rsp

class TestSystem(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer()

    def test_system_time(self):
        msg = encode_msg(0x03)
        k,v = decode_rsp(self.s.process_klv(msg))
        self.assertEqual(v['status'], 0)
        self.assertTrue(datetime.fromtimestamp(v['time']))

if __name__ == '__main__':
    unittest.main()