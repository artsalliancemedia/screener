import unittest
from screener.lib.util import encode_msg, decode_msg

BASE_EXPECTED_KEY = bytearray([0x06, 0x0e, 0x2b, 0x34, 0x02, 0x04, 0x01] + ([0x00] * 8))

class TestEncodeMsg(unittest.TestCase):
    def test_key(self):
        # First additional byte is the handler key, second byte is the length.
        self.assertEqual(encode_msg(0x00), BASE_EXPECTED_KEY + bytearray([0x00, 0x00]))
        self.assertEqual(encode_msg(0x10), BASE_EXPECTED_KEY + bytearray([0x10, 0x00]))
        self.assertEqual(encode_msg(0x0A), BASE_EXPECTED_KEY + bytearray([0x0A, 0x00]))
        self.assertEqual(encode_msg(0xFF), BASE_EXPECTED_KEY + bytearray([0xFF, 0x00]))

    def test_length(self):
        self.assertEqual(encode_msg(0x00)[16], 0x00)
        self.assertEqual(encode_msg(0x00, test=None)[16], 0x0e)
        self.assertEqual(encode_msg(0x00, test=True)[16], 0x0e)
        self.assertEqual(encode_msg(0x00, foo=1, bar=1.1)[16], 0x25)
        self.assertEqual(encode_msg(0x00, foo="bar")[16], 0x0e)
        self.assertEqual(encode_msg(0x00, foo=["bar"])[16], 0x10)
        self.assertEqual(encode_msg(0x00, foo={"bar": True})[16], 0x16)
        self.assertEqual(encode_msg(0x00, foo={"bar": [True]})[16], 0x18)

    def test_val(self):
        self.assertEqual(encode_msg(0x00), BASE_EXPECTED_KEY + bytearray([0x00, 0x00]))
        self.assertEqual(encode_msg(0x00, test=None), BASE_EXPECTED_KEY + bytearray([0x00, 0x0e] + list('{"test": null}')))
        self.assertEqual(encode_msg(0x00, test=True), BASE_EXPECTED_KEY + bytearray([0x00, 0x0e] + list('{"test": true}')))
        self.assertEqual(encode_msg(0x00, foo=1, bar=1.1), BASE_EXPECTED_KEY + bytearray([0x00, 0x25] + list('{"foo": 1, "bar": 1.1000000000000001}')))
        self.assertEqual(encode_msg(0x00, foo="bar"), BASE_EXPECTED_KEY + bytearray([0x00, 0x0e] + list('{"foo": "bar"}')))
        self.assertEqual(encode_msg(0x00, foo=["bar"]), BASE_EXPECTED_KEY + bytearray([0x00, 0x10] + list('{"foo": ["bar"]}')))
        self.assertEqual(encode_msg(0x00, foo={"bar": True}), BASE_EXPECTED_KEY + bytearray([0x00, 0x16] + list('{"foo": {"bar": true}}')))
        self.assertEqual(encode_msg(0x00, foo={"bar": [True]}), BASE_EXPECTED_KEY + bytearray([0x00, 0x18] + list('{"foo": {"bar": [true]}}')))


class TestDecodeMsg(unittest.TestCase):
    def test_key(self):
        msg = BASE_EXPECTED_KEY + bytearray([0x00, 0x00])
        k,v = decode_msg(msg)
        self.assertEqual(k[15], 0x00)

        msg = BASE_EXPECTED_KEY + bytearray([0x05, 0x00])
        k,v = decode_msg(msg)
        self.assertEqual(k[15], 0x05)

        msg = BASE_EXPECTED_KEY + bytearray([0xFF, 0x00])
        k,v = decode_msg(msg)
        self.assertEqual(k[15], 0xFF)

    def test_val(self):
        msg = BASE_EXPECTED_KEY + bytearray([0x00, 0x0e] + list('{"test": null}'))
        k,v = decode_msg(msg)
        self.assertEqual(v, {"test": None})

        msg = BASE_EXPECTED_KEY + bytearray([0x00, 0x0e] + list('{"test": true}'))
        k,v = decode_msg(msg)
        self.assertEqual(v, {"test": True})

        msg = BASE_EXPECTED_KEY + bytearray([0x00, 0x25] + list('{"foo": 1, "bar": 1.1000000000000001}'))
        k,v = decode_msg(msg)
        self.assertEqual(v, {"foo": 1, "bar": 1.1})

        msg = BASE_EXPECTED_KEY + bytearray([0x00, 0x18] + list('{"foo": {"bar": [true]}}'))
        k,v = decode_msg(msg)
        self.assertEqual(v, {"foo": {"bar": [True]}})

if __name__ == '__main__':
    unittest.main()