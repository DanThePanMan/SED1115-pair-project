from unittest import TestCase

from src.packet import format_packet, split_packet


class TestPacket(TestCase):
    def test_format_decode(self):
        packet = ['m', str(34923)]
        formatted = format_packet(packet)
        decoded = split_packet(formatted)

        self.assertEqual(formatted, b"m,34923;")
        self.assertEqual(decoded, packet)
