# SPDX-FileCopyrightText: Bryan Siepert 2019 for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ina260`
================================================================================
CircuitPython driver for the TI INA260 current and power sensor
* Author(s): Bryan Siepert
Implementation Notes
--------------------
**Hardware:**
* `INA260 Breakout <https://www.adafruit.com/products/4226>`_
**Software and Dependencies:**
* Adafruit CircuitPython firmware for the supported boards:
* https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_INA260.git"
from machine import SoftI2C, Pin
import time

_REG_CONFIG = 0x00  # CONFIGURATION REGISTER (R/W)
_REG_CURRENT = 0x01  # SHUNT VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE = 0x02  # BUS VOLTAGE REGISTER (R)
_REG_POWER = 0x03 # POWER REGISTER (R)
_REG_MASK_ENABLE = 0x06  # MASK ENABLE REGISTER (R/W)
_REG_ALERT_LIMIT = 0x07  # ALERT LIMIT REGISTER (R/W)
_REG_MFG_UID = 0xFE  # MANUFACTURER UNIQUE ID REGISTER (R)
_REG_DIE_UID = 0xFF  # DIE UNIQUE ID REGISTER (R)


# pylint: disable=too-few-public-methods
class Mode:
    """Modes avaible to be set

    +--------------------+---------------------------------------------------------------------+
    | Mode               | Description                                                         |
    +====================+=====================================================================+
    | ``Mode.CONTINUOUS``| Default: The sensor will continuously measure the bus voltage and   |
    |                    | shunt voltage across the shunt resistor to calculate ``power`` and  |
    |                    | ``current``                                                         |
    +--------------------+---------------------------------------------------------------------+
    | ``Mode.TRIGGERED`` | The sensor will immediately begin measuring and calculating current,|
    |                    | bus voltage, and power. Re-set this mode to initiate another        |
    |                    | measurement                                                         |
    +--------------------+---------------------------------------------------------------------+
    | ``Mode.SHUTDOWN``  |  Shutdown the sensor, reducing the quiescent current and turning off|
    |                    |  current into the device inputs. Set another mode to re-enable      |
    +--------------------+---------------------------------------------------------------------+

    """

    SHUTDOWN = 0x0
    TRIGGERED = 0x3
    CONTINUOUS = 0x7


class ConversionTime:
    """Options for ``current_conversion_time`` or ``voltage_conversion_time``

    +----------------------------------+------------------+
    | ``ConversionTime``               | Time             |
    +==================================+==================+
    | ``ConversionTime.TIME_140_us``   | 140 us           |
    +----------------------------------+------------------+
    | ``ConversionTime.TIME_204_us``   | 204 us           |
    +----------------------------------+------------------+
    | ``ConversionTime.TIME_332_us``   | 332 us           |
    +----------------------------------+------------------+
    | ``ConversionTime.TIME_588_us``   | 588 us           |
    +----------------------------------+------------------+
    | ``ConversionTime.TIME_1_1_ms``   | 1.1 ms (Default) |
    +----------------------------------+------------------+
    | ``ConversionTime.TIME_2_116_ms`` | 2.116 ms         |
    +----------------------------------+------------------+
    | ``ConversionTime.TIME_4_156_ms`` | 4.156 ms         |
    +----------------------------------+------------------+
    | ``ConversionTime.TIME_8_244_ms`` | 8.244 ms         |
    +----------------------------------+------------------+

    """

    TIME_140_us = 0x0
    TIME_204_us = 0x1
    TIME_332_us = 0x2
    TIME_588_us = 0x3
    TIME_1_1_ms = 0x4
    TIME_2_116_ms = 0x5
    TIME_4_156_ms = 0x6
    TIME_8_244_ms = 0x7

    @staticmethod
    def get_seconds(time_enum):
        """Retrieve the time in seconds giving value read from register"""
        conv_dict = {
            0: 140e-6,
            1: 204e-6,
            2: 332e-6,
            3: 588e-6,
            4: 1.1e-3,
            5: 2.116e-3,
            6: 4.156e-3,
            7: 8.244e-3,
        }
        return conv_dict[time_enum]


class AveragingCount:
    """Options for ``averaging_count``

    +-------------------------------+------------------------------------+
    | ``AveragingCount``            | Number of measurements to average  |
    +===============================+====================================+
    | ``AveragingCount.COUNT_1``    | 1 (Default)                        |
    +-------------------------------+------------------------------------+
    | ``AveragingCount.COUNT_4``    | 4                                  |
    +-------------------------------+------------------------------------+
    | ``AveragingCount.COUNT_16``   | 16                                 |
    +-------------------------------+------------------------------------+
    | ``AveragingCount.COUNT_64``   | 64                                 |
    +-------------------------------+------------------------------------+
    | ``AveragingCount.COUNT_128``  | 128                                |
    +-------------------------------+------------------------------------+
    | ``AveragingCount.COUNT_256``  | 256                                |
    +-------------------------------+------------------------------------+
    | ``AveragingCount.COUNT_512``  | 512                                |
    +-------------------------------+------------------------------------+
    | ``AveragingCount.COUNT_1024`` | 1024                               |
    +-------------------------------+------------------------------------+

    """

    COUNT_1 = 0x0
    COUNT_4 = 0x1
    COUNT_16 = 0x2
    COUNT_64 = 0x3
    COUNT_128 = 0x4
    COUNT_256 = 0x5
    COUNT_512 = 0x6
    COUNT_1024 = 0x7

    @staticmethod
    def get_averaging_count(avg_count):
        """Retrieve the number of measurements giving value read from register"""
        conv_dict = {0: 1, 1: 4, 2: 16, 3: 64, 4: 128, 5: 256, 6: 512, 7: 1024}
        return conv_dict[avg_count]


# pylint: enable=too-few-public-methods


class INA260:
    """Driver for the INA260 power and current sensor.

    :param ~busio.I2C i2c_bus: The I2C bus the INA260 is connected to.
    :param address: The I2C device address for the sensor. Default is ``0x40``.

    """

    def __init__(self, i2c_bus, address=0x40):
        self.i2c = i2c_bus
        self.ADDRESS = address


    def _issue_measurement(self, write_address):
        """Issue a measurement.
        Args:
            write_address (int): address to write to
        :return:
        """
        self.i2c.start()
        self.i2c.writeto_mem(int(self.ADDRESS), int(write_address), '')
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
        return raw

    @property
    def voltage(self):
        """The bus voltage in V"""
        raw = self._issue_measurement(_REG_BUSVOLTAGE)
        return raw * 0.00125

    @property
    def power(self):
        """The power being delivered to the load in mW"""
        
        raw = self._issue_measurement(_REG_POWER)
        return raw * 10