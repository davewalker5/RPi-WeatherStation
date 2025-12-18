import argparse
import signal
import threading
import os
from http.server import ThreadingHTTPServer
from registry import AppSettings, DeviceFactory, DeviceType
from service import RequestHandler, Sampler
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

    # Load the configuration settings, create the bus and the factory and construct the device wrappers
    settings = AppSettings(AppSettings.default_settings_file())
    bus = SMBus(settings.settings["bus_number"])
    factory = DeviceFactory(bus, i2c_msg, VocAlgorithm(), settings)
    devices = factory.create_all_devices()

    # Create the database access wrapper
    database = factory.create_database(args.db)
    database.create_database()

    # Create and start the sampler
    sample_interval = settings.settings["sample_interval"]
    display_interval = settings.settings["display_interval"]
    sampler = Sampler(devices, database, sample_interval, display_interval)
    sampler.start()

    # Set up the request handler
    RequestHandler.sampler = sampler

    # Create the server
    hostname = settings.settings["hostname"]
    port = settings.settings["port"]
    print(f"Starting the server on http://{hostname}:{port}")
    server = ThreadingHTTPServer((hostname, port), RequestHandler)
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
