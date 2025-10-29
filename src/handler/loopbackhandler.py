from handler.messagehandler import MessageHandler
from random import randint
from log import log_trace, log_debug, log_info

from protocol import Packet, PacketType

drop_packets = False

class LoopbackHandler(MessageHandler):
    """
    Implements a message handler that simply loops back
    requests with their appropriate response
    """
    duty_cycle: int
    log_src = "handler.loopback"
    measure_interval_ms: float
    retries: int
    timer: float

    def __init__(self, measure_interval_ms: float):
        super().__init__()

        self.measure_interval_ms = measure_interval_ms
        self.duty_cycle = randint(2000, 60000)
        self.retries = 0
        self.timer = 0

        log_trace(self.log_src, f"initialized duty_cycle={self.duty_cycle}")

    def tick(self, time: float): 
        self.timer += time
        if self.timer > self.measure_interval_ms:
            self.timer = 0
            log_debug("handler.loopback", f"mock request_measured retries={self.retries}")
            self.callback(PacketType.request_measured, None)

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
        elif packet_type == PacketType.response_measured:
            self.retries = 0
            log_info(self.log_src, f"response_measured={value}")
        