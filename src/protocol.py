# Utilities to deal with the protocol

from typing import Literal

# Used to indicate the beginning of a new frame
_frame_header = 0x47
_frame_header_escape = 0x57

# Used to indicate the end of a frame
_frame_tail = 0x48
_frame_tail_escape = 0x58

# Used to escape the frame header so we don't synchronize falsely
_frame_escape = 0x46
_frame_escape_escape = 0x56

def _create_general_frame(data: bytes) -> bytes:
    """
    Create a general frame given a body. Handles escaping and calculating the checksum.

    Args:
        data: The data of the frame. 
    
    Returns:
        An encoded frame.
    """

    # this is probably stupidly overcomplicated but it's a way to learn about framing!
    output = bytearray()

    # write data and calculate its checksum
    output.extend(data)
    output.append(calculate_checksum(data))

    # escape it and return our frame
    escaped = escape_content(output)

    return bytes([_frame_header, *escaped, _frame_tail])

def escape_content(content: bytes) -> bytes:
    """
    Escape content and make it suitable for transmission.

    Args:
        content: The content to escape.
    """

    output = bytearray()

    for byte in content:
        if byte == _frame_header:
            output.append(_frame_escape)
            output.append(_frame_header_escape)
        elif byte == _frame_tail:
            output.append(_frame_escape)
            output.append(_frame_tail_escape)
        elif byte == _frame_escape:
            output.append(_frame_escape)
            output.append(_frame_escape_escape)
        else:
            output.append(byte)
    
    return bytes(output)

def unescape_content(content: bytes) -> bytes:
    """
    Reverse the escaping process for transmitted bytes.

    Args:
        content: The escaped content to unescape.

    Raises:
        ValueError: Raised upon an invalid escape sequence
    """
    
    output = bytearray()

    pos = 0

    while pos < len(content):
        current = content[pos]

        # If we encounter the escape sequence,
        if current == _frame_escape:
            pos += 1

            # check there is another character
            if pos >= len(content):
                raise ValueError("Unterminated escape sequence")
            
            next = content[pos]

            # then try and decode the escape
            if next == _frame_escape_escape:
                output.append(_frame_escape)
            elif next == _frame_header_escape:
                output.append(_frame_header)
            elif next == _frame_tail_escape:
                output.append(_frame_tail)

            # otherwise raise an error
            else:
                raise ValueError("Invalid escape sequence")
        
        # if there's no escape sequence, just append the byte
        else:
            output.append(current)
        
        # advance
        pos += 1
    
    return bytes(output)
        

def calculate_checksum(content: bytes):
    """
    Calculate a checksum for the input content.
    
    Args:
        content: The content for which to calculate a checksum.
    """

    # rough implementation of LTE CRC-8
    crc = 0x00

    # I don't fully understand the math behind CRC nor do I want to
    # we truly stand on the shoulders of giants    
    for byte in content:
        crc ^= byte
        for _ in range(8): # we only use 8 bits so
            if crc & 0x80:
                crc = (crc << 1) ^ 0x9B
            else:
                crc = (crc << 1)

            # only keep 8 bits at any given time
            crc &= 0x0000_00FF
    
    return crc

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
    
    def __eq__(self, other: "object"):
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