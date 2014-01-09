"""
A DCI media server emulator
"""
from twisted.internet import protocol, reactor
import cfg
import klv
import logging
import json
from util import int_to_bytes, bytes_to_str
from system import system_time
from playback import Playback
from content import Content
from schedule import Schedule


# See SMPTE ST-336-2007 for details on the header format
HEADER = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 9)


class Screener(protocol.Protocol):

    def __init__(self, factory):
        logging.info('Instantiating Screener()')
        self.factory = factory

    def dataReceived(self, data):
        return_data = self.factory.process_klv(data)
        self.transport.write(str(return_data))


class ScreenerFactory(protocol.Factory):

    def __init__(self):
        logging.info('Instantiating ScreenerFactory()')
        self.content = Content()
        self.playback = Playback()
        self.schedule = Schedule()

        self.handlers = HANDLERS = {
                0x00 : self.playback.play,
                0x01 : self.playback.stop,
                0x02 : self.playback.status,
                0x03 : system_time,
                0x04 : self.content.get_cpl_uuids,
                0x05 : self.playback.pause,
                0x06 : self.content.ingest
            }

    def buildProtocol(self, addr):
        return Screener(self)

    def process_klv(self, msg):
        """
        Processes a KLV message by extracting JSON string from msg
        and passing it to the appropriate handler
        """
        k,v = klv.decode(msg, 16)
        handler = self.handlers[k[15]]
        v = json.loads(bytes_to_str(v))
        result = handler(v) or ''
        return klv.encode(HEADER, json.dumps({'response':result}))

    def reset(self):
        self.__init__()



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
    host, port = cfg.screener_host, cfg.screener_port
    setup_logging()
    logging.info('Setting up Screener')
    reactor.listenTCP(port, ScreenerFactory(), interface=host)
    logging.info('Serving on localhost:{0}'.format(port))
    reactor.run()
