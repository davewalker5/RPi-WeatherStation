from i2c import I2CLCD
from time import sleep
from os import environ, getenv
from smbus2 import SMBus

mux_addr = int(mux_addr, 16) if (mux_addr:= getenv("MUX_ADDR", "").strip()) else None
bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["LCD_ADDR"], 16)
channel = int(channel) if (channel:= getenv("LCD_CHANNEL", "").strip()) else None

bus = SMBus(bus_num)
lcd = I2CLCD(bus, addr, mux_addr, channel)

lcd.clear()
lcd.write("Hello, world!", line=1)
lcd.write("Raspberry Pi!", line=2)

sleep(5)
lcd.clear()
