from state.statecls import State
from state.normalstate import NormalState
from protocol import Packet, PacketType
from handler import MessageHandler
from log import log_trace, log_debug, log_warn, log_error
from exception import TimeoutError

class StartupState(State):
    time_since_last_config_req_ms: float
    retries: int
    max_retries: int
    timeout_ms: float
    expected_duty_cycle: int
    duty_cycle: int

    log_src = "state.startup"

    def __init__(self, handler: MessageHandler, duty_cycle: int, timeout_ms: float, max_retries: int):
        super().__init__(handler)
        log_debug(self.log_src, "enter")
        self.time_since_last_config_req_ms = 0
        self.duty_cycle = duty_cycle
        self.max_retries = max_retries
        self.timeout_ms = timeout_ms
        self.handler.callback = self.message_received
        self.retries = 0

        self.set_status("yellow")
        self.send_config_req()

    def tick(self, time_ms: float):
        # log_trace(self.log_src, f"tick delta={time_ms}")
        self.time_since_last_config_req_ms += time_ms
        
        if self.time_since_last_config_req_ms >= self.timeout_ms:
            self.retries += 1
            self.time_since_last_config_req_ms = 0
            
            if self.retries > self.max_retries:
                self.set_status("red")
                log_error(self.log_src, "timed out waiting for request_config response")
                raise TimeoutError("timed out waiting for request_config response")
            else:
                log_debug(self.log_src, f"time-out. retrying retries={self.retries}")
                self.send_config_req()
        
    def send_config_req(self):
        log_debug(self.log_src, "sending request_config")
        self.time_since_last_config_req_ms = 0
        self.handler.send_message(Packet.create_request_config())

    def message_received(self, packet_type: PacketType, value: int | None):
        log_trace(self.log_src, f"message received type={packet_type.name()} value={value}")
        if packet_type == PacketType.request_config:
            self.handler.send_message(Packet.create_response_config(self.duty_cycle))
        elif packet_type == PacketType.response_config:
            if value is None:
                log_warn(self.log_src, "invalid response_config packet; no value")
            else:
                log_debug(self.log_src, f"out transition requested")
                self.expected_duty_cycle = value
                self.request_transition(NormalState)
