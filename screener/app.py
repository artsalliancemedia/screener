"""
A DCI media server emulator
"""
from twisted.internet import protocol, reactor
import logging, json

import klv

from screener import cfg
from screener.lib import config as config_handler
from screener.lib.util import int_to_bytes, bytes_to_str
from screener.system import system_time
from screener.playback import Playback
from screener.playlists import Playlists
from screener.content import Content
from screener.schedule import Schedule


# See SMPTE ST-336-2007 for details on the header format
HEADER = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 8)

class ScreenServer(object):
    def __init__(self):
        self.content = Content()
        self.playlists = Playlists()
        self.playback = Playback(self.content, self.playlists)
        self.schedule = Schedule(self.content, self.playlists, self.playback)

        # @todo: Work out what to do with numbering. Provisional idea is content spans 1-20, playlists 21-40 etc.
        # @todo: Make these hex instead of decimal!!!
        self.handlers = {
                0x29 : self.content.get_cpl_uuids,
                0x30 : self.content.get_cpls,
                0x31 : self.content.get_cpl,
                0x06 : self.content.ingest,
                0x07 : self.content.get_ingests_info,
                0x08 : self.content.get_ingest_info,
                0x32 : self.content.cancel_ingest,
                0x33 : self.content.get_ingest_history,
                0x34 : self.content.clear_ingest_history,

                0x26 : self.playlists.get_playlist_uuids,
                0x27 : self.playlists.get_playlists,
                0x28 : self.playlists.get_playlist,
                0x16 : self.playlists.insert_playlist,
                0x17 : self.playlists.update_playlist,
                0x18 : self.playlists.delete_playlist,

                0x09 : self.playback.load_cpl,
                0x10 : self.playback.load_playlist,
                0x11 : self.playback.eject,
                0x00 : self.playback.play,
                0x01 : self.playback.stop,
                0x02 : self.playback.status,
                0x05 : self.playback.pause,
                0x12 : self.playback.skip_forward,
                0x13 : self.playback.skip_backward,
                0x14 : self.playback.skip_to_position,
                0x15 : self.playback.skip_to_event,

                0x19 : self.schedule.get_schedule_uuids,
                0x20 : self.schedule.get_schedules,
                0x21 : self.schedule.get_schedule,
                0x22 : self.schedule.schedule_cpl,
                0x23 : self.schedule.schedule_playlist,
                0x24 : self.schedule.delete_schedule,
                0x25 : self.schedule.set_mode,

                0x03 : system_time
            }

    def process_klv(self, msg):
        """
        Processes a KLV message by extracting JSON string from msg
        and passing it to the appropriate handlers
        """
        k, v = klv.decode(msg, 16)
        handler = self.handlers[k[15]]

        val = bytes_to_str(v)
        decoded_val = json.loads(val) if val else {}
        result = handler(**decoded_val)

        return klv.encode(HEADER + [k[15]], json.dumps(result))

    def reset(self):
        self.__init__()


class Screener(protocol.Protocol):
    def __init__(self, screen_server, factory):
        self.ss = screen_server
        self.factory = factory

    def connectionMade(self):
        self.factory.clients.add(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)

    def dataReceived(self, data):
        return_data = self.ss.process_klv(data)
        self.transport.write(str(return_data))


class ScreenerFactory(protocol.Factory):
    def startFactory(self):
        self.clients = set()

        logging.info('Instantiating ScreenServer()')
        # We want a singleton instance of the screen server so we persist storage of assets between calls.
        self.ss = ScreenServer()

    def stopFactory(self):
        for c in self.clients:
            c.transport.loseConnection()

    def buildProtocol(self, addr):
        return Screener(self.ss, self)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(threadName)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logging.getLogger('screener')


if __name__ == '__main__':
    config_handler.read(cfg.config_file())
    config_handler.save()
    setup_logging()

    logging.info('Setting up Screener')
    reactor.listenTCP(cfg.screener_port(), ScreenerFactory(), interface=cfg.screener_host())

    logging.info('Serving on localhost:{0}'.format(cfg.screener_port()))
    reactor.run()
