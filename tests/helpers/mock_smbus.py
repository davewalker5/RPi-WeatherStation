class MockSMBus:
    def __init__(self, trimming_parameters, measurement_blocks):
        self.trimming_parameters = trimming_parameters
        self.measurement_blocks = measurement_blocks

    def write_byte_data(self, addr, reg, value):
        pass

    def write_i2c_block_data(self, addr, reg, data):
        pass

    def close(self):
        pass

    def read_byte_data(self, _, reg):
        """
        Read one of the trimming parameters
        """
        return self.trimming_parameters.get(reg, 0x00)

    def read_i2c_block_data(self, addr, reg, length):
        """
        Read a measurement block
        """
        key = (addr, reg)
        block = self.measurement_blocks[key]
        assert len(block) >= length
        return block[:length]
