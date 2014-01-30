from uuid import uuid4
import traceback, os, json

from screener import rsp_codes
from smpteparsers.playlist import Playlist, PlaylistValidationError

class Playlists(object):
    def __init__(self, playlists_path=None):
        """
        Initialises the Playlist store, reads in playlists stored on disk if the path is supplied.

        Args:
            playlists_path (string, None): The directory containing the playlist files in json format.
        """
        self.playlists = {}
        self.playlists_path = playlists_path

        # If a playlists path is given we should read them in.
        if self.playlists_path is not None:
            # First ensure we have a directory to work from!
            if not os.path.isdir(self.playlists_path):
                os.mkdir(self.playlists_path)

            # Secondly read in the files themselves.
            for filename in os.listdir(self.playlists_path):
                filepath = os.path.path(self.playlists_path, filename)
                with open(filepath) as pl_file:
                    contents = json.load(pl_file)
                    self.playlists[filename] = Playlist(contents)

    def __del__(self):
        """
        Save all the playlists in memory to the disk before exiting. Each playlist is stored in a separate
        file named by the playlist UUID, it removes any old playlists first to clear out any deleted items.
        """
        if self.playlists_path is None:
            return
        else:
            # Clear out the directory ready for the next lot, gets around deleting easily.
            for filename in os.listdir(self.playlists_path):
                filepath = os.path.join(self.playlists_path, filename)
                if os.path.isfile(filepath):
                    os.unlink(filepath)

        for uuid, playlist in self.playlists.iteritems():
            playlist_path = os.path.join(self.playlists_path, uuid)
            with open(playlist_path, 'w') as pl_file:
                json.dumps(str(playlist), pl_file)

    def __getitem__(self, k):
        return self.playlists[k]

    def get_playlist_uuids(self, *args):
        """
        Grab the UUID's of all the playlists on the system

        Returns:
            The return status::

                0 -- Success
        """

        rsp = rsp_codes[0]
        rsp['playlist_uuids'] = self.playlists.keys()
        return rsp

    def get_playlists(self, playlist_uuids, *args):
        """
        Grab information about a particular playlist

        Args:
            playlist_uuids (list): The UUIDs of the playlists you want to grab info for.

        Returns:
            The return status::

                0 -- Success
                2 -- Playlist not found
        """

        playlists = []
        for playlist_uuid in playlist_uuids:
            status = self.get_playlist(playlist_uuid)
            if status['status'] != 0:
                return status # Error getting the playlist

            # Discard the other information and keep the playlist object :)
            playlists.append(status['playlist'])

        rsp = rsp_codes[0]
        rsp['playlists'] = playlists
        return rsp

    def get_playlist(self, playlist_uuid, *args):
        """
        Grab information about a particular playlist

        Args:
            playlist_uuid (string): The UUID of the playlist to grab info for

        Returns:
            The return status::

                0 -- Success
                2 -- Playlist not found
        """

        if playlist_uuid not in self.playlists:
            return rsp_codes[2]

        rsp = rsp_codes[0]
        rsp['playlist'] = self.playlists[playlist_uuid]
        return rsp

    def insert_playlist(self, playlist_contents):
        """
        Saves a show playlist into memory for playback.

        Args:
            playlist_contents (dict): Takes the dict structure used for the internal playlist representation in Screenwriter.

        Returns:
            The return status::

                0 -- Success
                8 -- Invalid playlist supplied

            The playlist_uuid generated for future reference. This should be stored in the client.
        """

        # Just make sure we don't overwrite an existing playlist! Silly python not having do-while..
        while True:
            playlist_uuid = str(uuid4())
            if playlist_uuid not in self.playlists:
                break

        try:
            playlist = Playlist(playlist_contents)
        except PlaylistValidationError as e:
            rsp = rsp_codes[8]
            rsp['trace'] = traceback.format_exc()
            return rsp

        self.playlists[playlist_uuid] = playlist

        rsp = rsp_codes[0]
        rsp['playlist_uuid'] = playlist_uuid
        return rsp

    def update_playlist(self, playlist_uuid, playlist_contents, *args):
        """
        Saves a show playlist into memory for playback.

        Args:
            playlist_uuid (string): UUID of the playlist to update
            playlist_contents (dict): Takes the dict structure used for the internal playlist representation in Screenwriter.

        Returns:
            The return status::

                0 -- Success
                2 -- Playlist not found
                8 -- Invalid playlist supplied
        """

        if playlist_uuid not in self.playlists:
            return rsp_codes[2]

        try:
            playlist = Playlist(playlist_contents)
        except PlaylistValidationError:
            rsp = rsp_codes[8]
            rsp['trace'] = traceback.format_exc()
            return rsp

        self.playlists[playlist_uuid] = playlist

        return rsp_codes[0]

    def delete_playlist(self, playlist_uuid, *args):
        """
        Saves a show playlist into memory for playback.

        Args:
            playlist_uuid (string): UUID of the playlist to delete

        Returns:
            The return status::

                0 -- Success
                2 -- Playlist not found
        """

        try:
            del(self.playlists[playlist_uuid])
        except KeyError:
            return rsp_codes[2]

        return rsp_codes[0]