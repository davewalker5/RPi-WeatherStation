class SMBus:
    def __init__(self, bus_number):
        self.fixtures = None

    def set_fixtures(self, fixtures):
        self.fixtures = fixtures

    def write_byte_data(self, addr, reg, value):
        pass

    def write_i2c_block_data(self, addr, reg, data):
        pass

    def close(self):
        pass

    def read_byte_data(self, addr, reg):
        return self.fixtures["trimming_parameters"].get(reg, 0x00)

    def read_i2c_block_data(self, addr, reg, length):
        key = (addr, reg)
        block = self.fixtures["measurement_blocks"][key]
        assert len(block) >= length
        return block[:length]
