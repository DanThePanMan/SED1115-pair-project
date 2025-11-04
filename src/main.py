# Version 3
# This was prepared very quickly after we did testing on version 2
# and observed way too many bugs in the previous version
# We decided to burn it all down and quickly hacked up the minimum 
# viable product for this project in person

from time import time_ns, sleep_ms
from machine import Pin, UART, I2C, ADC, PWM
from ads import ADS1015

from packet import *

# program config
debug = False
enable_potentiometer = True

# time in ms to send messages
send_interval = 500

# time in ms to update pwm value
pwm_poll_interval = 50

# time to wait before displaying an error message in ms
timeout_error = 3000

configured_duty_cycle = 1200
uart_obj = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# I2C config
i2c = I2C(1, sda=Pin(14), scl=Pin(15))
adc = ADS1015(i2c, 0x48, 1)
adc_pwm_port = 2

# PWM config
pwm = PWM(Pin(17))
pwm.freq(1000)

# potentiometer config
potent = ADC(Pin(27))

# error light
error_light = Pin(16, Pin.OUT)

uart_obj.init(stop=1, parity=None, bits=8)

# internal state
receive_buffer = bytearray()
timer = 0
connection_lost_timer = 0
connection_lost_ack = True
pwm_poll_timer = 0


# utility for logging with debug
def log(message, debug_only = False):
    if debug_only:
        if debug: print(f"[debug] {message}")
    else: print(f"[info ] {message}")

def uart_write(*values: str):
    """
    Write a UTF-8 message to UART.
    """
    uart_obj.write(format_packet(values))

def uart_receive() -> 'list[str] | None':
    """
    Receive a packet from UART.
    """
    global receive_buffer

    while uart_obj.any():
        receive_buffer.extend(uart_obj.read(1))

    # check if we have a complete packet waiting to be processed (marked by ;)
    semi_index = receive_buffer.find(b';')

    if semi_index != -1:
        # get the first packet from the buffer
        packet = receive_buffer[:semi_index + 1]
        
        # split into components
        receive_buffer = receive_buffer[semi_index + 1:]
        packet_list = split_packet(packet)
        
        log(f"received message: {packet}", debug_only=True)
        
        return packet_list
    
    return None

def read_rc_filter() -> int:
    # no idea why the number is 1639, but that's the max I've observed
    # so scale the read value by the appropriate factor
    adjusted = int(adc.read(0, adc_pwm_port) * (65535/1639))
    if adjusted < 0: return 0
    elif adjusted > 65535: return 65535
    else: return adjusted

start = time_ns()
while True:
    # get the elapsed time
    end = time_ns()
    elapsed = (end - start) / 1_000_000

    # update the timers
    timer += elapsed
    connection_lost_timer += elapsed
    pwm_poll_timer += elapsed
    
    start = end

    # display a message if we think we lost connection
    if connection_lost_timer > timeout_error and not connection_lost_ack:
        log("connection lost!")

        connection_lost_ack = True
        error_light.high()
    
    # update current duty cycle based on potentiometer
    if enable_potentiometer and pwm_poll_timer > pwm_poll_interval:
        log(f"potent={potent.read_u16()}", debug_only=True)

        configured_duty_cycle = potent.read_u16()
        pwm.duty_u16(configured_duty_cycle)
        pwm_poll_timer = 0
    
    # send a measure message every send_interval ms
    if timer > send_interval:
        log("timer elapsed, sending...", debug_only=True)
        uart_write('m', str(configured_duty_cycle))
        
        timer = 0

    try:
        # try and read a packet
        read = uart_receive()

        if read is not None:
            # if we have a measure packet
            if len(read) > 0 and read[0] == "m":
                log(f"got packet m, duty:{read[1]}", debug_only=True)
                try:
                    other_duty = int(read[1])
                    current_rc = read_rc_filter()
                    log(f"expected={other_duty}; actual={current_rc}; delta={abs(other_duty - current_rc)}", debug_only=True)
                    uart_write('e', str(current_rc), str(other_duty))
                except:
                    log("Something went wrong while processing a message packet!")
            
            # if we have an error packet (not a bad error1!!)
            elif len(read) > 0 and read[0] == "e":

                # reset error status
                error_light.low()
                connection_lost_timer = 0
                connection_lost_ack = False
                try:
                    own_duty = int(read[2])
                    actual = int(read[1])

                    # print out a message with the deviation
                    log(f"got packet expected:{read[1]}", debug_only=True)
                    print(f"Expected: {own_duty}; Actual: {read[1]}; Deviation: {abs(own_duty - actual)}")
                except:
                    log("Something went wrong while processing an error packet!")

            # some unknown packet
            else:
                log("unrecognized packet; ignoring")
                
    except Exception:
        log("malformed packet; ignoring")
    
    sleep_ms(10)
