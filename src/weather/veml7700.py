import time
from ..i2c.i2c_word_device import I2CWordDevice


class VEML7700:
    """
    VEML7700 ambient light sensor wrapper

    By default, the following are configured:
      - ALS_GAIN = 1/4
      - ALS_IT   = 100 ms

    This gives a useful range (~0–15 klx) with decent resolution, and a lux
    scaling of approximately 0.2304 lx/count for gain=1/4, IT=100 ms.
    """

    # Register addresses
    REG_ALS_CONF = 0x00
    REG_ALS_WH   = 0x01
    REG_ALS_WL   = 0x02
    REG_PSM      = 0x03
    REG_ALS      = 0x04
    REG_WHITE    = 0x05
    REG_ALS_INT  = 0x06

    # Bit field lookup tables for configuration register (#0)
    _GAIN_BITS = {
        1:      0b00,   # ALS gain x1
        2:      0b01,   # ALS gain x2
        1/8:    0b10,   # ALS gain x1/8
        0.125:  0b10,
        1/4:    0b11,   # ALS gain x1/4
        0.25:   0b11,
    }

    _IT_BITS = {
        25:   0b1100,
        50:   0b1000,
        100:  0b0000,
        200:  0b0001,
        400:  0b0010,
        800:  0b0011,
    }

    # Allowed gain/IT values for auto-ranging (sorted low→high)
    _ALLOWED_GAINS = [0.125, 0.25, 1.0, 2.0]
    _ALLOWED_IT    = [25, 50, 100, 200, 400, 800]  # ms

    # Baseline resolution used for scaling (gain=1/4, IT=100ms)
    _BASE_GAIN = 0.25
    _BASE_IT   = 100
    _BASE_RES  = 0.2304  # lux per count at BASE_GAIN/BASE_IT

    # Optional specific precomputed values (used if present)
    _RESOLUTION_LUX_PER_CT = {
        (_BASE_GAIN, _BASE_IT): _BASE_RES,
        (1/8, 25):  1.8432,
        (0.125, 25): 1.8432,
    }

    def __init__(self, bus, address, gain, integration_time_ms):
        self.dev = I2CWordDevice(bus, address)

        # Normalise / coerce types
        gain = float(gain)
        it   = int(integration_time_ms)

        # Snap to nearest allowed gain/IT (so auto-ranging works cleanly)
        self.gain = min(self._ALLOWED_GAINS, key=lambda g: abs(g - gain))
        self.integration_time_ms = min(self._ALLOWED_IT, key=lambda t: abs(t - it))

        # Configure sensor & compute resolution
        self._apply_settings(initial=True)

    # ------------------------------------------------------------------
    # Low-level / configuration helpers
    # ------------------------------------------------------------------

    def _update_resolution(self):
        """
        Update self._resolution based on current gain & integration time.

        Uses a direct lookup if available; otherwise scales from a known
        baseline (gain=1/4, IT=100ms) assuming sensitivity ∝ gain * IT.
        """
        key = (self.gain, self.integration_time_ms)
        if key in self._RESOLUTION_LUX_PER_CT:
            self._resolution = self._RESOLUTION_LUX_PER_CT[key]
            return

        # Scale from baseline: lux/count ∝ 1 / (gain * IT)
        scale = (self._BASE_GAIN * self._BASE_IT) / (self.gain * self.integration_time_ms)
        self._resolution = self._BASE_RES * scale

    def _build_conf_word(self, gain: float, it_ms: int) -> int:
        """
        Build the 16-bit configuration word for ALS_CONF register.
        - ALS_SD bit (0) is set to 0 => power on
        - Interrupts disabled, persistence = 1
        """
        gain_bits = self._GAIN_BITS.get(gain, self._GAIN_BITS[self._BASE_GAIN])
        it_bits   = self._IT_BITS.get(it_ms, self._IT_BITS[self._BASE_IT])

        word = 0
        # Gain bits 12:11
        word |= (gain_bits & 0b11) << 11
        # Integration time bits 9:6
        word |= (it_bits & 0b1111) << 6
        # ALS_PERS bits 5:4 -> 00b (1 sample)
        # ALS_INT_EN bit 1 -> 0 (INT disabled)
        # ALS_SD bit 0 -> 0 (power on)
        return word & 0xFFFF

    def _apply_settings(self, initial: bool = False):
        """
        Write current gain/IT into the sensor and wait one integration period.
        """
        conf = self._build_conf_word(self.gain, self.integration_time_ms)
        self.dev.write_u16(self.REG_ALS_CONF, conf)

        if initial:
            # Clear thresholds & power-saving for a clean start
            self.dev.write_u16(self.REG_ALS_WH, 0x0000)
            self.dev.write_u16(self.REG_ALS_WL, 0x0000)
            self.dev.write_u16(self.REG_PSM,    0x0000)

        # Wait at least one integration period for new config to take effect
        time.sleep(self.integration_time_ms / 1000.0)

        # Update lux resolution
        self._update_resolution()

    # ------------------------------------------------------------------
    # Low-level sensor reads
    # ------------------------------------------------------------------

    def read_id(self) -> int:
        """Return device ID (should be ~0xC481)."""
        return self.dev.read_u16(0x07)

    def read_conf(self) -> int:
        """Return ALS_CONF register value."""
        return self.dev.read_u16(self.REG_ALS_CONF)

    def read_als_raw(self) -> int:
        """Return raw ALS 16-bit count value."""
        return self.dev.read_u16(self.REG_ALS)

    def read_white_raw(self) -> int:
        """Return raw WHITE 16-bit count value."""
        return self.dev.read_u16(self.REG_WHITE)

    def is_saturated(self, als_raw: int) -> bool:
        """Return True if the ALS reading is (likely) saturated."""
        return als_raw >= 65500

    # ------------------------------------------------------------------
    # Auto-ranging helpers
    # ------------------------------------------------------------------

    def _increase_sensitivity(self) -> bool:
        """
        Increase sensor sensitivity (for low light) by:
          1. Increasing gain, then
          2. Increasing integration time.
        Returns True if a change was made.
        """
        # Try gain first
        gi = self._ALLOWED_GAINS.index(self.gain)
        if gi < len(self._ALLOWED_GAINS) - 1:
            self.gain = self._ALLOWED_GAINS[gi + 1]
            return True

        # Then integration time
        iti = self._ALLOWED_IT.index(self.integration_time_ms)
        if iti < len(self._ALLOWED_IT) - 1:
            self.integration_time_ms = self._ALLOWED_IT[iti + 1]
            return True

        # Already at maximum sensitivity
        return False

    def _decrease_sensitivity(self) -> bool:
        """
        Decrease sensor sensitivity (for bright light / saturation) by:
          1. Decreasing integration time, then
          2. Decreasing gain.
        Returns True if a change was made.
        """
        # Reduce integration time first
        iti = self._ALLOWED_IT.index(self.integration_time_ms)
        if iti > 0:
            self.integration_time_ms = self._ALLOWED_IT[iti - 1]
            return True

        # Then reduce gain
        gi = self._ALLOWED_GAINS.index(self.gain)
        if gi > 0:
            self.gain = self._ALLOWED_GAINS[gi - 1]
            return True

        # Already at minimum sensitivity
        return False
    
    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------

    def read_lux(self) -> float:
        """
        Return approximate lux based on current configuration, without
        changing gain/IT.
        """
        als = self.read_als_raw()
        return als * self._resolution

    def read(self, autorange: bool = True):
        """
        Return a tuple: (als_raw, white_raw, lux_estimate).

        If autorange=True (default), this may adjust gain and/or integration
        time to avoid saturation and improve low-light performance.
        """
        als = self.read_als_raw()
        white = self.read_white_raw()

        if autorange:
            # Saturation / very bright - decrease sensitivity
            if als >= 65500:
                if self._decrease_sensitivity():
                    self._apply_settings()
                    als = self.read_als_raw()
                    white = self.read_white_raw()

            # Very low readings - increase sensitivity
            elif als < 50:
                if self._increase_sensitivity():
                    self._apply_settings()
                    als = self.read_als_raw()
                    white = self.read_white_raw()

        lux = als * self._resolution
        return als, white, lux