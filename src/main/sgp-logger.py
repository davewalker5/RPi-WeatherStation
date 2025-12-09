import argparse
import signal
import time
import sys
import os
import datetime as dt
from weather import SGP40, Database
from i2c import I2CDevice, i2c_device_present
from smbus2 import SMBus, i2c_msg
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm


STOP = False

def _sig_handler(signum, frame):
    """
    Signal handler to break out of the sensor loop
    """
    global STOP
    STOP = True


def sample_sensors(sensor, database, report_readings):
    """
    Sample the SGP40 sensors, write the results to the database and echo them on the terminal
    """
    sraw, voc_index, voc_label, voc_rating = sensor.read()
    if report_readings:
        # Purge old data
        database.purge()

        # Store and report the reading
        timestamp = database.insert_sgp_row(sraw, voc_index, voc_label, voc_rating)
        print(f"{timestamp}  SRAW: {sraw}  VOC Index: {voc_index}  Assessment: {voc_label}  Rating: {voc_rating}")


def main():
    ap = argparse.ArgumentParser(description="SGP40 to SQLite and Console Logger")
    ap.add_argument("--db", default="weather.db", help="SQLite database path")
    ap.add_argument("--retention", type=int, default=43200, help="Data retention period (minutes)")
    ap.add_argument("--interval", type=int, default=60, help="Sample reporting interval in seconds")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number")
    ap.add_argument("--sgp-addr", default="0x10", help="SGP40 I2C address")
    ap.add_argument("--once", action="store_true", help="Take one reading and exit")
    args = ap.parse_args()

    # Show the argument values
    print()
    print(os.path.basename(__file__).upper())
    print()
    args_dict = vars(args)
    for name, value in args_dict.items():
        print(f"{name} : {value}")
    print()

    # Install signal handlers for graceful stop
    signal.signal(signal.SIGTERM, _sig_handler)

    # Create the wrapper to query the SGP40
    bus = SMBus(args.bus)
    addr = int(args.sgp_addr, 16)
    if not i2c_device_present(bus, addr, True):
        ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        print(f"{ts}  I2C error: No device found at address {args.sgp_addr}", file=sys.stderr)
        bus.close()
        return
    i2c_device = I2CDevice(bus, addr, i2c_msg)
    sensor = SGP40(i2c_device, VocAlgorithm())

    # Create the database access wrapper
    database = Database(args.db, args.retention, args.bus, None, None, None, None, args.sgp_addr)
    database.create_database()

    # If one-shot has been specified, sample the sensor, display the results and exit
    if args.once:
        sample_sensors(sensor, database, True)
        return

    try:
        report_counter = args.interval - 1
        global STOP
        while not STOP:
            
            try:  
                # Take the next readings
                report_counter += 1
                report_readings = report_counter == args.interval
                sample_sensors(sensor, database, report_readings)

                # Reset the counter, if necessary
                if report_readings:
                    report_counter = 0

            except OSError as ex:
                ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
                print(f"{ts}  I2C error: {ex}; retrying in {args.interval}s", file=sys.stderr)

            # Wait for 1 second, which is the sampling interval expected by the Sensiron VOC algorithm
            time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        # Close the bus and purge old data
        bus.close()


if __name__ == "__main__":
    main()