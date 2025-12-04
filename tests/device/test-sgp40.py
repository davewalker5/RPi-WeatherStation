from smbus2 import SMBus, i2c_msg
import time
from os import environ

bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["SGP40_ADDR"], 16)

print(f"Bus = {bus_num}, Address = {addr} (0x{addr:02X})")

# Full 'measure raw' command with default 50% RH, 25°C (no compensation)
CMD_MEASURE_RAW = [
    0x26, 0x0F,        # measure raw command
    0x80, 0x00, 0xA2,  # RH = 50%, CRC
    0x66, 0x66, 0x93   # T = 25°C, CRC
]

with SMBus(bus_num) as bus:
    try:
        # Send full command
        write = i2c_msg.write(addr, CMD_MEASURE_RAW)
        bus.i2c_rdwr(write)

        # Wait for measurement
        time.sleep(0.03)  # 30 ms

        # Read 3 bytes: MSB, LSB, CRC
        read = i2c_msg.read(addr, 3)
        bus.i2c_rdwr(read)
        data = list(read)

        raw = (data[0] << 8) | data[1]
        crc = data[2]

        print(f"Raw value: {raw}, CRC: {crc}")

    except Exception as e:
        print(f"Communication failed: {e}")