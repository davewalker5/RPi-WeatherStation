from i2c_lcd import I2CLCD
from time import sleep
from os import environ

bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["LCD_ADDR"], 16)

lcd = I2CLCD(i2c_addr=addr, i2c_bus = bus_num)

lcd.clear()
lcd.write("Hello, world!", line=1)
lcd.write("Raspberry Pi!", line=2)

sleep(5)
lcd.clear()
