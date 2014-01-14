"""
Playback functions
"""
import json

STOP, PLAY, PAUSE = range(3)

class Playback(object):
    """
    Playback state
    """

    def __init__(self):
        self.state = STOP
        self.loaded_cpl = None

    def load_cpl(self, cpl):
        """
        Loads a CPL for playback

        Args:
            cpl (str): Cpl struct that should be loaded into the server for playback.

        Returns:
            int. The return code::

                0 -- Success
        """
        self.loaded_cpl = cpl

        return 0

    def eject(self, *args):
        """
        Stop the playback and unload the current cpl

        Returns:
            int. The return code::

                0 -- Success
        """
        self.state = STOP
        self.loaded_cpl = None

        return 0

    def play(self, *args):
        self.state = PLAY

        print 0
        return 0

    def stop(self, *args):
        self.state = STOP
        return 0

    def pause(self, *args):
        self.state = PAUSE
        return 0

    def status(self, *args):
        state = { 'state' : self.state }
        if self.loaded_cpl:
            state['cpl'] = self.loaded_cpl

        return state