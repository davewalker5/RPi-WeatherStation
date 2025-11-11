import time
from smbus2 import SMBus


class BME280:
    def __init__(self, bus=0, address=0x76):
        self.busnum = bus
        self.addr = address
        self.bus = SMBus(bus)

        # Read calibration data
        self.dig_T1 = self._read_u16(0x88)
        self.dig_T2 = self._read_s16(0x8A)
        self.dig_T3 = self._read_s16(0x8C)

        self.dig_P1 = self._read_u16(0x8E)
        self.dig_P2 = self._read_s16(0x90)
        self.dig_P3 = self._read_s16(0x92)
        self.dig_P4 = self._read_s16(0x94)
        self.dig_P5 = self._read_s16(0x96)
        self.dig_P6 = self._read_s16(0x98)
        self.dig_P7 = self._read_s16(0x9A)
        self.dig_P8 = self._read_s16(0x9C)
        self.dig_P9 = self._read_s16(0x9E)

        self.dig_H1 = self._read_u8(0xA1)
        self.dig_H2 = self._read_s16(0xE1)
        self.dig_H3 = self._read_u8(0xE3)
        e4 = self._read_s8(0xE4)
        e5 = self._read_u8(0xE5)
        e6 = self._read_s8(0xE6)
        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        self.dig_H6 = self._read_s8(0xE7)

        # Configure: humidity x1; temp/press x1; normal mode
        self._write_u8(0xF2, 0x01)
        self._write_u8(0xF4, 0x27)
        time.sleep(0.1)

    # ---- I2C helpers
    def _read_u8(self, reg):
        return self.bus.read_byte_data(self.addr, reg)

    def _read_s8(self, reg):
        v = self._read_u8(reg)
        return v - 256 if v > 127 else v

    def _read_u16(self, reg):
        lo = self._read_u8(reg)
        hi = self._read_u8(reg + 1)
        return (hi << 8) | lo

    def _read_s16(self, reg):
        lo = self._read_u8(reg)
        hi = self._read_u8(reg + 1)
        val = (hi << 8) | lo
        return val - 65536 if val > 32767 else val

    def _write_u8(self, reg, val):
        self.bus.write_byte_data(self.addr, reg, val)

    # ---- read one sample (returns temp °C, pressure hPa, humidity %)
    def read(self):
        data = self.bus.read_i2c_block_data(self.addr, 0xF7, 8)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_h = (data[6] << 8) | data[7]

        # Temperature
        var1 = (((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        t_fine = var1 + var2
        temp_c = ((t_fine * 5 + 128) >> 8) / 100.0

        # Pressure
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            pressure_hpa = 0.0
        else:
            p = 1048576 - adc_p
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
            pressure_hpa = pressure / 25600.0

        # Humidity
        h = t_fine - 76800
        h = (((((adc_h << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) + 16384) >> 15)
             * (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152)
             * self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = max(min(h, 419430400), 0)
        humidity = (h >> 12) / 1024.0

        return temp_c, pressure_hpa, humidity
