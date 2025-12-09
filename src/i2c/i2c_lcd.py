from time import sleep

LCD_CHR = 1  # RS bit = 1 for data
LCD_CMD = 0  # RS bit = 0 for command

LCD_BACKLIGHT = 0x08  # backlight on (0x00 to turn off)
ENABLE = 0b00000100   # E bit

LCD_LINE_1 = 0x80     # DDRAM addr for line 1
LCD_LINE_2 = 0xC0     # DDRAM addr for line 2

E_PULSE = 0.0005      # 500 µs
E_DELAY = 0.0005


class I2CLCD:
    def __init__(self, bus, addr):
        """
        bus: smbus.SMBus(1)
        addr: I2C address of the PCF8574 (e.g. 0x27)
        """
        self.bus = bus
        self.addr = addr

        # init the display
        self._init_display()

    def _safe_write(self, value):
        """
        Write a byte to the I2C expander, with a simple retry on transient errors.
        """
        try:
            self.bus.write_byte(self.addr, value)
        except OSError:
            # brief pause and one retry; if this fails too, let it raise
            sleep(0.01)
            self.bus.write_byte(self.addr, value)

    def _lcd_strobe(self, data):
        """
        Toggle the enable pin to latch data into the LCD.
        """
        # Enable high
        self._safe_write(data | ENABLE)
        sleep(E_PULSE)

        # Enable low
        self._safe_write(data & ~ENABLE)
        sleep(E_DELAY)

    def _lcd_byte(self, bits, mode):
        """
        Send a single byte to the LCD in 4-bit mode (two nibbles).
        mode: LCD_CMD (0) for command, LCD_CHR (1) for data.
        """
        # High nibble
        high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        # Low nibble
        low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        self._safe_write(high)
        self._lcd_strobe(high)

        self._safe_write(low)
        self._lcd_strobe(low)

    def _init_display(self):
        """
        Run the recommended HD44780 4-bit initialisation sequence.
        """
        # Wait for LCD power-up
        sleep(0.05)

        self._lcd_byte(0x33, LCD_CMD)  # initialise
        self._lcd_byte(0x32, LCD_CMD)  # set to 4-bit mode
        self._lcd_byte(0x28, LCD_CMD)  # 2 line, 5x8 font
        self._lcd_byte(0x0C, LCD_CMD)  # display on, cursor off, blink off
        self._lcd_byte(0x06, LCD_CMD)  # entry mode
        self._lcd_byte(0x01, LCD_CMD)  # clear display
        sleep(0.002)

    def clear(self):
        """
        Clear the display and home the cursor.
        """
        self._lcd_byte(0x01, LCD_CMD)
        sleep(0.002)

    def write(self, text, line=1):
        """
        Write up to 16 characters to the given line (1 or 2).
        Text longer than 16 chars will be truncated.
        """
        if line == 1:
            self._lcd_byte(LCD_LINE_1, LCD_CMD)
        else:
            self._lcd_byte(LCD_LINE_2, LCD_CMD)

        # Pad or truncate to exactly 16 characters
        for char in text.ljust(16)[:16]:
            self._lcd_byte(ord(char), LCD_CHR)

    def reinit(self):
        """
        Public method you can call if you suspect the LCD is confused.
        """
        self._init_display()
