import time
from os import environ, getenv
import datetime as dt
from sensors import SGP40
from smbus2 import SMBus, i2c_msg
from i2c import I2CDevice
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm


def main():
    bus = SMBus(int(environ["BUS_NUMBER"]))
    addr = int(environ["SGP_ADDR"], 16)
    mux_addr = int(mux_addr, 16) if (mux_addr:= getenv("MUX_ADDR", "").strip()) else None
    channel = int(channel) if (channel:= getenv("SGP_CHANNEL", "").strip()) else None
    i2c_device = I2CDevice(bus, addr, mux_addr, channel, i2c_msg)
    sensor = SGP40(i2c_device, VocAlgorithm() )

    try:
        while True:
            sraw, voc_index, voc_label, voc_rating = sensor.read()
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
            print(f"{timestamp}  SRAW: {sraw}  VOC Index: {voc_index}  Assessment: {voc_label}  Rating: {voc_rating}")
            time.sleep(1.0)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
