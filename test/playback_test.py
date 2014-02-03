import unittest, os, shutil
from screener.app import ScreenServer
from screener.lib import config as config_handler
from screener import cfg

incoming_path = os.path.join(os.path.dirname(__file__), 'INCOMING')
assets_path = os.path.join(os.path.dirname(__file__), 'ASSET')
ingest_path = os.path.join(os.path.dirname(__file__), 'INGEST')
playlists_path = os.path.join(os.path.dirname(__file__), 'PLAYLISTS')

class TestPlaybackNoContentLoaded(unittest.TestCase):
    def setUp(self):
        paths = {
            "incoming": incoming_path,
            "assets": assets_path,
            "ingest": ingest_path,
            "playlists": playlists_path
        }
        self.s = ScreenServer(paths=paths)

    def tearDown(self):
        # Manually call this so it doesn't complain about not having the playlists_path when it deletes itself going out of scope.
        del(self.s)

        # Clear up the playlists path
        if os.path.isdir(incoming_path):
            shutil.rmtree(incoming_path)

        if os.path.isdir(assets_path):
            shutil.rmtree(assets_path)

        if os.path.isdir(ingest_path):
            shutil.rmtree(ingest_path)

        if os.path.isdir(playlists_path):
            shutil.rmtree(playlists_path)

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
