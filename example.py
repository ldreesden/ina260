from ina260 import INA260
from machine import SoftI2C,Pin
from time import sleep

i2c=SoftI2C(Pin(22),Pin(21))
ina=INA260(i2c)
while True:
    
    voltage=round(ina.voltage,2)
    current=int(ina.current//1)
    power=round(ina.power,2)
    print(str(current)+'mA,  '+str(voltage)+'V,   '+str(power)+'mW')
    sleep(0.1)