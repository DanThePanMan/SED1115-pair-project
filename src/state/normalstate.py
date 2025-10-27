from state.statecls import State
from handler import MessageHandler
from measureprovider import MeasureProvider
from protocol import PacketType, Packet
from log import log_trace, log_debug, log_warn, log_info, log_error
from exception import TimeoutError

from config import TYPECHECKING

class NormalState(State):
    """
    Represents the normal state that periodically requests a measurement from the other device.
    """

    # Time in milliseconds since the last request was sent
    time_since_last_req_ms: float

    # Retries on current request
    retries: int


    # config
    handler: MessageHandler
    timeout_ms: float
    max_retries: int
    duty_cycle: int
    expected_duty_cycle: int
    measure_provider: MeasureProvider

    log_src = "state.normal"

    def __init__(self, handler: MessageHandler, measure_provider: MeasureProvider, expected_duty_cycle: int, 
                 duty_cycle: int, measure_interval_ms: float, timeout_ms: float, max_retries: int):
        """
        Arguments:
            handler: The message handler.
            measure_provider: The provider of measured values.
            expected_duty_cycle: The expected duty cycle of the other device that the measurements will be
                compared against.
            duty_cycle: The duty cycle configured for this device.
            measure_interval_ms: The interval at which measurement requests should nominally be sent to the
                other device.
            timeout_ms: The amount of time before a single request is considered as timed out.
            max_retries: The maximum number of retries before we give up. 
        """
        super().__init__(handler)
        log_debug(self.log_src, "enter")

        self.time_since_last_req_ms = 0
        self.retries = 0

        self.expected_duty_cycle = expected_duty_cycle
        self.duty_cycle = duty_cycle
        self.timeout_ms = timeout_ms
        self.measure_interval_ms = measure_interval_ms
        self.max_retries = max_retries
        self.handler = handler
        self.handler.callback = self.message_received
        self.measure_provider = measure_provider

        self.set_status("green")
        self.send_measure_req()

    def tick(self, time_ms: float):
        self.time_since_last_req_ms += time_ms
        
        # retries = -1 -> first request
        if self.retries == -1 and self.time_since_last_req_ms > self.measure_interval_ms:
            log_trace(self.log_src, "requesting measurement")
            self.retries = 0
            self.set_status("yellow")
            self.send_measure_req()

        # retries >= 0 -> retry
        elif self.time_since_last_req_ms >= self.timeout_ms:
            self.time_since_last_req_ms = 0
            self.retries += 1

            if self.retries > self.max_retries:
                log_error(self.log_src, "timed out waiting for request_measure response")
                self.set_status("red")
                raise TimeoutError("timed out waiting for request_measure response")
            else:
                log_debug(self.log_src, f"time-out. retrying retries={self.retries}")
                self.send_measure_req()

    def send_measure_req(self):
        log_debug(self.log_src, "sending request_measure")
        self.handler.send_message(Packet.create_request_measured())

    def measure_req_received(self, value: int):
        """
        Handle a RESPONSE_MEASURED response
        """
        self.set_status("green")
        self.retries = -1
        self.time_since_last_req_ms = 0
        log_info(self.log_src, f"expected={self.expected_duty_cycle} value={value} error={abs(self.expected_duty_cycle - value)}")

    def message_received(self, packet_type: PacketType, value: int | None):
        log_trace(self.log_src, f"message received type={packet_type.name()} value={value}")

        if packet_type == PacketType.request_config:
            self.handler.send_message(Packet.create_response_config(self.duty_cycle))

        elif packet_type == PacketType.request_measured:
            self.handler.send_message(Packet.create_response_measured(self.measure_provider.measure()))

        elif packet_type == PacketType.response_measured:
            if value is None:
                log_warn(self.log_src, "invalid response_measured packet; no value")
            else:
                self.measure_req_received(value)

        else:
            log_warn(self.log_src, f"unexpected packet type packet_type={packet_type.name()} value={value}")
