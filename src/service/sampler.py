
import logging
import threading
import time
import datetime as dt
from sensors import BME280
from sensors import VEML7700
from sensors import SGP40
from registry import DeviceType
from db import Database
from .bme280_sampler import BME280Sampler
from .veml770_sampler import VEML7700Sampler
from .sgp40_sampler import SGP40Sampler
from .lcd_display import LCDDisplay


class Sampler(threading.Thread):
    bme280: BME280 = None
    veml7700: VEML7700 = None
    sgp40: SGP40 = None
    database: Database = None
    sample_interval: int = None
    display_interval: int = None

    def __init__(self, bme280, veml7700, sgp40, lcd, database, sample_interval, display_interval):
        super().__init__(daemon=True)
        self.bme280_sampler = BME280Sampler(bme280, database)
        self.veml7700_sampler = VEML7700Sampler(veml7700, database)
        self.sgp40_sampler = SGP40Sampler(sgp40, self.bme280_sampler, database)
        self.lcd_display = LCDDisplay(lcd)
        self.sample_interval = sample_interval
        self.display_interval = display_interval
        self.stop = threading.Event()
        self._lock = threading.Lock()

    def run(self):
        """
        Run the sampler event loop
        """
        logging.info(f"Sampler started: interval={self.sample_interval:.3f} s")

        # Start the timer and loop until we're interrupted. The loop needs to report at the specified interval
        # but sample the SGP40 at ~1s intervals to match the requirements of the Sensiron VOC algorithm
        capture_counter = self.sample_interval - 1
        display_counter = self.display_interval - 1
        while not self.stop.is_set():
            try:
                # Increment the reporting counter
                capture_counter += 1
                capture_readings = capture_counter == self.sample_interval

                # Increment the display counter
                display_counter += 1
                display_next_reading = display_counter == self.display_interval

                # If we've reached the capture interval, capture sensors other than the SGP40
                if capture_readings:
                    # Reset the reporting counter
                    capture_counter = 0

                    # Purge old data and snapshot sizes
                    self.database.purge()
                    self.database.snapshot_sizes()

                    # Take the next set of BME280 and VEML770 readings
                    self.bme280_sampler.sample_and_store()
                    self.veml7700_sampler.sample_and_store()

                # Take the next set of SGP40 readings
                self.sgp40_sampler.sample_and_store()

                # If we've reached the display interval, display the next reading
                if display_next_reading and self.lcd_enabled:
                    with self._lock:
                        display_counter = 0
                        self.lcd_display.display_next(self)

            except Exception as ex:
                logging.warning("Sampler error: %s", ex)

            # Wait for 1s
            time.sleep(1)

        logging.info("Sampler stopped.")


    def get_latest_bme(self):
        """
        Return the most recent BME280 readings captured by the sampler
        """
        latest_reading = self.bme280_sampler.latest_reading
        return dict(latest_reading) if latest_reading else None

    def get_latest_veml(self):
        """
        Return the most recent VEML7700 readings captured by the sampler
        """
        latest_reading = self.veml7700_sampler.latest_reading
        return dict(latest_reading) if latest_reading else None

    def get_latest_sgp(self):
        """
        Return the most recent SGP40 readings captured by the sampler
        """
        latest_reading = self.sgp40_sampler.latest_reading
        return dict(latest_reading) if latest_reading else None

    def enable_device(self, device):
        if device == DeviceType.BME280:
            self.bme280_sampler.enable()
        elif device == DeviceType.VEML7700:
            self.veml7700_sampler.enable()
        elif device == DeviceType.SGP40:
            self.sgp40_sampler.enable()
        elif device == DeviceType.LCD:
            with self._lock:
                self.lcd_display.enable()

    def disable_device(self, device):
        if device == DeviceType.BME280:
            self.bme280_sampler.disable()
        elif device ==  DeviceType.VEML7700:
            self.veml7700_sampler.disable()
        elif device ==  DeviceType.SGP40:
            self.sgp40_sampler.disable()
        elif device ==  DeviceType.LCD:
            with self._lock:
                self.lcd_display.disable()
