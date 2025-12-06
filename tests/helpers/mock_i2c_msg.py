class MockI2CMsg:
    def __init__(self):
        pass

    class _message(dict):
        """
        Mock I2C message object constructed so that bytes(o) gives the bytes written/read
        """
        def __bytes__(self):
            buf = self.get("buffer", b"")
            return bytes(buf)

    def write(self, address, data):
        return self._message(
            type="write",
            address=address,
            buffer=bytes(data),
        )

    def read(self, address, length):
        return self._message(
            type="read",
            address=address,
            buffer=bytes(length),
        )