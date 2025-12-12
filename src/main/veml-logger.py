import argparse
import signal
import time
import sys
import os
import datetime as dt
from sensors import VEML7700
from db import Database
from smbus2 import SMBus, i2c_msg
from i2c import I2CDevice, i2c_device_present


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
    ap.add_argument("--retention", type=int, default=43200, help="Data retention period (minutes)")
    ap.add_argument("--interval", type=float, default=60.0, help="Sample interval seconds")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number")
    ap.add_argument("--veml-addr", default="0x10", help="VEML7700 I2C address")
    ap.add_argument("--veml-gain", type=float, default=0.25, help="Gain (light sensor sensitivity)")
    ap.add_argument("--veml-integration-ms", type=int, default=100, help="Integration time (light collection time to produce a reading), ms")
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

    # Create the wrapper to query the BME280
    bus = SMBus(args.bus)
    addr = int(args.veml_addr, 16)
    if not i2c_device_present(bus, addr, False):
        ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        print(f"{ts}  I2C error: No device found at address {args.veml_addr}", file=sys.stderr)
        bus.close()
        return
    i2c_device = I2CDevice(bus, addr, i2c_msg)
    sensor = VEML7700(i2c_device, args.veml_gain, args.veml_integration_ms)

    # Create the database access wrapper
    database = Database(args.db, args.retention, args.bus, None, args.veml_addr, args.veml_gain, args.veml_integration_ms, None)
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
                print(f"{ts}  I2C error: {ex}; retrying in {args.interval}s", file=sys.stderr)

            # Wait for the specified interval
            next_t += args.interval
            delay = max(0.0, next_t - time.monotonic())
            time.sleep(delay)
    
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()


if __name__ == "__main__":
    main()