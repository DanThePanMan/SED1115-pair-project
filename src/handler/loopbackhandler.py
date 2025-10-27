from handler.messagehandler import MessageHandler
from random import randint
from log import log_trace

from protocol import Packet, PacketType

drop_packets = True

class LoopbackHandler(MessageHandler):
    """
    Implements a message handler that simply loops back
    requests with their appropriate response
    """
    duty_cycle: int
    log_src = "handler.loopback"

    def __init__(self):
        super().__init__()
        self.duty_cycle = randint(2000, 60000)
        log_trace(self.log_src, f"initialized duty_cycle={self.duty_cycle}")

    def send_message(self, message: bytes):
        packet_type, value = Packet.decode(message)
        log_trace(self.log_src, f"message sent type={packet_type.name()} value={value}")

        # Drop packets with a probability
        if drop_packets and randint(0, 10) > 1: 
            log_trace(self.log_src, "dropping packet")
            return

        if packet_type == PacketType.request_config:
            self.callback(PacketType.response_config, self.duty_cycle)
        elif packet_type == PacketType.request_measured:
            self.callback(PacketType.response_measured, self.duty_cycle + randint(-100, 100))
        