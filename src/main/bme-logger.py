import argparse
import signal
import time
import datetime as dt
from ..weather import BME280, create_database, insert_row

STOP = False

def _sig_handler(signum, frame):
    global STOP
    STOP = True


def sample_sensor(sensor, db_path, table_name, bus, addr):
    t, p, h = sensor.read()
    ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
    insert_row(db_path, table_name, bus, addr, ts, t, p, h)
    print(f"{ts}  T={t:.2f}°C  P={p:.2f} hPa  H={h:.2f}%")


def main():
    ap = argparse.ArgumentParser(description="BME280 → SQLite logger")
    ap.add_argument("--db", default="bme280.db", help="SQLite database path")
    ap.add_argument("--interval", type=float, default=60.0, help="Sample interval seconds")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number (0 or 1 on Pi 1B)")
    ap.add_argument("--addr", default="0x76", help="I2C address (0x76 or 0x77)")
    ap.add_argument("--table", default="readings", help="Table name to insert into")
    ap.add_argument("--once", action="store_true", help="Take one reading and exit")
    args = ap.parse_args()

    # Install signal handlers for graceful stop
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    addr = int(args.addr, 16)

    create_database(args.db)

    sensor = BME280(bus=args.bus, address=addr)

    if args.once:
        sample_sensor()
        return

    print(f"Logging to {args.db} (table `{args.table}`) every {args.interval}s "
          f"on bus {args.bus} addr {hex(addr)}. Ctrl-C to stop.")
    next_t = time.monotonic()
    while not STOP:
        try:
            sample_sensor(sensor, args.db, args.table, args.bus, args.addr)
        except OSError as ex:
            ts = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            print(f"{ts}  I2C error: {ex}; retrying in {args.interval}s", file=sys.stderr)

        next_t += args.interval
        sleep_for = max(0.0, next_t - time.monotonic())
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()