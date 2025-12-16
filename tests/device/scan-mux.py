from smbus2 import SMBus
import time
import os

I2C_BUS = 1
MUX_ADDR = int(os.environ["MUX_ADDR"], 16)
I2C_MIN = 0x03
I2C_MAX = 0x77

def select_channel(bus, channel):
    """Enable a single channel on the TCA9548A."""
    bus.write_byte(MUX_ADDR, 1 << channel)
    time.sleep(0.01)     # short settle time

def scan_bus(bus):
    """Return list of detected I2C addresses."""
    found = []
    for addr in range(I2C_MIN, I2C_MAX + 1):
        try:
            bus.read_byte(addr)
            found.append(addr)
        except OSError:
            pass
    return found

def main():
    print("TCA9548A I2C MUX scan\n")

    with SMBus(I2C_BUS) as bus:
        for channel in range(8):
            try:
                select_channel(bus, channel)
            except OSError as e:
                print(f"Channel {channel}: MUX select failed ({e})")
                continue

            devices = scan_bus(bus)

            if devices:
                addrs = ", ".join(f"0x{a:02X}" for a in devices)
                print(f"Channel {channel}: {addrs}")
            else:
                print(f"Channel {channel}: no devices found")

        # Disable all channels at end
        bus.write_byte(MUX_ADDR, 0x00)

if __name__ == "__main__":
    main()