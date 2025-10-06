# Module 'protocol'

Contains a series of functions and classes related to the protocol.

## Usage
**Creating a packet**:

Use the `Packet` class's constructor to create new packets.
```py
from src.protocol import Packet, FrameReader

ack = Packet("ack", True)
data = Packet("data", True, b"Hello, world!")
```

To convert a packet to bytes for writing, call `bytes()` or use `Packet.encode`

```py
print(ack.encode()) # b'G dH'
```

**Decoding a packet**:

If you're decoding a Packet and have the full frame, use `Packet.parse`:

```py
packet = Packet.parse(b'G dH') # Packet(type=ack, sequence=1, data=b'')
```

If you're directly reading from the serial communication, use the `FrameReader` class. It automatically handles constructing packets:
```py
reader = FrameReader()

while True:
    # read bytes from serial here
    serial_bytes = read_bytes()
    reader.read(serial_bytes)

    for packet in reader.get_queued_packets():
        print(packet)
```

e.g.
```py
reader = FrameReader()

reader.read(b'G\x80FX')
print(reader.get_queued_packets()) # []
reader.read(b'ello, world!\xe8H')
print(reader.get_queued_packets()) # [Packet(type=data, sequence=0, data=b'Hello, world!')]
print(reader.get_queued_packets()) # []
```

## Contents
### util.py
Contains the utilities for creating and reading packets and frames.
```py
class Packet():
    type: Literal['ack', 'nack', 'data']
    sequence_bit: bool
    body: bytes
    
    def __init__(self, type: Literal['ack', 'nack', 'data'], sequence_bit: bool, body: bytes|None = None): ...
    def __repr__(self) -> str: ...
    def __bytes__(self) -> bytes: ...
    def __eq__(self, other: object) -> bool: ...
    
    @staticmethod
    def parse(frame: bytes) -> Packet|None: ...
    
    def encode(self) -> bytes: ...

class FrameReader():
    def __init__(self): ...
    def read(self, bytes: bytes): ...
    def get_queued_packets(self) -> list[Packet]: ...
```

### frame.py

Generally contains lower-level implementation details. You should not be working with these functions directly.
```py
    _frame_header: int = 0x47
    _frame_header_escape: int = 0x57
    _frame_tail: int = 0x48
    _frame_tail_escape: int = 0x58
    _frame_escape: int = 0x46
    _frame_escape_escape: int = 0x56

    def escape_content(content: bytes) -> bytes: ...
    def unescape_content(content: bytes) -> bytes: ...
    def calculate_checksum(content: bytes) -> int: ... 
    def _create_general_frame(data: bytes) -> bytes: ...
```

