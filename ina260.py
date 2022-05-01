T"""
INA250
------------------------
Voltage,current and power sensor via i2c bus.

GitHub: https://github.com/ldreesden/ina260
Author: L. Drees
Version: 1.0
Date:05/01/2022
Based on datasheet: https://www.ti.com/lit/ds/symlink/ina260.pdf?ts=1651398339904&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FINA260


"""

#--- Imports

from machine import SoftI2C, Pin
import time

#--- Registeradresses

_REG_CURRENT = 0x01  # SHUNT VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE = 0x02  # BUS VOLTAGE REGISTER (R)
_REG_POWER = 0x03 # POWER REGISTER (R)


#############################################################################


class INA260:
    """Driver for the INA260 power and current sensor.

    
    """

    def __init__(self, i2cBus, address=0x40):
        """
        Args:
            i2cBus: SoftI2C(Pin(*SCLpin*),Pin(*SDApin*))
            address: i2c address in hex (0x40 by default)
        """
        self.i2c = i2cBus
        self.ADDRESS = address


    def _issue_measurement(self, writeAddress):
        """Issue a measurement.
        Args:
            writeAddress (int): address to write to
        :return:
        """
        self.i2c.start()
        self.i2c.writeto_mem(int(self.ADDRESS), int(writeAddress), '')
        self.i2c.stop()
        time.sleep_ms(50)
        data = bytearray(3)
        self.i2c.readfrom_into(self.ADDRESS, data)
        raw = (data[0] << 8) + data[1]
        raw &= 0xFFFF
        return raw

    @property
    def current(self):
        """The current (between V+ and V-) in mA"""
        raw = self._issue_measurement(_REG_CURRENT)
        raw *= 1.25
        if raw >36000:
            raw=0
        return int(raw//1)

    @property
    def voltage(self):
        """The bus voltage in V"""
        raw = self._issue_measurement(_REG_BUSVOLTAGE)
        return round(raw * 0.00125,2)

    @property
    def power(self):
        """The power being delivered to the load in mW"""
        
        raw = self._issue_measurement(_REG_POWER)
        return round(raw * 10,0)