
import logging
import threading
import time
from .bme280 import BME280
from .veml7700 import VEML7700
from .database import Database


class Sampler(threading.Thread):
    bme280: BME280 = None
    veml7700: VEML7700 = None
    database: Database = None
    interval: float = None

    def __init__(self, bme280, veml7700, database, interval):
        super().__init__(daemon=True)
        self.bme280 = bme280
        self.veml7700 = veml7700
        self.database = database
        self.interval = float(interval)
        self.stop = threading.Event()
        self.latest_bme = None
        self.latest_veml = None
        self._lock = threading.Lock()
        self.last_purged = None

    def _sample_bme_sensors(self):
        """
        Sample the BME280 sensors, write the results to the database and log them
        """
        temperature, pressure, humidity = self.bme280.read()
        timestamp = self.database.insert_bme_row(temperature, pressure, humidity)
        logging.info(f"{timestamp}  T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")
        return timestamp, temperature, pressure, humidity

    def _set_latest_bme(self, timestamp, temperature, pressure, humidity):
        """
        Store the latest BME280 readings
        """
        with self._lock:
            self.latest_bme = {
                "time_utc": timestamp,
                "temperature_c": round(temperature, 2),
                "pressure_hpa": round(pressure, 2),
                "humidity_pct": round(humidity, 2),
            }

    def _sample_veml_sensors(self):
        """
        Sample the VEML7700 sensors, write the results to the database and log them
        """
        als, white, lux = self.veml7700.read()
        is_saturated = self.veml7700.is_saturated(als)
        timestamp = self.database.insert_veml_row(als, white, lux, is_saturated)
        logging.info(f"{timestamp}  Gain={self.veml7700.gain}  Integration Time={self.veml7700.integration_time_ms} ms  ALS={als}  White={white}  Illuminance={lux:.2f} lux  IsSaturated={is_saturated}")
        return timestamp, als, white, lux, is_saturated

    def _set_latest_veml(self, timestamp, als, white, lux, is_saturated):
        """
        Store the latest VEML7700 readings
        """
        with self._lock:
            self.latest_veml = {
                "time_utc": timestamp,
                "gain": self.veml7700.gain,
                "integration_time_ms": self.veml7700.integration_time_ms,
                "als": als,
                "white": white,
                "illuminance_lux": round(lux, 2),
                "saturated": is_saturated
            }

    def run(self):
        """
        Run the sampler event loop
        """
        # Start the timer and loop until we're interrupted
        next_tick = time.monotonic()
        logging.info(f"Sampler started: interval={self.interval:.3f} s")
        while not self.stop.is_set():
            try:
                # Purge old data
                self.database.purge()

                # Take the next set of BME280 readings and cache them as the latest readings
                timestamp, temperature, pressure, humidity = self._sample_bme_sensors()
                self._set_latest_bme(timestamp, temperature, pressure, humidity)

                # Take the next set of VEML7700 readings and cache them as the latest readings
                timestamp, als, white, lux, is_saturated = self._sample_veml_sensors()
                self._set_latest_veml(timestamp, als, white, lux, is_saturated)
            except Exception as ex:
                logging.warning("Sampler error: %s", ex)

            # Wait for the next "tick"
            next_tick += self.interval
            time.sleep(max(0.0, next_tick - time.monotonic()))

        logging.info("Sampler stopped.")

    def get_latest_bme(self):
        """
        Return the most recent BME280 readings captured by the sampler
        """
        with self._lock:
            return dict(self.latest_bme) if self.latest_bme else None

    def get_latest_veml(self):
        """
        Return the most recent VEML7700 readings captured by the sampler
        """
        with self._lock:
            return dict(self.latest_veml) if self.latest_veml else None
