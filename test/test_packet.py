from unittest import TestCase

from src.packet import format_packet, split_packet


class TestPacket(TestCase):
    def test_format_decode(self):
        packet = ['m', str(34923)]
        formatted = format_packet(packet)
        decoded = split_packet(formatted)

        self.assertEqual(formatted, b"m,34923;")
        self.assertEqual(decoded, packet)

    def test_format_decode_2(self):
        packet = ['e', str(43023), str(2340)]

        formatted = format_packet(packet)
        decoded = split_packet(formatted)

        self.assertEqual(formatted, b"e,43023,2340;")
        self.assertEqual(decoded, packet)

    def test_one_arg(self):
        packet = ['t']

        formatted = format_packet(packet)
        decoded = split_packet(formatted)

        self.assertEqual(formatted, b"t;")
        self.assertEqual(decoded, packet)

    def test_empty_args(self):
        packet = ['t', '', '3']

        formatted = format_packet(packet)
        decoded = split_packet(formatted)

        self.assertEqual(formatted, b"t,,3;")
        self.assertEqual(decoded, packet)