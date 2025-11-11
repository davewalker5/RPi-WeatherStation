#!/usr/bin/env python3
# Minimal BME280 reader for Raspberry Pi using smbus2
# Works on Pi 1B + smbus2 + BME280 (addr 0x76 or 0x77)

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

I2C_BUS = 0
ADDRESS = 0x76

bus = SMBus(I2C_BUS)

# ----------------------------------------------------------------------
# Helpers: read registers
# ----------------------------------------------------------------------
def read_u8(reg):
    return bus.read_byte_data(ADDRESS, reg)

def read_s8(reg):
    result = read_u8(reg)
    return result - 256 if result > 127 else result

def read_u16(reg):
    lo = read_u8(reg)
    hi = read_u8(reg+1)
    return (hi << 8) | lo

def read_s16(reg):
    lo = read_u8(reg)
    hi = read_u8(reg+1)
    result = (hi << 8) | lo
    return result - 65536 if result > 32767 else result

# ----------------------------------------------------------------------
# Read compensation parameters (factory calibration stored in chip)
# ----------------------------------------------------------------------
dig_T1 = read_u16(0x88)
dig_T2 = read_s16(0x8A)
dig_T3 = read_s16(0x8C)

dig_P1 = read_u16(0x8E)
dig_P2 = read_s16(0x90)
dig_P3 = read_s16(0x92)
dig_P4 = read_s16(0x94)
dig_P5 = read_s16(0x96)
dig_P6 = read_s16(0x98)
dig_P7 = read_s16(0x9A)
dig_P8 = read_s16(0x9C)
dig_P9 = read_s16(0x9E)

dig_H1 = read_u8(0xA1)
dig_H2 = read_s16(0xE1)
dig_H3 = read_u8(0xE3)
e4 = read_s8(0xE4)
e5 = read_u8(0xE5)
e6 = read_s8(0xE6)
dig_H4 = (e4 << 4) | (e5 & 0x0F)
dig_H5 = (e6 << 4) | (e5 >> 4)
dig_H6 = read_s8(0xE7)

# ----------------------------------------------------------------------
# Configure the sensor (normal mode, oversampling x1)
# ----------------------------------------------------------------------
bus.write_byte_data(ADDRESS, 0xF2, 0x01)  # humidity oversampling x1
bus.write_byte_data(ADDRESS, 0xF4, 0x27)  # temp/pressure oversampling x1, mode normal

time.sleep(0.1)

# ----------------------------------------------------------------------
# Main read functions
# ----------------------------------------------------------------------
def read_raw_data():
    data = bus.read_i2c_block_data(ADDRESS, 0xF7, 8)
    adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    adc_h = (data[6] << 8) | data[7]
    return adc_t, adc_p, adc_h

def compensate(adc_t, adc_p, adc_h):
    # Temperature
    var1 = (((adc_t >> 3) - (dig_T1 << 1)) * dig_T2) >> 11
    var2 = (((((adc_t >> 4) - dig_T1) * ((adc_t >> 4) - dig_T1)) >> 12) * dig_T3) >> 14
    t_fine = var1 + var2
    temp = (t_fine * 5 + 128) >> 8

    # Pressure
    var1 = t_fine - 128000
    var2 = var1 * var1 * dig_P6
    var2 = var2 + ((var1 * dig_P5) << 17)
    var2 = var2 + (dig_P4 << 35)
    var1 = ((var1 * var1 * dig_P3) >> 8) + ((var1 * dig_P2) << 12)
    var1 = (((1 << 47) + var1) * dig_P1) >> 33
    if var1 == 0:
        pressure = 0
    else:
        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (dig_P8 * p) >> 19
        pressure = ((p + var1 + var2) >> 8) + (dig_P7 << 4)

    # Humidity
    h = t_fine - 76800
    h = (((((adc_h << 14) - (dig_H4 << 20) - (dig_H5 * h)) + 16384) >> 15)
         * (((((((h * dig_H6) >> 10) * (((h * dig_H3) >> 11) + 32768)) >> 10) + 2097152)
         * dig_H2 + 8192) >> 14))
    h = h - (((((h >> 15) * (h >> 15)) >> 7) * dig_H1) >> 4)
    h = max(min(h, 419430400), 0)
    humidity = h >> 12

    return temp / 100.0, pressure / 25600.0, humidity / 1024.0

# ----------------------------------------------------------------------
# Read & display
# ----------------------------------------------------------------------
if __name__ == "__main__":
    adc_t, adc_p, adc_h = read_raw_data()
    t, p, h = compensate(adc_t, adc_p, adc_h)

    print(f"Temperature: {t:.2f} °C")
    print(f"Pressure:    {p:.2f} hPa")
    print(f"Humidity:    {h:.2f} %")