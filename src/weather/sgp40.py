import time

class SGP40:
    """
    Wrapper for the Sensirion SGP40 VOC sensor
    """

    def __init__(self, i2c_device, voc_algorithm, measurement_delay = 0.03):
        self.i2c_device = i2c_device
        self.delay = measurement_delay
        self._voc = voc_algorithm

    # ---------- low-level command construction ----------

    def _crc8_sgp40(self, two_bytes: bytes) -> int:
        """
        CRC-8 for SGP40 (polynomial 0x31, init 0xFF).
        'two_bytes' must be length 2.
        """
        crc = 0xFF
        for b in two_bytes:
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc


    def _humidity_to_ticks(self, h: float) -> int:
        """
        Convert relative humidity from %RH (0..100) to SGP40 'ticks' (0..65535).
        Formula from SGP40 datasheet: RH_ticks = (RH/100) * 65535
        """
        h = max(0.0, min(100.0, h))
        return int(round(h * 65535.0 / 100.0))


    def _temperature_to_ticks(self, t: float) -> int:
        """
        Convert temperature from C to SGP40 'ticks' (0..65535).
        Formula from SGP40 datasheet: T_ticks = (T + 45) * 65535 / 175
        where T is in C and valid range is roughly -45..130.
        """
        t = max(-45.0, min(130.0, t))
        return int(round((t + 45.0) * 65535.0 / 175.0))


    def _build_command(self, humidity, temperature) -> bytes:
        """
        Build the 8-byte 'measure raw' command frame with humidity &
        temperature compensation
        """
        rh_ticks = self._humidity_to_ticks(humidity)
        t_ticks = self._temperature_to_ticks(temperature)

        rh_msb = (rh_ticks >> 8) & 0xFF
        rh_lsb = rh_ticks & 0xFF
        t_msb = (t_ticks >> 8) & 0xFF
        t_lsb = t_ticks & 0xFF

        rh_crc = self._crc8_sgp40(bytes([rh_msb, rh_lsb]))
        t_crc = self._crc8_sgp40(bytes([t_msb, t_lsb]))

        # Command 0x26 0x0F = "measure raw signal"
        return bytes(
            [
                0x26,
                0x0F,
                rh_msb,
                rh_lsb,
                rh_crc,
                t_msb,
                t_lsb,
                t_crc,
            ]
        )

    # ---------- core measurement ----------

    def _measure_sraw(self, humidity = 50.0, temperature = 25.0) -> int:
        """
        Trigger one SRAW measurement with humidity & temperature
        compensation and return the raw VOC signal (0..65535).
        """
        cmd = self._build_command(humidity, temperature)
        self.i2c_device.write_bytes_raw(cmd)
        time.sleep(self.delay)

        data = self.i2c_device.read_bytes_raw(3)  # MSB, LSB, CRC
        if len(data) != 3:
            raise IOError(f"SGP40: expected 3 bytes, got {len(data)}")

        msb, lsb, crc_recv = data
        crc_calc = self._crc8_sgp40(data[:2])
        if crc_calc != crc_recv:
            raise ValueError(
                f"SGP40 CRC mismatch: got 0x{crc_recv:02X}, expected 0x{crc_calc:02X}"
            )

        return (msb << 8) | lsb


    def _classify_voc_index(self, index: int) -> str:
        """
        Simple human-readable classification for display / logs.
        """
        if index < 80:
            return "Excellent"
        elif index < 120:
            return "Good"
        elif index < 160:
            return "Moderate"
        elif index < 220:
            return "Unhealthy"
        else:
            return "Very Unhealthy"

    # ---------- public API ----------

    def read(self, humidity = 50.0, temperature = 25.0):
        """
        Read a full sample and return a dict:

        {
            "sraw": <int>,
            "voc_index": <int> or None,
            "voc_label": <str> or None,
        }
        """
        sraw = self._measure_sraw(humidity, temperature)

        voc_index = None
        voc_label = None

        if self._voc is not None:
            voc_index = int(self._voc.process(sraw))
            voc_label = self._classify_voc_index(voc_index)

        return {
            "sraw": sraw,
            "voc_index": voc_index,
            "voc_label": voc_label,
        }
