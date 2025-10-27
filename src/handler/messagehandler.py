from protocol import PacketType
from config import TYPECHECKING

if TYPECHECKING:
    from typing import Callable

class MessageHandler():
    """
    Abstract base class representing an interface for sending and receiving messages.
    """
    callback: 'Callable[[PacketType, int|None], None]'

    def tick(self, time: float):
        ...

    def set_callback(self, callback: 'Callable[[PacketType, int|None], None]'):
        self.callback = callback

    def send_message(self, message: bytes):
        ...
