from handler.messagehandler import MessageHandler
from protocol import Packet, PacketType
from log import log_debug, log_trace, log_error

from config import TARGET, TYPECHECKING

if TYPECHECKING:
    from typing import Callable

if TARGET == "micropython":
    # specific for pico
    from machine import UART, Pin

class UARTMessageHandler(MessageHandler):
    def __init__(self, uart_id: int = 1, baudrate: int = 9600, tx_pin: int = 8, rx_pin: int = 9):
        """args:
        
        uart_id: peripheral number, 0 or 1
        baudrate: serial baud rate, defaults to 9600
        tx_pin: pin for tx
        rx_pin pin for rx
        """

        # throw if target is not micropython
        if TARGET != "micropython":
            raise NotImplementedError("UART only works on micropython targets.")

        # init
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.uart.init(bits=8, parity=None, stop = 1)
        self.last_header = None
        
        log_debug("uart", f"UART{uart_id} initialized: TX=GP{tx_pin}, RX=GP{rx_pin}, baud={baudrate}")
        self.buffer = bytearray()
        
        
    def tick(self, time: float):
        log_trace("uart", f"uart bytes waiting {self.uart.any()}")
        while self.uart.any():
            self.buffer.extend(self.uart.read(1))
        self._parse_packets()

    def _parse_packets(self):
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
                    log_trace("uart", f"processing packet last_header={self.last_header} buffer.len={len(self.buffer)} pos={pos}")
                    packet_type, value = Packet.decode(self.buffer[self.last_header:pos])
                    self.buffer = self.buffer[pos:]
                    log_trace("uart", f"got packet packet_type={packet_type.name()} value={value}")
                    self.callback(packet_type, value)
                else:
                    pos += 1
            else:
                pos += 1
            pass
    
    def send_message(self, message: bytes):
        try:
            self.uart.write(message)
            log_trace("uart", f"Sent {len(message)}bytes")
        except Exception as e:
            log_error("uart", f"failed to send message: {e}")
    
    def set_callback(self, callback: 'Callable[[PacketType, int|None], None]'):
        """
        Register callback for received messages.
        
        Args:
            callback: Function to call when a packet is received.
                      Signature: callback(packet_type: PacketType, value: int|None)
        """
        self.callback = callback
        log_debug("uart", "Callback registered")
