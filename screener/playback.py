"""
Playback functions
"""
import json
from util import int_to_bytes, str_to_bytes

STOP, PLAY, PAUSE = range(3)

class Playback(object):
    """
    Playback state
    """

    def __init__(self):
        self.state = STOP
        self.loaded = None

    def load(self, cpl):
        """
        Loads a CPL for playback
        """
        self.loaded = cpl

    def play(self, *args):
        self.state = PLAY
        return int_to_bytes(0)

    def stop(self, *args):
        self.state = STOP
        return int_to_bytes(0)

    def pause(self, *args):
        self.state = PAUSE
        return int_to_bytes(0)

    def status(self, *args):
        state = { 'state' : self.state }
        if self.loaded:
            state['cpl'] = self.loaded
        return str_to_bytes(json.dumps(state))