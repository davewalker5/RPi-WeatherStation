import logging

class VEML7700Sampler:
    def __init__(self, veml7700, database):
        self.database = database
        self.sensor = veml7700
        self.enabled = veml7700 is not None
        self.latest = None

    # --------------------------------------------------
    # VEML7700 reading capture and storage
    # --------------------------------------------------

    def _sample(self):
        """
        Sample the sensors, write the results to the database and log them
        """
        als, white, lux = self.sensor.read()
        is_saturated = self.sensor.is_saturated(als)
        timestamp = self.database.insert_veml_row(als, white, lux, is_saturated)
        logging.info(f"{timestamp}  Gain={self.sensor.gain}  Integration Time={self.sensor.integration_time_ms} ms  ALS={als}  White={white}  Illuminance={lux:.2f} lux  IsSaturated={is_saturated}")
        return timestamp, als, white, lux, is_saturated

    def _store(self, timestamp, als, white, lux, is_saturated):
        """
        Store the latest readings
        """
        with self._lock:
            self.latest_veml = {
                "time_utc": timestamp,
                "gain": self.sensor.gain,
                "integration_time_ms": self.sensor.integration_time_ms,
                "als": als,
                "white": white,
                "illuminance_lux": round(lux, 2),
                "saturated": is_saturated
            }

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def sample_and_store(self):
        if self.sensor and self.enabled:
            timestamp, als, white, lux, is_saturated = self._sample()
            self._store(timestamp, als, white, lux, is_saturated)

    @property
    def latest_reading(self):
        return self.latest

    def disable(self):
        self.enabled = False
        self.latest = None

    def enable(self):
        self.enabled = self.sensor is not None
