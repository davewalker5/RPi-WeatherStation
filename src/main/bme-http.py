import argparse
import signal
from http.server import ThreadingHTTPServer
from weather import BME280, create_database, insert_row, RequestHandler


STOP = None


def main():
    global cur

    ap = argparse.ArgumentParser(description="BME280 JSON HTTP server")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 to expose on LAN)")
    ap.add_argument("--bus", type=int, default=1)
    ap.add_argument("--addr", default="0x76")
    ap.add_argument("--db", default=None, help="optional SQLite path to enable /api/last")
    ap.add_argument("--table", default="readings", help="Table name to insert into")
    args = ap.parse_args()

    addr_hex = int(args.addr, 16)
    sensor = BME280(bus=args.bus, address=addr_hex)

    create_database(args.db)

    def _stop(signum, frame):
        global STOP; STOP = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    RequestHandler.sensor = sensor
    RequestHandler.db_path = args.db
    RequestHandler.db_table = args.table
    RequestHandler.bus = args.bus
    RequestHandler.addr = args.addr

    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"Serving on http://{args.host}:{args.port}  (bus={args.bus} addr={hex(addr_hex)})")
    if args.db:
        print(f"/api/last reads from: {args.db}")
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
