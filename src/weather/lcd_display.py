
import logging
import threading
import time
import datetime
from .sampler import Sampler

DEGREE = chr(223)


class LCDDisplay(threading.Thread):
    sampler: Sampler = None

    def __init__(self, lcd, sampler, interval):
        super().__init__(daemon=True)
        self.lcd = lcd
        self.sampler = sampler
        self.interval = float(interval)
        self.stop = threading.Event()

    def _display_reading(self, values, member, label, units):
        # Extract the timestamp and reading
        text = f"{label}={values[member]}{units}" if values else f"No {label} reading"

        # Display the timestamp and reading
        self.lcd.clear()
        self.lcd.write(datetime.datetime.now().strftime('%H:%M:%S'), line=1)
        self.lcd.write(text, line=2)

    def _display_temperature(self):
        bme = self.sampler.get_latest_bme()
        self._display_reading(bme, "temperature_c", "T", f"{DEGREE}C")

    def _display_pressure(self):
        bme = self.sampler.get_latest_bme()
        self._display_reading(bme, "pressure_hpa", "P", f" hPa")

    def _display_humidity(self):
        bme = self.sampler.get_latest_bme()
        self._display_reading(bme, "humidity_pct", "H", f"%")

    def run(self):
        """
        Run the LCD display event loop
        """
        # Define the callback functions to display values
        functions = [
            self._display_temperature,
            self._display_pressure,
            self._display_humidity
        ]

        # Initialise the callback index
        index = 0

        # Start the timer and loop until we're interrupted
        next_tick = time.monotonic()
        logging.info(f"LCD display started: interval={self.interval:.3f} s")
        while not self.stop.is_set():
            try:
                functions[index]()
                index = index + 1
                if index >= len(functions):
                    index = 0

            except Exception as ex:
                logging.warning("Display error: %s", ex)

            # Wait for the next "tick"
            next_tick += self.interval
            time.sleep(max(0.0, next_tick - time.monotonic()))

        logging.info("LCD display stopped.")
