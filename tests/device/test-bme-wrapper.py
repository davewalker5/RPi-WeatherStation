import time
from os import environ
from weather import BME280


def main():
    bus = SMBus(int(environ["BUS_NUMBER"]))
    addr = int(args.veml_addr, 16)
    sensor = BME280(bus, addr)

    try:
        while True:
            temperature, pressure, humidity = sensor.read()
            print(f"T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")
            time.sleep(1.0)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
