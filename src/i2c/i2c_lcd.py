from time import sleep

LCD_CHR = 1  # RS bit = 1 for data
LCD_CMD = 0  # RS bit = 0 for command

ENABLE = 0b00000100   # E bit

LCD_LINE_1 = 0x80     # DDRAM addr for line 1
LCD_LINE_2 = 0xC0     # DDRAM addr for line 2

E_PULSE = 0.0005      # 500 µs
E_DELAY = 0.0005


class I2CLCD:
    def __init__(self, bus, addr, backlight=True, max_retries=3):
        """
        bus: Mock or real SMBus()
        addr: I2C address of the LCD
        backlight: Initial backlight state
        max_retries: Retries on I2C error before reinitialising the display
        """
        self.bus = bus
        self.addr = addr
        self.backlight = backlight
        self.max_retries = max_retries
        self.i2c_errors = 0  # count of Remote I/O errors seen

        self._init_display()

    # -------------------------------
    # Backlight control
    # -------------------------------

    def backlight_on(self):
        self.backlight = True
        self._refresh_backlight()

    def backlight_off(self):
        self.backlight = False
        self._refresh_backlight()

    def toggle_backlight(self):
        self.backlight = not self.backlight
        self._refresh_backlight()

    def _bl_bit(self):
        return 0x08 if self.backlight else 0x00

    def _refresh_backlight(self):
        """
        Force a write so the LCD output updates immediately
        """
        # Best-effort write; ignore errors here
        try:
            self.bus.write_byte(self.addr, self._bl_bit())
        except OSError:
            pass

    # -------------------------------
    # Low level I2C helpers
    # -------------------------------

    def _safe_write(self, value):
        """
        Write a byte to the I2C expander with retries.

        Returns True on success, False after self.max_retries failures
        Never raises OSError
        """
        last_exc = None
        for _ in range(self.max_retries):
            try:
                self.bus.write_byte(self.addr, value)
                return True
            except OSError as e:
                last_exc = e
                # Small back-off before retrying
                sleep(0.002)

        # All retries failed
        self.i2c_errors += 1
        print(f"I2CLCD: I2C write failed after {self.max_retries} retries "
              f"(errors so far: {self.i2c_errors}): {last_exc}")

        # Try to get LCD back into a sane state, but ignore any errors here
        try:
            self._init_display()
        except Exception:
            pass

        return False

    def _lcd_strobe(self, data):
        """
        Toggle the enable pin to latch data into the LCD
        """
        if not self._safe_write(data | ENABLE):
            return  # give up if we can't talk to the device
        sleep(E_PULSE)
        if not self._safe_write(data & ~ENABLE):
            return
        sleep(E_DELAY)

    def _lcd_byte(self, bits, mode):
        """
        Send a single byte to the LCD in 4-bit mode (two nibbles)
        mode: LCD_CMD (0) for command, LCD_CHR (1) for data
        """
        bl = self._bl_bit()

        high = mode | (bits & 0xF0) | bl
        low = mode | ((bits << 4) & 0xF0) | bl

        # High nibble
        if not self._safe_write(high):
            return
        self._lcd_strobe(high)

        # Low nibble
        if not self._safe_write(low):
            return
        self._lcd_strobe(low)

    # -------------------------------
    # LCD initialisation & commands
    # -------------------------------

    def _init_display(self):
        """
        Run the recommended HD44780 4-bit initialisation sequence.
        """
        sleep(0.05)

        # If I2C is really dead, these calls will just quietly fail via _safe_write.
        self._lcd_byte(0x33, LCD_CMD)
        self._lcd_byte(0x32, LCD_CMD)
        self._lcd_byte(0x28, LCD_CMD)
        self._lcd_byte(0x0C, LCD_CMD)
        self._lcd_byte(0x06, LCD_CMD)
        self._lcd_byte(0x01, LCD_CMD)
        sleep(0.002)

    def clear(self):
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

        for char in text.ljust(16)[:16]:
            self._lcd_byte(ord(char), LCD_CHR)

    def reinit(self):
        self._init_display()