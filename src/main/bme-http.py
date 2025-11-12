import argparse
import signal
from http.server import ThreadingHTTPServer
from weather import BME280, Database, RequestHandler


STOP = False

def _sig_handler(signum, frame):
    """
    Signal handler to break out of the request handler loop
    """
    global STOP
    STOP = True


def main():
    ap = argparse.ArgumentParser(description="BME280 JSON HTTP server")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 to expose on LAN)")
    ap.add_argument("--bus", type=int, default=1)
    ap.add_argument("--addr", default="0x76")
    ap.add_argument("--db", default=None, help="optional SQLite path to enable /api/last")
    args = ap.parse_args()

    # Install signal handlers for graceful stop
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    # Create the wrapper to query the BME280
    addr = int(args.addr, 16)
    sensor = BME280(bus=args.bus, address=addr)

    # Create the database access wrapper
    database = Database(args.bus, args.addr, args.db)
    database.create_database()

    # Set up the request handler
    RequestHandler.sensor = sensor
    RequestHandler.database = database

    # Create the server
    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"BME280 is on bus {args.bus} at address {hex(addr)}")
    print(f"Serving on http://{args.host}:{args.port}")
    print("Ctrl-C to stop")

    # Enter the request handling loop
    try:
        while not STOP:
            server.handle_request()
    finally:
        try:
            sensor.bus.close()
        except Exception:
            pass
        print("Server stopped.")


if __name__ == "__main__":
    main()
