'''
A basic testing client for the Screener app
'''
import socket, json, traceback, time
from datetime import datetime
from threading import Thread, RLock

import klv
from screener.lib.util import bytes_to_str, encode_msg, decode_msg

"""
Core communication methods to and from the server.
"""

class CommMixin(object):
    """
    Deal with low level calls to the socket, i.e. deal with bytestream encoding (KLV).
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port,))

        return self

    def close(self, *args):
        self.s.close()

    def send_msg(self, handler_key, **kwargs):
        msg = encode_msg(handler_key, **kwargs)
        self.s.sendall(msg)

    def recv_rsp(self, key_len=16, length_len=4):
        """
        The key is a a fixed size with the value length parameter variable but up to 4 bytes. Therefore read the first 20
        bytes to determine to value length and read the rest of the value for the socket into rsp and return it for processing.
        """
        rsp = bytearray(self.s.recv(key_len + length_len))
        val_length, ber_length = klv.decode_ber(rsp[key_len:])
        rsp += bytearray(self.s.recv(val_length - (4 - ber_length)))

        return decode_msg(rsp)


class Client(CommMixin):
    """
    Deal with high level, app specific details of the implementation of the client.
    """
    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        # Just used for testing, make sure that only one thread can write to the console at any one time.
        self.out_lock = RLock()

        self.playback = Playback(self)
        self.content = Content(self)
        self.system = System(self)

        self.rsp_handlers = {
            0x06: self.content.ingest_rsp,
            0x07: self.content.get_ingests_info_rsp,
            0x08: self.content.get_ingest_info_rsp
        }

        # Kick off a background thread to handle and messages that come back from the screen server.
        self.rsp_thread = Thread(target=self.process_rsp, args=(self.rsp_handlers,), name='ProcessResponse')
        self.rsp_thread.daemon = True
        self.rsp_thread.start()

    def process_rsp(self, rsp_handlers):
        # This function runs continuously and will read anything back from the socket and process it.
        k, v = self.recv_rsp()

        # @todo: Implement a back-pressure queue to avoid potentially lost messages from the server.
        rsp_handlers[k[15]](**v)

"""
Potenital Response Messages
"""

class ContentResponseMixin(object):
    def ingest_rsp(self, ingest_uuid, *args, **kwargs):
        with self.c.out_lock:
            print u'Ingesting DCP... Queue UUID: "{ingest_uuid}"'.format(ingest_uuid=ingest_uuid)

    def get_ingests_info_rsp(self, info):
        with self.c.out_lock:
            print u'DCP Info (should be a list): ', info

    def get_ingest_info_rsp(self, info):
        with self.c.out_lock:
            print u'DCP Info: ', info

"""
Available Client Actions
"""

# Not the biggest fan of this class but not sure of better option.
class ClientAPI(object):
    def __init__(self, client):
        self.c = client

class Playback(ClientAPI):
    def play(self):
        self.c.send_msg(0x00)

    def stop(self):
        self.c.send_msg(0x01)

    def status(self):
        self.c.send_msg(0x02)

    def pause(self):
        self.c.send_msg(0x05)

class System(ClientAPI):
    def system_time(self):
        self.c.send_msg(0x03)

class Content(ClientAPI, ContentResponseMixin):
    def content_uuids(self):
        self.c.send_msg(0x04)

    def ingest(self, connection_details, dcp_path):
        # Sends the ingest DCP command to screener, returns the ingest queue uuid.
        self.c.send_msg(0x06, connection_details=connection_details, dcp_path=dcp_path)

    def get_ingests_info(self, ingest_uuids):
        self.c.send_msg(0x07, ingest_uuids=ingest_uuids)

    def get_ingest_info(self, ingest_uuid):
        self.c.send_msg(0x08, ingest_uuid=ingest_uuid)


if __name__ == '__main__':
    while True:
        try:
            client = Client(host=u'localhost', port=9500)

            connection_details = {"host": "10.58.4.8", "port": 21, "user": "pullingest", "passwd": "pullingest"}
            dcp_path = '0bb2e1a7-d5fd-49dd-b480-8f4deb61e82a'
            # 0bb2e1a7-d5fd-49dd-b480-8f4deb61e82a # With sub-folder
            # 00a2c129-891d-4fec-a567-01ddc335452d # Without sub-folder.

            with client.out_lock:
                print "Beginning to ingest"

            client.content.ingest(connection_details, dcp_path)

            with client.out_lock:
                print "Ingest call complete, await a response I guess"

            time.sleep(10)

        except socket.error as e:
            print "Socket Error: \n"
            print traceback.format_exc()
            print "Reconnecting in 2 seconds..."
            time.sleep(2)
        finally:
            client.close()

