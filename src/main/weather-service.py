import argparse
import signal
import threading
import os
from http.server import ThreadingHTTPServer
from i2c import I2CLCD
from weather import BME280, Database, RequestHandler, Sampler, VEML7700, LCDDisplay
from smbus2 import SMBus


stop = None

def _sig_handler(signum, frame):
    """
    Signal handler to signal stop to the handler and HTTP server
    """
    global stop
    stop.set()


def main():
    ap = argparse.ArgumentParser(description="Raspberry Pi Weather Service")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 to expose on LAN)")
    ap.add_argument("--bus", type=int, default=1, help="I2C bus number")
    ap.add_argument("--bme-addr", default="0x76", help="BME280 I2C address")
    ap.add_argument("--veml-addr", default="0x10", help="VEML7700 I2C address")
    ap.add_argument("--veml-gain", type=float, default=0.25, help="Gain (light sensor sensitivity)")
    ap.add_argument("--veml-integration-ms", type=int, default=100, help="Integration time (light collection time to produce a reading), ms")
    ap.add_argument("--lcd-addr", default="0x27", help="LCD display address")
    ap.add_argument("--db", default=None, help="optional SQLite path to enable /api/last")
    ap.add_argument("--interval", type=float, default=60.0, help="Sample interval seconds")
    ap.add_argument("--retention", type=int, default=43200, help="Data retention period (minutes)")
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

    # Create the wrapper to query the BME280
    bus = SMBus(args.bus)
    bme_addr = int(args.bme_addr, 16)
    bme280 = BME280(bus, bme_addr)

    # Create the wrapper to query the VEML770
    addr = int(args.veml_addr, 16)
    veml7700 = VEML7700(bus, addr, args.veml_gain, args.veml_integration_ms)

    # Create the database access wrapper
    database = Database(args.db, args.retention, args.bus, args.bme_addr, args.veml_addr, args.veml_gain, args.veml_integration_ms)
    database.create_database()

    # Create and start the sampler
    sampler = Sampler(bme280, veml7700, database, args.interval)
    sampler.start()

    # Create and start the LCD display handler
    lcd_addr = int(args.lcd_addr, 16)
    lcd = I2CLCD(bus, lcd_addr)
    display = LCDDisplay(lcd, sampler, args.interval)
    display.start()

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
