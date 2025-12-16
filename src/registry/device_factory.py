from i2c import i2c_device_present, I2CDevice, I2CLCD
from sensors import BME280, VEML7700, SGP40

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
        if i2c_device_present(self.bus, address, mux_address, channel, False):
            # Identify the method used to create an instance of the wrapper for this device and call it
            instantiator = getattr(self, f"_create_{name.lower()}")
            device = instantiator(mux_address, address, channel, properties)
        else:
            device = None

        # Return the device instance
        return device

