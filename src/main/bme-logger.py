import argparse
import signal
import time
import sys
import datetime as dt
from weather import BME280, Database

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
    t, p, h = sensor.read()
    ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
    database.insert_row(ts, t, p, h)
    print(f"{ts}  T={t:.2f}°C  P={p:.2f} hPa  H={h:.2f}%")


def main():
    ap = argparse.ArgumentParser(description="BME280 → SQLite logger")
    ap.add_argument("--db", default="bme280.db", help="SQLite database path")
    ap.add_argument("--interval", type=float, default=60.0, help="Sample interval seconds")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number (0 or 1 on Pi 1B)")
    ap.add_argument("--addr", default="0x76", help="I2C address (0x76 or 0x77)")
    ap.add_argument("--once", action="store_true", help="Take one reading and exit")
    args = ap.parse_args()

    # Install signal handlers for graceful stop
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    # Create the wrapper to query the BME280
    addr = int(args.addr, 16)
    sensor = BME280(bus=args.bus, address=addr)

    # Create the database access wrapper
    database = Database(args.bus, args.addr, args.db)
    database.create_database()

    # If one-shot has been specified, sample the sensor, display the results and exit
    if args.once:
        sample_sensors(sensor, database)
        return

    print(f"BME280 is on bus {args.bus} at address {hex(addr)}")
    print(f"Logging to {args.db} every {args.interval}s")
    print("Ctrl-C to stop")

    # Set up for readings at specified intervals
    next_t = time.monotonic()
    while not STOP:
        # Take the next readings
        try:
            sample_sensors(sensor, database)
        except OSError as ex:
            ts = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            print(f"{ts}  I2C error: {ex}; retrying in {args.interval}s", file=sys.stderr)

        # Wait for the specified interval
        next_t += args.interval
        delay = max(0.0, next_t - time.monotonic())
        time.sleep(delay)


if __name__ == "__main__":
    main()