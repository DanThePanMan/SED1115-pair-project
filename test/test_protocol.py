import unittest
from src.protocol.frame import *
from src.protocol.frame import _frame_header, _frame_header_escape, \
    _frame_escape, _frame_escape_escape, _frame_tail, _frame_tail_escape, \
    _create_general_frame
from src.protocol.util import Packet, FrameReader

class TestEscapeFunctions(unittest.TestCase):
    def test_no_escapes(self):
        data = b"Bello, world!"
        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertEqual(escaped, data)
        self.assertEqual(escaped, unescaped)
        
    def test_escaped_header(self):
        data = b"Hello,%b World!" % _frame_header.to_bytes()

        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertNotEqual(escaped, data)
        self.assertEqual(data, unescaped)

    def test_escaped_escape(self):
        data = b"Hello,%b World!" % _frame_escape.to_bytes()

        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertNotEqual(escaped, data)
        self.assertEqual(data, unescaped)

    def test_escaped_on_bounds(self):
        data = b"%bBello, world%b" % (_frame_escape.to_bytes(), _frame_header.to_bytes())

        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertNotEqual(escaped, data)
        self.assertEqual(bytes([_frame_escape, _frame_escape_escape, *b"Bello, world", _frame_escape, _frame_header_escape]), escaped)
        self.assertEqual(data, unescaped)

    def test_frame_creation(self):
        data = b"HelloG, world!"

        expected = bytearray()
        
        expected.extend(data)
        expected.append(calculate_checksum(data))
        expected = escape_content(expected)

        actual = _create_general_frame(data)

        self.assertEqual(bytes([_frame_header, *expected, _frame_tail]), actual)

    def test_packet_encode_decode(self):
        ackPacket = Packet("ack", True)
        nackPacket = Packet("nack", True)
        dataPacket = Packet("data", False, b"Hello, world!")

        ackBytes = bytes(ackPacket)
        nackBytes = bytes(nackPacket)
        dataBytes = bytes(dataPacket)

        decodedAckPacket = Packet.parse(ackBytes)
        decodedNackPacket = Packet.parse(nackBytes)
        decodedDataPacket = Packet.parse(dataBytes)

        self.assertEqual(ackPacket, decodedAckPacket)
        self.assertEqual(nackPacket, decodedNackPacket)
        self.assertEqual(dataPacket, decodedDataPacket)


    def test_packet_create(self):
        packet = Packet("data", False, b"Hello, world!")

        data = b"Hello, world!"
        escaped = escape_content(data)
        packet_bytes = bytes([_frame_header, *escaped, _frame_tail])

        self.assertEqual(bytes(packet), packet_bytes)