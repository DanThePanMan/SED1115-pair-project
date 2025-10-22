from machine import UART as _UART
from protocol.util import FrameReader, Packet

class UART():
    max_retries: int
    frame_reader: FrameReader 

    def __init__(self, pin_tx: int, pin_rx: int, baud_rate: int, max_retries: int, timeout_ms=1000):
        self.max_retries = max_retries
        self.uart = _UART(1)
        self.uart.init(baudrate=baud_rate, bits=8, parity=1, stop=1,
                       tx=pin_tx, rx=pin_rx, timeout=timeout_ms, timeout_char=timeout_ms)
        
    def read(self, max_retries_override = None):
        """
        Read a single packet from the UART line.

        Arguments:
            max_retries_override: Override for the max retries. None by default which uses the class setting. Negative values indicate unlimited retries 
        """
        # keep track of how many retries
        retries = 0
        max_retries = max_retries_override if max_retries_override is not None else self.max_retries

        while True:
            if max_retries >= 0 and retries > max_retries:
                raise TimeoutError("read timed out")

            rx_bytes = self.uart.read()
            
            # on timeout returns None
            if rx_bytes is None:
                retries += 1
                continue
                
            # read into the frame handler and try to get a packet
            self.frame_reader.read(rx_bytes)

            if self.frame_reader.has_queued_packet():
                next = self.frame_reader.get_next_packet()
                
                # this SHOULD be a no-op
                # maybe assert for debug? something's gone wrong if
                # this actually clears anything
                self.frame_reader.clear_packets()

                return next
            