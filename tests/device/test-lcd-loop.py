import smbus
from time import sleep
from os import environ
from i2c import I2CLCD

bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["LCD_ADDR"], 16)

bus = smbus.SMBus(bus_num)
lcd = I2CLCD(bus, addr)

i = 0
while True:
    lcd.write(f"Count: {i}", line=1)
    lcd.write("Pi Weather Stn", line=2)
    i += 1
    sleep(1)
