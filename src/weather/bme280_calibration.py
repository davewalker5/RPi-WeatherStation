class BME280Calibration:
    def __init__(self, sm_bus):
        self.sm_bus = sm_bus

        e4 = self._read_s8(0xE4)
        e5 = self._read_u8(0xE5)
        e6 = self._read_s8(0xE6)

        self.calibration = {
            "T1": self._read_u16(0x88),
            "T2": self._read_s16(0x8A),
            "T3": self._read_s16(0x8C),

            "P1": self._read_u16(0x8E),
            "P2": self._read_s16(0x90),
            "P3": self._read_s16(0x92),
            "P4": self._read_s16(0x94),
            "P5": self._read_s16(0x96),
            "P6": self._read_s16(0x98),
            "P7": self._read_s16(0x9A),
            "P8": self._read_s16(0x9C),
            "P9": self._read_s16(0x9E),

            "H1": self._read_u8(0xA1),
            "H2": self._read_s16(0xE1),
            "H3": self._read_u8(0xE3),
            "H4": (e4 << 4) | (e5 & 0x0F),
            "H5": (e6 << 4) | (e5 >> 4),
            "H6": self._read_s8(0xE7)
        }

    # ---- I2C helpers
    def _read_u8(self, reg):
        return self.sm_bus.read_byte_data(self.addr, reg)

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
        self.sm_bus.write_byte_data(self.addr, reg, val)

    def get_calibration_digit(self, name):
        return self.calibration[name]
