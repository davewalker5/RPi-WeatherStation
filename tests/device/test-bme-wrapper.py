import time
from os import environ, getenv
import datetime as dt
from sensors import BME280
from smbus2 import SMBus


def main():
    mux_addr = int(mux_addr, 16) if (mux_addr:= getenv("MUX_ADDR", "").strip()) else None
    bus = SMBus(int(environ["BUS_NUMBER"]))
    addr = int(environ["BME_ADDR"], 16)
    channel = int(channel) if (channel:= getenv("BME_CHANNEL", "").strip()) else None
    sensor = BME280(bus, addr, mux_addr, channel)

    try:
        while True:
            temperature, pressure, humidity = sensor.read()
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
            print(f"{timestamp} T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")
            time.sleep(1.0)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
