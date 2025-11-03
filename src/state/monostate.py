from state.statecls import State
from handler import MessageHandler
from measureprovider import MeasureProvider
from protocol import PacketType, Packet
from log import log_trace, log_debug, log_warn, log_info, log_error
from exception import TimeoutError

from config import TYPECHECKING

if TYPECHECKING:
    from typing import Literal

class MonoState(State):
    """
    Represents the normal state that periodically requests a measurement from the other device.
    """

    handler: MessageHandler

    timeout_retries: int
    timeout_last_req: 'Literal["measure", "config", "none"]'
    timeout_timer: float

    # config
    timeout_ms: float
    max_retries: int
    duty_cycle: int
    expected_duty_cycle: int|None
    measure_provider: MeasureProvider
    measure_interval_ms: float

    log_src = "state.normal"

    def __init__(self, handler: MessageHandler, measure_provider: MeasureProvider, 
                 duty_cycle: int, measure_interval_ms: float, timeout_ms: float, max_retries: int):
        """
        Arguments:
            handler: The message handler.
            measure_provider: The provider of measured values.
            duty_cycle: The duty cycle configured for this device.
            measure_interval_ms: The interval at which measurement requests should nominally be sent to the
                other device.
            timeout_ms: The amount of time before a single request is considered as timed out.
            max_retries: The maximum number of retries before we give up. 
        """
        super().__init__(handler)
        log_debug(self.log_src, "enter")

        self.handler = handler
        self.timeout_retries = 0
        self.timeout_last_req = "none"
        self.timeout_timer = 0

        self.timeout_ms = timeout_ms
        self.max_retries = max_retries
        self.duty_cycle = duty_cycle
        self.expected_duty_cycle = None
        self.measure_provider = measure_provider
        self.measure_interval_ms = measure_interval_ms
        self.handler.callback = self.message_received

        self.set_status("green")
        self.send_config_req()

    def tick(self, time_ms: float):
        self.timeout_timer += time_ms

        # if we know what to expect and we don't have an outstanding request
        # we should be sending a measure request
        if self.timeout_last_req == "none" and self.timeout_timer > self.measure_interval_ms:
            self.timeout_timer = 0
            self.send_measure_req()
        
        # otherwise, if we have a request outstanding perform retries if necessary
        elif self.timeout_last_req != "none" and self.timeout_timer > self.timeout_ms:
            self.timeout_retries += 1
            self.timeout_timer = 0
            
            log_trace(self.log_src, f"timeout; request={self.timeout_last_req} retries={self.timeout_retries}")

            # raise if we're exceeding max retries
            if self.timeout_retries > self.max_retries:
                raise TimeoutError(f"Timed out on {self.timeout_last_req} request")
            
            # otherwise retry
            elif self.timeout_last_req == "config":
                self.send_config_req()
            else:
                self.send_measure_req()

    def send_config_req(self):
        log_debug(self.log_src, "sending request_config")
        self.set_status("yellow")
        self.timeout_last_req = "config"
        self.timeout_timer = 0
        self.timeout_retries = 0
        self.handler.send_message(Packet.create_request_config(self.duty_cycle))

    def send_measure_req(self):
        log_debug(self.log_src, "sending request_measure")
        self.set_status("yellow")
        self.timeout_last_req = "measure"
        self.timeout_timer = 0
        self.timeout_retries = 0
        self.handler.send_message(Packet.create_request_measured())

    def send_config_resp(self):
        log_debug(self.log_src, "sending response_config")
        self.set_status("yellow")
        self.timeout_last_req = "config"
        self.timeout_timer = 0
        self.timeout_retries = 0
        self.handler.send_message(Packet.create_response_config(self.duty_cycle))

    def measure_resp_received(self, value: int):
        """
        Handle a RESPONSE_MEASURED response
        """
        assert self.expected_duty_cycle is not None
        self.set_status("green")
        self.retries = 0
        self.timeout_timer = 0
        self.timeout_last_req = "none"
        log_info(self.log_src, f"expected={self.expected_duty_cycle} value={value} error={abs(self.expected_duty_cycle - value)}")

    def config_resp_received(self, value: int):
        self.expected_duty_cycle = value
        self.set_status("green")
        self.retries = 0
        self.timeout_timer = 0
        self.timeout_last_req = "none"

    def message_received(self, packet_type: PacketType, value: int | None):
        log_trace(self.log_src, f"message received type={packet_type.name()} value={value}")

        if packet_type == PacketType.request_measured:
            if self.expected_duty_cycle is None:
                log_warn(self.log_src, "got measurement_request without having an expected_duty_cycle")
            else:
                measurement = self.measure_provider.measure()
                self.handler.send_message(Packet.create_response_measured(measurement))
        elif packet_type == PacketType.request_config:
            assert value is not None
            self.expected_duty_cycle = value
            self.send_config_resp()
        elif packet_type == PacketType.response_measured:
            assert value is not None
            self.measure_resp_received(value)
        elif packet_type == PacketType.response_config:
            assert value is not None
            self.expected_duty_cycle = value
            self.config_resp_received(value)
        else:
            log_warn(self.log_src, f"unexpected packet type packet_type={packet_type.name()} value={value}")

    def update_duty_cycle(self, new: int):
        new = 0 if new < 0 else (65535 if new > 65535 else new) 
        if new == self.duty_cycle:
            return
        log_debug(self.log_src, f"updating duty_cycle old={self.duty_cycle} new={self.duty_cycle}")
        self.send_config_req()