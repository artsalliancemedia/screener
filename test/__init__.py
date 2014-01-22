import json

import klv
from screener.util import bytes_to_str

def encode_msg(handler_key, **kwargs):
    '''
    Takes json serialisable python objects and constructs a SMTPE conformant KVL message
    '''
    # See SMPTE ST-336-2007 for details on the header format
    key = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 8) + [handler_key]
    if kwargs:
        value = json.dumps(kwargs)
        msg = klv.encode(key, value)
    else:
        msg = bytearray(key+[0x00]) # 0 length, 0 message

    return msg

def decode_rsp(rsp):
    k, v = klv.decode(rsp, 16)
    return k, json.loads(bytes_to_str(v))