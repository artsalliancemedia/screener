import unittest, os, shutil
from screener.app import ScreenServer
from screener.lib import config as config_handler
from screener import cfg

paths = {
    'incoming': os.path.join(os.path.dirname(__file__), 'INCOMING'),
    'assets': os.path.join(os.path.dirname(__file__), 'ASSET'),
    'ingest': os.path.join(os.path.dirname(__file__), 'INGEST'),
    'playlists': os.path.join(os.path.dirname(__file__), 'PLAYLISTS')
}

class TestPlaybackNoContentLoaded(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer(paths=paths)

    def tearDown(self):
        # Manually call this so it doesn't complain about not having the playlists_path when it deletes itself going out of scope.
        del(self.s)

        for v in paths.itervalues():
            shutil.rmtree(v)

    def test_status(self):
        # Check status starts at EJECT
        k,v = self.s.process_msg(0x02)
        self.assertEqual(k, 0x02)
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

    def test_play(self):
        # Send PLAY
        k,v = self.s.process_msg(0x00)
        self.assertEqual(k, 0x00)
        self.assertEqual(v['status'], 3) # No CPL or playlist loaded

        # Check status is EJECT
        k,v = self.s.process_msg(0x02)
        self.assertEqual(k, 0x02)
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

    def test_pause(self):
        # Send PAUSE
        k,v = self.s.process_msg(0x05)
        self.assertEqual(k, 0x05)
        self.assertEqual(v['status'], 3) # No CPL or playlist loaded

        # Check status is EJECT
        k,v = self.s.process_msg(0x02)
        self.assertEqual(k, 0x02)
        self.assertEqual(v['status'], 0)
        self.assertEqual(v['state'], 0)

# @todo: Add in content loading/playing tests

if __name__ == '__main__':
    unittest.main()
