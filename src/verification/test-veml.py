import time
from os import environ

try:
    from smbus2 import SMBus
except ImportError:
    from ..i2c.mock_smbus import SMBus

BUS = int(environ["BUS_NUMBER"])
ADDR = int(environ["VEML_ADDR"], 16)

REG_CONF  = 0x00
REG_ALS   = 0x04
REG_WHITE = 0x05
REG_ID    = 0x07

def write_u16(bus, reg, value):
    value &= 0xFFFF
    lsb = value & 0xFF
    msb = (value >> 8) & 0xFF
    bus.write_i2c_block_data(ADDR, reg, [lsb, msb])

def read_u16(bus, reg):
    data = bus.read_i2c_block_data(ADDR, reg, 2)
    return data[0] | (data[1] << 8)

with SMBus(BUS) as bus:
    # 1. Check ID
    dev_id = read_u16(bus, REG_ID)
    print(f"ID register: 0x{dev_id:04X} (expected 0xC481 or 0xD481)")

    # 2. See current config
    conf_before = read_u16(bus, REG_CONF)
    print(f"ALS_CONF_0 before: 0x{conf_before:04X}")

    # 3. Write a known-good config:
    #    gain = 1/4, IT = 100ms, ALS enabled, INT disabled
    #    This is the same config used in working Pi examples
    #    (https://forums.raspberrypi.com/viewtopic.php?t=198082)
    conf_lsb  = 0x00
    conf_msb  = 0x18   # 0001 1000b → gain=1/4, IT=100ms
    bus.write_i2c_block_data(ADDR, REG_CONF, [conf_lsb, conf_msb])

    time.sleep(0.2)  # at least one integration period

    conf_after = read_u16(bus, REG_CONF)
    print(f"ALS_CONF_0 after : 0x{conf_after:04X}")

    # 4. Read ALS/WHITE repeatedly
    while True:
        als   = read_u16(bus, REG_ALS)
        white = read_u16(bus, REG_WHITE)
        print(f"ALS={als:5d}  WHITE={white:5d}")
        time.sleep(1)