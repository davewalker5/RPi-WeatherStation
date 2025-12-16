from typing import Sequence


class I2CDevice:
    """
    Helper around SMBus for devices that use 16-bit registers with
    LSB-first order on the bus
    """

    def __init__(self, bus, address, mux_addr, channel, msg_module):
        self.bus = bus
        self.address = address
        self.mux_addr = mux_addr
        self.channel = channel
        self.msg_module = msg_module

    def _select_channel(self):
        if self.mux_addr and self.channel:
            self.bus.write_byte(self.mux_addr, 1 << self.channel)

    def write_u16(self, register: int, value: int):
        """
        Write a 16-bit value, LSB then MSB, to 'register'.
        """
        value &= 0xFFFF
        lsb = value & 0xFF
        msb = (value >> 8) & 0xFF
        self._select_channel()
        self.bus.write_i2c_block_data(self.address, register, [lsb, msb])

    def read_u16(self, register: int) -> int:
        """
        Read a 16-bit value from 'register' (LSB then MSB on the wire).
        """
        self._select_channel()
        data = self.bus.read_i2c_block_data(self.address, register, 2)
        return data[0] | (data[1] << 8)

    def write_bytes_raw(self, data):
        """
        Raw I2C write
        """
        if isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = bytes(data)

        self._select_channel()
        msg = self.msg_module.write(self.address, data_bytes)
        self.bus.i2c_rdwr(msg)

    def read_bytes_raw(self, length: int) -> bytes:
        """
        Raw I2C read
        """
        self._select_channel()
        msg = self.msg_module.read(self.address, length)
        self.bus.i2c_rdwr(msg)
        return bytes(msg)
