import logging
import datetime as dt


class SGP40Sampler:
    def __init__(self, sgp40, bme280_sampler, database):
        self.database = database
        self.sensor = sgp40
        self.bme280_sampler = bme280_sampler
        self.enabled = sgp40 is not None
        self.latest = None

    # --------------------------------------------------
    # SGP40 reading capture and storage
    # --------------------------------------------------

    def _sample(self, capture_readings):
        """
        Sample the SGP40 sensors, write the results to the database and log them
        """
        # Get the latest BME280 reading and extract the humidity and temperature for SGP40
        # VOC index compensation
        latest_bme = self.bme280_sampler.latest
        temperature = latest_bme["temperature_c"] if latest_bme else 25.0
        humidity = latest_bme["humidity_pct"] if latest_bme else 50.0

        # Sample the sensors
        sraw, voc_index, voc_label, voc_rating = self.sensor.read(humidity, temperature)
        if capture_readings:
            timestamp = self.database.insert_sgp_row(sraw, voc_index, voc_label, voc_rating)
            logging.info(f"{timestamp}  SRAW={sraw}  VOC Index={voc_index}  VOC Label={voc_label}  Rating={voc_rating}")
        else:
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"

        return timestamp, sraw, voc_index, voc_label, voc_rating, temperature, humidity

    def _store(self, timestamp, sraw, voc_index, voc_label, voc_rating, temperature, humidity):
        """
        Store the latest SGP40 readings
        """
        self.latest_sgp = {
            "time_utc": timestamp,
            "sraw": sraw,
            "voc_index": voc_index,
            "voc_label": voc_label,
            "voc_rating": voc_rating,
            "temperature_c": temperature,
            "humidity_pc": humidity
        }

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def sample_and_store(self):
        if self.sensor and self.enabled:
            timestamp, sraw, voc_index, voc_label, voc_rating, temperature, humidity = self._sample()
            self._store(timestamp, sraw, voc_index, voc_label, voc_rating, temperature, humidity)

    @property
    def latest_reading(self):
        return self.latest

    def disable(self):
        self.enabled = False
        self.latest = None

    def enable(self):
        self.enabled = self.sensor is not None
