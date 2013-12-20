

class Schedule(object):
    def __init__(self):
        # List of upcoming scheduled showings ordered by closest date to now() first
        self.schedule = []

    def get_schedule_uuids(self, *args):
        raise NotImplementedError

    def get_schedule_info(self, schedule_uuid, *args):
        raise NotImplementedError

    def schedule_playlist(self, playlist_id, start_datetime, *args):
        raise NotImplementedError

    def delete(self, schedule_id, *args):
        raise NotImplementedError

    def set_mode(mode, *args):
        """
        Set if the screen server is in schedule mode, i.e. does it obey the specified schedule or is it being manually overridden
        """
        raise NotImplementedError
