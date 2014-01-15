from uuid import uuid4
from screener import rsp_codes

class Schedule(object):
    def __init__(self, content, playlists, playback):
        self.content = content
        self.playlists = playlists
        self.playback = playback

        # List of upcoming scheduled showings ordered by closest date to now() first
        self.schedule = {}

        self.available_modes = {0: "schedule", 1: "manual"}
        self.mode = 0 # Default to schedule mode

        # @todo: Start up thread to actually run the schedule if in schedule mode.

    def get_schedule_uuids(self, *args):
        raise NotImplementedError

    def get_schedule_info(self, schedule_uuid, *args):
        raise NotImplementedError

    def schedule_cpl(self, cpl_uuid, start_datetime, *args):
        """
        Schedules a cpl to play at a specified date/time.

        Args:
            cpl_uuid (string): The UUID of the cpl to be scheduled
            start_datetime (datetime): The date and time at which playback should begin

        Returns:
            The return status::

                0 -- Success
                1 -- CPL not found

            The schedule_uuid generated for future reference. This should be stored in the client.
        """

        try:
            cpl = self.content[cpl_uuid]
        except KeyError:
          return rsp_codes[1]

        while True:
            schedule_uuid = str(uuid4())

            # Just make sure we don't overwrite an existing schedule!
            if schedule_uuid not in self.schedule:
                self.schedule[schedule_uuid] = {"start": start_datetime, "cpl": cpl}
                break

        rsp = rsp_codes[0]
        rsp['schedule_uuid'] = schedule_uuid
        return rsp

    def schedule_playlist(self, playlist_uuid, start_datetime, *args):
        """
        Schedules a playlist to play at a specified date/time.

        Args:
            playlist_uuid (string): The UUID of the playlist to be scheduled
            start_datetime (datetime): The date and time at which playback should begin

        Returns:
            The return status::

                0 -- Success
                2 -- Playlist not found

            The schedule_uuid generated for future reference. This should be stored in the client.
        """

        try:
            playlist = self.playlists[playlist_uuid]
        except KeyError:
          return rsp_codes[2]

        while True:
            schedule_uuid = str(uuid4())

            # Just make sure we don't overwrite an existing schedule!
            if schedule_uuid not in self.schedule:
                self.schedule[schedule_uuid] = {"start": start_datetime, "playlist": playlist}
                break

        rsp = rsp_codes[0]
        rsp['schedule_uuid'] = schedule_uuid
        return rsp

    def delete_schedule(self, schedule_uuid, *args):
        """
        Schedules a playlist to play at a specified date/time.

        Args:
            schedule_uuid (string): The UUID of the schedule to be deleted

        Returns:
            The return status::

                0 -- Success
                2 -- Playlist not found
        """
        raise NotImplementedError

        try:
            schedule = self.schedule[schedule_uuid]
        except KeyError:
          return rsp_codes[2]

        return rsp_codes[0]

    def set_mode(self, mode, *args):
        """
        Set if the screen server is in schedule mode, i.e. does it obey the specified schedule or is it being manually overridden

        Args:
            mode (int): Mode to change to the scheduler into, see "Available Modes" below for the options

        Available Modes::

            0 (default) -- Schedule: Observes the scheduler, i.e. will automatically playback when has been scheduled
            1 -- Manual: Will not playback automatically, will only respond to manual playback requests


        Returns:
            The return status::

                0 -- Success
                9 -- Schedule mode not recognised
        """

        if mode not in self.available_modes:
            return rsp_codes[9]

        # @todo: Trigger change of mode itself! i.e. start/stop the thread!

        return rsp_codes[0]
