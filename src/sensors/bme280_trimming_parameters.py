# Temperature
DIG_T1 = 0x88
DIG_T2 = 0x8A
DIG_T3 = 0x8C

# Pressure
DIG_P1 = 0x8E
DIG_P2 = 0x90
DIG_P3 = 0x92
DIG_P4 = 0x94
DIG_P5 = 0x96
DIG_P6 = 0x98
DIG_P7 = 0x9A
DIG_P8 = 0x9C
DIG_P9 = 0x9E

# Humidity
DIG_H1 = 0xA1
DIG_H2 = 0xE1
DIG_H3 = 0xE3
DIG_H4 = 0xE4
DIG_H5 = 0xE5
DIG_H6 = 0xE7
REG_E6 = 0xE6


class BME280TrimmingParameters:
    def __init__(self, sm_bus, address):
        self.sm_bus = sm_bus
        self.address = address

        e4 = self._read_s8(DIG_H4)
        e5 = self._read_u8(DIG_H5)
        e6 = self._read_s8(REG_E6)

        self.trimming_parameters = {
            DIG_T1: self._read_u16(0x88),
            DIG_T2: self._read_s16(0x8A),
            DIG_T3: self._read_s16(0x8C),

            DIG_P1: self._read_u16(0x8E),
            DIG_P2: self._read_s16(0x90),
            DIG_P3: self._read_s16(0x92),
            DIG_P4: self._read_s16(0x94),
            DIG_P5: self._read_s16(0x96),
            DIG_P6: self._read_s16(0x98),
            DIG_P7: self._read_s16(0x9A),
            DIG_P8: self._read_s16(0x9C),
            DIG_P9: self._read_s16(0x9E),

            DIG_H1: self._read_u8(0xA1),
            DIG_H2: self._read_s16(0xE1),
            DIG_H3: self._read_u8(0xE3),
            DIG_H4: (e4 << 4) | (e5 & 0x0F),
            DIG_H5: (e6 << 4) | (e5 >> 4),
            REG_E6: self._read_u8(0xE6),
            DIG_H6: self._read_s8(0xE7)
        }

    # ---- I2C helpers
    def _read_u8(self, reg):
        return self.sm_bus.read_byte_data(self.address, reg)

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
        self.sm_bus.write_byte_data(self.address, reg, val)

    def get_trimming_parameter(self, reg):
        return self.trimming_parameters[reg]
