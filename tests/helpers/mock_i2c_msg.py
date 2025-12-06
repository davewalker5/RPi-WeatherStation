class MockI2CMsg:
    def __init__(self):
        pass

    def write(self, address, bytes):
        """
        Construct an I2C message to write a set of bytes targetting the specified address. The return
        is a conception of what would really be constructed, not an actual i2c message
        """
        return {
            "type": "write",
            "address": address,
            "buffer": bytes
        }

    def read(self, address, length):
        """
        Construct an I2C message to read a set of bytes from the specified address. The return
        is a conception of what would really be constructed, not an actual i2c message
        """
        return {
            "type": "read",
            "address": address,
            "buffer": bytes(length)
        }
