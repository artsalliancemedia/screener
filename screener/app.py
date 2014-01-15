"""
A DCI media server emulator
"""
from twisted.internet import protocol, reactor
import logging, json

import klv

from screener import cfg
from screener.lib import config as config_handler
from screener.util import int_to_bytes, bytes_to_str
from screener.system import system_time
from screener.playback import Playback
from screener.playlists import Playlists
from screener.content import Content
from screener.schedule import Schedule


# See SMPTE ST-336-2007 for details on the header format
HEADER = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 9)

class ScreenServer(object):
    def __init__(self):
        self.content = Content()
        self.playlists = Playlists(self.content)
        self.playback = Playback(self.content, self.playlists)
        self.schedule = Schedule(self.content, self.playlists, self.playback)

        self.handlers = {
                0x00 : self.playback.play,
                0x01 : self.playback.stop,
                0x02 : self.playback.status,
                0x03 : system_time,
                0x04 : self.content.get_cpl_uuids,
                0x05 : self.playback.pause,
                0x06 : self.content.ingest,
                0x07 : self.content.get_ingests_info,
                0x08 : self.content.get_ingest_info,
                0x09 : self.playback.load_cpl,
                0x10 : self.playback.load_playlist,
                0x11 : self.playback.eject,
                0x12 : self.playback.skip_forward,
                0x13 : self.playback.skip_backward,
                0x14 : self.playback.skip_to_position,
                0x15 : self.playback.skip_to_event,
                0x16 : self.playlists.insert_playlist,
                0x17 : self.playlists.update_playlist,
                0x18 : self.playlists.delete_playlist
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

        return klv.encode(HEADER, json.dumps(result))

    def reset(self):
        self.__init__()


class Screener(protocol.Protocol):
    def __init__(self):
        logging.info('Instantiating Screener()')
        self.screener = ScreenServer()

    def dataReceived(self, data):
        return_data = self.screener.process_klv(data)
        self.transport.write(str(return_data))


class ScreenerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Screener()


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
