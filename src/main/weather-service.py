import argparse
import signal
import threading
import os
from http.server import ThreadingHTTPServer
from weather import BME280, Database, RequestHandler, Sampler

stop = None

def _sig_handler(signum, frame):
    """
    Signal handler to signal stop to the handler and HTTP server
    """
    global stop
    stop.set()


def main():
    ap = argparse.ArgumentParser(description="BME280 JSON HTTP server")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 to expose on LAN)")
    ap.add_argument("--bus", type=int, default=1)
    ap.add_argument("--bme-addr", default="0x76")
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
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    # Create the wrapper to query the BME280
    addr = int(args.bme_addr, 16)
    sensor = BME280(bus=args.bus, address=addr)

    # Create the database access wrapper
    database = Database(args.db, args.retention, args.bus, args.bme_addr)
    database.create_database()

    # Create and start the sampler
    sampler = Sampler(sensor, database, args.interval)
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
    finally:
        try:
            sensor.bus.close()
        except Exception:
            pass
        print("Server stopped.")


if __name__ == "__main__":
    main()
