import json
import klv
from screener.util import bytes_to_int, bytes_to_str

def decode_rsp(rsp):
    k, v = klv.decode(rsp, 16)
    return k, json.loads(bytes_to_str(v))