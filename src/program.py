from handler import MessageHandler
from state import StartupState, NormalState
from measureprovider import MeasureProvider
from log import *
from exception import TimeoutError

from config import TARGET

def loop(handler: MessageHandler, measure_provider: MeasureProvider,
          timeout_ms: int, request_ms: int, duty_cycle: int, max_retries: int,
          auto_restart: bool = False):
    while True:
        # initialize startup state
        message_handler = handler
        current_state = StartupState(message_handler, duty_cycle, timeout_ms, max_retries=max_retries)

        start = get_time_us()
        
        while True:
            end = get_time_us()
            
            # us to ms
            elapsed = get_time_diff(end, start) / 1_000.0
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

            # check if state requests a transition
            next_state = current_state.next_state
            
            if next_state is not None:
                
                # startup -> normal
                if type(current_state) == StartupState:
                    if next_state != NormalState:
                        raise Exception(f"Invalid transition from {current_state} to {next_state}")
                    log_debug("main", f"state transition new={next_state}")
                    
                    # extract the expected duty cycle we received 
                    expected_duty_cycle = current_state.expected_duty_cycle
                    log_info("main", f"entering normal state; expected_duty_cycle={expected_duty_cycle}")
                    
                    current_state = NormalState(
                        handler=message_handler,
                        measure_provider=measure_provider,
                        expected_duty_cycle=expected_duty_cycle,
                        duty_cycle=duty_cycle,
                        timeout_ms=timeout_ms,
                        measure_interval_ms=request_ms,
                        max_retries=max_retries
                    )

                # normal
                elif current_state is NormalState:
                    raise Exception(f"Invalid transition from {current_state} to {next_state}")
        
        # if we've exited the loop
        # we had an error that requires a restart
        if not auto_restart:
            log_info("main", "waiting for user input")
            wait_for_reset()

        log_info("main", "resetting")

def get_time_us() -> int: # type: ignore
    from time import time_ns
    return time_ns() // 1000

def get_time_diff(end: int, start: int) -> int: # type: ignore
    return end - start

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