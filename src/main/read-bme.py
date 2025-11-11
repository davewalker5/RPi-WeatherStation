import argparse
import datetime as dt
from weather import BME280

STOP = False

def sample_sensor(sensor):
    t, p, h = sensor.read()
    ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
    print(f"{ts}  T={t:.2f}°C  P={p:.2f} hPa  H={h:.2f}%")


def main():
    ap = argparse.ArgumentParser(description="BME280 → SQLite logger")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number (0 or 1 on Pi 1B)")
    ap.add_argument("--addr", default="0x76", help="I2C address (0x76 or 0x77)")
    args = ap.parse_args()

    addr = int(args.addr, 16)

    sensor = BME280(bus=args.bus, address=addr)
    sample_sensor(sensor)

if __name__ == "__main__":
    main()
