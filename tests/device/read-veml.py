import argparse
import os
import datetime as dt
from sensors import VEML7700
from smbus2 import SMBus


def main():
    ap = argparse.ArgumentParser(description="VEML770 Sensor Check")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number")
    ap.add_argument("--veml-addr", default="10", help="VEML7700 I2C address")
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

    # Create the VEML7700 wrapper
    bus = SMBus(args.bus)
    addr = int(args.veml_addr, 16)
    sensor = VEML7700(bus, addr, args.veml_gain, args.veml_integration_ms)
    
    # Read the sensors
    als, white, lux = sensor.read()
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
    print(f"{timestamp}  Gain={sensor.gain}  Integration Time={sensor.integration_time_ms} ms  ALS={als}  White={white}  Illuminance={lux:.2f} lux")


if __name__ == "__main__":
    main()
