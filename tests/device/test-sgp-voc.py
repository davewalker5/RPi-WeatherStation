import time
from os import environ
import datetime as dt
from smbus2 import SMBus, i2c_msg
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm


def _crc8_sgp40(two_bytes: bytes) -> int:
    """
    CRC-8 for SGP40 (polynomial 0x31, init 0xFF).
    two_bytes must be length 2.
    """
    crc = 0xFF
    for b in two_bytes:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def read_sgp40_sraw(bus: SMBus, addr: int = 0x59) -> int:
    """
    Read one SRAW VOC sample from SGP40.
    Returns the raw value (0..65535) or None on error/CRC failure.
    """
    # 'measure raw' with default 50% RH / 25°C (no real compensation)
    cmd = [
        0x26, 0x0F,        # command
        0x80, 0x00, 0xA2,  # RH = 50%, CRC
        0x66, 0x66, 0x93   # T = 25°C, CRC
    ]

    # Send command
    write = i2c_msg.write(addr, cmd)
    bus.i2c_rdwr(write)

    # Wait for measurement to complete
    time.sleep(0.03)

    # Read 3 bytes: MSB, LSB, CRC
    read = i2c_msg.read(addr, 3)
    bus.i2c_rdwr(read)
    data = bytes(read)  # length 3

    msb, lsb, crc_recv = data
    crc_calc = _crc8_sgp40(data[:2])

    if crc_calc != crc_recv:
        print(f"SGP40 CRC mismatch: got {crc_recv:#04x}, expected {crc_calc:#04x}")
        return None

    raw = (msb << 8) | lsb
    return raw


def classify_voc_index(index: int) -> str:
    if index < 80:
        return "Excellent"
    elif index < 120:
        return "Good"
    elif index < 160:
        return "Moderate"
    elif index < 220:
        return "Unhealthy"
    else:
        return "Very Unhealthy"
    

def main():
    bus_num = int(environ["BUS_NUMBER"])
    addr = int(environ["SGP_ADDR"], 16)

    print(f"Bus = {bus_num}, Address = {addr} (0x{addr:02X})")

    voc_algo = VocAlgorithm()  # official Sensirion VOC index algorithm

    with SMBus(bus_num) as bus:
        while True:
            sraw = read_sgp40_sraw(bus, addr)
            if sraw is None:
                print("Failed to read SGP40 sample (CRC or I2C error)")
                time.sleep(1)
                continue

            voc_index = voc_algo.process(sraw)  # 0–500-ish, 100 = “typical”
            label = classify_voc_index(voc_index)

            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
            print(f"{timestamp}  SRAW: {sraw:5d}  VOC Index: {voc_index:3d}  {label}")
            time.sleep(1)  # algorithm is designed around ~1 Hz updates


if __name__ == "__main__":
    main()
