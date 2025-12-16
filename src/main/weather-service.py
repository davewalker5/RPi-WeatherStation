import argparse
import signal
import threading
import os
from http.server import ThreadingHTTPServer
from registry import AppSettings, DeviceFactory, DeviceType
from service import RequestHandler, Sampler, LCDDisplay
from smbus2 import SMBus, i2c_msg
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm


stop = None

def _sig_handler(signum, frame):
    """
    Signal handler to signal stop to the handler and HTTP server
    """
    global stop
    stop.set()


def main():
    ap = argparse.ArgumentParser(description="Raspberry Pi Weather Service")
    ap.add_argument("--db", default=None, help="optional SQLite path to enable /api/last")
    ap.add_argument("--no-lcd", action="store_true", help="Suppress output to the LCD display")
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

    # Load the configuration settings, create the bus and the factory and construct the sensor wrappers
    settings = AppSettings(AppSettings.default_settings_file())
    bus = SMBus(settings.settings["bus_number"])
    factory = DeviceFactory(bus, i2c_msg, VocAlgorithm(), settings)
    bme280 = factory.create_device(DeviceType.SGP40)
    veml7700 = factory.create_device(DeviceType.VEML7700)
    sgp40 = factory.create_device(DeviceType.SGP40)

    # Create the LCD display wrapper
    if not args.no_lcd:
        lcd = factory.create_device(DeviceType.LCD)
        if lcd:
            display = LCDDisplay(lcd)

    # Create the database access wrapper
    database = factory.create_database(args.db)
    database.create_database()

    # Create and start the sampler
    sampler = Sampler(bme280, veml7700, sgp40, display, database, args.sample_interval, args.display_interval)
    sampler.start()

    # Set up the request handler
    RequestHandler.sampler = sampler

    # Create the server
    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    global stop
    stop = threading.Event()

    # Enter the request handling loop
    try:
        while not stop.is_set():
            server.handle_request()
    except KeyboardInterrupt:
        stop.set()
    finally:
        bus.close()


if __name__ == "__main__":
    main()
