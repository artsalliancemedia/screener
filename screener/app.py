"""
A DCI media server emulator
"""
from twisted.internet import protocol, reactor
import klv
from util import int_to_bytes
from system import system_time
from playback import Playback
from content import Content

content = Content()
playback = Playback()

HEADER = '\x00' * 16

HANDLERS = {0x00 : playback.play,  0x01 : playback.stop,
            0x02 : playback.status, 0x03 : system_time,
            0x04 : content.uuids}

def process_klv(msg):
    """
    Processes a KLV message
    """
    k,v = klv.decode(msg, 16)
    result = HANDLERS[k[15]](v) or ''
    return klv.encode(HEADER, result)

# Twisted socket server

class Screener(protocol.Protocol):
    def dataReceived(self, data):
        return_data = process_klv(data)
        self.transport.write(str(return_data))
        
class ScreenerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Screener()

if __name__ == '__main__':
    reactor.listenTCP(1234, ScreenerFactory())
    reactor.run()