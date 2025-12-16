import argparse
import os
import datetime as dt
from sensors import BME280
from smbus2 import SMBus


def main():
    ap = argparse.ArgumentParser(description="BME280 Sensor Check")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number (0 or 1 on Pi 1B)")
    ap.add_argument("--mux-addr", default="0x70", help="Multiplexer address")
    ap.add_argument("--bme-addr", default="0x76", help="I2C address (0x76 or 0x77)")
    ap.add_argument("--bme-channel", default="5", help="Multiplexer channel")
    args = ap.parse_args()

    # Show the argument values
    print()
    print(os.path.basename(__file__).upper())
    print()
    args_dict = vars(args)
    for name, value in args_dict.items():
        print(f"{name} : {value}")
    print()

    # Create the BME280 wrapper
    mux_addr = int(args.mux_addr, 16) if (args.mux_addr.strip()) else None
    bus = SMBus(args.bus)
    addr = int(args.bme_addr, 16)
    channel = int(args.bme_channel, 16) if (args.bme_channel.strip()) else None
    sensor = BME280(bus, addr, mux_addr, channel)
    
    # Read the sensors
    temperature, pressure, humidity = sensor.read()
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
    print(f"{timestamp}  T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")


if __name__ == "__main__":
    main()
