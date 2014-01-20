'''
A basic testing client for the Screener app
'''
import socket, json
from datetime import datetime

import klv
from util import bytes_to_int, bytes_to_str


class Comm(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __enter__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port,))
        return self
        
    def __exit__(self, *args):
        self.s.close()

    def send_recv(self, msg):
        self.s.sendall(msg)
        return self.s.recv(1024)


class Client(object):
    def __init__(self):
        self.host = u'localhost'
        self.port = 9500

    def decode_rsp(self, rsp):
        k, v = klv.decode(rsp, 16)
        return json.loads(bytes_to_str(v))

    def send(self, handler_key, **kwargs):
        '''
        Takes json serialisable python objects and constructs a
        SMTPE conformant KVL message and sends it via an instance of
        the connection class, Comm, on the given host and port.
        '''
        # See SMPTE ST-336-2007 for details on the header format
        key = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 8) + [handler_key]
        if kwargs:
            value = json.dumps(kwargs)
            msg = klv.encode(key, value)
        else:
            msg = bytearray(key+[0x00]) # 0 length, 0 message

        with Comm(self.host, self.port) as c:
            return c.send_recv(msg)


    def play(self):
        rsp = self.send(0x00)
        return self.decode_rsp(rsp)

    def stop(self):
        rsp = self.send(0x01)
        return self.decode_rsp(rsp)

    def status(self):
        rsp = self.send(0x02)
        return self.decode_rsp(rsp)

    def system_time(self):
        rsp = self.send(0x03)
        return datetime.fromtimestamp(self.decode_rsp(rsp))

    def content_uuids(self):
        rsp = self.send(0x04)
        return self.decode_rsp(rsp)

    def pause(self):
        rsp = self.send(0x05)
        return self.decode_rsp(rsp)

    def ingest(self, connection_details, dcp_path):
        # Sends the ingest DCP command to screener, returns the ingest queue uuid.
        rsp = self.send(0x06, connection_details=connection_details, dcp_path=dcp_path)
        return self.decode_rsp(rsp)

    def get_ingests_info(self, ingest_uuids):
        rsp = self.send(0x07, ingest_uuids=ingest_uuids)
        return self.decode_rsp(rsp)

    def get_ingest_info(self, ingest_uuid):
        rsp = self.send(0x08, ingest_uuid=ingest_uuid)
        return self.decode_rsp(rsp)


if __name__ == '__main__':
    client = Client()

    #CR 13/01 14:40 added 'mode' arg
    connection_details = {"host": "10.58.4.8", "port": 21, "user": "pullingest", "passwd":
	    "pullingest", "mode": "active"}
    dcp_path = '0bb2e1a7-d5fd-49dd-b480-8f4deb61e82a'
    # dcp_path = '010ab1b1-8ef7-9440-b2f7-a47ea84ee010'
#     dcp_path = 'ef32ddd6-80ee-4f85-93b9-449230804b0b'
#     dcp_path = '0b56b850-eda7-441e-bc20-d48062e5b2f3'
    # 0bb2e1a7-d5fd-49dd-b480-8f4deb61e82a # With sub-folder
    # 00a2c129-891d-4fec-a567-01ddc335452d # Without sub-folder.

    ingest_uuid = client.ingest(connection_details, dcp_path)
    print u'Ingesting DCP: {dcp_path}. Queue UUID: "{ingest_uuid}"'.format(dcp_path=dcp_path, ingest_uuid=ingest_uuid)

    info = client.get_ingests_info([ingest_uuid])
    print u'DCP Info (should be a list): ', info

    info = client.get_ingest_info(ingest_uuid)
    print u'DCP Info: ', info

