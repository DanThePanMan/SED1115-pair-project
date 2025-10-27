from protocol import PacketType
from handler import MessageHandler

from config import TYPECHECKING, TARGET
if TYPECHECKING:
    from typing import Literal

class State():
    """
    Abstract base class representing a state for the message handler.
    """
    handler: MessageHandler
    next_state: 'type[State]|None'
    status: 'Literal["green", "yellow", "red"]'
    last_status: 'Literal["green","yellow","red"]|None'

    def __init__(self, handler: MessageHandler):
        self.handler = handler
        self.next_state = None
        self.last_status = None
        self.set_status("green")

    def tick(self, time_ms: float):
        ...

    def message_received(self, packet_type: PacketType, value: int|None):
        ...

    def set_status(self, status: 'Literal["green", "yellow", "red"]'):
        if TARGET == "micropython":
            from machine import Pin # type: ignore

            ds = Pin("GP20", Pin.OUT)
            shcp = Pin("GP18", Pin.OUT)
            stcp = Pin("GP19", Pin.OUT)
            oe = Pin("GP21", Pin.OUT)
            oe.low()

            config = [False] * 16
            config[1:4] = [
                status == "green",
                status == "yellow",
                status == "red"
            ]
            
            for i in range(len(config)):
                ds.value(config[i])
                shcp.high()
                shcp.low()
            ds.low()
            stcp.high()
            stcp.low()

            self.last_status = status

    def request_transition(self, state: 'type[State]'):
        self.next_state = state
