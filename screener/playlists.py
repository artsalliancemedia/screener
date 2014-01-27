from uuid import uuid4
import traceback

from screener import rsp_codes
from smpteparsers.playlist import Playlist, PlaylistValidationError

class Playlists(object):
    def __init__(self):
        self.playlists = {}

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

    def insert_playlist(self, playlist_contents, *args):
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

        try:
            playlist = Playlist(playlist_contents)
        except PlaylistValidationError as e:
            rsp = rsp_codes[8]
            rsp['trace'] = traceback.format_exc()
            return rsp

        while True:
            playlist_uuid = str(uuid4())

            # Just make sure we don't overwrite an existing playlist!
            if playlist_uuid not in self.playlists:
                self.playlists[playlist_uuid] = playlist
                break

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
            playlist_uuid (str): UUID of the playlist to delete

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