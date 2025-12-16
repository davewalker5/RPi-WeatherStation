import argparse
import signal
import time
import sys
import os
import datetime as dt
from registry import AppSettings, DeviceFactory, DeviceType
from db import Database
from smbus2 import SMBus


STOP = False

def _sig_handler(signum, frame):
    """
    Signal handler to break out of the sensor loop
    """
    global STOP
    STOP = True


def sample_sensors(sensor, database):
    """
    Sample the BME280 sensors, write the results to the database and echo them on the terminal
    """
    temperature, pressure, humidity = sensor.read()
    timestamp = database.insert_bme_row(temperature, pressure, humidity)
    print(f"{timestamp}  T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")


def main():
    ap = argparse.ArgumentParser(description="BME280 to SQLite and Console Logger")
    ap.add_argument("--db", default="weather.db", help="SQLite database path")
    ap.add_argument("--once", action="store_true", help="Take one reading and exit")
    args = ap.parse_args()

    # Show the argument values
    print()
    print(os.path.basename(__file__).upper())
    print()
    args_dict = vars(args)
    for name, value in args_dict.items():
        print(f"{name} : {value}")
    print()

    # Install signal handlers for graceful stop
    signal.signal(signal.SIGTERM, _sig_handler)

    # Load the configuration settings and construct the sensor wrapper
    settings = AppSettings(AppSettings.default_settings_file())
    bus = SMBus(settings.settings["bus_number"])
    factory = DeviceFactory(bus, None, None, settings)
    sensor = factory.create_device(DeviceType.BME280)
    if not sensor:
        ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        print(f"{ts} Error: BME280 not detected", file=sys.stderr)
        bus.close()
        return

    # Create the database access wrapper
    database = factory.create_database(args.db)
    database.create_database()

    # If one-shot has been specified, sample the sensor, display the results and exit
    if args.once:
        sample_sensors(sensor, database)
        return

    # Set up for readings at specified intervals
    next_t = time.monotonic()

    try:
        global STOP
        while not STOP:
            try:
                # Purge old data and snapshot database sizes
                database.purge()
                database.snapshot_sizes()

                # Take the next readings
                sample_sensors(sensor, database)
            except OSError as ex:
                ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
                print(f"{ts} Error: {ex}", file=sys.stderr)

            # Wait for the specified interval
            next_t += settings.settings["sample_interval"]
            delay = max(0.0, next_t - time.monotonic())
            time.sleep(delay)
    
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    main()