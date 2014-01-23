import unittest
from screener.app import ScreenServer

class TestPlaybackNoContentLoaded(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer()

    def test_status(self):
        # Check status starts at EJECT
        k,v = self.s.process_msg(0x02)
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

    def test_play(self):
        # Send PLAY
        k,v = self.s.process_msg(0x00)
        self.assertEqual(v['status'], 3) # No CPL or playlist loaded

        # Check status is EJECT
        k,v = self.s.process_msg(0x02)
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

    def test_pause(self):
        # Send PAUSE
        k,v = self.s.process_msg(0x05)
        self.assertEqual(v['status'], 3) # No CPL or playlist loaded

        # Check status is EJECT
        k,v = self.s.process_msg(0x02)
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

# @todo: Add in content loading/playing tests

if __name__ == '__main__':
    unittest.main()