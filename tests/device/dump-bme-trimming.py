import argparse
import os
from helpers.bme280_inversion_helper import BME280InversionHelper
from smbus2 import SMBus


def main():
    ap = argparse.ArgumentParser(description="BME280 Trimming Parameter Dump")
    ap.add_argument("--bus", type=int, default=1, help="I2C bus number")
    ap.add_argument("--bme-addr", default="0x76", help="BME280 I2C address")
    args = ap.parse_args()

    # Show the argument values
    print()
    print(os.path.basename(__file__).upper())
    print()
    args_dict = vars(args)
    for name, value in args_dict.items():
        print(f"{name} : {value}")
    print()

    # Create the wrapper to query the BME280
    bus = SMBus(args.bus)
    helper = BME280InversionHelper(bus)

    # Dump the parameters
    address = int(args.bme_addr, 16)
    helper.dump_bme280_trimming_parameters(address)
