
import logging
import threading
import time
import datetime as dt
from .bme280 import BME280
from .veml7700 import VEML7700
from .sgp40 import SGP40
from .database import Database


class Sampler(threading.Thread):
    bme280: BME280 = None
    veml7700: VEML7700 = None
    sgp40: SGP40 = None
    database: Database = None
    interval: int = None

    def __init__(self, bme280, veml7700, database, interval, sgp40):
        super().__init__(daemon=True)
        self.bme280 = bme280
        self.veml7700 = veml7700
        self.sgp40 = sgp40
        self.database = database
        self.interval = float(interval)
        self.stop = threading.Event()
        self.latest_bme = None
        self.latest_veml = None
        self.latest_sgp = None
        self._lock = threading.Lock()

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

    def _sample_sgp_sensors(self, humidity, temperature, capture_readings):
        """
        Sample the SGP40 sensors, write the results to the database and log them
        """
        sraw, voc_index, voc_label, voc_rating = self.sgp40.read(humidity, temperature)
        if capture_readings:
            timestamp = self.database.insert_sgp_row(sraw, voc_index, voc_label, voc_rating)
            logging.info(f"{timestamp}  SRAW={sraw}  VOC Index={voc_index}  VOC Label={voc_label}  Rating={voc_rating}")
        else:
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        return timestamp, sraw, voc_index, voc_label

    def _set_latest_sgp(self, timestamp, sraw, voc_index, voc_label, voc_rating):
        """
        Store the latest SGP40 readings
        """
        with self._lock:
            self.latest_sgp = {
                "time_utc": timestamp,
                "sraw": sraw,
                "voc_index": voc_index,
                "voc_label": voc_label,
                "voc_rating": voc_rating
            }

    def run(self):
        """
        Run the sampler event loop
        """
        logging.info(f"Sampler started: interval={self.interval:.3f} s")

        # Start the timer and loop until we're interrupted. The loop needs to report at the specified interval
        # but sample the SGP40 at ~1s intervals to match the requirements of the Sensiron VOC algorithm
        counter = self.interval - 1
        while not self.stop.is_set():
            try:
                # Increment the reporting counter
                counter += 1
                capture_readings = counter == self.interval

                # If we've reached the capture interval, capture sensors other than the SGP40
                if capture_readings:
                    # Reset the reporting counter
                    counter = 0

                    # Purge old data
                    self.database.purge()

                    # Take the next set of BME280 readings and cache them as the latest readings
                    timestamp, temperature, pressure, humidity = self._sample_bme_sensors()
                    self._set_latest_bme(timestamp, temperature, pressure, humidity)

                    # Take the next set of VEML7700 readings and cache them as the latest readings
                    timestamp, als, white, lux, is_saturated = self._sample_veml_sensors()
                    self._set_latest_veml(timestamp, als, white, lux, is_saturated)

                # Sample the SGP40 sensors, passing in the latest values from the BM280 for humidity
                # and temperature compensation 
                timestamp, sraw, voc_index, voc_label, voc_rating = self._sample_sgp_sensors(self.latest_bme["humidity_pct"], self.latest_bme["temperature_c"], capture_readings)
                self._set_latest_sgp(timestamp, sraw, voc_index, voc_label, voc_rating)

            except Exception as ex:
                logging.warning("Sampler error: %s", ex)

            # Wait for 1s
            time.sleep(1)

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

    def get_latest_sgp(self):
        """
        Return the most recent SGP40 readings captured by the sampler
        """
        with self._lock:
            return dict(self.latest_sgp) if self.latest_sgp else None
