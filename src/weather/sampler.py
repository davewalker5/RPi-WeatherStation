
import logging
import threading
import time
import datetime as dt
from .bme280 import BME280
from .database import Database


class Sampler(threading.Thread):
    sensor: BME280 = None
    database: Database = None
    interval: float = None

    def __init__(self, sensor, database, interval):
        super().__init__(daemon=True)
        self.sensor = sensor
        self.database = database
        self.interval = float(interval)
        self.stop = threading.Event()
        self.latest = None
        self._lock = threading.Lock()

    def _sample_sensors(self):
        """
        Sample the BME280 sensors, write the results to the database and log them
        """
        temperature, pressure, humidity = self.sensor.read()
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        self.database.insert_row(timestamp, temperature, pressure, humidity)
        logging.info(f"{timestamp}  T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")
        return timestamp, temperature, pressure, humidity

    def run(self):
        """
        Run the sampler event loop
        """
        # Start the timer and loop until we're interrupted
        next_tick = time.monotonic()
        logging.info(f"Sampler started: interval={self.interval:.3f} s")
        while not self.stop.is_set():
            try:
                # Take the next reading and cache it as the latest reading
                timestamp, temperature, pressure, humidity = self._sample_sensors()
                with self._lock:
                    self.latest = {
                        "time_utc": timestamp,
                        "temperature_c": round(temperature, 2),
                        "pressure_hpa": round(pressure, 2),
                        "humidity_pct": round(humidity, 2),
                    }
            except Exception as ex:
                logging.warning("Sampler error: %s", ex)

            # Wait for the next "tick"
            next_tick += self.interval
            time.sleep(max(0.0, next_tick - time.monotonic()))

        logging.info("Sampler stopped.")

    def get_latest(self):
        """
        Return the most recent reading captured by the sampler
        """
        with self._lock:
            return dict(self.latest) if self.latest else None
