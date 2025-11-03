class PacketType:
    # Sorry this code sucks


    # A request to get the configured duty cycle.
    request_config: 'PacketType'

    # A response to REQUEST_CONFIG, containing a uint16
    response_config: 'PacketType'

    # A request to get the measured duty cycle
    request_measured: 'PacketType'

    # A respone to REQUEST_MEASURED, containing a uint16
    response_measured: 'PacketType'
    
    value: int 
    def __init__(self, value: int):
        if not (0 <= value <= 3):
            raise ValueError("Value must be between 0 .. 3")
        self.value = value

    def __eq__(self, other: object):
        return isinstance(other, PacketType) and self.value == other.value
    
    def __hash__(self):
        return hash(self.value)
    
    def name(self) -> str:
        return {
            0: "request_config",
            1: "response_config",
            2: "request_measured",
            3: "response_measured"
        }[self.value]

# set static instances
PacketType.request_config = PacketType(0)
PacketType.response_config = PacketType(1)
PacketType.request_measured = PacketType(2)
PacketType.response_measured = PacketType(3)


class Packet():
    # Packet header: marks the beginning of a packet.
    # Used for synchronization if an error occurs.
    ctrl_header = 0x10
    header_escape = 0x11

    # Packet escape: marks an escape sequence.
    ctrl_escape = 0x12

    @staticmethod
    def _make_packet(type: PacketType, data: bytearray|None):
        buffer = bytearray()
        
        # Write the header and type to the buffer.
        buffer.append(Packet.ctrl_header)
        Packet._escape(bytes([type.value]), buffer)

        # Write the data to the buffer if any.
        if data is not None: 
            Packet._escape(data, buffer)

        return bytes(buffer)

    @staticmethod
    def _escape(data: bytes, buffer: bytearray) -> bytearray:
        """
        Escapes a given sequence of bytes, replacing control characters
        with an appropriate sequence. 

        Arguments:
            data (bytes): The data to escape
            buffer (bytearray): The bytearray to write to
        """
        for byte in data:
            if byte == Packet.ctrl_header:
                buffer.append(Packet.ctrl_escape)
                buffer.append(Packet.header_escape)
            elif byte == Packet.ctrl_escape:
                buffer.append(Packet.ctrl_escape)
                buffer.append(Packet.ctrl_escape)
            else:
                buffer.append(byte)

        return buffer

    @staticmethod
    def _unescape(data: bytes):
        """
        Unescapes a given sequence of bytes, replacing escape sequences
        with appropriate control characters.
        """
        out_data = bytearray()

        last_was_escape = False
        for byte in data:
            if byte == Packet.ctrl_escape and not last_was_escape:
                last_was_escape = True
                continue
            
            elif last_was_escape:
                if byte == Packet.ctrl_escape:
                    out_data.append(Packet.ctrl_escape)
                elif byte == Packet.header_escape:
                    out_data.append(Packet.ctrl_header)
                else:
                    raise ValueError(f"Invalid escape sequence (char {byte})")
                last_was_escape = False
            
            else:
                out_data.append(byte)

        if last_was_escape:
            raise ValueError("Last byte cannot be escape sequence")
        return out_data
            
    @staticmethod
    def create_response_config(value: int):
        """
        Arguments:
            value (int): The value as a uint16.

        Raises:
            ValueError: if value is not convertible to a uint16.
        """
        try:
            value_bytes = bytearray(value.to_bytes(2, 'big'))
        except OverflowError:
            raise ValueError("The provided value cannot be converted to a uint16.")
        
        return Packet._make_packet(PacketType.response_config, value_bytes)
    
    @staticmethod
    def create_request_config(value: int):
        """
        Arguments:
            value (int): The value as a uint16.

        Raises:
            ValueError: if value is not convertible to a uint16.
        """
        try:
            value_bytes = bytearray(value.to_bytes(2, 'big'))
        except OverflowError:
            raise ValueError("The provided value cannot be converted to a uint16.")
        return Packet._make_packet(PacketType.request_config, value_bytes)
    
    @staticmethod
    def create_request_measured():
        return Packet._make_packet(PacketType.request_measured, None)
    
    @staticmethod
    def create_response_measured(value: int):
        """
        Arguments:
            value (int): The value as a uint16.

        Raises:
            ValueError: if value is not convertible to a uint16.
        """
        try:
            value_bytes = bytearray(value.to_bytes(2, 'big'))
        except OverflowError:
            raise ValueError("The provided value cannot be converted to a uint16.")
        return Packet._make_packet(PacketType.response_measured, value_bytes)
    
    @staticmethod
    def decode(packet_bytes: bytes) -> 'tuple[PacketType, int|None]':
        """
        Decode a packet from its bytes.
        
        Raises:
            ValueError: The provided bytes do not form a valid packet.
        """
        if len(packet_bytes) < 2:
            raise ValueError("Packet too short!")
        
        if packet_bytes[0] != Packet.ctrl_header:
            raise ValueError("Packet must start with a header!")
        
        packet_bytes = Packet._unescape(packet_bytes[1:])

        try:
            packet_type = PacketType(packet_bytes[0])
        except ValueError:
            raise

        # extract a value from the packet if it has one
        if packet_type == PacketType.response_measured or packet_type == PacketType.response_config \
                or packet_type == PacketType.request_config:
            assert len(packet_bytes) == 3, f"packet with data should be 4 bytes long, got {len(packet_bytes) + 1}"

            val = int.from_bytes(packet_bytes[1:3], 'big')
            return packet_type, val
        else:
            assert len(packet_bytes) == 1, f"packet with no data should be 2 bytes long, got {len(packet_bytes) + 1}"

            return packet_type, None