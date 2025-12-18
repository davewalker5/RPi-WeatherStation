class MockSMBus:
    BME280_ADDRESS = 0x76
    VEML7700_ADDRESS = 0x10
    SGP40_ADDRESS = 0x59

    def __init__(self, trimming_parameters, block_data, queue_data):
        # BME280 trimming parameters
        self.trimming_parameters = trimming_parameters
        # Block data for simulating BME280 and VEML7700 reads
        self.block_data = block_data
        # Queue data for simulating I2C read messages
        self.queue_data = [bytes(queue_data)] if queue_data else []
        self.i2c_messages = []

    # --- Mocks for MUX channel selection -------------------------

    def write_byte(self, addr, byte):
        pass

    def read_byte(self, addr):
        return None

    # --- Mocks for the BME280 / VEML7700 -------------------------

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
        Read block data
        """
        match addr:
            case self.BME280_ADDRESS:
                # Flat sequence of bytes - just "read" the specified number of bytes
                return self.block_data[:length]
            case self.VEML7700_ADDRESS:
                # Per-register mapping - return the specified number of bytes for the register
                return self.block_data[reg][:length]
            case _:
                return None

    # --- Mocks for the SGP40 -------------------------------------

    def write_quick(self, addr):
        pass

    def i2c_rdwr(self, *msgs):
        """
        Record I2C transactions. For reads, use the queue data to satisfy the transaction
        """
        # Store the messages
        self.i2c_messages.append(msgs)

        # Satisfy read transactions
        read_messages = [m for m in msgs if isinstance(m, dict) and m["type"] == "read"]
        for m in read_messages:
            # If the queue data's empty, break out
            if not self.queue_data:
                break

            # Set the message buffer to the next entry in the queue data
            m["buffer"] = self.queue_data.pop(0)
