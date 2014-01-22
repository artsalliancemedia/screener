Screener
============

Screener is the Arts Alliance Media test screen server. It is designed to replicate a working digital cinema screen server as closely as possible handling content ingestion, scheduling and playback amongst many other tasks. The API itself is an amalgamation of the best practices we've seen from various vendors we support within our Screenwriter TMS software.

The API is socket based with data encoding at the socket level in KLV format and at the app level in JSON. This documentation attempts to describe the API is close detail.

Content API
-----------

The Content API handles all aspects of content management of site on both screen and library servers.

.. autoclass:: screener.content.Content
   :members: get_cpl_uuids, get_cpls, get_cpl, ingest, cancel_ingest, get_ingest_history, clear_ingest_history, get_ingests_info, get_ingest_info

Playlists API
-------------

The Playlists API stores user generated playlists of content ready for schedule or playback by Screener.

.. autoclass:: screener.playlists.Playlists
   :members: get_playlist_uuids, get_playlists, get_playlist, insert_playlist, update_playlist, delete_playlist


Playback API
------------

The Playback API handles common playback tasks the screen server performs.

.. autoclass:: screener.playback.Playback
   :members: load_cpl, load_playlist, eject, play, pause, stop, status, skip_forward, skip_backward, skip_to_position, skip_to_event


Schedule API
------------

The Schedule API handles automatic playback of content at times specified by the client.

.. autoclass:: screener.schedule.Schedule
   :members: get_schedule_uuids, get_schedules, get_schedule, schedule_cpl, schedule_playlist, delete_schedule, set_mode

