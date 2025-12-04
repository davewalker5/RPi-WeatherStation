from smbus2 import SMBus
import time
from os import environ

bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["SGP40_ADDR"], 16)

print(f"Bus = {bus_num}, Address = {addr}")

# "Measure raw signal" command (no humidity compensation)
MEASURE_CMD = [0x26, 0x0F]

bus = SMBus(bus_num)

try:
    # Send measure command
    bus.write_i2c_block_data(addr, MEASURE_CMD[0], [MEASURE_CMD[1]])
    time.sleep(0.03)  # 30ms for measurement
    
    # Read 3 bytes (2 data + CRC)
    data = bus.read_i2c_block_data(addr, 0, 3)

    raw = data[0] << 8 | data[1]
    crc = data[2]

    print(f"Raw value: {raw}, CRC: {crc}")

except Exception as e:
    print(f"Communication failed: {e}")