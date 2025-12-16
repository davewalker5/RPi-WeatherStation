import argparse
import signal
import time
import sys
import os
import datetime as dt
from registry import AppSettings, DeviceFactory, DeviceType
from smbus2 import SMBus, i2c_msg


STOP = False

def _sig_handler(signum, frame):
    """
    Signal handler to break out of the sensor loop
    """
    global STOP
    STOP = True


def sample_sensors(sensor, database):
    """
    Sample the VEML770 sensors, write the results to the database and echo them on the terminal
    """
    als, white, lux = sensor.read()
    is_saturated = sensor.is_saturated(als)
    timestamp = database.insert_veml_row(als, white, lux, is_saturated)
    print(f"{timestamp}  Gain={sensor.gain}  Integration Time={sensor.integration_time_ms} ms  ALS={als}  White={white}  Illuminance={lux:.2f} lux  IsSaturated={is_saturated}")


def main():
    ap = argparse.ArgumentParser(description="VEML7700 to SQLite and Console Logger")
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
    factory = DeviceFactory(bus, i2c_msg, None, settings)
    sensor = factory.create_device(DeviceType.VEML7700)
    if not sensor:
        ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        print(f"{ts} Error: VEML7700 not detected", file=sys.stderr)
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