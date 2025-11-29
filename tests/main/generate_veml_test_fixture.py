import argparse
import os
from helpers import VEML7700InversionHelper

def stepped_range(x, y, steps):
    step = (y - x) / steps
    for i in range(steps + 1):
        yield x + i * step


def main():
    ap = argparse.ArgumentParser(description="VEML7700 Test Case Generator")
    ap.add_argument("--illuminance", type=float, default=None, help="Target illuminance")
    ap.add_argument("--veml-gain", type=float, default=0.25, help="Gain (light sensor sensitivity)")
    ap.add_argument("--veml-integration-ms", type=int, default=100, help="Integration time (light collection time to produce a reading), ms")
    args = ap.parse_args()

    # Show the argument values
    print()
    print(os.path.basename(__file__).upper())
    print()
    args_dict = vars(args)
    for name, value in args_dict.items():
        print(f"{name} : {value}")
    print()

    # Create the helper
    helper = VEML7700InversionHelper(args.veml_gain, args.veml_integration_ms)
    print(f"Maximum lux with the specified gain and IT is {helper.max_lux}")

    fixtures = []
    if args.illuminance is not None:
        # If illuminance is specfied, generate one test fixture for that illuminance
        fixtures.append(helper.make_test_fixture(args.illuminance, None))
    else:
        # Generate a range of test cases up to a little below maximum lux
        maximum_lux = int(helper.max_lux * 0.9)
        for lux in stepped_range(0, maximum_lux, 10):
            fixtures.append(helper.make_test_fixture(lux, None))

        # Generate a saturation test
        fixtures.append(helper.make_test_fixture(helper.max_lux * 1.2, None))

    # Dump the fixtures
    for fixture in fixtures:
        print(fixture)


if __name__ == "__main__":
    main()
