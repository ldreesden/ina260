# ina260

based on datasheet: https://www.ti.com/lit/ds/symlink/ina260.pdf?ts=1651398339904&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FINA260

needed imports
--------------

    from ina260 import INA260
    from machine import SoftI2C, Pin
    from time import sleep

For recent Micropython firmwares is SoftI2C neccesary, for older version will I2C work.

Init INA260
-------------

    i2c=SoftI2C(scl = Pin(22), sda = Pin(21))
    ina=INA260(i2cBus = i2c, address = 0x40)

The I2C address is by default 0x40, if you need to adjust the address take a look on the datasheet.

Get values
-------------

    voltage=ina.voltage
    current=ina.current
    power=ina.power
    print(str(current)+'mA,  '+str(voltage)+'V,   '+str(power)+'mW')
    
Current returns in mA
Voltage returns in V
Power returns in mW

Output example:

    20mA,  4,71V, 235mW
