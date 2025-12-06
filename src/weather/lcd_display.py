
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
        self.started = False

    def _display_startup(self):
        self.lcd.clear()
        self.lcd.write("Weather Service", line=1)
        self.lcd.write("starting ...", line=2)

    def _display_reading(self, values, member, label, units):
        # Extract the timestamp and reading
        text = f"{label} = {values[member]}{units}" if values else f"No {label} reading"

        # Display the timestamp and reading
        self.lcd.clear()
        self.lcd.write(datetime.datetime.now().strftime('%H:%M:%S'), line=1)
        self.lcd.write(text, line=2)

    def _display_temperature(self):
        values = self.sampler.get_latest_bme()
        self._display_reading(values, "temperature_c", "T", f"{DEGREE}C")

    def _display_pressure(self):
        values = self.sampler.get_latest_bme()
        self._display_reading(values, "pressure_hpa", "P", f" hPa")

    def _display_humidity(self):
        values = self.sampler.get_latest_bme()
        self._display_reading(values, "humidity_pct", "H", f"%")

    def _display_illuminance(self):
        values = self.sampler.get_latest_veml()
        self._display_reading(values, "illuminance_lux", "I", f" lux")

    def _display_air_quality(self):
        values = self.sampler.get_latest_sgp()
        self._display_reading(values, "voc_label", "Quality", "")

    def run(self):
        """
        Run the LCD display event loop
        """
        # Define the callback functions to display values
        functions = [
            self._display_temperature,
            self._display_pressure,
            self._display_humidity,
            self._display_illuminance,
            self._display_air_quality
        ]

        # Initialise the callback index
        index = 0

        # Start the timer and loop until we're interrupted
        next_tick = time.monotonic()
        logging.info(f"LCD display started: interval={self.interval:.3f} s")
        while not self.stop.is_set():
            try:
                # First time, show the startup messages - this gives the sampler a chance
                # to start recording readings
                if not self.started:
                    self.started = True
                    self._display_startup()
                else:
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
