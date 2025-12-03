from i2c import I2CLCD
from time import sleep
from os import environ
from smbus2 import SMBus

bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["LCD_ADDR"], 16)

bus = SMBus(bus_num)
lcd = I2CLCD(bus, addr)

lcd.clear()
lcd.write("Hello, world!", line=1)
lcd.write("Raspberry Pi!", line=2)

sleep(5)
lcd.clear()
