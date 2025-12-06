import argparse
import os
from helpers import BME280InversionHelper, MockSMBus, BME280_TRIMMING_PARAMETERS


def main():
    ap = argparse.ArgumentParser(description="BME280 Test Case Generator")
    ap.add_argument("--temperature", type=float, help="Target temperature (C)")
    ap.add_argument("--pressure", type=float, help="Target pressure (HPa)")
    ap.add_argument("--humidity", type=int, help="Target humidity (%)")
    args = ap.parse_args()

    # Show the argument values
    print()
    print(os.path.basename(__file__).upper())
    print()
    args_dict = vars(args)
    for name, value in args_dict.items():
        print(f"{name} : {value}")
    print()

    bus = MockSMBus(BME280_TRIMMING_PARAMETERS, None, None)
    helper = BME280InversionHelper(bus, None)
    fixture = helper.make_test_fixture(args.temperature, args.pressure, args.humidity, 100, 0.01)

    print(fixture)


if __name__ == "__main__":
    main()
