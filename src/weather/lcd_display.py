
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

    def _display_string(self, timestamp, text):
        text = f"{timestamp.strftime('%H:%M:%S')} : {text}"
        self.lcd.clear()
        self.lcd.write(text, line=1)

    def display_temperature(self):
        bme = self.sampler.get_latest_bme()
        if bme:
            self._display_string(bme["time_utc"], f"T = {bme['temperature_c']:.2f}{DEGREE}C")
        else:
            self._display_string(datetime.datetime.now(), "No reading")

    def run(self):
        """
        Run the LCD display event loop
        """
        # Start the timer and loop until we're interrupted
        next_tick = time.monotonic()
        logging.info(f"LCD display started: interval={self.interval:.3f} s")
        while not self.stop.is_set():
            try:
                self.display_temperature()

            except Exception as ex:
                logging.warning("Display error: %s", ex)

            # Wait for the next "tick"
            next_tick += self.interval
            time.sleep(max(0.0, next_tick - time.monotonic()))

        logging.info("LCD display stopped.")
