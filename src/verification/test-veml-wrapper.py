import time
from os import environ
from weather import VEML7700

try:
    from smbus2 import SMBus
except ImportError:
    from ..i2c.mock_smbus import SMBus

def main():
    bus = SMBus(int(environ["BUS_NUMBER"]))
    sensor = VEML7700(
        bus=bus,
        address=int(environ["VEML_ADDR"], 16),
        gain=float(environ["VEML_GAIN"]),
        integration_time_ms=int(environ["VEML_INTEGRATION_TIME"])
    )

    # Confirm ID + config
    try:
        dev_id = sensor.read_id()
        conf   = sensor.read_conf()
        print(f"ID=0x{dev_id:04X}, CONF=0x{conf:04X}")
    except AttributeError:
        pass

    try:
        while True:
            als, white, lux = sensor.read()
            print(f"ALS={als:5d}  WHITE={white:5d}  LUX≈{lux:8.2f}")
            time.sleep(1.0)
    finally:
        bus.close()


if __name__ == "__main__":
    main()