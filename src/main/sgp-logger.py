import argparse
import signal
import time
import sys
import os
import datetime as dt
from registry import AppSettings, DeviceFactory, DeviceType
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
        # Purge old data and snapshot sizes
        database.purge()
        database.snapshot_sizes()

        # Store and report the reading
        timestamp = database.insert_sgp_row(sraw, voc_index, voc_label, voc_rating)
        print(f"{timestamp}  SRAW: {sraw}  VOC Index: {voc_index}  Assessment: {voc_label}  Rating: {voc_rating}")


def main():
    ap = argparse.ArgumentParser(description="SGP40 to SQLite and Console Logger")
    ap.add_argument("--db", default="weather.db", help="SQLite database path")
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

    # Load the configuration settings and extract the communication properties
    settings = AppSettings(AppSettings.default_settings_file())
    bus = SMBus(settings.settings["bus_number"])
    factory = DeviceFactory(bus, i2c_msg, VocAlgorithm(), settings)
    sensor = factory.create_device(DeviceType.SGP40)
    if not sensor:
        ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        print(f"{ts} Error: SGP40 not detected", file=sys.stderr)
        bus.close()
        return

    # Create the database access wrapper
    database = factory.create_database(args.db)
    database.create_database()

    # If one-shot has been specified, sample the sensor, display the results and exit
    if args.once:
        sample_sensors(sensor, database, True)
        return

    try:
        report_counter = settings.settings["sample_interval"] - 1
        global STOP
        while not STOP:
            
            try:  
                # Take the next readings
                report_counter += 1
                report_readings = report_counter == settings.settings["sample_interval"]
                sample_sensors(sensor, database, report_readings)

                # Reset the counter, if necessary
                if report_readings:
                    report_counter = 0

            except OSError as ex:
                ts = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
                print(f"{ts} Error: {ex}", file=sys.stderr)

            # Wait for 1 second, which is the sampling interval expected by the Sensiron VOC algorithm
            time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        # Close the bus and purge old data
        bus.close()


if __name__ == "__main__":
    main()