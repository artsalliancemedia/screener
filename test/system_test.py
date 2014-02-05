import unittest, os, shutil
from datetime import datetime

from screener.app import ScreenServer
from screener.lib import config as config_handler
from screener import cfg

paths = {
    'incoming': os.path.join(os.path.dirname(__file__), 'INCOMING'),
    'assets': os.path.join(os.path.dirname(__file__), 'ASSET'),
    'ingest': os.path.join(os.path.dirname(__file__), 'INGEST'),
    'playlists': os.path.join(os.path.dirname(__file__), 'PLAYLISTS')
}

class TestSystem(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer(paths=paths)

    def tearDown(self):
        # Manually call this so it doesn't complain about not having the playlists_path when it deletes itself going out of scope.
        del(self.s)

        for v in paths.itervalues():
            shutil.rmtree(v)

    def test_system_time(self):
        k,v = self.s.process_msg(0x03)
        self.assertEqual(k, 0x03)
        self.assertEqual(v['status'], 0)
        self.assertTrue(datetime.fromtimestamp(v['time']))

if __name__ == '__main__':
    unittest.main()
