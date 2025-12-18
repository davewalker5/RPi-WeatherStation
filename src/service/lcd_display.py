
import logging
import datetime
import threading

DEGREE = chr(223)


class LCDDisplay:
    def __init__(self, lcd):
        # Capture the LCD display wrappe
        self.lcd = lcd
        self.enabled = lcd is not None
        self.lock = threading.Lock()

        # Define the callback functions to display values
        self.functions = [
            self._display_temperature,
            self._display_pressure,
            self._display_humidity,
            self._display_illuminance,
            self._display_air_quality
        ]

        # Initialise the callback index
        self.index = 0

    def _display_reading(self, values, member, label, units):
        # Check there's a reading to display
        have_reading = values is not None
        if have_reading:
            # Extract the timestamp and reading
            text = f"{label} = {values[member]}{units}" if values else f"No {label} reading"

            # Display the timestamp and reading
            self.lcd.clear()
            self.lcd.write(datetime.datetime.now().strftime('%H:%M:%S'), line=1)
            self.lcd.write(text, line=2)

        return have_reading

    def _display_temperature(self, sampler):
        values = sampler.get_latest_bme()
        return self._display_reading(values, "temperature_c", "T", f"{DEGREE}C")

    def _display_pressure(self, sampler):
        values = sampler.get_latest_bme()
        return self._display_reading(values, "pressure_hpa", "P", f" hPa")

    def _display_humidity(self, sampler):
        values = sampler.get_latest_bme()
        return self._display_reading(values, "humidity_pct", "H", f"%")

    def _display_illuminance(self, sampler):
        values = sampler.get_latest_veml()
        return self._display_reading(values, "illuminance_lux", "I", f" lux")

    def _display_air_quality(self, sampler):
        values = sampler.get_latest_sgp()
        return self._display_reading(values, "voc_rating", "VOC", "")

    def display_next(self, sampler):
        """
        Show the next reading in the sequence
        """

        # Do nothing if the display's not enabled
        if not self.enabled:
            return

        with self.lock:
            try:
                # Loop until we've found and displayed a reading for a sensor
                sensor_counter = 0
                while True:
                    # Count the passes through this loop and break out if we've tried them all and there's
                    # nothing there
                    sensor_counter = sensor_counter + 1
                    if sensor_counter >= len(self.functions):
                        break

                    # Try to display the reading for the sensor at the current index
                    with self.lock:
                        if self.enabled:
                            have_reading = self.functions[self.index](sampler)

                    # Move on to the next index
                    self.index = self.index + 1
                    if self.index >= len(self.functions):
                        self.index = 0

                    # If we got a reading, break out
                    if have_reading:
                        break

            except Exception as ex:
                logging.warning("Display error: %s", ex)

    def disable(self):
        self.enabled = False
        if self.lcd:
            with self.lock:
                self.lcd.clear()
                self.lcd.backlight_off()

    def enable(self):
        if self.lcd and not self.enabled:
            with self.lock:
                self.enabled = True
                self.lcd.clear()
                self.lcd.backlight_on()
