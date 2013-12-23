import unittest
from screener import playlist, schedule

class TestSchedule(unittest.TestCase):

    def setUp(self):
        self.playlist = playlist.Playlist()

    def tearDown(self):
        pass

    def test_play(self):
        self.assertEqual(self.playback.status(), bytearray(b'{"state": 0}'))
        
        self.playback.play()
        self.assertEqual(self.playback.status(), bytearray(b'{"state": 1}'))

    def test_stop(self):
        self.assertEqual(self.playback.status(), bytearray(b'{"state": 0}'))
        
        self.playback.stop()
        self.assertEqual(self.playback.status(), bytearray(b'{"state": 0}'))

    def test_pause(self):
        self.assertEqual(self.playback.status(), bytearray(b'{"state": 0}'))
        
        self.playback.play()
        self.assertEqual(self.playback.status(), bytearray(b'{"state": 1}'))

        self.playback.pause()
        self.assertEqual(self.playback.status(), bytearray(b'{"state": 2}'))
