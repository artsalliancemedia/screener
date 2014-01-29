import unittest, os, shutil
from test import uuid_re
from screener.app import ScreenServer

# Minimal info required for a playlist to be successful.
success_playlist = """
{
    "title": "Test playlist",
    "duration": 3600,
    "events": [
        {
            "cpl_id": "00000000-0000-0000-0000-100000000001",
            "type": "composition",
            "text": "Test CPL",
            "duration_in_frames": 43200,
            "duration_in_seconds": 1800,
            "edit_rate": [24, 1]
        },
        {
            "cpl_id": "00000000-0000-0000-0000-100000000002",
            "type": "composition",
            "text": "Test CPL 2",
            "duration_in_frames": 43200,
            "duration_in_seconds": 1800,
            "edit_rate": [24, 1]
        }
    ]
}
"""

playlists_path = os.path.join(os.path.dirname(__file__), 'PLAYLISTS')

class TestPlaylistsDefaultState(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer(playlists_path=playlists_path)

    def tearDown(self):
        # Manually call this so it doesn't complain about not having the playlists_path when it deletes itself going out of scope.
        del(self.s)

        # Clear up the playlists path
        if os.path.isdir(playlists_path):
            shutil.rmtree(playlists_path)

    def test_defaults(self):
        # Try to get the list of playlist_uuids
        k,v = self.s.process_msg(0x26)
        self.assertEqual(k, 0x26)
        self.assertEqual(v['status'], 0)
        self.assertEqual(len(v['playlist_uuids']), 0)

    def test_no_playlist_found(self):
        # Try to get a playlist that doesn't exist
        k,v = self.s.process_msg(0x27, playlist_uuids=["00000000-0000-0000-0000-000000000000"])
        self.assertEqual(k, 0x27)
        self.assertEqual(v['status'], 2)

        # Try to get a playlist that doesn't exist
        k,v = self.s.process_msg(0x28, playlist_uuid="00000000-0000-0000-0000-000000000000")
        self.assertEqual(k, 0x28)
        self.assertEqual(v['status'], 2)

        # Try to update a playlist that doesn't exist
        k,v = self.s.process_msg(0x17, playlist_uuid="00000000-0000-0000-0000-000000000000", playlist_contents="")
        self.assertEqual(k, 0x17)
        self.assertEqual(v['status'], 2)

        # Try to delete a playlist that doesn't exist
        k,v = self.s.process_msg(0x18, playlist_uuid="00000000-0000-0000-0000-000000000000")
        self.assertEqual(k, 0x18)
        self.assertEqual(v['status'], 2)

    def test_insert_success(self):
        # Try to insert a playlist that should be successful
        k,v = self.s.process_msg(0x16, playlist_contents=success_playlist)
        self.assertEqual(k, 0x16)
        self.assertEqual(v['status'], 0)
        self.assertTrue(uuid_re.match(v['playlist_uuid']))

        # Try to get the list of playlist_uuids, make sure it's been put in the store correctly.
        k,v = self.s.process_msg(0x26)
        self.assertEqual(k, 0x26)
        self.assertEqual(v['status'], 0)
        self.assertEqual(len(v['playlist_uuids']), 1)

    def test_insert_fail(self):
        # Try to insert a blank playlist, this should fail as invalid!
        k,v = self.s.process_msg(0x16, playlist_contents="")
        self.assertEqual(k, 0x16)
        self.assertEqual(v['status'], 8)

        # Try to get the list of playlist_uuids, make sure it's not been put into the content store by mistake.
        k,v = self.s.process_msg(0x26)
        self.assertEqual(k, 0x26)
        self.assertEqual(v['status'], 0)
        self.assertEqual(len(v['playlist_uuids']), 0)

class TestPlaylistsExists(unittest.TestCase):
    def setUp(self):
        self.s = ScreenServer(playlists_path=playlists_path)

        # Insert a playlist that we can manipulate.
        k,v = self.s.process_msg(0x16, playlist_contents=success_playlist)
        self.playlist_uuid = v['playlist_uuid']

    def tearDown(self):
        # Manually call this so it doesn't complain about not having the playlists_path when it deletes itself going out of scope.
        del(self.s)

        # Clear up the playlists path
        if os.path.isdir(playlists_path):
            shutil.rmtree(playlists_path)

    def test_update_success(self):
        # Try to update a playlist that should be successful
        k,v = self.s.process_msg(0x17, playlist_uuid=self.playlist_uuid, playlist_contents=success_playlist)
        self.assertEqual(k, 0x17)
        self.assertEqual(v['status'], 0)

        # Try to get the list of playlist_uuids, make sure nothing weird has happened as a result
        k,v = self.s.process_msg(0x26)
        self.assertEqual(k, 0x26)
        self.assertEqual(v['status'], 0)
        self.assertEqual(len(v['playlist_uuids']), 1)

    def test_update_fail(self):
        # Try to update the playlist to be blank, this should fail as invalid!
        k,v = self.s.process_msg(0x17, playlist_uuid=self.playlist_uuid, playlist_contents="")
        self.assertEqual(k, 0x17)
        self.assertEqual(v['status'], 8)

        # Try to get the list of playlist_uuids, make sure nothing weird has happened as a result.
        k,v = self.s.process_msg(0x26)
        self.assertEqual(k, 0x26)
        self.assertEqual(v['status'], 0)
        self.assertEqual(len(v['playlist_uuids']), 1)

    def test_delete_success(self):
        # Try to delete a playlist, it should be successful
        k,v = self.s.process_msg(0x18, playlist_uuid=self.playlist_uuid)
        self.assertEqual(k, 0x18)
        self.assertEqual(v['status'], 0)

        # Try to get the list of playlist_uuids, make sure it's actually gone.
        k,v = self.s.process_msg(0x26)
        self.assertEqual(k, 0x26)
        self.assertEqual(v['status'], 0)
        self.assertEqual(len(v['playlist_uuids']), 0)

if __name__ == '__main__':
    unittest.main()