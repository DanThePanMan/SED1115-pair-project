from handler.messagehandler import MessageHandler
from protocol import Packet, PacketType
from log import log_debug, log_trace, log_error
from typing import Callable


# specific for pico
from machine import UART, Pin

class UARTMessageHandler(MessageHandler):
    def __init__(self, uart_id: int = 0, baudrate: int = 9600, tx_pin: int = 0, rx_pin: int = 1):
        """args:
        
        uart_id: peripheral number, 0 or 1
        baudrate: serial baud rate, defaults to 9600
        tx_pin: pin for tx
        rx_pin pin for rx
        """
        # init
        self.uart = UART(uart_id, baudrate,tx_pin, rx_pin)
        self.uart.init(baudrate=baudrate, bits=8, parity=None, stop = 1)
        
        log_debug("uart", f"UART{uart_id} initialized: TX=GP{tx_pin}, RX=GP{rx_pin}, baud={baudrate}")
        self.buffer = bytearray()
        self.callback = None
        
        
    def tick(self, time: float):
        data = self.uart.read()
        if data:
            self.buffer.extend(data)
            log_trace("uart", f"Received {len(data)} bytes")
        self._parse_packets()

            

    def _parse_packets(self):
        pass
    # do this soon
    
    
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
    
