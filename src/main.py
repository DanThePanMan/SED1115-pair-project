from protocol import PacketType, Packet
from handler import LoopbackHandler, PipeMessageHandler, MessageHandler
from state import MonoState
from measureprovider import MockMeasureProvider, RealMeasureProvider, MeasureProvider
from log import *
from time import time_ns
from exception import TimeoutError

from config import MODE, TARGET

duty_cycle = 1200
timeout_ms = 1000
max_retries = 3
poll_ms = 500
provider = MockMeasureProvider((5000, 6000))
pwm_out_port = 16
pwm_duty = 1340
pwm_freq = 1000
duty_in_pin = 2

# PWM output
if TARGET == "micropython":
    from machine import PWM, Pin # type: ignore
    pwm = PWM(Pin(pwm_out_port))
    pwm.duty_u16(pwm_duty)
    pwm.freq(pwm_freq)

def process(connection):
    """
    Used for the pipe message handler
    """
    handler = PipeMessageHandler(connection)
    loop(handler, provider, timeout_ms, poll_ms, duty_cycle, max_retries,
         auto_restart=True)

def loop(handler: MessageHandler, measure_provider: MeasureProvider,
          timeout_ms: int, request_ms: int, duty_cycle: int, max_retries: int,
          auto_restart: bool = False):
    """
    Contains the main loop for the program. Handles ticking of the message handler and the state.
    """
    while True:
        # initialize startup state
        message_handler = handler
        current_state = MonoState(message_handler, measure_provider, duty_cycle, request_ms, timeout_ms, max_retries)

        start = time_ns() // 1000
        
        while True:
            end = time_ns() // 1000
            
            # us to ms
            elapsed = (end - start) / 1_000.0
            start = end

            # tick and handle the exceptions
            try:
                message_handler.tick(elapsed)
                current_state.tick(elapsed)
            except TimeoutError:
                log_info("main", "exiting loop")
                break
            except Exception as e:
                log_error("main", f"unexpected exception {e}")
                log_info("main", "exiting loop")
                break

        # if we've exited the loop
        # we had an error that requires a restart
        if not auto_restart:
            log_info("main", "waiting for user input")
            wait_for_reset()

        log_info("main", "resetting")

def wait_for_reset():
    if TARGET == "python":
        input()
    elif TARGET == "micropython":
        from machine import Pin # type: ignore
        from time import sleep_ms # type: ignore
        pin = Pin(13, Pin.IN)
        while True:
            if pin.value():
                return
            else:
                sleep_ms(1)

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
