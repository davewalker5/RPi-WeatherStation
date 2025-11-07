from smbus2 import SMBus
import time

# Before running this script, run the following command:
#
# sudo i2cdetect -y <bus-number>
#
# Try values for 0 and 1 for the <bus-number>. One of them will return an error and the 
# other will return output similar to the following:
#
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f                                                                                                                                 
# 00:                         -- -- -- -- -- -- -- --                                                                                                                                 
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --                                                                                                                                 
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --                                                                                                                                 
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --                                                                                                                                 
# 40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --                                                                                                                                 
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --                                                                                                                                 
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --                                                                                                                                 
# 70: -- -- -- -- -- -- 76 --   
#
# Only one entry will appear. The bus number and that entry should be used to populate the
# bus number and address, below.

bus_num = 0
addr = 0x76

bus = SMBus(bus_num)
chip_id = bus.read_byte_data(addr, 0xD0)
print("BME280 chip ID:", hex(chip_id))
