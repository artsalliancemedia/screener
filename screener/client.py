import socket
from datetime import datetime
import json
import klv
from util import bytes_to_int, bytes_to_str

def comm(msg):
    HOST = 'localhost'
    PORT = 1234
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT,))
    s.sendall(msg)
    data = s.recv(1024)
    s.close()
    return data

def play(comm=comm):
    msg = bytearray('\x00' * 15 + '\x00' + '\x00')
    rst = comm(msg)
    k,v = klv.decode(rst, 16)
    return bytes_to_int(v)

def stop(comm=comm):
    msg = bytearray('\x00' * 15 + '\x01' + '\x00')
    rst = comm(msg)
    k,v = klv.decode(rst, 16)
    return bytes_to_int(v)

def status(comm=comm):
    msg = bytearray('\x00' * 15 + '\x02' + '\x00')
    rst = comm(msg)
    k,v = klv.decode(rst, 16)
    return bytes_to_str(v)

def system_time(comm=comm):
    msg = bytearray('\x00' * 15 + '\x03' + '\x00')
    rst = comm(msg)
    k,v = klv.decode(rst, 16)
    return datetime.fromtimestamp(bytes_to_int(v))

def content_uuids(comm=comm):
    msg = bytearray('\x00' * 15 + '\x04' + '\x00')
    rst = comm(msg)
    k,v = klv.decode(rst, 16)
    return json.loads(bytes_to_str(v))

class Comms(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def open(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port,))

    def send_recv(self, msg):
        self.s.sendall(msg)
        return self.s.recv(1024)

    def close(self):
        self.s.close()

comms = Comms('localhost', 1234)
comms.open()
print 'System time: %s' % system_time(comms.send_recv).isoformat()
print 'Content UUIDs: %s' % content_uuids(comms.send_recv)
print 'Stop response: %d' % stop(comms.send_recv)
print 'Playing status: %s' % status(comms.send_recv)
print 'Play response: %d' % play(comms.send_recv)
print 'Playing status: %s' % status(comms.send_recv)
comms.close()