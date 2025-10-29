from protocol import PacketType, Packet
from state import StartupState, NormalState
from handler import LoopbackHandler, PipeMessageHandler
from measureprovider import MockMeasureProvider
from log import *
from program import loop

from config import MODE, TARGET


# all the pico imports

duty_cycle = 1200
timeout_ms = 1000
max_retries = 3
poll_ms = 500
provider = MockMeasureProvider((5000, 6000))

def process(connection):
    handler = PipeMessageHandler(connection)
    loop(handler, provider, timeout_ms, poll_ms, duty_cycle, max_retries,
         auto_restart=True)

if __name__ == "__main__":
    if MODE == "multiprocess":
        if TARGET != "python":
            raise NotImplementedError("multiprocess mode only works on 'python' target")
        from multiprocessing import Pipe, Process # type: ignore
        from os import devnull # type: ignore

        connection_1, connection_2 = Pipe()
        process_1 = Process(target=process, args=(connection_1, ))
        process_2 = Process(target=process, args=(connection_2, ))

        process_1.start()
        process_2.start()
        process_1.join()
        process_2.join()
    elif MODE == "loopback":
        handler = LoopbackHandler(measure_interval_ms=500)
        loop(
            handler, 
            measure_provider=provider, 
            timeout_ms=timeout_ms, 
            request_ms=poll_ms, 
            duty_cycle=duty_cycle, 
            max_retries=max_retries,
            auto_restart=False,
        )
    elif MODE == "uart":
        if TARGET != "micropython":
            raise NotImplementedError("multiprocess mode only works on 'python' target")
        # new imports
        from handler.UARTHandler import UARTMessageHandler
        
        # using lab params, not tested yet, will need to be replaced by real params and real pins
        handler = UARTMessageHandler(uart_id=1, baudrate=9600, tx_pin=8, rx_pin=9)
        
        log_info("main", "Starting UART mode")
        loop(
            handler=handler,
            measure_provider=provider,
            timeout_ms=timeout_ms,
            request_ms=poll_ms,
            duty_cycle=duty_cycle,
            max_retries=max_retries,
            auto_restart=False  # Auto-restart on Pico
        )