import argparse
import datetime as dt
from weather import BME280


def main():
    ap = argparse.ArgumentParser(description="BME280 Sensor Check")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number (0 or 1 on Pi 1B)")
    ap.add_argument("--bme-addr", default="0x76", help="I2C address (0x76 or 0x77)")
    args = ap.parse_args()

    # Create the BME280 wrapper
    addr = int(args.bme_addr, 16)
    sensor = BME280(bus=args.bus, address=addr)
    
    # Read the sensors
    temperature, pressure, humidity = sensor.read()
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
    print(f"{timestamp}  T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")


if __name__ == "__main__":
    main()
