from screener import rsp_codes
from smpteparsers.cpl import CPL
from smpteparsers.playlist import Playlist, PlaylistValidationError

EJECT, STOP, PLAY, PAUSE = range(4)

class Playback(object):
    def __init__(self, content, playlists):
        self.content = content
        self.playlists = playlists

        self.state = EJECT
        self.loaded_item = None

    def load_cpl(self, cpl_uuid, *args):
        """
        Loads a CPL for playback

        Args:
            cpl_uuid (string): Cpl uuid of the content to load

        Returns:
            The return status::

                0 -- Success
                1 -- CPL not found
        """
        status = self.eject()
        if status['status'] != 0:
            return status # Problem ejecting, lets return.

        try:
            self.loaded_item = self.content[cpl_uuid]
        except KeyError:
            return rsp_codes[1]

        # @todo: Validate loaded item, use XSD perhaps? This validation should be built into the CPL parser in smpteparsers!


        try:
            self.loaded_item.validate()
        except CPLPlaylistValidationError as e:
            rsp = rsp_codes[8]
            rsp['trace'] = traceback.format_exc()
            return rsp

        status = self.stop()
        if status['status'] != 0:
            return status # Problem stopping, lets return.

        return rsp_codes[0]

    def load_playlist(self, playlist_uuid, *args):
        """
        Loads a show playlist into memory for playback.

        Args:
            playlist_uuid (string): UUID of the playlist to load

        Returns:
            The return status::

                0 -- Success
                2 -- Playlist not found
                8 -- Invalid playlist supplied
        """
        status = self.eject()
        if status['status'] != 0:
            return status # Problem ejecting, lets return.

        try:
            self.loaded_item = self.playlists[playlist_uuid]
        except KeyError:
            return rsp_codes[2]

        try:
            # @todo: Make this an extended validation, i.e. include whether the content/KDMs exist on the server as well as just that the playlist isn't malformed.
            self.loaded_item.validate()
        except PlaylistValidationError as e:
            rsp = rsp_codes[8]
            rsp['trace'] = traceback.format_exc()
            return rsp

        status = self.stop()
        if status['status'] != 0:
            return status # Problem stopping, lets return.

        return rsp_codes[0]

    def eject(self, *args):
        """
        Stop the playback and unload the current item

        Returns:
            The return status::

                0 -- Success
        """
        self.state = EJECT
        self.loaded_item = None

        return rsp_codes[0]

    def play(self, *args):
        """
        Plays the loaded item

        Returns:
            The return status::

                0 -- Success
                3 -- No CPL or Playlist loaded
        """
        if self.loaded_item is None:
            return rsp_codes[3]

        self.state = PLAY
        return rsp_codes[0]

    def stop(self, *args):
        """
        Stops the current item playing

        Returns:
            The return status::

                0 -- Success
        """

        self.state = STOP
        return rsp_codes[0]

    def pause(self, *args):
        """
        Pauses the loaded item

        Returns:
            The return status::

                0 -- Success
                3 -- No CPL or Playlist loaded
        """
        if self.loaded_item is None:
            return rsp_codes[3]

        self.state = PAUSE
        return rsp_codes[0]

    def skip_forward(self, *args):
        """
        Skip forward to the next item in the playlist

        Returns:
            The return status::

                0 -- Success
                4 -- CPL loaded. Load a playlist to skip
                5 -- No Playlist loaded
        """
        if isinstance(self.loaded_item, CPL):
            return rsp_codes[4]

        if not isinstance(self.loaded_item, Playlist):
            return rsp_codes[5]

        # @todo: Implement logic

        return rsp_codes[0]

    def skip_backward(self, *args):
        """
        Skip backward to the next item in the playlist

        Returns:
            The return status::

                0 -- Success
                4 -- CPL loaded. Load a playlist to skip
                5 -- No Playlist loaded
        """
        if isinstance(self.loaded_item, CPL):
            return rsp_codes[4]

        if not isinstance(self.loaded_item, Playlist):
            return rsp_codes[5]

        # @todo: Implement logic

        return rsp_codes[0]

    def skip_to_position(self, position, *args):
        """
        Skip to a specific position in the playlist

        Args:
            position (int): The index position of the event in the playlist to skip to.

        Returns:
            The return status::

                0 -- Success
                4 -- CPL loaded. Load a playlist to skip
                5 -- No Playlist loaded
                6 -- Position not found
        """
        if isinstance(self.loaded_item, CPL):
            return rsp_codes[4]

        if not isinstance(self.loaded_item, Playlist):
            return rsp_codes[5]

        # @todo: Implement logic

        return rsp_codes[0]

    def skip_to_event(self, event_uuid, *args):
        """
        Skip to a specific event in the playlist, i.e. a particular piece of content

        Args:
            event_uuid (string): The uuid of the event in the playlist to skip to.

        Returns:
            The return status::

                0 -- Success
                4 -- CPL loaded. Load a playlist to skip
                5 -- No Playlist loaded
                7 -- Playlist event not found
        """
        if isinstance(self.loaded_item, CPL):
            return rsp_codes[4]

        if not isinstance(self.loaded_item, Playlist):
            return rsp_codes[5]

        # @todo: Implement logic

        return rsp_codes[0]

    def status(self, *args):
        """
        Skip to a specific event in the playlist, i.e. a particular piece of content

        Returns:
            The return status::

                0 -- Success

            Possible playback state values::

                0 -- Ejected
                1 -- Stopped
                2 -- Playing
                3 -- Paused

            Also brief information on playlist or cpl loaded, if one is loaded.
        """
        rsp = rsp_codes[0]
        rsp['state'] = self.state

        if isinstance(self.loaded_item, Playlist):
            rsp['playlist'] = unicode(self.loaded_item)
        elif isinstance(self.loaded_item, CPL):
            rsp['cpl'] = unicode(self.loaded_item)

        return rsp