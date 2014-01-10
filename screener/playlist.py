import json
from uuid import uuid4
from smpteparsers.spl import SPLParser, SPLParserError
from playback import Playback
from util import str_to_bytes, int_to_bytes


class Playlist(object):
    def __init__(self, playlist_uuid=None):
        self._playlists = {}
        self.spl_parser = SPLParser()

        self.load_spl(playlist_uuid)

    def insert_spl(self, spl, *args):
        """
        Saves a show playlist into memory for playback.

        Args:
            spl (dict): 

        Returns:
            dict. The return code::

                0 -- Success
                1 -- Invalid show playlist supplied
        """

        try:
            self.spl_parser.validate(spl)
        except SPLParserError:
            return str_to_bytes(json.dumps({'state': 1}))

        playlist_uuid = str(uuid4())
        self._playlists[playlist_uuid] = spl

        return str_to_bytes(json.dumps({'playlist_uuid': playlist_uuid, 'state': 0}))

    def update_spl(self, playlist_uuid, spl, *args):
        """
        Saves a show playlist into memory for playback.

        Args:
            playlist_uuid (str): UUID of the playlist to load
            spl (dict): 

        Returns:
            int. The return code::

                0 -- Success
                1 -- Invalid show playlist supplied
                2 -- Show playlist not found
        """

        try:
            self.spl_parser.validate(spl)
        except SPLParserError:
            return int_to_bytes(1)

        try:
            self._playlists[playlist_uuid] = spl
        except KeyError:
            return int_to_bytes(2)

        return int_to_bytes(0)

    def delete_spl(self, playlist_uuid, *args):
        """
        Saves a show playlist into memory for playback.

        Args:
            playlist_uuid (str): UUID of the playlist to load

        Returns:
            int. The return code::

                0 -- Success
                1 -- Show playlist not found
        """

        try:
            del(self._playlists[playlist_uuid])
        except KeyError:
            return int_to_bytes(1)

        return int_to_bytes(0)

    def load_spl(self, playlist_uuid):
        """
        Loads a show playlist into memory for playback.

        Args:
            playlist_uuid (str): UUID of the playlist to load

        Returns:
            int. The return code::

                0 -- Success
                1 -- Playlist not found
        """

        self.loaded_spl = self._playlists.get(playlist_uuid, None)

        if self.loaded_spl is not None:
            return int_to_bytes(0)

        return int_to_bytes(1)

    def status(self, *args):
        raise NotImplementedError

    def eject(self, *args):
        """
        Stop the playback and unload the current show playlist
        """
        raise NotImplementedError

    def skip_forward(self, *args):
        """
        Skip forward to the next item in the playlist
        """
        raise NotImplementedError

    def skip_backward(self, *args):
        """
        Skip backward to the next item in the playlist
        """
        raise NotImplementedError

    def skip_to_position(self, position, *args):
        """
        Skip to a specific position in the playlist
        """
        raise NotImplementedError

    def skip_to_event(self, event_id, *args):
        """
        Skip to a specific event in the playlist, i.e. a particular piece of content
        """
        raise NotImplementedError