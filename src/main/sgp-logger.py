import argparse
import signal
import time
import sys
import os
import datetime as dt
from weather import SGP40, Database
from smbus2 import SMBus, i2c_msg
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm
from i2c import I2CDevice


STOP = False

def _sig_handler(signum, frame):
    """
    Signal handler to break out of the sensor loop
    """
    global STOP
    STOP = True


def sample_sensors(sensor, database):
    """
    Sample the SGP40 sensors, write the results to the database and echo them on the terminal
    """
    sraw, index, label = sensor.read()
    timestamp = database.insert_sgp_row(sraw, index, label)
    print(f"{timestamp}  SRAW: {sraw}  VOC Index: {index}   {label}")


def main():
    ap = argparse.ArgumentParser(description="SGP40 to SQLite and Console Logger")
    ap.add_argument("--db", default="weather.db", help="SQLite database path")
    ap.add_argument("--retention", type=int, default=43200, help="Data retention period (minutes)")
    ap.add_argument("--interval", type=float, default=60.0, help="Sample interval seconds")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number")
    ap.add_argument("--sgp-addr", default="0x10", help="SGP40 I2C address")
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
    addr = int(args.sgp_addr, 16)
    i2c_device = I2CDevice(bus, addr, i2c_msg)
    sensor = SGP40(i2c_device, VocAlgorithm())

    # Create the database access wrapper
    database = Database(args.db, args.retention, args.bus, None, None, None, None, args.sgp_addr)
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
                # Purge old data
                database.purge()

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