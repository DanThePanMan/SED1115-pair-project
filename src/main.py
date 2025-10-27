from protocol import PacketType, Packet
from state import StartupState, NormalState
from handler import LoopbackHandler, PipeMessageHandler
from measureprovider import MockMeasureProvider
from log import *
from program import loop

from config import MODE

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
        from multiprocessing import Pipe, Process
        from os import devnull

        connection_1, connection_2 = Pipe()
        process_1 = Process(target=process, args=(connection_1, ))
        process_2 = Process(target=process, args=(connection_2, ))

        process_1.start()
        process_2.start()
        process_1.join()
        process_2.join()
    elif MODE == "loopback":
        handler = LoopbackHandler()
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
        # TODO:
        pass