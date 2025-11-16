from smbus2 import SMBus
from os import environ

bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["BME_ADDR"], 16)

bus = SMBus(bus_num)
chip_id = bus.read_byte_data(addr, 0xD0)
print("BME280 chip ID:", hex(chip_id))
