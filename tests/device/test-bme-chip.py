from smbus2 import SMBus
from registry import AppSettings, DeviceType

# Load the configuration settings and extract the communication properties
settings = AppSettings(AppSettings.default_settings_file())
mux_address = int(settings.devices[DeviceType.MUX]["address"], 16)
bme_address = int(settings.devices[DeviceType.BME280]["address"], 16)
bme_channel = settings.devices[DeviceType.BME280]["channel"]

# Create the SMBus instance
bus = SMBus(settings.settings["bus_number"])

# Select the BME280 channel
if mux_address and bme_channel:
    bus.write_byte(mux_address, 1 << bme_channel)

# Get the chip ID
chip_id = bus.read_byte_data(bme_address, 0xD0)
print("BME280 chip ID:", hex(chip_id))
