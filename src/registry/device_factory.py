from i2c import i2c_device_present, I2CDevice, I2CLCD
from sensors import BME280, VEML7700, SGP40
from db import Database
from .device_type import DeviceType


class DeviceFactory:
    def __init__(self, bus, msg_module, voc_algorithm, app_settings):
        self.bus = bus
        self.msg_module = msg_module
        self.voc_algorithm = voc_algorithm
        self.app_settings = app_settings

    def _get_device_address(self, properties):
        return int(properties["address"], 16) if properties["address"].strip() else None

    def _get_mux_address(self):
        mux_settings = self.app_settings.devices["MUX"]
        return self._get_device_address(mux_settings)

    def _create_bme280(self, mux_address, address, channel, _):
        return BME280(self.bus, address, mux_address, channel)

    def _create_veml7700(self, mux_address, address, channel, properties):
        i2c_device = I2CDevice(self.bus, address, mux_address, channel, self.msg_module)
        return VEML7700(i2c_device, properties["gain"], properties["integration_time"])

    def _create_sgp40(self, mux_address, address, channel, _):
        i2c_device = I2CDevice(self.bus, address, mux_address, channel, self.msg_module)
        return SGP40(i2c_device, self.voc_algorithm)

    def _create_lcd(self, mux_address, address, channel, _):
        return I2CLCD(self.bus, address, mux_address, channel)

    def create_device(self, name):
        # Get the MUX address
        mux_address = self._get_mux_address()

        # Get the device-specific properties
        properties = self.app_settings.devices[name]
        address = self._get_device_address(properties)
        channel = properties["channel"]

        # Check the device is attached
        device = None
        if i2c_device_present(self.bus, address, mux_address, channel, properties["use_write_quick"]):
            # Identify the method used to create an instance of the wrapper for this device and call it
            instantiator = getattr(self, f"_create_{name.lower()}")
            if instantiator:
                device = instantiator(mux_address, address, channel, properties)

        # Return the device instance
        return device

    def create_all_devices(self):
        devices = {}

        # Iterate over all possible device types
        for device_type in DeviceType:
            # Exclude the MUX
            if device_type != DeviceType.MUX:
                # Create the device and construct a dictionary containing it and it's enabled state
                # Enabled depends on successful creation of the device and the initial state in the
                # application settings
                device = self.create_device(device_type)
                devices[device_type] = {
                    "device": device,
                    "enabled": device and self.app_settings.devices[device_type]["initial_state"] 
                }
        
        return devices

    def create_database(self, database_path):
        # Extract the database and persistence properties from the settings
        retention = self.app_settings.settings["retention"]
        bus_number = self.app_settings.settings["bus_number"]
        bme_address = self.app_settings.devices[DeviceType.BME280]["address"]
        veml_address = self.app_settings.devices[DeviceType.VEML7700]["address"]
        veml_gain = self.app_settings.devices[DeviceType.VEML7700]["gain"]
        veml_it = self.app_settings.devices[DeviceType.VEML7700]["integration_time"]
        sgp_address = self.app_settings.devices[DeviceType.VEML7700]["address"]

        # Create the database wrapper
        database = Database(database_path, retention, bus_number, bme_address, veml_address, veml_gain, veml_it, sgp_address)
        return database

