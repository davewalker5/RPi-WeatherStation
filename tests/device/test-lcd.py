from i2c import I2CLCD
from time import sleep
from registry import AppSettings, DeviceType
from smbus2 import SMBus

# Load the configuration settings and extract the communication properties
settings = AppSettings(AppSettings.default_settings_file())
bus_num = settings.settings["bus_number"]
mux_addr = int(settings.devices[DeviceType.MUX]["address"], 16)
addr = int(settings.devices[DeviceType.LCD]["address"], 16)
channel = settings.devices[DeviceType.LCD]["channel"]

bus = SMBus(bus_num)
lcd = I2CLCD(bus, addr, mux_addr, channel)

lcd.clear()
lcd.write("Hello, world!", line=1)
lcd.write("Raspberry Pi!", line=2)

sleep(5)
lcd.clear()
