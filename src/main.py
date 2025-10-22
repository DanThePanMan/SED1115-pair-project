from time import sleep_ms
from machine import Pin, PWM

from typing import Literal

# Wait for 3 seconds to check if a button is pressed
# - pressed: transmitter mode
# - not pressed: receiver mode

# Transmitter loop:
# - Get initial duty cycle
# - Send receiver initial duty cycle
# - Start PWM
# - Print out update packets

# Receiver loop:
# - Receive initial duty cycle from transmitter
# - Periodically measure and print/send measured and expected average

# this code will definitely need to be refactored I just want to get smth up

def startup_get_mode(pin_in: int, max_wait_ms: int) -> 'Literal["transmitting", "receiving"]':
    mode = "receiving"
    wait_time_ms = max_wait_ms
    pin = Pin(pin_in, Pin.IN)

    while wait_time_ms > 0:
        if pin.value():
            mode = "transmitting"
            break
        sleep_ms(10)
        wait_time_ms -= 10

    return mode

def get_duty_cycle() -> int:
    """
    Prompts the user and returns a duty cycle as a `uint16`
    """
    while True:
        duty_cycle = input("Enter a duty cycle% (0 - 100): ")
        try:
            duty_cycle_float = float(duty_cycle)
            if duty_cycle_float < 0 or duty_cycle_float > 100:
                print("Invalid input; duty cycle must be within range 0 - 100")
            
            # convert pct to 0 - 65535 
            duty_cycle_int = (duty_cycle_float / 100) * (2 ** 32 - 1)
            return duty_cycle_int
        except ValueError:
            print("Invalid input; not a valid number")
            continue

def transmitter(pwm_pin_out: int):
    # get user duty cycle
    duty_cycle = get_duty_cycle()
    try:
        # uart interface is still up for debate
        uart.send(f"duty_cycle:{duty_cycle}")
    except TimeoutError:
        print("Failed to transmit; timed out.")


def receiver():
    # perhaps callback handlers?
    uart.handler("duty_cycle", lambda m: print("m"))

    # or just a big handler method would work fine for a project
    # this size

def main():
    mode = startup_get_mode(22, 3_000)

    print(f"entering {mode} mode")
    if mode == "receiving":
        receiver()
    elif mode == "transmitting":
        transmitter()
    else:
        raise ValueError(f"invalid base state: {mode}")

if __name__ == "__main__":
    main()