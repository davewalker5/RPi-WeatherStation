import time
from os import environ
import datetime as dt
from weather import VEML7700
from smbus2 import SMBus, i2c_msg
from i2c import I2CDevice


def main():
    bus = SMBus(int(environ["BUS_NUMBER"]))
    addr = int(environ["VEML_ADDR"], 16)
    i2c_device = I2CDevice(bus, addr, i2c_msg)
    sensor = VEML7700(
        i2c_device,
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
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
            als, white, lux = sensor.read()
            print(f"{timestamp}  ALS={als:5d}  WHITE={white:5d}  LUX≈{lux:8.2f}")
            time.sleep(1.0)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
