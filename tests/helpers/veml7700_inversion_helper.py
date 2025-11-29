class VEML7700InversionHelper:
    """
    Invert the VEML7700 lux formula to get raw ALS/WHITE counts for tests.

    Assumes a fixed configuration (gain + integration time).
    """

    # These constants match the Adafruit library / Vishay application note
    # MAX_RES is the base resolution at gain=2, IT=800ms: 0.0036 lx/ct
    IT_MAX_MS = 800.0
    GAIN_MAX = 2.0
    MAX_RES = 0.0036

    def __init__(self, gain_value, integration_ms):
        """
        gain_value: actual numeric gain (1/8, 1/4, 1, 2)
        integration_ms: integration time in milliseconds (25, 50, 100, 200, 400, 800)
        """
        self.gain_value = float(gain_value)
        self.integration_ms = float(integration_ms)

        # Resolution in lux per count, same as Adafruit getResolution()
        # res = MAX_RES * (IT_MAX / IT) * (GAIN_MAX / gain)
        self.resolution = (
            self.MAX_RES
            * (self.IT_MAX_MS / self.integration_ms)
            * (self.GAIN_MAX / self.gain_value)
        )

    def _lux_from_raw(self, raw_als):
        """Forward mapping: raw ALS -> lux (linear, no non-linear correction)"""
        return self.resolution * float(raw_als)

    def _raw_from_lux(self, target_lux):
        """
        Invert linear lux -> rawALS. Clamps to 0..65535 (16-bit) and returns an int
        """
        if target_lux <= 0:
            return 0

        raw = int(round(target_lux / self.resolution))

        # Clamp to valid 16-bit range
        if raw < 0:
            raw = 0
        elif raw > 0xFFFF:
            raw = 0xFFFF

        return raw

    @staticmethod
    def _raw_to_bytes_little_endian(raw):
        """
        Convert a 16-bit raw value to [LSB, MSB] as returned by read_i2c_block_data(addr, reg, 2) with LSB first config
        """
        raw &= 0xFFFF
        lsb = raw & 0xFF
        msb = (raw >> 8) & 0xFF
        return [lsb, msb]
    
    @property
    def max_raw(self):
        return 0xFFFF

    @property
    def max_lux(self):
        return self._lux_from_raw(self.max_raw)

    def make_test_fixture(self, target_lux, target_white_raw=None):
        """
        Given target values for lux and raw, calculate the relevant ALS value and measurement bytes
        """
        # Invert lux -> raw ALS
        raw_als = self._raw_from_lux(target_lux)
        lux_actual = self._lux_from_raw(raw_als)

        # Choose WHITE raw:
        if target_white_raw is None:
            raw_white = raw_als
        else:
            raw_white = max(0, min(0xFFFF, int(round(target_white_raw))))

        # Convert to byte blocks as read_i2c_block_data would return
        als_bytes = self._raw_to_bytes_little_endian(raw_als)
        white_bytes = self._raw_to_bytes_little_endian(raw_white)

        return {
            "raw_als": raw_als,
            "raw_white": raw_white,
            "als_bytes": als_bytes,
            "white_bytes": white_bytes,
            "actual_lux": lux_actual,
        }