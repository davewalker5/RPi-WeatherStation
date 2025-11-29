class I2CWordDevice:
    """
    Helper around SMBus for devices that use 16-bit registers with
    LSB-first order on the bus
    """

    def __init__(self, bus, address):
        self.bus = bus
        self.address = address

    def write_u16(self, register: int, value: int):
        """
        Write a 16-bit value, LSB then MSB, to 'register'.
        """
        value &= 0xFFFF
        lsb = value & 0xFF
        msb = (value >> 8) & 0xFF
        self.bus.write_i2c_block_data(self.address, register, [lsb, msb])

    def read_u16(self, register: int) -> int:
        """
        Read a 16-bit value from 'register' (LSB then MSB on the wire).
        """
        data = self.bus.read_i2c_block_data(self.address, register, 2)
        return data[0] | (data[1] << 8)
