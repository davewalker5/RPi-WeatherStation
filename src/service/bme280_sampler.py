import logging

class BME280Sampler:
    def __init__(self, bme280, database):
        self.database = database
        self.sensor = bme280
        self.enabled = bme280 is not None
        self.latest = None

    # --------------------------------------------------
    # BME280 reading capture and storage
    # --------------------------------------------------

    def _sample(self):
        """
        Sample the sensors, write the results to the database and log them
        """
        temperature, pressure, humidity = self.sensor.read()
        timestamp = self.database.insert_bme_row(temperature, pressure, humidity)
        logging.info(f"{timestamp}  T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")
        return timestamp, temperature, pressure, humidity

    def _store(self, timestamp, temperature, pressure, humidity):
        """
        Store the latest readings
        """
        self.latest = {
            "time_utc": timestamp,
            "temperature_c": round(temperature, 2),
            "pressure_hpa": round(pressure, 2),
            "humidity_pct": round(humidity, 2),
        }

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def sample_and_store(self):
        if self.sensor and self.enabled:
            timestamp, temperature, pressure, humidity = self._sample()
            self._store(timestamp, temperature, pressure, humidity)

    @property
    def latest_reading(self):
        return self.latest

    def disable(self):
        self.enabled = False
        self.latest = None

    def enable(self):
        self.enabled = self.sensor is not None
