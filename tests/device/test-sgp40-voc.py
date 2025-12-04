import time
from smbus2 import SMBus
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm
from os import environ

bus_num = int(environ["BUS_NUMBER"])
addr = int(environ["LCD_ADDR"], 16)

MEASURE_CMD = [0x26, 0x0F]  # "measure raw" command, no humidity compensation


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


def read_sgp40_raw(bus: SMBus) -> int:
    # Trigger measurement wan wait for ~30 ms
    bus.write_i2c_block_data(addr, MEASURE_CMD[0], [MEASURE_CMD[1]])
    time.sleep(0.03)

    # Read 3 bytes: 2 data + 1 CRC (we ignore CRC here for brevity)
    data = bus.read_i2c_block_data(addr, 0, 3)
    raw = (data[0] << 8) | data[1]
    return raw


def main():
    # Sensirion’s official VOC index algorithm
    voc_algo = VocAlgorithm()

    with SMBus(bus_num) as bus:
        while True:
            sraw_voc = read_sgp40_raw(bus)
            voc_index = voc_algo.process(sraw_voc)  # 0–500-ish, 100 = “typical”

            label = classify_voc_index(voc_index)
            print(f"SRAW: {sraw_voc:5d} | VOC Index: {voc_index:3d} | {label}")

            # The algorithm assumes ~1s sampling intervals
            time.sleep(1)


if __name__ == "__main__":
    main()
