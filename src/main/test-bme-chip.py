from smbus2 import SMBus
from os import environ

bus_num = environ["BUS_NUMBER"]
addr = environ["ADDR"]

bus = SMBus(bus_num)
chip_id = bus.read_byte_data(addr, 0xD0)
print("BME280 chip ID:", hex(chip_id))
