import time
import datetime as dt
from registry import AppSettings, DeviceFactory, DeviceType
from smbus2 import SMBus, i2c_msg
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm


def main():
    # Load the configuration settings and extract the communication properties
    settings = AppSettings(AppSettings.default_settings_file())
    bus = SMBus(settings.settings["bus_number"])
    factory = DeviceFactory(bus, i2c_msg, VocAlgorithm(), settings)
    sensor = factory.create_device(DeviceType.SGP40)

    try:
        while True:
            sraw, voc_index, voc_label, voc_rating = sensor.read()
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
            print(f"{timestamp}  SRAW: {sraw}  VOC Index: {voc_index}  Assessment: {voc_label}  Rating: {voc_rating}")
            time.sleep(1.0)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
