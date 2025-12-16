import argparse
import signal
import threading
import os
from http.server import ThreadingHTTPServer
from i2c import I2CLCD, I2CDevice, i2c_device_present
from sensors import BME280, VEML7700, SGP40
from db import Database
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
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 to expose on LAN)")
    ap.add_argument("--bus", type=int, default=1, help="I2C bus number")
    ap.add_argument("--mux-addr", default="0x70", help="Multiplexer address")
    ap.add_argument("--bme-addr", default="0x76", help="BME280 I2C address")
    ap.add_argument("--bme-channel", default="5", help="BME280 multiplexer channel")
    ap.add_argument("--veml-addr", default="0x10", help="VEML7700 I2C address")
    ap.add_argument("--veml-channel", default="6", help="VEML7700 multiplexer channel")
    ap.add_argument("--veml-gain", type=float, default=0.25, help="Gain (light sensor sensitivity)")
    ap.add_argument("--veml-integration-ms", type=int, default=100, help="Integration time (light collection time to produce a reading), ms")
    ap.add_argument("--sgp-addr", default="59", help="SPG40 I2C address")
    ap.add_argument("--sgp-channel", default="7", help="SGP40 multiplexer channel")
    ap.add_argument("--lcd-addr", default="0x27", help="LCD display address")
    ap.add_argument("--lcd-channel", default="4", help="LCD multiplexer channel")
    ap.add_argument("--db", default=None, help="optional SQLite path to enable /api/last")
    ap.add_argument("--sample-interval", type=float, default=60.0, help="Sample interval seconds")
    ap.add_argument("--display-interval", type=float, default=5.0, help="Display interval seconds")
    ap.add_argument("--no-lcd", action="store_true", help="Suppress output to the LCD display")
    ap.add_argument("--retention", type=int, default=0, help="Data retention period (minutes)")
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

    # Create the bus and get the MUX address
    bus = SMBus(args.bus)
    mux_addr = int(args.mux_addr, 16) if (args.mux_addr.strip()) else None

    # Create the wrapper to query the BME280
    bme_addr = int(args.bme_addr, 16)
    bme_channel = int(args.bme_channel, 16) if (args.bme_channel.strip()) else None
    bme280 = BME280(bus, bme_addr, mux_addr, bme_channel) if i2c_device_present(bus, bme_addr, mux_addr, bme_channel, False) else None

    # Create the wrapper to query the VEML770
    veml_addr = int(args.veml_addr, 16)
    veml_channel = int(args.veml_channel, 16) if (args.veml_channel.strip()) else None
    i2c_device = I2CDevice(bus, veml_addr, mux_addr, veml_channel, i2c_msg)
    veml7700 = VEML7700(i2c_device, args.veml_gain, args.veml_integration_ms) if i2c_device_present(bus, veml_addr, mux_addr, veml_channel, False) else None

    # Create the wrapper to query the SGP40
    sgp_addr = int(args.sgp_addr, 16)
    sgp_channel = int(args.sgp_channel, 16) if (args.sgp_channel.strip()) else None
    i2c_device = I2CDevice(bus, sgp_addr, mux_addr, sgp_channel, i2c_msg)
    sgp40 = SGP40(i2c_device, VocAlgorithm()) if i2c_device_present(bus, sgp_addr, mux_addr, sgp_channel, True) else None

    # Create the database access wrapper
    database = Database(args.db, args.retention, args.bus, args.bme_addr, args.veml_addr, args.veml_gain, args.veml_integration_ms, args.sgp_addr)
    database.create_database()

    # Create and start the sampler
    sampler = Sampler(bme280, veml7700, database, args.sample_interval, sgp40)
    sampler.start()

    # Create and start the LCD display handler
    if not args.no_lcd:
        lcd_addr = int(args.lcd_addr, 16)
        lcd_channel = int(args.lcd_channel, 16) if (args.lcd_channel.strip()) else None
        if i2c_device_present(bus, lcd_addr, mux_addr, lcd_channel, False):
            lcd = I2CLCD(bus, lcd_addr)
            display = LCDDisplay(lcd, sampler, args.display_interval)
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
