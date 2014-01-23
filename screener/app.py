"""
A DCI media server emulator
"""
from twisted.internet import protocol, reactor
import logging, json

from screener import cfg
from screener.lib import config as config_handler
from screener.lib.util import encode_msg, decode_msg
from screener.lib.bus import Bus
from screener.system import system_time
from screener.playback import Playback
from screener.playlists import Playlists
from screener.content import Content
from screener.schedule import Schedule


class ScreenServer(object):
    def __init__(self):
        self.bus = Bus()

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

    def process_msg(self, handler_key, **kwargs):
        """
        Processes a KLV message by extracting JSON string from msg
        and passing it to the appropriate handlers
        """
        handler = self.handlers[handler_key]
        result = handler(**kwargs) or {}

        return handler_key, result

    def reset(self):
        self.__init__()


class Screener(protocol.Protocol):
    def __init__(self, screen_server, factory):
        self.ss = screen_server

        self.factory = factory

    def connectionMade(self):
        self.factory.clients.add(self)
        self.ss.bus.subscribe('to_client', self.send_rsp)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        self.ss.bus.unsubscribe('to_client', self.send_rsp)

    def dataReceived(self, data):
        header, params = decode_msg(data)
        response_key, return_data = self.ss.process_msg(header[15], params)

        # Send acknowledgement message back straight away, this should be keyed the same as the request.
        self.send_rsp(response_key, return_data)

    def send_rsp(self, response_key, result):
        encoded_data = encode_msg(response_key, **result)
        self.transport.write(str(encoded_data))


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
