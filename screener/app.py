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

# See SMPTE ST-336-2007 for details on the header format
HEADER = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 9)

class ScreenServer(object):

    def __init__(self):
        self.content = Content()
        self.playback = Playback()
        self.schedule = Schedule()

        self.handlers = HANDLERS = {
                0x00 : self.playback.play,
                0x01 : self.playback.stop,
                0x02 : self.playback.status,
                0x03 : system_time,
                0x04 : self.content.get_cpl_uuids,
                0x05 : self.playback.pause
            }

    def process_klv(self, msg):
        """
        Processes a KLV message
        """
        k,v = klv.decode(msg, 16)
        result = self.handlers[k[15]](v) or ''
        return klv.encode(HEADER, result)

    def reset(self):
        self.__init__()

# Twisted socket server

class Screener(protocol.Protocol):

    def __init__(self):
        self.screener = ScreenServer()

    def dataReceived(self, data):
        return_data = self.screener.process_klv(data)
        self.transport.write(str(return_data))
        
class ScreenerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Screener()

if __name__ == '__main__':
    reactor.listenTCP(9500, ScreenerFactory())
    reactor.run()