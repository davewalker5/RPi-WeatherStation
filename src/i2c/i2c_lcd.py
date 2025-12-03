from smbus2 import SMBus
from time import sleep

# PCF8574 pin mapping (typical for most 1602 I2C backpacks)
LCD_CHR = 1  # Mode - Sending data
LCD_CMD = 0  # Mode - Sending command

LCD_BACKLIGHT = 0x08  # On
# LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100  # Enable bit

LCD_LINE_1 = 0x80  # First line
LCD_LINE_2 = 0xC0  # Second line

class I2CLCD:
    def __init__(self, bus, addr):
        self.bus = bus
        self.addr = addr
        self._init_lcd()

    def _init_lcd(self):
        # Initialise display
        self._lcd_byte(0x33, LCD_CMD)
        self._lcd_byte(0x32, LCD_CMD)
        self._lcd_byte(0x06, LCD_CMD)
        self._lcd_byte(0x0C, LCD_CMD)
        self._lcd_byte(0x28, LCD_CMD)
        self._lcd_byte(0x01, LCD_CMD)
        sleep(0.005)

    def _lcd_strobe(self, data):
        self.bus.write_byte(self.addr, data | ENABLE)
        sleep(0.0005)
        self.bus.write_byte(self.addr, data & ~ENABLE)
        sleep(0.0001)

    def _lcd_byte(self, bits, mode):
        high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        self.bus.write_byte(self.addr, high)
        self._lcd_strobe(high)

        self.bus.write_byte(self.addr, low)
        self._lcd_strobe(low)

    def clear(self):
        self._lcd_byte(0x01, LCD_CMD)
        sleep(0.002)

    def write(self, text, line=1):
        if line == 1:
            self._lcd_byte(LCD_LINE_1, LCD_CMD)
        else:
            self._lcd_byte(LCD_LINE_2, LCD_CMD)

        for char in text.ljust(16):  # pad to 16 chars
            self._lcd_byte(ord(char), LCD_CHR)
