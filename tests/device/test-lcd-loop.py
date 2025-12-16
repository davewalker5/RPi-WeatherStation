import smbus
from time import sleep
from os import environ, getenv
from i2c import I2CLCD

mux_addr = int(mux_addr, 16) if (mux_addr:= getenv("MUX_ADDR", "").strip()) else None
bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["LCD_ADDR"], 16)
channel = int(channel) if (channel:= getenv("LCD_CHANNEL", "").strip()) else None

bus = smbus.SMBus(bus_num)
lcd = I2CLCD(bus, addr, mux_addr, channel)

i = 0
while True:
    success, attempts = lcd.write(f"Count: {i}", line=1)
    print(f"{i}: Line 1: Status {success} after {attempts} attempt(s)")
    success, attempts = lcd.write("Pi Weather Stn", line=2)
    print(f"{i}: Line 2: Status {success} after {attempts} attempt(s)")
    i += 1
    sleep(1)
