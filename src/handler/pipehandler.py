# Partly AI Generated for testing purposes

from handler.messagehandler import MessageHandler
from protocol import Packet, PacketType
from config import TYPECHECKING, TARGET
from log import log_trace, log_error

if TYPECHECKING:
    from typing import Callable
    from multiprocessing.connection import Connection

class PipeMessageHandler(MessageHandler):
    def __init__(self, conn: 'Connection'):
        if TARGET != "python":
            raise NotImplementedError("Not implemented for targets other than python")
        self.conn = conn
        self.callback: 'Callable[[PacketType, int | None], None]' = lambda *_: None
        self.buffer = bytearray()
        self.last_header = None

    def tick(self, time: float):
        while self.conn.poll():
            data = self.conn.recv()
            if isinstance(data, bytes):
                self.buffer.extend(data)
                self.process_buffer()

    def process_buffer(self):
        pos = 0
        while pos < len(self.buffer):
            if self.buffer[pos] == Packet.ctrl_header:
                if self.last_header is None:
                    # dump current bytes
                    self.buffer = self.buffer[pos:]
                    pos = 0
                    self.last_header = 0
                    continue
                elif self.last_header != pos:
                    log_trace("handler.pipe", f"processing packet last_header={self.last_header} buffer.len={len(self.buffer)} pos={pos}")
                    packet_type, value = Packet.decode(self.buffer[self.last_header:pos])
                    self.buffer = self.buffer[pos:]
                    log_trace("handler.pipe", f"got packet packet_type={packet_type.name()} value={value}")
                    self.callback(packet_type, value)
                else:
                    pos += 1
            else:
                pos += 1
            pass


    
    def send_message(self, message: bytes):
        packet_type, value = Packet.decode(message)
        log_trace("handler.pipe", f"sending packet packet_type={packet_type.name()} value={value}")
        self.conn.send(message)