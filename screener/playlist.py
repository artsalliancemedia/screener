
class Playlist(object):
    def __init__(self):
        self.loaded = None

    def load(self, spl):
        """
        Loads a SPL for playback
        """
        self.loaded = spl

    def status(self, *args):
        raise NotImplementedError

    def eject(self, *args):
        """
        Stop and unload the show playlist
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