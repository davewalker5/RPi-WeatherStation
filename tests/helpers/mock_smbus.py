class MockSMBus:
    BME280_ADDRESS = 0x76
    VEML7700_ADDRESS = 0x10

    def __init__(self, trimming_parameters, block_data):
        self.trimming_parameters = trimming_parameters
        self.block_data = block_data

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
        Read block data from the specified register
        """
        match addr:
            case self.BME280_ADDRESS:
                return self.block_data[:length]
            case self.VEML7700_ADDRESS:
                return self.block_data[reg][:length]
            case _:
                return None
