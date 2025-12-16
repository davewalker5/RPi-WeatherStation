import time
import datetime as dt
from registry import AppSettings, DeviceFactory, DeviceType
from smbus2 import SMBus, i2c_msg


def main():
    # Load the configuration settings and extract the communication properties
    settings = AppSettings(AppSettings.default_settings_file())
    bus = SMBus(settings.settings["bus_number"])
    factory = DeviceFactory(bus, i2c_msg, None, settings)
    sensor = factory.create_device(DeviceType.VEML7700)

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
