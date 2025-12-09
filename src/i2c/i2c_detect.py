def i2c_device_present(bus, addr, use_write_quick) -> bool:
    """
    Return True if a device at `addr` ACKs on the I2C bus, False otherwise
    """
    try:
        if use_write_quick:
            # Perform a quick transaction to see if the device is there 
            bus.write_quick(addr)
        else:
            # Read and discard one byte
            _ = bus.read_byte(addr)
        return True
    except OSError as e:
        # Remote I/O error = no ACK from a device at that address
        if e.errno == 121:
            return False

        # Unexpected error -> re-raise
        raise
