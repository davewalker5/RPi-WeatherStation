import time
from os import environ
import datetime as dt
from weather import SGP40
from smbus2 import SMBus, i2c_msg
from i2c import I2CDevice
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm


def main():
    bus = SMBus(int(environ["BUS_NUMBER"]))
    addr = int(environ["SGP40_ADDR"], 16)
    i2c_device = I2CDevice(bus, addr, i2c_msg)
    sensor = SGP40(i2c_device, VocAlgorithm() )

    try:
        while True:
            result = sensor.read()
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
            print(f"{timestamp}  SRAW: {result['sraw']}  VOC Index: {result['voc_index']}   {result['voc_label']}")
            time.sleep(1.0)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
