from os import environ, getenv
from smbus2 import SMBus

mux_addr = int(mux_addr, 16) if (mux_addr:= getenv("MUX_ADDR", "").strip()) else None
bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["BME_ADDR"], 16)
channel = int(channel) if (channel:= getenv("BME_CHANNEL", "").strip()) else None

bus = SMBus(bus_num)
if mux_addr:
    bus.write_byte(mux_addr, 1 << channel)
chip_id = bus.read_byte_data(addr, 0xD0)
print("BME280 chip ID:", hex(chip_id))
