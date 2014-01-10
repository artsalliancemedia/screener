import playlist

class Schedule(object):
    def __init__(self):
        # List of upcoming scheduled showings ordered by closest date to now() first
        self.schedule = []
        self.mode = "schedule"

        # @todo: Start up thread to actually run the schedule if in schedule mode.

    def get_schedule_uuids(self, *args):
        raise NotImplementedError

    def get_schedule_info(self, schedule_uuid, *args):
        raise NotImplementedError

    def schedule_playlist(self, playlist_uuid, start_datetime, *args):
        """
        Schedules a saved playlist for a specified datetime.

        Returns:
            int. The return code::

                0 -- Success
                1 -- Playlist not found
        """

        try:
            found_playlist = playlist.stored_playlists[playlist_uuid]
        except KeyError:
          return int_to_bytes(1)

        self.schedule.append({"start": start_datetime, "end": end_datetime, "playlist": found_playlist})

        return int_to_bytes(0)

    def delete(self, schedule_id, *args):
        raise NotImplementedError

    def set_mode(mode, *args):
        """
        Set if the screen server is in schedule mode, i.e. does it obey the specified schedule or is it being manually overridden

        Returns:
            int. The return code::

                0 -- Success
        """

        raise NotImplementedError
