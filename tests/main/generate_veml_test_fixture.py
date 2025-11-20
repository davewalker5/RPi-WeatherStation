import argparse
from helpers import VEML7700InversionHelper


def main():
    ap = argparse.ArgumentParser(description="VEML7700 Test Case Generator")
    ap.add_argument("--illuminance", type=float, help="Target illuminance")
    ap.add_argument("--white", type=float, default=None, help="Target raw white value")
    ap.add_argument("--veml-gain", type=float, default=0.25, help="Gain (light sensor sensitivity)")
    ap.add_argument("--veml-integration-ms", type=int, default=100, help="Integration time (light collection time to produce a reading), ms")
    args = ap.parse_args()

    helper = VEML7700InversionHelper(args.veml_gain, args.veml_integration_ms)
    fixture = helper.make_test_fixture(args.illuminance, args.white)

    print(fixture)


if __name__ == "__main__":
    main()
