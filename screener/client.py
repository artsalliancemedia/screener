'''
A basic testing client for the Screener app
'''
import socket
from datetime import datetime
import json
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

def decode_repsonse(rsp):
    k,v = klv.decode(rsp)
    try:
        return json.loads(bytes_to_str(v))

def send(handler_key, obj=None, host='localhost', port=9500):
    '''
    Takes json serialisable python objects and constructs a
    SMTPE conformant KVL message and sends it via an instance of
    the connection class, Comm, on the given host and port.
    '''
    # See SMPTE ST-336-2007 for details on the header format
    key = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 8) + [handler_key]
    if obj:
        value = json.dumps(obj)
        msg = klv.encode(key,value)
    else:
        msg = bytearray(key+[0x00]) # 0 length, 0 message

    with Comm(host, port) as c:
        return c.send_recv(msg)


def play(host='localhost', port=9500):
    rsp = send(0x00)
    k,v = klv.decode(rsp, 16)
    return bytes_to_int(v)

def stop(host='localhost', port=9500):
    rsp = send(0x01)
    k,v = klv.decode(rsp, 16)
    return bytes_to_int(v)

def status(host='localhost', port=9500):
    rsp = send(0x02)
    k,v = klv.decode(rsp, 16)
    return bytes_to_int(v)

def content_uuids(host='localhost', port=9500):
    rsp = send(0x20)
    k,v = klv.decode(rsp, 16)
    return json.loads(bytes_to_str(v))

def system_time(host='localhost', port=9500):
    rsp = send(0x40)
    k,v = klv.decode(rsp, 16)
    return datetime.fromtimestamp(bytes_to_int(v))


def ingest(uuid,
           connection_details={'host':'10.58.4.8',
                               'user':'pullingest',
                               'passwd':'pullingest'},
           host='localhost',
           port=9500):
    '''
    Sends the ingest DCP command to screener, returns the ingest queue uuid.
    '''
    rsp = send(0x06,
               {'dcp_path':uuid,
               'connection_details': connection_details},
               host,
               port)
    k,v = klv.decode(rsp, 16)
    return json.loads(bytes_to_str(v))


if __name__ == '__main__':

    uuid = '00a2c129-891d-4fec-a567-01ddc335452d'
    print 'Ingesting: {0}.\nQueue UUID = {1}'.format(uuid, ingest(uuid)['uuid'])


