"""
A DCI media server emulator
"""
from twisted.internet import protocol, reactor
import klv
from util import int_to_bytes
from system import system_time
from playback import Playback
from content import Content
from schedule import Schedule
import logging

# See SMPTE ST-336-2007 for details on the header format
HEADER = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 9)


class Screener(protocol.Protocol):

    def __init__(self, factory):
        logging.info('Instantiating Screener()')
        self.factory = factory
        # self.screener = ScreenServer()

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
        Processes a KLV message
        """
        k,v = klv.decode(msg, 16)
        result = self.handlers[k[15]](v) or ''
        return klv.encode(HEADER, result)

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
    port = 9500
    setup_logging()
    logging.info('Setting up Screener')
    reactor.listenTCP(port, ScreenerFactory())
    logging.info('Serving on localhost:{0}'.format(port))
    reactor.run()
