import smbus
from time import sleep
from registry import AppSettings, DeviceType
from i2c import I2CLCD

# Load the configuration settings and extract the communication properties
settings = AppSettings(AppSettings.default_settings_file())
bus_num = settings.settings["bus_number"]
mux_addr = int(settings.devices[DeviceType.MUX]["address"], 16)
addr = int(settings.devices[DeviceType.LCD]["address"], 16)
channel = settings.devices[DeviceType.LCD]["channel"]

bus = smbus.SMBus(bus_num)
lcd = I2CLCD(bus, addr, mux_addr, channel)

i = 0
while True:
    success, attempts = lcd.write(f"Count: {i}", line=1)
    print(f"{i}: Line 1: Status {success} after {attempts} attempt(s)")
    success, attempts = lcd.write("Pi Weather Stn", line=2)
    print(f"{i}: Line 2: Status {success} after {attempts} attempt(s)")
    i += 1
    sleep(1)
