import os
import datetime as dt
from registry import AppSettings, DeviceFactory, DeviceType
from smbus2 import SMBus


def main():
    # Show the argument values
    print()
    print(os.path.basename(__file__).upper())
    print()

    # Load the configuration settings and extract the communication properties
    settings = AppSettings(AppSettings.default_settings_file())
    bus = SMBus(settings.settings["bus_number"])
    factory = DeviceFactory(bus, None, None, settings)
    sensor = factory.create_device(DeviceType.BME280)
    
    # Read the sensors
    temperature, pressure, humidity = sensor.read()
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
    print(f"{timestamp}  T={temperature:.2f}°C  P={pressure:.2f} hPa  H={humidity:.2f}%")


if __name__ == "__main__":
    main()
