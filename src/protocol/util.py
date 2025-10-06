from .frame import _frame_escape, _frame_escape_escape, _frame_header, _frame_header_escape, _frame_tail, _frame_tail_escape, _create_general_frame
from .frame import *

class Packet():
    """
    Class for representing, parsing, and encoding packets.
    """

    type: "Literal['ack', 'nack', 'data']"
    sequence_bit: bool
    body: bytes

    def __init__(self, type: "Literal['ack', 'nack', 'data']", 
                 sequence_bit: bool, body: "bytes|None" = None):
        self.type = type
        self.sequence_bit = sequence_bit
        self.body = bytes() if body is None else body

    def __repr__(self) -> str:
        return f"Packet(type={self.type}, sequence={1 if self.sequence_bit else 0}, data={self.body})"

    def __bytes__(self) -> bytes:
        return self.encode()
    
    def __eq__(self, other: "object") -> bool:
        return isinstance(other, Packet) and self.type == other.type \
            and self.sequence_bit == other.sequence_bit and self.body == other.body

    @staticmethod
    def parse(frame: bytes) -> 'Packet | None':
        """
        Takes a frame and attempts to parse it into a packet.

        Args:
            packet: The bytes of the packet to parse.
        
        Returns:
            A Packet if it can be successfully parsed, otherwise None.
        """

        # 1 byte for header + 1 byte for (type + sequence) + 1 byte for checksum + 1 byte for tail
        if len(frame) < 4 or frame[0] != _frame_header or frame[-1] != _frame_tail:
            print("Packet too short")
            return None

        # Find the unescaped content and its checksum
        unescaped = unescape_content(frame[1:-1])

        # Exclude the checksum itself from the checksum calculation!
        expected_checksum = calculate_checksum(unescaped[:-1])

        if unescaped[-1] != expected_checksum:
            print("Unexpected checksum")
            return None
        
        # Decode the type
        type_bits = (unescaped[0] & 0b1100_0000) >> 6

        type_map: "dict[int, Literal['ack', 'nack', 'data']]" = \
        {
            0b00: "ack",
            0b01: "nack",
            0b10: "data",
            0b11: "data",
        }

        try:
            type = type_map[type_bits]
        except KeyError:
            raise Exception("error in packet type handling logic: invalid packet type")

        # Extract the sequence
        sequence = (unescaped[0] & 0b0010_0000) >> 5
        sequence = True if sequence != 0 else False

        # Data is what's left over
        data = unescaped[1:-1]

        return Packet(type=type, sequence_bit=sequence, body=data)

    def encode(self) -> bytes:
        """
        Encode a Packet object as bytes.
        """
        type_map = {
            "ack": 0b00,
            "nack": 0b01,
            "data": 0b10,
        }

        type_bytes = type_map[self.type] << 6
        sequence_bytes = (1 if self.sequence_bit else 0) << 5

        output = bytearray()
        
        header = type_bytes | sequence_bytes
        output.append(header)

        output.extend(self.body)

        return _create_general_frame(output)

class FrameReader():
    """
    Class to aid in reading frames and processing packets from bytes.
    """
    
    # store received bytes
    _bytes_buffer: bytearray

    # store packets
    _packets_buffer: "list[Packet]"

    # whether or not we're reading a specific frame currently
    _reading_frame: bool

    def __init__(self):
        self._bytes_buffer = bytearray()
        self._packets_buffer = []
        self._reading_frame = False
    
    def read(self, bytes: bytes):
        """
        Read a bytes object into the buffer and process packets as they occur.
        """
        pos = 0
        while pos < len(bytes):
            if not self._reading_frame:
                if bytes[pos] == _frame_header:
                    self._reading_frame = True
                    self._bytes_buffer.append(bytes[pos])
                pos += 1
            else:
                self._bytes_buffer.append(bytes[pos])
                if bytes[pos] == _frame_tail:
                    self._reading_frame = False
                    self._process_packet()
                pos += 1

    def get_queued_packets(self):
        """
        Return a list of all the currently queued packets.
        """
        current_packets = self._packets_buffer
        self._packets_buffer = [] 
        return current_packets

    def _process_packet(self):
        """
        Called when the buffer currently contains a frame. Try and process a packet from the byte buffer.
        """
        parsed = Packet.parse(self._bytes_buffer)
        if parsed is not None:
            self._packets_buffer.append(parsed)
        self._bytes_buffer.clear()

