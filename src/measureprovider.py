from random import randint
from log import log_debug, log_info, log_error

from config import TARGET
if TARGET == "micropython":
    from machine import Pin, ADC, I2C
    from ads import ADS1015

class MeasureProvider():
    """
    Abstract base class representing a source of measurements.
    """
    def measure(self) -> int:
        """
        Get a measurement from the RC filter.
        """
        ...

class MockMeasureProvider(MeasureProvider):
    """
    Generates a fake measurement within a given range.
    """
    range: 'tuple[int, int]'
    
    def __init__(self, range: 'tuple[int, int]'):
        if range[0] < 0 or range[0] > range[1] or range[1] > 65535:
            raise ValueError("invalid range")
        self.range = range

    def measure(self) -> int:
        return randint(self.range[0], self.range[1])
    
class RealMeasureProvider(MeasureProvider):
    """this one does REAL measuring with ADC

    Args:
        MeasureProvider (_type_): _description_
    """
    
    def __init__(self, i2c_id=1, sda_pin=14, scl_pin=15, adc_address=0x48, pwm_port=2):
        """
            Initialize the ADS1015 ADC.
            
            Args:
                i2c_id: I2C peripheral (1 for instructor's setup)
                sda_pin: GPIO for SDA (14)
                scl_pin: GPIO for SCL (15)
                adc_address: I2C address (0x48)
                pwm_port: ADC port with PWM signal (2)
            """
        if TARGET != "micropython":
            raise NotImplementedError("Not implemented for targets other than micropython.")
        
        # this is how initializing looks like
        # i2c = I2C(1, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL))
        # adc = ADS1015(i2c, ADS1015_ADDR, 1)\
            
        # Initialize I2C
        self.i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin))
        
        # Initialize ADS1015 ADC
        self.adc = ADS1015(self.i2c, adc_address, 1)
        self.pwm_port = pwm_port
        
        
        # make sure ADC is connected
        addresses = self.i2c.scan()
        log_info("adc", f"I2C devices: {[hex(addr) for addr in addresses]}") # cool little list comprehension for ya
        # very cool ~cf
        
        if adc_address not in addresses:
            log_error("adc", f"ADS1015 not found at {hex(adc_address)}")
        
        log_info("adc", f"ADS1015 ready on port {pwm_port}")

            
    def measure(self) -> int:
        """Read ADC value form the PWM port

        Returns:
            int: ADC value representing the duty cycle
        """
        
        try:
            value = self.adc.read(0, self.pwm_port)
            log_debug("adc", f"ADC value:{value}")
            return value
        except Exception as e:
            log_error("adc", f"read failed, error: {e}")
            return 0
            
        
