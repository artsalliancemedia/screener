import unittest
from datetime import datetime

from screener.app import ScreenServer

class TestSystem(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer()

    def test_system_time(self):
        k,v = self.s.process_msg(0x03)
        self.assertEqual(k, 0x3)
        self.assertEqual(v['status'], 0)
        self.assertTrue(datetime.fromtimestamp(v['time']))

if __name__ == '__main__':
    unittest.main()