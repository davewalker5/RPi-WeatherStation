import time
from .i2c_word_device import I2CWordDevice


class VEML7700:
    """
    VEML7700 ambient light sensor wrapper

    By default, the following are configured:
      - ALS_GAIN = 1/4
      - ALS_IT   = 100 ms

    This gives a useful range (~0–15 klx) with decent resolution, and a lux scaling of approximately 0.2304 lx/count
    (https://forums.raspberrypi.com/viewtopic.php?t=198082)
    """

    # Register addresses
    # https://www.vishay.com/docs/84323/designingveml7700.pdf
    REG_ALS_CONF = 0x00
    REG_ALS_WH   = 0x01
    REG_ALS_WL   = 0x02
    REG_PSM      = 0x03
    REG_ALS      = 0x04
    REG_WHITE    = 0x05
    REG_ALS_INT  = 0x06

    # Bit field lookup tables for configuration register (#0)
    # https://www.vishay.com/docs/84286/veml7700.pdf
    _GAIN_BITS = {
        1:    0b00,   # ALS gain x1
        2:    0b01,   # ALS gain x2
        1/8:  0b10,   # ALS gain x1/8
        0.125:0b10,
        1/4:  0b11,   # ALS gain x1/4
        0.25: 0b11,
    }

    _IT_BITS = {
        25:   0b1100,
        50:   0b1000,
        100:  0b0000,
        200:  0b0001,
        400:  0b0010,
        800:  0b0011,
    }

    # Precomputed lux/ct for some common settings. The tuples are (gain, integration_time_ms)
    # https://forums.raspberrypi.com/viewtopic.php?t=198082
    _RESOLUTION_LUX_PER_CT = {
        (1/4, 100): 0.2304,
        (0.25, 100): 0.2304,
        (1/8, 25): 1.8432,
        (0.125, 25): 1.8432,
    }

    def __init__(self, bus, address, gain, integration_time_ms):
        self.dev = I2CWordDevice(bus, address)

        # Normalise / coerce types
        self.gain = float(gain)
        self.integration_time_ms = int(integration_time_ms)

        # Configure sensor
        conf = self._build_conf_word(self.gain, self.integration_time_ms)
        self.dev.write_u16(self.REG_ALS_CONF, conf)

        # Clear thresholds & power-saving for a clean start
        self.dev.write_u16(self.REG_ALS_WH, 0x0000)
        self.dev.write_u16(self.REG_ALS_WL, 0x0000)
        self.dev.write_u16(self.REG_PSM,    0x0000)

        time.sleep(self.integration_time_ms / 1000.0)

        self._resolution = self._RESOLUTION_LUX_PER_CT.get(
            (self.gain, self.integration_time_ms),
            0.2304
        )

    def _build_conf_word(self, gain: float, it_ms: int) -> int:
        """
        Build the 16-bit configuration word for ALS_CONF register.
        - ALS_SD bit (0) is set to 0 => power on
        - Interrupts disabled, persistence = 1
        """
        gain_bits = self._GAIN_BITS.get(gain, self._GAIN_BITS[1/4])
        it_bits   = self._IT_BITS.get(it_ms, self._IT_BITS[100])

        word = 0
        # Gain bits 12:11
        word |= (gain_bits & 0b11) << 11
        # Integration time bits 9:6
        word |= (it_bits & 0b1111) << 6
        # ALS_PERS bits 5:4 -> 00b (1 sample)
        # Reserved bits already 0
        # ALS_INT_EN bit 1 -> 0 (INT disabled)
        # ALS_SD bit 0 -> 0 (power on)
        return word & 0xFFFF

    def read_id(self) -> int:
        """Return device ID (should be ~0xC481)."""
        return self.dev.read_u16(0x07)

    def read_conf(self) -> int:
        """Return ALS_CONF register value."""
        return self.dev.read_u16(self.REG_ALS_CONF)
    def close(self):
        self.dev.close()

    def read_als_raw(self) -> int:
        """Return raw ALS 16-bit count value."""
        return self.dev.read_u16(self.REG_ALS)

    def read_white_raw(self) -> int:
        """Return raw WHITE 16-bit count value."""
        return self.dev.read_u16(self.REG_WHITE)

    def is_saturated(self, als_raw):
        """Return true if the ALS is saturated"""
        return als_raw >= 65500

    def read_lux(self) -> float:
        """
        Return approximate lux based on current configuration.

        For (gain=1/4, it=100 ms) or (gain=1/8, it=25 ms), the scaling constants are taken from Vishay’s
        app note and example code. For other settings, this uses the same default resolution as gain=1/4,
        100 ms unless _RESOLUTION_LUX_PER_CT is extended.
        """
        als = self.read_als_raw()
        lux = als * self._resolution
        return lux

    def read(self):
        """
        Return a tuple: (als_raw, white_raw, lux_estimate).
        """
        als = self.read_als_raw()
        white = self.read_white_raw()
        lux = als * self._resolution
        return als, white, lux
